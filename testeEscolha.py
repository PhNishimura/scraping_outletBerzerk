import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# --- CONFIGURAÇÕES ---
TOKEN = "8128120473:AAHCSbpVVR8FRsLnt82OuWqJnEepQHmZ8Eg"
URL_BASE = 'https://berzerk.com.br'
URL_BUSCA = URL_BASE + '/search?q={termo_busca}'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- FUNÇÃO DE SCRAPING (VERSÃO ATUALIZADA E MAIS ROBUSTA) ---
def buscar_produtos_no_site(termo_busca: str) -> list:
    url_formatada = URL_BUSCA.format(termo_busca=quote(termo_busca))
    logger.info(f"Fazendo scraping em: {url_formatada}")
    try:
        pagina = requests.get(url_formatada, headers={'User-Agent': 'Mozilla/5.0'})
        pagina.raise_for_status()
        dados_pagina = BeautifulSoup(pagina.text, 'html.parser')

        # --- PONTO DA MUDANÇA ---
        # Suspeita 1: Os produtos são itens de uma lista em um grid.
        # Usamos .select() que é mais flexível para seletores CSS.
        produtos_encontrados = dados_pagina.select('li.grid__item')
        
        # Se a suspeita 1 falhar, o log abaixo nos avisará.
        if not produtos_encontrados:
             logger.warning(f"Nenhum produto encontrado com o seletor 'li.grid__item'. Verifique o HTML da página de busca.")
             return [] # Retorna vazio para o bot poder avisar o usuário.

        logger.info(f"Encontrados {len(produtos_encontrados)} contêineres de produto. Processando...")

        resultados = []
        for item_container in produtos_encontrados:
            # Agora, procuramos os dados DENTRO de cada 'item_container'
            link_tag = item_container.find('a', href=True)
            # Na página de busca, o nome do produto costuma estar dentro de um link com a classe 'full-unstyled-link'
            nome_tag = item_container.find('a', class_='full-unstyled-link')
            preco_tag = item_container.find('span', class_='price-item--regular') # O preço também pode ter outra classe aqui

            if not all([link_tag, nome_tag, preco_tag]):
                logger.warning("Um item foi pulado por não ter link, nome ou preço.")
                continue

            link_completo = URL_BASE + link_tag['href']
            # O nome agora é pego diretamente do texto do link do título
            nome = nome_tag.text.strip()
            preco_texto = preco_tag.text.strip()

            resultados.append({'nome': nome, 'preco': preco_texto, 'link': link_completo})
        
        return resultados
    except Exception as e:
        logger.error(f"Erro no scraping para o termo '{termo_busca}': {e}", exc_info=True)
        return []

# --- NOVA FUNÇÃO AUXILIAR PARA APRESENTAR RESULTADOS ---
async def apresentar_resultados(update_or_query, context: ContextTypes.DEFAULT_TYPE, resultados: list):
    """Pega uma lista de produtos e os apresenta como botões."""
    context.user_data['search_results'] = resultados
    keyboard = []
    for index, produto in enumerate(resultados):
        # Adicionamos o prefixo 'produto:' para diferenciar os cliques
        botao = InlineKeyboardButton(produto['nome'], callback_data=f"produto:{index}")
        keyboard.append([botao])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Descobre se deve enviar uma nova mensagem ou editar uma existente
    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_text('✅ Encontrei estes produtos. Escolha um:', reply_markup=reply_markup)
    else: # É um objeto 'query', então editamos a mensagem anterior
        await update_or_query.edit_message_text('✅ Encontrei estes produtos. Escolha um:', reply_markup=reply_markup)


# --- FUNÇÕES DO BOT (HANDLERS) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Olá! Bem-vindo ao Buscador Berzerk.\n\n'
        'Use o comando /buscar para ver sugestões ou /buscar <termo> para pesquisar diretamente.'
    )

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lida com o comando /buscar, agora com lógica de sugestões."""
    # Se o usuário digitou algo DEPOIS de /buscar
    if context.args:
        termo_busca = ' '.join(context.args)
        await update.message.reply_text(f'🔎 Buscando por "{termo_busca}"... Aguarde.')
        resultados = buscar_produtos_no_site(termo_busca)
        if not resultados:
            await update.message.reply_text(f'😕 Nenhum resultado encontrado para "{termo_busca}".')
        else:
            await apresentar_resultados(update, context, resultados)
    # Se o usuário digitou APENAS /buscar
    else:
        sugestoes = ['Oversized', 'Regata', 'Moletom', 'Acessórios']
        keyboard = []
        for sugestao in sugestoes:
            # Adicionamos o prefixo 'sugestao:'
            botao = InlineKeyboardButton(sugestao, callback_data=f"sugestao:{sugestao}")
            keyboard.append([botao])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('O que você gostaria de ver?', reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Função ÚNICA para lidar com TODOS os cliques de botão."""
    query = update.callback_query
    await query.answer()
    
    # Separa o prefixo e o valor do callback_data
    prefixo, valor = query.data.split(':', 1)

    # Se o botão clicado foi uma SUGESTÃO de busca
    if prefixo == 'sugestao':
        termo_busca = valor
        await query.edit_message_text(f'🔎 Buscando por "{termo_busca}"... Aguarde.')
        resultados = buscar_produtos_no_site(termo_busca)
        if not resultados:
            await query.edit_message_text(f'😕 Nenhum resultado encontrado para "{termo_busca}".')
        else:
            # Passamos 'query' em vez de 'update' para a função poder editar a mensagem
            await apresentar_resultados(query, context, resultados)
            
    # Se o botão clicado foi um PRODUTO da lista de resultados
    elif prefixo == 'produto':
        product_index = int(valor)
        resultados = context.user_data.get('search_results')
        if not resultados or product_index >= len(resultados):
            await query.message.reply_text("😕 Erro. Por favor, faça a busca novamente.")
            return
        
        produto_selecionado = resultados[product_index]
        mensagem = (
            f"👕 *{produto_selecionado['nome']}*\n\n"
            f"💰 *Preço:* {produto_selecionado['preco']}\n\n"
            f"🔗 [Clique aqui para ver o produto no site]({produto_selecionado['link']})"
        )
        await query.message.reply_text(mensagem, parse_mode="Markdown")

# --- FUNÇÃO PRINCIPAL QUE RODA O BOT (sem alteração) ---
def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buscar", buscar))
    application.add_handler(CallbackQueryHandler(button_click))
    print("🚀 Bot com sugestões iniciado! Pressione Ctrl+C para parar.")
    application.run_polling()

if __name__ == '__main__':
    if "SEU_BOT_TOKEN_AQUI" in TOKEN:
        print("!!! ATENÇÃO: PREENCHA SEU BOT_TOKEN NO CÓDIGO!!!")
    else:
        main()