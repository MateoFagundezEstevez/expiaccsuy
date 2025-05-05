import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Cargar archivos CSV
@st.cache
def cargar_datos():
    mercados_df = pd.read_csv('mercados.csv')
    afinidad_df = pd.read_csv('afinidad_producto_país.csv')
    return mercados_df, afinidad_df

mercados_df, afinidad_df = cargar_datos()

# Interfaz de usuario para seleccionar el producto
st.title("Recomendador de Mercados de Exportación")
producto = st.selectbox("Selecciona un producto para exportar", afinidad_df['Producto'].unique())

# Función para calcular afinidad
def calcular_afinidad(producto, mercados_df, afinidad_df):
    afinidad_producto = afinidad_df[afinidad_df['Producto'] == producto]
    mercados_afinidad = pd.merge(mercados_df, afinidad_producto, on="País", how="left")
    
    # Calcular afinidad ponderada (simplificado)
    mercados_afinidad['Afinidad'] = (
        0.2 * mercados_afinidad['PIB per cápita (USD)'] +
        0.2 * mercados_afinidad['Tamaño del Mercado Total (Millones USD)'] +
        0.2 * mercados_afinidad['Logística (LPI 2023)'] +
        0.2 * mercados_afinidad['Crecimiento Importaciones (%)'] +
        0.1 * mercados_afinidad['Distancia a Uruguay (km)']
    )
    
    # Ordenar por afinidad
    mercados_afinidad = mercados_afinidad.sort_values(by='Afinidad', ascending=False)
    return mercados_afinidad

# Calcular mercados recomendados
mercados_recomendados = calcular_afinidad(producto, mercados_df, afinidad_df)

# Mostrar los mercados recomendados
st.subheader("Mercados recomendados")
st.dataframe(mercados_recomendados[['País', 'Afinidad', 'PIB per cápita (USD)', 'Tamaño del Mercado Total (Millones USD)', 'Logística (LPI 2023)', 'Crecimiento Importaciones (%)']])

# Visualización en mapa interactivo con Plotly
st.subheader("Mapa interactivo de mercados recomendados")
fig = px.scatter_geo(mercados_recomendados,
                     locations="País",
                     size="Afinidad",
                     hover_name="País",
                     size_max=100,
                     template="plotly", 
                     projection="natural earth",
                     title=f"Mercados recomendados para el producto: {producto}")

st.plotly_chart(fig)

# Filtros adicionales
st.sidebar.header("Filtros adicionales")
poblacion_min = st.sidebar.slider("Población mínima (millones)", min_value=0, max_value=mercados_df['Población'].max(), value=0)
mercados_recomendados_filtrados = mercados_recomendados[mercados_recomendados['Población'] >= poblacion_min]

# Mostrar los mercados filtrados
st.subheader(f"Mercados recomendados (Población >= {poblacion_min} millones)")
st.dataframe(mercados_recomendados_filtrados[['País', 'Afinidad', 'PIB per cápita (USD)', 'Población', 'Tamaño del Mercado Total (Millones USD)', 'Logística (LPI 2023)']])

# Generación de un reporte descargable
@st.cache
def generar_reporte(mercados_recomendados):
    # Selección de las columnas relevantes para el reporte
    reporte = mercados_recomendados[['País', 'Afinidad', 'PIB per cápita (USD)', 'Tamaño del Mercado Total (Millones USD)', 'Logística (LPI 2023)', 'Crecimiento Importaciones (%)']]
    return reporte

reporte = generar_reporte(mercados_recomendados_filtrados)

# Botón para descargar el reporte
st.subheader("Generar reporte descargable")
csv = reporte.to_csv(index=False)
st.download_button("Descargar reporte", csv, "reporte_mercados_recomendados.csv", "text/csv")

