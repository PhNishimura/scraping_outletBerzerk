
-----

# 🤖 Berzerk Outlet Monitor Bot Scraping 🤖

Eu não queria mais perder as promoções do outlet da loja [Berzerk](https://berzerk.com.br/collections/outlet), portanto fiz esse bot, que faz um scraping da pagina de outlet e me envia uma mensagem no telegram na hora que um produto é postado e se ouve alteração de preço e se o produto é removio. 

✨ Funcionalidades Principais

  - **Notificações Instantâneas:** Recebo alertas no Telegram assim que algo uma promoção é postada.
  - **Detecção de Novos Produtos:** Sou o primeiro a saber quando um novo item entra no outlet.
  - **Alerta de Alteração de Preço:** O bot informa se o preço de um produto aumentou ou diminuiu.
  - **Aviso de Itens Removidos:** Sei quando um produto não está mais disponível na página.
  - **Memória Persistente:** O bot se lembra dos produtos que já viu (usando um arquivo `json`), evitando notificações repetidas.
  - **Agendamento Flexível:** Roda automaticamente em intervalos de tempo definidos.
  - **Seguro e Inteligente:** O script evita apagar sua base de dados se o site da Berzerk estiver fora do ar ou com algum problema.

## 🛠️ Tecnologias Utilizadas

  - [Python](https://www.python.org/)
  - [Requests](https://docs.python-requests.org/en/latest/) - Para fazer as requisições HTTP e buscar o conteúdo da página.
  - [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) - Para extrair as informações (web scraping) do HTML da página.
  - [python-telegram-bot](https://python-telegram-bot.org/) - Para enviar as notificações para o seu canal ou chat no Telegram.
  - [Schedule](https://schedule.readthedocs.io/en/stable/) - Para agendar a execução do monitoramento.

## ⚙️ Configuração e Instalação

Siga estes passos para colocar seu bot para rodar.

### 1\. Pré-requisitos

  - Python 3.6 ou superior instalado.
  - Um Bot no Telegram e suas credenciais. Se não tiver, é fácil:
    1.  Fale com o [@BotFather](https://t.me/BotFather) no Telegram.
    2.  Crie um novo bot com o comando `/newbot`.
    3.  Dê um nome e um username para ele.
    4.  O BotFather te dará um **Token de Acesso (API Token)**. Guarde-o\!
  - O ID do seu chat do Telegram.
    1.  Fale com o [@userinfobot](https://t.me/userinfobot).
    2.  Ele te mostrará seu **Chat ID**.

### 2\. Clonando o Repositório

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

### 3\. Instalando as Dependências

É altamente recomendável usar um ambiente virtual (`venv`) para isolar as dependências do projeto.

```bash
# Crie o ambiente virtual
python -m venv venv

# Ative o ambiente (Windows)
.\venv\Scripts\activate

# Ative o ambiente (Linux/Mac)
source venv/bin/activate

# Instale as bibliotecas necessárias
pip install requests beautifulsoup4 python-telegram-bot schedule
```

### 4\. Configurando suas Credenciais

Abra o arquivo `nome_do_seu_script.py` e edite estas duas linhas com as informações que você pegou no passo 1:

```python
# SEU BOT_TOKEN E CHAT_ID
BOT_TOKEN = "SEU BOT TOKEN AQUI"  # Cole o Token do BotFather aqui
CHAT_ID = "SEU CHAT ID AQUI"        # Cole o seu ID de chat aqui
```

## 🚀 Como Executar

Com tudo configurado, basta iniciar o script a partir do seu terminal:

```bash
python nome_do_seu_script.py
```

Você verá uma mensagem indicando que a primeira verificação foi feita e que o agendamento foi configurado. Agora é só deixar o terminal aberto e esperar a mágica acontecer\! O bot fará as verificações automaticamente a cada 2 a 5 minutos.

## 📂 Estrutura do Projeto

  - **`nome_do_seu_script.py`**: O coração do projeto. Contém toda a lógica de scraping, comparação e notificação.
  - **`produtos_monitorados.json`**: Arquivo criado automaticamente na primeira execução. Ele funciona como a "memória" do bot, armazenando os produtos já encontrados e seus preços. **Não apague este arquivo** a menos que queira resetar o monitoramento.

## 🤝 Contribuições

Contribuições são bem-vindas\! Se você tem alguma ideia para melhorar o bot, sinta-se à vontade para abrir uma *issue* ou enviar um *pull request*.

-----
