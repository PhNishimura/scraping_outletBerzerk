import requests
from bs4 import BeautifulSoup
import re
import telegram
import asyncio
import os # Usaremos o 'os' para verificar se nosso arquivo de "memória" existe

# SEU BOT_TOKEN E CHAT_ID (COLOQUE OS SEUS VALORES REAIS AQUI)
# ATENÇÃO: Nunca compartilhe esses valores publicamente.
BOT_TOKEN = "8128120473:AAHCSbpVVR8FRsLnt82OuWqJnEepQHmZ8Eg" # Ex: "8128120473:AAHCSbpVVR8FRsLnt82OuWqJnEepQHmZ8Eg"
CHAT_ID = "-1002258395718"   # Ex: "-1002258395718"

# URLS DA BERZERK
URL_BASE = 'https://berzerk.com.br'
URL_PAGINA = f'{URL_BASE}/collections/oversized'

# NOME DO ARQUIVO QUE SERVIRÁ DE MEMÓRIA
ARQUIVO_MEMORIA = 'produtos_enviados_berzerk.txt'


# --- FUNÇÕES AUXILIARES (DO SEU CÓDIGO ORIGINAL, POUCAS MUDANÇAS) ---

def escapar_markdown_v2(texto: str) -> str:
    """Prepara o texto para ser enviado via Telegram no modo MarkdownV2."""
    caracteres_reservados = r'([_*\[\]()~`>#+\-=|{}.!])'
    return re.sub(caracteres_reservados, r'\\\1', texto)

def carregar_links_enviados() -> set:
    """Carrega os links do nosso arquivo de memória para um set."""
    if not os.path.exists(ARQUIVO_MEMORIA):
        return set()
    with open(ARQUIVO_MEMORIA, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def salvar_link_enviado(link: str):
    """Salva um novo link no nosso arquivo de memória."""
    with open(ARQUIVO_MEMORIA, 'a', encoding='utf-8') as f:
        f.write(link + '\n')

async def send_telegram_message(bot_token, chat_id, message):
    """Envia a mensagem formatada para o Telegram."""
    try:
        bot = telegram.Bot(token=bot_token)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')
        print(f"✅ Notificação enviada com sucesso para o Telegram!")
    except Exception as e:
        print(f"❌ Falha ao enviar mensagem para o Telegram: {e}")


# --- FUNÇÃO PRINCIPAL (TOTALMENTE ADAPTADA PARA A BERZERK) ---

async def monitorar_berzerk():
    """Função principal que raspa o site da Berzerk e notifica sobre novos produtos."""
    print("🤖 Iniciando monitoramento de novidades na Berzerk...")
    
    links_ja_enviados = carregar_links_enviados()
    print(f"📄 Encontrados {len(links_ja_enviados)} produtos já notificados anteriormente.")

    try:
        # --- Lógica de Scraping que já tínhamos ---
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

        # --- Loop e Lógica de Notificação ---
        for link_completo, info_div in zip(links_unicos, blocos_de_info):
            
            # A MÁGICA ACONTECE AQUI: Pular o produto se o link já foi enviado antes
            if link_completo in links_ja_enviados:
                continue

            # Se chegou aqui, é um produto novo!
            novos_produtos_encontrados += 1
            print(f"🎉 NOVO PRODUTO ENCONTRADO: {link_completo}")

            # Extrair os dados do produto (como já fazíamos)
            nome_tag = info_div.find('span', class_="product-card__title")
            nome = nome_tag.text.strip() if nome_tag else "Nome não encontrado"
            
            preco_tag = info_div.find('sale-price', class_="text-on-sale")
            if preco_tag:
                preco_texto = preco_tag.text.replace("Preço promocional", "").strip()
            else:
                preco_texto = "Preço não encontrado"
            
            # Preparar a mensagem para o Telegram
            nome_escapado = escapar_markdown_v2(nome)
            preco_escapado = escapar_markdown_v2(preco_texto)

            message = (
                f"🚨 *NOVO DROP NA BERZERK* 🚨\n\n"
                f"👕 *Produto*: {nome_escapado}\n"
                f"💰 *Preço*: {preco_escapado}\n\n"
                f"🔗 *Acesse agora mesmo*:\n"
                f"[Clique aqui para ver o produto]({link_completo})"
            )

            # Enviar a notificação e salvar na memória
            await send_telegram_message(BOT_TOKEN, CHAT_ID, message)
            salvar_link_enviado(link_completo)
            
            # Pequena pausa para não sobrecarregar a API do Telegram
            await asyncio.sleep(1)

        if novos_produtos_encontrados == 0:
            print("✅ Nenhum produto novo encontrado desta vez.")
        
        print("🏁 Monitoramento finalizado.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão ao acessar a página da Berzerk: {e}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")


# --- PONTO DE ENTRADA DO SCRIPT ---
if __name__ == "__main__":
    # Verifica se as credenciais foram preenchidas
    if "SEU_BOT_TOKEN_AQUI" in BOT_TOKEN or "SEU_CHAT_ID_AQUI" in CHAT_ID:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! ATENÇÃO: PREENCHA SEU BOT_TOKEN E CHAT_ID NO CÓDIGO!!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        asyncio.run(monitorar_berzerk())