import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Ruta de los archivos CSV ya subidos
afinidad_file_path = "afinidad_producto_país.csv"
mercados_file_path = "mercados.csv"

# Función para cargar los archivos CSV
def load_csv_file(file_path):
    try:
        return pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding='ISO-8859-1')

# Cargar los archivos CSV directamente desde las rutas
afinidad_df = load_csv_file(afinidad_file_path)
mercados_df = load_csv_file(mercados_file_path)

# Verificación de la carga de datos
if afinidad_df is not None:
    st.write("### Datos de 'afinidad_producto_país.csv':")
    st.write(afinidad_df)

if mercados_df is not None:
    st.write("### Datos de 'mercados.csv':")
    st.write(mercados_df)

# Interfaz para seleccionar el producto
producto_seleccionado = st.selectbox('Selecciona un Producto:', afinidad_df['Producto'].unique())

# Filtrar los datos de afinidad por el producto seleccionado
afinidad_producto = afinidad_df[afinidad_df['Producto'] == producto_seleccionado]

# Mostrar la afinidad del producto en diferentes países
st.write(f"### Afinidad del Producto '{producto_seleccionado}' en los países:")
st.write(afinidad_producto[['País', 'Afinidad']])

# Función para recomendar los mejores mercados
def recomendar_mercados(afinidad_producto, mercados_df):
    # Merge para combinar los datos de afinidad y mercado
    df_completo = pd.merge(afinidad_producto[['País', 'Afinidad']], mercados_df, on='País', how='inner')

    # Calcular una puntuación ponderada combinando los índices del mercado
    df_completo['Puntaje'] = (
        0.4 * df_completo['Afinidad'] + # Ponderación para la afinidad
        0.3 * df_completo['Demanda esperada'] + # Ponderación para la demanda
        0.2 * df_completo['Facilidad para hacer negocios'] + # Ponderación para la facilidad para hacer negocios
        0.1 * df_completo['Estabilidad política'] # Ponderación para la estabilidad política
    )

    # Ordenar por la puntuación en orden descendente y seleccionar los 5 mejores mercados
    df_recomendado = df_completo.sort_values(by='Puntaje', ascending=False).head(5)

    # Generar los fundamentos
    recomendaciones = []
    for index, row in df_recomendado.iterrows():
        fundamento = (
            f"**Mercado recomendado: {row['País']}**\n\n"
            f"- **Afinidad del producto con el mercado**: {row['Afinidad']}\n"
            f"- **Demanda esperada**: {row['Demanda esperada']}\n"
            f"- **Facilidad para hacer negocios**: {row['Facilidad para hacer negocios']}\n"
            f"- **Beneficios arancelarios**: {row['Beneficios arancelarios']}\n"
            f"- **Estabilidad política**: {row['Estabilidad política']}\n\n"
            "En base a estos indicadores, se recomienda este mercado debido a su alto nivel de afinidad con el producto seleccionado, su "
            "alta demanda esperada, y sus condiciones favorables para hacer negocios. Además, ofrece beneficios arancelarios competitivos "
            "y una estabilidad política que lo convierte en una opción segura para la exportación."
        )
        recomendaciones.append(fundamento)
    
    return df_recomendado[['País', 'Puntaje']], recomendaciones

# Llamar a la función para obtener las recomendaciones
mercados_recomendados, fundamentos = recomendar_mercados(afinidad_producto, mercados_df)

# Mostrar las recomendaciones de los mejores mercados
st.write(f"### Los 5 mejores mercados de exportación para el Producto '{producto_seleccionado}':")
st.write(mercados_recomendados)

# Mostrar los fundamentos para cada recomendación
st.write(f"### Fundamentos de la recomendación:")
for i, fundamento in enumerate(fundamentos):
    st.write(f"**{i+1}. {mercados_recomendados.iloc[i]['País']}**")
    st.write(fundamento)

