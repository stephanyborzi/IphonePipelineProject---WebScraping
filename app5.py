import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import sqlite3

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

def create_connection(db_name='iphone_prices.db'):
    conn = sqlite3.connect(db_name)
    return conn

def database(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS prices(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   product_name TEXT,
                   old_price INTEGER,
                   new_price INTEGER,
                   installment_price INTEGER,
                   timestamp TEXT)''')
    conn.commit()

def save_to_database(conn, product_info):
    new_row = pd.DataFrame([product_info])
    new_row.to_sql('prices', conn, if_exists='append', index=False)

def get_max_price(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(new_price), timestamp from prices')
    result = cursor.fetchone()
    return result[0], result[1]

if __name__ == '__main__':
    conn = create_connection()
    database(conn)
    
    url = 'https://www.mercadolivre.com.br/apple-iphone-16-pro-1-tb-titnio-preto-distribuidor-autorizado/p/MLB1040287851#polycard_client=search-nordic&wid=MLB5054621110&sid=search&searchVariation=MLB1040287851&position=6&search_layout=stack&type=product&tracking_id=92c2ddf6-f70e-475b-b41e-fe2742459774'
    while True:
        page_content = fetch_page(url)
        product_info = parse_page(page_content)

        max_price, max_timestamp = get_max_price(conn)
        current_price = product_info['new_price']
        if current_price  > max_price:
            print('Preço maior detectado')
            max_price  =  current_price 
            max_price_timestamp = product_info['timestamp']
        else:
            print('O preço máximo registrado é o antigo')

        save_to_database(conn, product_info)
        print('dados salvos no banco de dados', product_info)
        time.sleep(10)
