import requests
from bs4 import BeautifulSoup
import time
import psycopg2
import pandas as pd
import asyncio
from telegram import Bot
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
bot = Bot(token=TOKEN)

def fetch_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    return response.text

def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')

    product_name_tag = soup.find('h1', class_='ui-pdp-title')
    product_name = product_name_tag.get_text() if product_name_tag else "Produto não encontrado"

    prices = soup.find_all('span', class_='andes-money-amount__fraction')

    print("Lista de preços extraída:", [p.get_text() for p in prices])  

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

def create_connection():
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_DB_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT')
    )
    return conn

def database(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS prices(
                   id SERIAL PRIMARY KEY,
                   product_name TEXT,
                   old_price INTEGER,
                   new_price INTEGER,
                   installment_price INTEGER,
                   timestamp TEXT)''')
    conn.commit()

def save_to_database(conn, product_info):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO prices (product_name, old_price, new_price, installment_price, timestamp)
        VALUES (%s, %s, %s, %s, %s)
    ''', (product_info['product_name'], product_info['old_price'], product_info['new_price'], 
          product_info['installment_price'], product_info['timestamp']))
    conn.commit()

def get_max_price(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT new_price, timestamp FROM prices ORDER BY new_price DESC LIMIT 1')
    result = cursor.fetchone()
    cursor.close()
    return result if result else (0, "Nenhum registro")

async def send_telegram_message(text):
    await bot.send_message(chat_id=CHAT_ID, text=text)

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

asyncio.run(main())
