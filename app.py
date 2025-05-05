# Importar las bibliotecas necesarias
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

# Mostrar la tabla con los mercados recomendados
st.subheader(f"🌎 Mercados recomendados para {producto_seleccionado}")
st.dataframe(df_producto[['País', 'Afinidad']])

# Mostrar un gráfico interactivo de los mercados recomendados
fig = px.bar(df_producto, x='País', y='Afinidad', title=f"Afinidad de los mercados para {producto_seleccionado}")
st.plotly_chart(fig)

# Mapa interactivo de la facilidad para hacer negocios
st.subheader("📍 Mapa Interactivo de los Mercados - Facilidad para hacer negocios")

# Asegurarse de que la columna "Facilidad Negocios (WB 2019)" esté en el DataFrame
df_producto_map = mercados_df[mercados_df['País'].isin(df_producto['País'])]

# Verificar que las columnas de latitud y longitud existan
if 'Latitud' in df_producto_map.columns and 'Longitud' in df_producto_map.columns:
    # Crear el mapa usando latitud y longitud
    fig_map = px.scatter_geo(df_producto_map,
                             lat="Latitud",
                             lon="Longitud",
                             size="Facilidad Negocios (WB 2019)",
                             hover_name="País",
                             size_max=100,
                             title=f"Facilidad para hacer negocios en los mercados recomendados para {producto_seleccionado}",
                             color="Facilidad Negocios (WB 2019)",
                             color_continuous_scale="Viridis")
    # Mostrar el mapa interactivo
    st.plotly_chart(fig_map)
else:
    st.error("El archivo de datos no contiene las columnas de Latitud y Longitud necesarias para mostrar el mapa.")

# Botón de recomendación
if st.button('Recomendar mercados'):
    st.markdown("""
    ### Recomendaciones:
    Los siguientes mercados tienen una alta afinidad para el producto seleccionado.
    Los mercados con mayor puntaje de afinidad son los más recomendados.
    """)
    st.write(df_producto[['País', 'Afinidad']].sort_values(by='Afinidad', ascending=False))

# Agregar algún cuadro interactivo (ejemplo con Slider)
st.subheader("🔄 Personaliza tu Recomendación")
slider = st.slider("Ajusta la Afinidad mínima para la recomendación", 0, 100, 50)
mercados_filtrados = df_producto[df_producto['Afinidad'] >= slider]

st.write(f"🛍️ Mercados con afinidad mayor a {slider}:")
st.dataframe(mercados_filtrados[['País', 'Afinidad']])

# Mensaje final
st.markdown("""
Gracias por usar nuestro **Bot de Recomendación de Mercados de Exportación**. 
¡Esperamos que esta herramienta te ayude a tomar decisiones informadas sobre tus exportaciones! 🌍
""")

