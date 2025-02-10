import requests
from bs4 import BeautifulSoup
import time
import sqlite3
import pandas as pd
import asyncio
from telegram import Bot
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
bot = Bot(token=TOKEN)

# Função para buscar página com cabeçalho de user-agent
def fetch_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    return response.text

# Função para extrair informações da página
def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Capturar nome do produto
    product_name_tag = soup.find('h1', class_='ui-pdp-title')
    product_name = product_name_tag.get_text() if product_name_tag else "Produto não encontrado"

    # Capturar preços
    prices = soup.find_all('span', class_='andes-money-amount__fraction')

    print("Lista de preços extraída:", [p.get_text() for p in prices])  # Depuração

    old_price = int(prices[0].get_text().replace('.', '')) if len(prices) > 0 else None
    new_price = int(prices[1].get_text().replace('.', '')) if len(prices) > 1 else None
    installment_price = int(prices[2].get_text().replace('.', '')) if len(prices) > 2 else None

    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    return {
        'product_name': product_name,
        'old_price': old_price,
        'new_price': new_price,
        'installment_price': installment_price,
        'timestamp': timestamp
    }

# Criar conexão com banco de dados
def create_connection(db_name='iphone_prices.db'):
    return sqlite3.connect(db_name)

# Criar tabela no banco de dados
def database(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS prices(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   product_name TEXT,
                   old_price INTEGER NULL,
                   new_price INTEGER NULL,
                   installment_price INTEGER NULL,
                   timestamp TEXT)''')
    conn.commit()

# Salvar dados no banco de dados
def save_to_database(conn, product_info):
    new_row = pd.DataFrame([product_info])
    new_row.to_sql('prices', conn, if_exists='append', index=False)

# Obter maior preço registrado
def get_max_price(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(new_price), timestamp FROM prices')
    result = cursor.fetchone()
    return result if result else (0, "Nenhum registro")

# Enviar notificação no Telegram
async def send_telegram_message(text):
    await bot.send_message(chat_id=CHAT_ID, text=text)

# Loop principal do programa
async def main():
    conn = create_connection()
    database(conn)

    url = 'https://www.mercadolivre.com.br/apple-iphone-16-pro-1-tb-titnio-preto-distribuidor-autorizado/p/MLB1040287851#polycard_client=search-nordic&wid=MLB5054621110&sid=search&searchVariation=MLB1040287851&position=6&search_layout=stack&type=product&tracking_id=92c2ddf6-f70e-475b-b41e-fe2742459774'
    
    while True:
        page_content = fetch_page(url)
        product_info = parse_page(page_content)

        max_price, max_timestamp = get_max_price(conn)
        current_price = product_info['new_price']

        if current_price and current_price > max_price:
            print(f'Preço maior detectado: {current_price}')
            await send_telegram_message(f'Preço maior detectado: {current_price}')
        else:
            print(f'O preço máximo registrado é {max_price} em {max_timestamp}')
            await send_telegram_message(f'O preço máximo registrado é {max_price} em {max_timestamp}')

        save_to_database(conn, product_info)
        print(' Dados salvos no banco de dados:', product_info)

        await asyncio.sleep(10)

    conn.close()

# Executar o programa
asyncio.run(main())
