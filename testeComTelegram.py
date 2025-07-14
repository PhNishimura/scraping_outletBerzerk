import requests
from bs4 import BeautifulSoup
import re
import telegram
import asyncio
import os
import time      # <--- ADICIONADO: Para a pausa no loop
import schedule  # <--- ADICIONADO: A biblioteca de agendamento


# Pega o caminho absoluto do diretório onde o script está
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))


# SEU BOT_TOKEN E CHAT_ID (COLOQUE OS SEUS VALORES REAIS AQUI)
# ATENÇÃO: Nunca compartilhe esses valores publicamente.
BOT_TOKEN = "7864806675:AAEg5rwZ_z2yPUmUkidYbuSPHjSTZb4m_K4"
CHAT_ID = "-1002512544169"

# URLS DA BERZERK
URL_BASE = 'https://berzerk.com.br'
URL_PAGINA = f'{URL_BASE}/collections/outlet'

# NOME DO ARQUIVO QUE SERVIRÁ DE MEMÓRIA
# Une o caminho do diretório com o nome do arquivo
ARQUIVO_MEMORIA = os.path.join(DIRETORIO_ATUAL, 'produtos_enviados_berzerk.txt')


# --- FUNÇÕES AUXILIARES (sem alterações) ---

def escapar_markdown_v2(texto: str) -> str:
    caracteres_reservados = r'([_*\[\]()~`>#+\-=|{}.!])'
    return re.sub(caracteres_reservados, r'\\\1', texto)

def carregar_links_enviados() -> set:
    if not os.path.exists(ARQUIVO_MEMORIA):
        return set()
    with open(ARQUIVO_MEMORIA, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def salvar_link_enviado(link: str):
    with open(ARQUIVO_MEMORIA, 'a', encoding='utf-8') as f:
        f.write(link + '\n')

async def send_telegram_message(bot_token, chat_id, message):
    try:
        bot = telegram.Bot(token=bot_token)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')
        print(f"✅ Notificação enviada com sucesso para o Telegram!")
    except Exception as e:
        print(f"❌ Falha ao enviar mensagem para o Telegram: {e}")


# --- FUNÇÃO PRINCIPAL (sem alterações na lógica interna) ---

async def monitorar_berzerk():
    print("🤖 Iniciando monitoramento de novidades na Berzerk...")
    
    links_ja_enviados = carregar_links_enviados()
    print(f"📄 Encontrados {len(links_ja_enviados)} produtos já notificados anteriormente.")

    try:
        pagina = requests.get(URL_PAGINA, headers={'User-Agent': 'Mozilla/5.0'})
        pagina.raise_for_status()
        dados_pagina = BeautifulSoup(pagina.text, 'html.parser')

        tags_de_link = dados_pagina.select('a[href*="/products/"]')
        blocos_de_info = dados_pagina.find_all('div', class_="v-stack gap-0.5 w-full justify-items-center")

        links_unicos = []
        links_vistos = set()
        for tag in tags_de_link:
            href = tag['href']
            if href not in links_vistos:
                links_unicos.append(URL_BASE + href)
                links_vistos.add(href)
        
        if not links_unicos or not blocos_de_info:
            print("⚠️ Não foi possível encontrar produtos na página. Verifique o site.")
            return

        print(f"🔎 Encontrados {len(links_unicos)} produtos na página. Verificando novidades...")
        novos_produtos_encontrados = 0

        for link_completo, info_div in zip(links_unicos, blocos_de_info):
            
            if link_completo in links_ja_enviados:
                continue

            novos_produtos_encontrados += 1
            print(f"🎉 NOVO PRODUTO ENCONTRADO: {link_completo}")

            nome_tag = info_div.find('span', class_="product-card__title")
            nome = nome_tag.text.strip() if nome_tag else "Nome não encontrado"
            
            preco_tag = info_div.find('sale-price', class_="text-on-sale")
            if preco_tag:
                preco_texto = preco_tag.text.replace("Preço promocional", "").strip()
            else:
                preco_texto = "Preço não encontrado"
            
            nome_escapado = escapar_markdown_v2(nome)
            preco_escapado = escapar_markdown_v2(preco_texto)

            message = (
                f"🚨 *NOVO DROP NA BERZERK* 🚨\n\n"
                f"👕 *Produto*: {nome_escapado}\n"
                f"💰 *Preço*: {preco_escapado}\n\n"
                f"🔗 *Acesse agora mesmo*:\n"
                f"[Clique aqui para ver o produto]({link_completo})"
            )

            await send_telegram_message(BOT_TOKEN, CHAT_ID, message)
            salvar_link_enviado(link_completo)
            
            await asyncio.sleep(1)

        if novos_produtos_encontrados == 0:
            print("✅ Nenhum produto novo encontrado desta vez.")
        
        print("🏁 Monitoramento finalizado.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão ao acessar a página da Berzerk: {e}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")


# --- PONTO DE ENTRADA E AGENDAMENTO (PRINCIPAIS MUDANÇAS AQUI) ---

def executar_tarefa():
    """
    Função que "empacota" a chamada assíncrona para ser usada pelo agendador.
    """
    print("\n----------------------------------------------------")
    print(f"[{time.ctime()}] Acionando a verificação agendada...")
    try:
        asyncio.run(monitorar_berzerk())
    except Exception as e:
        print(f"❌ Erro ao executar a tarefa assíncrona: {e}")
    print("----------------------------------------------------\n")


if __name__ == "__main__":
    if "7864806675:AAEg5rwZ_z2yPUmUkidYbuSPHjSTZb4m_K4" in BOT_TOKEN or "-1002512544169" in CHAT_ID:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! ATENÇÃO: PREENCHA SEU BOT_TOKEN E CHAT_ID NO CÓDIGO!!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        # 1. Agendar a tarefa para rodar a cada 6 horas
        schedule.every(6).hours.do(executar_tarefa)
        
        print("✅ Agendamento configurado! O script irá rodar a cada 6 horas.")
        print("🚀 Executando a primeira verificação imediatamente...")
        
        # Executa a tarefa uma vez logo no início
        executar_tarefa()

        # 2. Loop infinito para manter o script rodando e verificando o agendamento
        while True:
            schedule.run_pending() # Verifica se há alguma tarefa agendada para rodar
            time.sleep(1)          # Pausa por 1 segundo para não consumir CPU desnecessariamente