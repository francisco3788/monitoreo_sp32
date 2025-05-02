import os
import time
import requests
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
import pytz

# Cargar variables de entorno
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# CONFIGURACIÓN THINGSPEAK
CHANNEL_ID = '2936695'
API_KEY = 'SGHMO66Y8C0QHDN0'
FETCH_URL = f'https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={API_KEY}&results=1'

# Crear tabla si no existe
def inicializar_bd():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS datos (
            id SERIAL PRIMARY KEY,
            timestamp TEXT UNIQUE,
            field1 REAL,
            field2 REAL,
            field3 REAL,
            field4 REAL,
            field5 REAL,
            field6 REAL
        )
    ''')
    conn.commit()
    conn.close()

# Obtener datos desde ThingSpeak y convertir hora a Colombia
def obtener_dato():
    try:
        res = requests.get(FETCH_URL)
        if res.text.strip() == "-1":
            print("❌ Error: API Key inválida o canal privado sin permiso de lectura.")
            return (None,) * 7

        data = res.json()
        print("✅ Respuesta de ThingSpeak:", data)

        if 'feeds' in data and data['feeds']:
            feed = data['feeds'][0]

            # Convertir hora UTC a hora de Colombia
            utc_time = feed.get('created_at')
            if utc_time:
                utc_dt = datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
                colombia_time = utc_dt.astimezone(pytz.timezone('America/Bogota'))
                timestamp_colombia = colombia_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp_colombia = None

            return (
                timestamp_colombia,
                feed.get('field1'),
                feed.get('field2'),
                feed.get('field3'),
                feed.get('field4'),
                feed.get('field5'),
                feed.get('field6'),
            )
        else:
            print("⚠️ No hay datos disponibles en feeds.")
            return (None,) * 7
    except Exception as e:
        print(f"❌ Error al obtener datos: {e}")
        return (None,) * 7

# Guardar si es nuevo
def guardar_dato(datos):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT * FROM datos WHERE timestamp = %s", (datos[0],))
    if not cur.fetchone():
        cur.execute('''
            INSERT INTO datos (timestamp, field1, field2, field3, field4, field5, field6)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', datos)
        conn.commit()
        print("✅ Dato guardado:", datos)
    else:
        print("ℹ️ Dato ya existente:", datos[0])
    conn.close()

# Loop principal
def correr():
    inicializar_bd()
    while True:
        datos = obtener_dato()
        if datos[0] and datos[1]:
            guardar_dato(datos)
        time.sleep(10)

if __name__ == '__main__':
    correr()
