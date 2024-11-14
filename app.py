from flask import Flask, render_template
from pymongo import MongoClient
import os
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd

app = Flask(__name__)

# Cargar la URI de MongoDB desde las variables de entorno
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['graficos']  # Nombre de la base de datos 'graficos'
collection = db['graficos']  # Nombre de la colección 'graficas'

@app.route('/')
def grafico_linea():
    # Obtener los datos de MongoDB y crear el DataFrame
    datos = list(collection.find())
    df = pd.DataFrame(datos)

    # Imprimir las columnas para verificar si los campos existen
    print(df.columns)

    # Verificar si los campos 'VIGENCIADESDE' y 'VALOR' están presentes
    if 'VIGENCIADESDE' in df.columns and 'VALOR' in df.columns:
        # Convierte 'VIGENCIADESDE' a formato datetime, manejando errores en el formato
        df['fecha'] = pd.to_datetime(df['VIGENCIADESDE'], format='%d/%m/%Y', errors='coerce')

        # Asegúrate de que no haya valores nulos en 'fecha' después de la conversión
        df = df.dropna(subset=['fecha'])

        # Renombramos la columna 'VALOR' a 'valor' para compatibilidad
        df['valor'] = df['VALOR']
    else:
        return "Los campos 'VIGENCIADESDE' o 'VALOR' no existen en los datos."

    # Crear el gráfico de línea
    plt.figure(figsize=(10, 6))
    plt.plot(df['fecha'], df['valor'], color='blue', marker='o', linestyle='-')
    plt.xlabel('Fecha')
    plt.ylabel('Valor (COP)')
    plt.title('Suma de Valores por Fecha')
    plt.xticks(rotation=45)

    # Convertir el gráfico a imagen en base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    grafico_linea_url = base64.b64encode(img.getvalue()).decode()

    return render_template('index.html', grafico_linea=grafico_linea_url)

if __name__ == '__main__':
    app.run(debug=True)
