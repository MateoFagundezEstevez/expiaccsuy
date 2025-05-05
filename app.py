import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Cargar los archivos CSV con los datos
mercados_df = pd.read_csv('mercados.csv')
afinidad_df = pd.read_csv('afinidad_producto_país.csv')

# Título e imagen
st.image('logo_ccsuy.png', width=200)  # Logo de la Cámara de Comercio y Servicios
st.title("🌍 Bot de Recomendación de Mercados de Exportación")

# Descripción
st.markdown("""
Bienvenido al **Bot de Recomendación de Mercados de Exportación**. 
Este bot le ayudará a encontrar los mercados más adecuados para exportar sus productos, basándose en una serie de indicadores clave de cada país. 
Seleccione un producto y vea los mercados recomendados. 🚀
""")

# Selección de Producto
productos = afinidad_df['Producto'].unique()
producto_seleccionado = st.selectbox("🔍 Elija un Producto", productos)

# Filtrar los datos según el producto seleccionado
df_producto = afinidad_df[afinidad_df['Producto'] == producto_seleccionado]

# Agregar el filtro de mercados latinoamericanos primero
latam_mercados = df_producto[df_producto['País'].isin(['Argentina', 'Brasil', 'México', 'Chile', 'Perú', 'Colombia', 'Ecuador', 'Venezuela', 'Bolivia', 'Paraguay', 'Cuba'])]
otros_mercados = df_producto[~df_producto['País'].isin(['Argentina', 'Brasil', 'México', 'Chile', 'Perú', 'Colombia', 'Ecuador', 'Venezuela', 'Bolivia', 'Paraguay', 'Cuba'])]

# Mostrar los primeros 5 mercados latinoamericanos
st.subheader(f"🌎 Principales 5 mercados recomendados en Latinoamérica para {producto_seleccionado}")
st.dataframe(latam_mercados.head(5)[['País', 'Afinidad', 'Tamaño del Mercado Total (Millones USD)', 'Crecimiento Anual PIB (%)', 'Crecimiento Importaciones (%)', 'Facilidad Negocios (WB 2019)', 'Logística (LPI 2023)', 'Distancia a Uruguay (km)']])

# Mostrar los demás mercados después de los primeros 5 latinoamericanos
st.subheader(f"🌍 Otros mercados recomendados para {producto_seleccionado}")
st.dataframe(otros_mercados[['País', 'Afinidad', 'Tamaño del Mercado Total (Millones USD)', 'Crecimiento Anual PIB (%)', 'Crecimiento Importaciones (%)', 'Facilidad Negocios (WB 2019)', 'Logística (LPI 2023)', 'Distancia a Uruguay (km)']])

# Mostrar un gráfico interactivo de los mercados recomendados
fig = px.bar(df_producto, x='País', y='Afinidad', title=f"Afinidad de los mercados para {producto_seleccionado}")
st.plotly_chart(fig)

# Mostrar un mapa interactivo de los países recomendados
st.subheader("📍 Mapa Interactivo de los Mercados")
fig_map = px.scatter_geo(df_producto, locations="País", size="Afinidad", hover_name="País", size_max=50, title=f"Mercados recomendados para {producto_seleccionado}")
st.plotly_chart(fig_map)

# Cuadro de recomendación con afinidad ajustable
st.subheader("🔄 Personaliza tu Recomendación")
slider = st.slider("Ajusta la Afinidad mínima para la recomendación", 0, 100, 50)
mercados_filtrados = df_producto[df_producto['Afinidad'] >= slider]

st.write(f"🛍️ Mercados con afinidad mayor a {slider}:")
st.dataframe(mercados_filtrados[['País', 'Afinidad', 'Tamaño del Mercado Total (Millones USD)', 'Crecimiento Anual PIB (%)', 'Crecimiento Importaciones (%)', 'Facilidad Negocios (WB 2019)', 'Logística (LPI 2023)', 'Distancia a Uruguay (km)']])

# Mensaje final
st.markdown("""
Gracias por usar nuestro **Bot de Recomendación de Mercados de Exportación**. 
¡Esperamos que esta herramienta te ayude a tomar decisiones informadas sobre tus exportaciones! 🌍
""")
