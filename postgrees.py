import requests
from bs4 import BeautifulSoup
import time
import psycopg2
from psycopg2 import sql
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
    response = requests.get(url)
    return response.text

def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    product_name = soup.find('h1', class_='ui-pdp-title').get_text()
    prices = soup.find_all('span', class_='andes-money-amount__fraction')
    old_price = int(prices[0].get_text().replace('.', ''))
    new_price = int(prices[1].get_text().replace('.', ''))
    installment_price = int(prices[2].get_text().replace('.', ''))
    
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
        dbname='iphonepricing',
        user='postgres',
        password='Ste@14725369',
        host='localhost',
        port='5432'
    )
    return conn

def database(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices(
            id SERIAL PRIMARY KEY,
            product_name TEXT,
            old_price INTEGER,
            new_price INTEGER,
            installment_price INTEGER,
            timestamp TIMESTAMP
        )
    ''')
    conn.commit()

def save_to_database(conn, product_info):
    cursor = conn.cursor()
    cursor.execute(
        sql.SQL('''
            INSERT INTO prices (product_name, old_price, new_price, installment_price, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        '''), 
        (product_info['product_name'], product_info['old_price'], product_info['new_price'], 
         product_info['installment_price'], product_info['timestamp'])
    )
    conn.commit()

def get_max_price(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(new_price), MAX(timestamp) FROM prices')
    result = cursor.fetchone()
    max_price = result[0] if result[0] is not None else 0
    return max_price, result[1]

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
        
        if current_price > max_price:
            print(f'Preço maior detectado: {current_price}')
            await send_telegram_message(f'Preço maior detectado: {current_price}')
            max_price = current_price
            max_price_timestamp = product_info['timestamp']
        else:
            print(f'O preço máximo registrado é o {max_price} em {max_timestamp}')
            await send_telegram_message(f'O preço máximo registrado é o {max_price} em {max_timestamp}')
        
        save_to_database(conn, product_info)
        print('dados salvos no banco de dados', product_info)
        await asyncio.sleep(10)
        
    conn.close()
    
asyncio.run(main())


