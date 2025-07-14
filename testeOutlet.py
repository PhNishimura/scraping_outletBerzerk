import requests
from bs4 import BeautifulSoup


# URL base do site, para montagem dos links
URL_BASE = 'https://berzerk.com.br'
URL_PAGINA = f'{URL_BASE}/collections/outlet'

try:
    pagina = requests.get(URL_PAGINA)
    pagina.raise_for_status()

    dados_pagina = BeautifulSoup(pagina.text, 'html.parser')

    # CAPTURAR TODOS OS LINKS ---
    
    # Usamos um seletor CSS para encontrar tags <a> cujo href contenha "/products/"
    # Isso nos dá todos os links que apontam para uma página de produto.
    tags_de_link = dados_pagina.select('a[href*="/products/"]')
    
    # O seletor pode pegar links duplicados (ex: na imagem e no título).
    # Vamos filtrar para ter uma lista de links únicos e na ordem correta.
    links_unicos = []
    links_vistos = set() # Usamos um set para registrar os links que já vimos
    for tag in tags_de_link:
        href = tag['href']
        if href not in links_vistos:
            links_unicos.append(URL_BASE + href)
            links_vistos.add(href)
            
    # CAPTURAR TODOS OS BLOCOS DE INFO ---
    
    # Usamos sua descoberta original, que é nosso ponto de referência confiável.
    blocos_de_info = dados_pagina.find_all('div', class_="v-stack gap-0.5 w-full justify-items-center")

    # --- VERIFICAÇÃO ---
    if not blocos_de_info or not links_unicos:
        print("Não foi possível encontrar os links ou os blocos de informação. A estrutura do site mudou.")
        print(f"Links encontrados: {len(links_unicos)}")
        print(f"Infos encontradas: {len(blocos_de_info)}")

    print("--- ROUPAS OVERSIZED NA BERZERK (Estratégia Final) ---")

    # COMBINAR AS LISTAS COM ZIP ---
    
    # A função zip() junta as duas listas, permitindo iterar por elas ao mesmo tempo.
    # Ex: Pega o link[0] e o info[0], depois link[1] e info[1], e assim por diante.
    for link, info_div in zip(links_unicos, blocos_de_info):
        
        # O link já temos da nossa primeira lista!
        link_completo = link
        
        # Agora extraimos o nome e preço de dentro do bloco de info
        nome_tag = info_div.find('span', class_="product-card__title")
        nome = nome_tag.text.strip() if nome_tag else "Nome não encontrado"
        
        preco_tag = info_div.find('sale-price', class_="text-on-sale")
        if preco_tag:
            texto_completo_preco = preco_tag.text.replace("Preço promocional", "")
            preco_final = texto_completo_preco.strip()
        else:
            preco_final = "Preço não encontrado"

        print("\n") 
        print(f"Modelo: {nome}")
        print(f"Preço: {preco_final}")
        print(f"Link: {link_completo}")
        print("---------------------------------")

except requests.exceptions.RequestException as e:
    print(f"Ocorreu um erro ao tentar acessar a página: {e}")