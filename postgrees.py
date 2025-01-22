import aiohttp
import asyncio
from bs4 import BeautifulSoup
import time
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
bot = Bot(token=TOKEN)

async def fetch_page(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    product_name = soup.find('h1', class_='ui-pdp-title').get_text()
    
    # Find all price elements
    prices = soup.find_all('span', class_='andes-money-amount__fraction')
    
    # Check that prices contain the expected number of elements
    if len(prices) < 3:
        print("Error: Not enough price elements found.")
        return None

    try:
        old_price = int(prices[0].get_text().replace('.', ''))
        new_price = int(prices[1].get_text().replace('.', ''))
        installment_price = int(prices[2].get_text().replace('.', ''))
    except (IndexError, ValueError) as e:
        print(f"Error processing price data: {e}")
        return None
    
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    return {
        'product_name': product_name,
        'old_price': old_price,
        'new_price': new_price,
        'installment_price': installment_price,
        'timestamp': timestamp
    }

def create_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_DB_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT')
        )
        print("Database connection established.")
        return conn
    except Exception as e:
        print(f"Error: Unable to connect to the database. {e}")
        return None

def database(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS prices(
        id SERIAL PRIMARY KEY,
        product_name TEXT,
        old_price INTEGER,
        new_price INTEGER,
        installment_price INTEGER,
        timestamp TIMESTAMP
    )''')
    conn.commit()

def save_to_database(conn, product_info):
    cursor = conn.cursor()
    cursor.execute(
        sql.SQL('''INSERT INTO prices (product_name, old_price, new_price, installment_price, timestamp)
            VALUES (%s, %s, %s, %s, %s)'''),
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
    if conn is None:
        print("Falha ao conectar ao banco de dados.")
        return
    
    database(conn)
    
    url = 'https://www.mercadolivre.com.br/apple-iphone-16-pro-1-tb-titnio-preto-distribuidor-autorizado/p/MLB1040287851#polycard_client=search-nordic&wid=MLB5054621110&sid=search&searchVariation=MLB1040287851&position=6&search_layout=stack&type=product&tracking_id=92c2ddf6-f70e-475b-b41e-fe2742459774'
    while True:
        page_content = await fetch_page(url)
        product_info = parse_page(page_content)
        
        if product_info is None:
            print("Erro ao processar as informações do produto.")
            await asyncio.sleep(10)
            continue
        
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
