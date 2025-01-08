import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import asyncio
from telegram import Bot
import os
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Telegram Bot
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Impressões de Depuração
print(f"TOKEN: {TOKEN}")
print(f"CHAT_ID: {CHAT_ID}")

bot = Bot(token=TOKEN)

# Configurações do banco de dados PostgreSQL
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_DB_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')

# Impressões de Depuração
print(f"POSTGRES_DB: {POSTGRES_DB}")
print(f"POSTGRES_USER: {POSTGRES_USER}")
print(f"POSTGRES_PASSWORD: {POSTGRES_PASSWORD}")
print(f"POSTGRES_HOST: {POSTGRES_HOST}")
print(f"POSTGRES_PORT: {POSTGRES_PORT}")

# Criar a URL de conexão com o banco de dados
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(DATABASE_URL)

def test_database_connection():
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT
        )
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return False

# Teste de conexão com o banco de dados
if test_database_connection():
    print("Conexão com o banco de dados PostgreSQL bem-sucedida!")
    bot.send_message(chat_id=CHAT_ID, text="Conexão com o banco de dados PostgreSQL bem-sucedida!")
else:
    print("Falha na conexão com o banco de dados PostgreSQL.")
    bot.send_message(chat_id=CHAT_ID, text="Falha na conexão com o banco de dados PostgreSQL.")

# Continue com o restante do código aqui...
