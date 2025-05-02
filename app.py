import os
import psycopg2
import pandas as pd
from flask import Flask, render_template, request, send_file
from dotenv import load_dotenv
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# =========================
# 🔎 Consulta con filtrado
# =========================
def consultar_datos(fecha_inicio=None, fecha_fin=None):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    if fecha_inicio and fecha_fin:
        # Normalizar formato (datetime-local) → ISO sin segundos
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%dT%H:%M').isoformat()
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%dT%H:%M').isoformat()
        except Exception as e:
            print("❌ Error al convertir fechas:", e)
            fecha_inicio = fecha_fin = None

    if fecha_inicio and fecha_fin:
        cur.execute("""
            SELECT * FROM datos
            WHERE timestamp BETWEEN %s AND %s
            ORDER BY timestamp ASC
        """, (fecha_inicio, fecha_fin))
    else:
        cur.execute("SELECT * FROM datos ORDER BY timestamp ASC")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    df = pd.DataFrame(rows, columns=columns)
    conn.close()
    return df

# =========================
# 🌐 Página principal
# =========================
@app.route('/', methods=['GET', 'POST'])
def index():
    datos = None
    if request.method == 'POST':
        inicio = request.form['inicio']
        fin = request.form['fin']
        datos = consultar_datos(inicio, fin).to_dict(orient='records')
    return render_template('index.html', datos=datos)

# =========================
# 📥 Exportar por rango
# =========================
@app.route('/exportar', methods=['POST'])
def exportar():
    inicio = request.form['inicio']
    fin = request.form['fin']
    df = consultar_datos(inicio, fin)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name="datos_filtrados.xlsx", as_attachment=True)

# =========================
# 📥 Exportar todo
# =========================
@app.route('/exportar_todo')
def exportar_todo():
    df = consultar_datos()
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name="todos_los_datos.xlsx", as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)