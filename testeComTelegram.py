import requests
from bs4 import BeautifulSoup
import re
import telegram
import asyncio
import os
import time
import schedule
import json # ### NOVO ###: Biblioteca para manipular arquivos JSON

# Pega o caminho absoluto do diretório onde o script está
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))

# SEU BOT_TOKEN E CHAT_ID
BOT_TOKEN = "7864806675:AAEg5rwZ_z2yPUmUkidYbuSPHjSTZb4m_K4"
CHAT_ID = "-1002512544169"

# URLS DA BERZERK
URL_BASE = 'https://berzerk.com.br'
URL_PAGINA = f'{URL_BASE}/collections/outlet'

# ### ALTERAÇÃO ###: Nome do arquivo de memória agora é .json
ARQUIVO_MEMORIA_JSON = os.path.join(DIRETORIO_ATUAL, 'produtos_monitorados.json')

# --- FUNÇÕES AUXILIARES ---

def escapar_markdown_v2(texto: str) -> str:
    caracteres_reservados = r'([_*\[\]()~`>#+\-=|{}.!])'
    return re.sub(caracteres_reservados, r'\\\1', texto)

# ### ALTERAÇÃO ###: Função para carregar dados do arquivo JSON
def carregar_dados_salvos() -> dict:
    """Carrega os dados dos produtos do arquivo JSON e retorna um dicionário."""
    if not os.path.exists(ARQUIVO_MEMORIA_JSON):
        return {}
    try:
        with open(ARQUIVO_MEMORIA_JSON, 'r', encoding='utf-8') as f:
            lista_produtos = json.load(f)
            # Transforma a lista de produtos em um dicionário para busca rápida pelo link
            return {produto['link']: produto for produto in lista_produtos}
    except (json.JSONDecodeError, IOError):
        # Se o arquivo estiver corrompido ou vazio, começa do zero
        return {}

# ### NOVO ###: Função para salvar todos os produtos no arquivo JSON
def salvar_dados_produtos(dados_produtos: dict):
    """Salva o dicionário de produtos de volta em uma lista no arquivo JSON."""
    with open(ARQUIVO_MEMORIA_JSON, 'w', encoding='utf-8') as f:
        # Converte os valores do dicionário (que são os dados do produto) em uma lista
        lista_para_salvar = list(dados_produtos.values())
        json.dump(lista_para_salvar, f, indent=4, ensure_ascii=False)

async def send_telegram_message(bot_token, chat_id, message):
    try:
        bot = telegram.Bot(token=bot_token)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')
        print(f"✅ Notificação enviada com sucesso para o Telegram!")
    except Exception as e:
        print(f"❌ Falha ao enviar mensagem para o Telegram: {e}")

# --- FUNÇÃO PRINCIPAL (COM A NOVA LÓGICA) ---

async def monitorar_berzerk():
    print("🤖 Iniciando monitoramento de produtos e preços na Berzerk...")
    
    dados_salvos = carregar_dados_salvos()
    print(f"📄 Encontrados {len(dados_salvos)} produtos na memória JSON.")

    # Dicionário para guardar os dados atuais dos produtos para salvar no final
    dados_produtos_atuais = dados_salvos.copy()
    notificacoes_enviadas = 0

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

        print(f"🔎 Encontrados {len(links_unicos)} produtos na página. Verificando novidades e alterações...")

        for link_completo, info_div in zip(links_unicos, blocos_de_info):
            nome_tag = info_div.find('span', class_="product-card__title")
            nome = nome_tag.text.strip() if nome_tag else "Nome não encontrado"
            
            preco_tag = info_div.find('sale-price', class_="text-on-sale")
            preco_atual_texto = "Preço não encontrado"
            if preco_tag:
                preco_atual_texto = preco_tag.text.replace("Preço promocional", "").strip()

            # Prepara os dados do produto atual para comparações e para salvar
            info_produto_atual = {'link': link_completo, 'nome': nome, 'preco': preco_atual_texto}

            ### ### ALTERAÇÃO CENTRAL DA LÓGICA ### ###

            # Cenário 1: O produto é NOVO
            if link_completo not in dados_salvos:
                print(f"🎉 NOVO PRODUTO ENCONTRADO: {nome}")
                notificacoes_enviadas += 1
                
                message = (
                    f"🚨 *NOVO DROP NA BERZERK* 🚨\n\n"
                    f"👕 *Produto*: {escapar_markdown_v2(nome)}\n"
                    f"💰 *Preço*: {escapar_markdown_v2(preco_atual_texto)}\n\n"
                    f"🔗 *Acesse agora mesmo*:\n"
                    f"[Clique aqui para ver o produto]({link_completo})"
                )
                await send_telegram_message(BOT_TOKEN, CHAT_ID, message)
                dados_produtos_atuais[link_completo] = info_produto_atual
            
            # Cenário 2: O produto JÁ EXISTE, verificar alteração de preço
            else:
                preco_salvo = dados_salvos[link_completo].get('preco', 'Preço não salvo')
                if preco_atual_texto != preco_salvo and preco_atual_texto != "Preço não encontrado":
                    print(f"💰 ALTERAÇÃO DE PREÇO: {nome}")
                    notificacoes_enviadas += 1
                    
                    message = (
                        f"💸 *ALTERAÇÃO DE PREÇO DETECTADA* 💸\n\n"
                        f"👕 *Produto*: {escapar_markdown_v2(nome)}\n"
                        f"📉 *Preço Antigo*: {escapar_markdown_v2(preco_salvo)}\n"
                        f"📈 *Preço Novo*: {escapar_markdown_v2(preco_atual_texto)}\n\n"
                        f"🔗 *Acesse agora mesmo*:\n"
                        f"[Clique aqui para ver o produto]({link_completo})"
                    )
                    await send_telegram_message(BOT_TOKEN, CHAT_ID, message)
                    dados_produtos_atuais[link_completo] = info_produto_atual
            
            await asyncio.sleep(1) # Pausa entre as verificações para não sobrecarregar

        # Cenário 3: Não houve nenhuma notificação (nem novo, nem alteração)
        if notificacoes_enviadas == 0:
            print("✅ Nenhuma novidade ou alteração de preço encontrada.")
            mensagem_sem_novidades = "✅ Nenhuma nova promoção ou alteração de preço encontrada no outlet da Berzerk desta vez\\."
            await send_telegram_message(BOT_TOKEN, CHAT_ID, mensagem_sem_novidades)

        # Salva o estado mais recente de todos os produtos encontrados na página
        salvar_dados_produtos(dados_produtos_atuais)
        print(f"💾 Dados de {len(dados_produtos_atuais)} produtos foram salvos no JSON.")
        
        print("🏁 Monitoramento finalizado.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão ao acessar a página da Berzerk: {e}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")
        # Em caso de erro, é mais seguro não sobrescrever o arquivo de memória
        print("❗️ O arquivo JSON não foi modificado devido ao erro.")


# --- PONTO DE ENTRADA E AGENDAMENTO (Sem alterações aqui) ---

def executar_tarefa():
    print("\n----------------------------------------------------")
    print(f"[{time.ctime()}] Acionando a verificação agendada...")
    try:
        asyncio.run(monitorar_berzerk())
    except Exception as e:
        print(f"❌ Erro ao executar a tarefa assíncrona: {e}")
    print("----------------------------------------------------\n")

if __name__ == "__main__":
    if "7864806675:AAEg5rwZ_z2yPUmUkidYbuSPHjSTZb4m_K4" in BOT_TOKEN or "-1002512544169" in CHAT_ID:

        schedule.every(6).hours.do(executar_tarefa)
        
        print("✅ Agendamento configurado! O script irá rodar a cada 6 hours.")
        print("🚀 Executando a primeira verificação imediatamente...")
        
        executar_tarefa()

        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! ATENÇÃO: PREENCHA SEU BOT_TOKEN E CHAT_ID NO CÓDIGO!!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
