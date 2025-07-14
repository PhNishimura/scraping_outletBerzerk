import requests
from bs4 import BeautifulSoup
import re
import telegram
import asyncio
import os
import time
import schedule
import json

# Pega o caminho absoluto do diretório onde o script está
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))

# SEU BOT_TOKEN E CHAT_ID
BOT_TOKEN = "7864806675:AAEg5rwZ_z2yPUmUkidYbuSPHjSTZb4m_K4"
CHAT_ID = "-1002512544169"

# URLS DA BERZERK
URL_BASE = 'https://berzerk.com.br'
URL_PAGINA = f'{URL_BASE}/collections/outlet'

ARQUIVO_MEMORIA_JSON = os.path.join(DIRETORIO_ATUAL, 'produtos_monitorados.json')

# --- FUNÇÕES AUXILIARES (sem alterações) ---

def escapar_markdown_v2(texto: str) -> str:
    caracteres_reservados = r'([_*\[\]()~`>#+\-=|{}.!])'
    return re.sub(caracteres_reservados, r'\\\1', texto)

def carregar_dados_salvos() -> dict:
    if not os.path.exists(ARQUIVO_MEMORIA_JSON):
        return {}
    try:
        with open(ARQUIVO_MEMORIA_JSON, 'r', encoding='utf-8') as f:
            lista_produtos = json.load(f)
            return {produto['link']: produto for produto in lista_produtos}
    except (json.JSONDecodeError, IOError):
        return {}

def salvar_dados_produtos(dados_produtos: dict):
    with open(ARQUIVO_MEMORIA_JSON, 'w', encoding='utf-8') as f:
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
    print("🤖 Iniciando monitoramento silencioso na Berzerk...")
    
    dados_salvos = carregar_dados_salvos()
    print(f"📄 Encontrados {len(dados_salvos)} produtos na memória JSON.")

    try:
        pagina = requests.get(URL_PAGINA, headers={'User-Agent': 'Mozilla/5.0'})
        pagina.raise_for_status()
        dados_pagina = BeautifulSoup(pagina.text, 'html.parser')

        # ### ALTERAÇÃO ###: Dicionário para guardar apenas os produtos encontrados NESTA rodada.
        # Isso é crucial para detectar os removidos.
        dados_produtos_na_pagina = {}

        blocos_de_info = dados_pagina.find_all('div', class_="v-stack gap-0.5 w-full justify-items-center")
        
        # Se não encontrar nenhum bloco de produto, encerra para evitar apagar a memória por um erro do site.
        if not blocos_de_info:
            print("⚠️ Não foi possível encontrar blocos de produtos na página. Verificação abortada para proteger a memória.")
            return

        print(f"🔎 Encontrados {len(blocos_de_info)} produtos na página. Verificando...")

        # --- Loop 1: Detectar produtos novos e alterações de preço ---
        for info_div in blocos_de_info:
            link_tag = info_div.find('a', href=re.compile(r'/products/'))
            if not link_tag:
                continue
            
            link_completo = URL_BASE + link_tag['href']
            
            nome_tag = info_div.find('span', class_="product-card__title")
            nome = nome_tag.text.strip() if nome_tag else "Nome não encontrado"
            
            preco_tag = info_div.find('sale-price', class_="text-on-sale")
            preco_atual_texto = "Preço não encontrado"
            if preco_tag:
                preco_atual_texto = preco_tag.text.replace("Preço promocional", "").strip()

            info_produto_atual = {'link': link_completo, 'nome': nome, 'preco': preco_atual_texto}
            dados_produtos_na_pagina[link_completo] = info_produto_atual

            # Cenário 1: O produto é NOVO
            if link_completo not in dados_salvos:
                print(f"🎉 NOVO PRODUTO ENCONTRADO: {nome}")
                message = (
                    f"🚨 *NOVO DROP NA BERZERK* 🚨\n\n"
                    f"👕 *Produto*: {escapar_markdown_v2(nome)}\n"
                    f"💰 *Preço*: {escapar_markdown_v2(preco_atual_texto)}\n\n"
                    f"🔗 *Acesse agora mesmo*:\n"
                    f"[{escapar_markdown_v2('Clique aqui para ver o produto')}]({link_completo})"
                )
                await send_telegram_message(BOT_TOKEN, CHAT_ID, message)
            
            # Cenário 2: O produto JÁ EXISTE, verificar alteração de preço
            else:
                preco_salvo = dados_salvos[link_completo].get('preco', 'Preço não salvo')
                if preco_atual_texto != preco_salvo and preco_atual_texto != "Preço não encontrado":
                    print(f"💰 ALTERAÇÃO DE PREÇO: {nome}")
                    message = (
                        f"💸 *ALTERAÇÃO DE PREÇO DETECTADA* 💸\n\n"
                        f"👕 *Produto*: {escapar_markdown_v2(nome)}\n"
                        f"📉 *Preço Antigo*: {escapar_markdown_v2(preco_salvo)}\n"
                        f"📈 *Preço Novo*: {escapar_markdown_v2(preco_atual_texto)}\n\n"
                        f"🔗 *Acesse agora mesmo*:\n"
                        f"[{escapar_markdown_v2('Clique aqui para ver o produto')}]({link_completo})"
                    )
                    await send_telegram_message(BOT_TOKEN, CHAT_ID, message)
            
            await asyncio.sleep(1)

        # ### NOVO BLOCO ###: Detectar produtos que foram REMOVIDOS ---
        links_salvos_set = set(dados_salvos.keys())
        links_atuais_set = set(dados_produtos_na_pagina.keys())
        
        links_removidos = links_salvos_set - links_atuais_set

        if links_removidos:
            print(f"🗑️ Encontrados {len(links_removidos)} produtos removidos/esgotados.")
            for link_removido in links_removidos:
                produto_removido = dados_salvos[link_removido]
                nome_removido = produto_removido.get('nome', 'Nome não disponível')
                
                message = (
                    f"❌ *PRODUTO REMOVIDO OU ESGOTADO* ❌\n\n"
                    f"👕 *Produto*: {escapar_markdown_v2(nome_removido)}\n\n"
                    f"Este item não está mais listado na página de outlet\\."
                )
                await send_telegram_message(BOT_TOKEN, CHAT_ID, message)
                await asyncio.sleep(1)

        # ### REMOVIDO ###: Bloco que enviava mensagem quando não havia novidades foi removido.

        # Salva o estado mais recente de todos os produtos ENCONTRADOS NA PÁGINA
        salvar_dados_produtos(dados_produtos_na_pagina)
        print(f"💾 Dados de {len(dados_produtos_na_pagina)} produtos foram salvos no JSON.")
        
        print("🏁 Monitoramento finalizado.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão ao acessar a página: {e}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")
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
    # Inverti a lógica para ser mais segura. O código só roda se as credenciais estiverem preenchidas.
    if "7864806675:AAEg5rwZ_z2yPUmUkidYbuSPHjSTZb4m_K4" in BOT_TOKEN or "-1002512544169" in CHAT_ID:

        
        schedule.every(2).to(5).minutes.do(executar_tarefa)

        print("✅ Agendamento configurado! O script irá rodar em intervalos de 2 a 5 minutos.")
        print("🚀 Executando a primeira verificação imediatamente...")
        
        executar_tarefa()

        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! ATENÇÃO: PREENCHA SEU BOT_TOKEN E CHAT_ID NO CÓDIGO!!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
