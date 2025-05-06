import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Cargar los archivos CSV
mercados_df = pd.read_csv('mercados.csv')
afinidad_df = pd.read_csv('afinidad_producto_país.csv')
acuerdos_df = pd.read_csv('acuerdos_comerciales.csv')

# Unir la columna "Acuerdo Comercial" al DataFrame de afinidad
df_merged = pd.merge(afinidad_df, acuerdos_df[['País', 'Acuerdo Comercial']], on='País', how='left')

# Estilo CSS personalizado
st.markdown("""
    <style>
        .logo-container { text-align: center; }
        .logo-container img { width: 400px; }
        .section-title { color: #003B5C; font-size: 24px; font-weight: bold; }
        .section-description { color: #9E2A2F; font-size: 16px; }
        .section { background-color: #E8F4F9; padding: 15px; margin-bottom: 20px; border-radius: 10px; }
        .expander-title { font-size: 20px; color: #003B5C; }
        .expander-content { font-size: 14px; color: #4A4A4A; }
        .button { background-color: #9E2A2F; color: white; padding: 10px 20px; font-size: 16px; border-radius: 5px; }
        .button:hover { background-color: #C84B53; }
    </style>
""", unsafe_allow_html=True)

# Mostrar logo
from PIL import Image
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    logo = Image.open("logo_ccsuy.png")
    st.image(logo, width=400)

# Título y descripción
st.title("\U0001F30D Bot de Recomendación de Mercados de Exportación")

with st.expander("\U0001F4C4 Ver Instrucciones", expanded=False):
    try:
        with open("README.md", "r", encoding="utf-8") as file:
            readme_content = file.read()
        st.markdown(f'<div class="expander-content">{readme_content}</div>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("El archivo README.md no se encuentra disponible.")

st.markdown("""
<div class="section">
    <p class="section-description">
        Bienvenido al <strong>Bot de Recomendación de Mercados de Exportación</strong>. 
        Este bot le ayudará a encontrar los mercados más adecuados para exportar sus productos, basándose en una serie de indicadores clave de cada país.
        Seleccione un producto y vea los mercados recomendados. 🚀
    </p>
</div>
""", unsafe_allow_html=True)

# Selección de Producto
productos = afinidad_df['Producto'].unique()
producto_seleccionado = st.selectbox("\U0001F50D Elija un Producto", productos)

df_producto = df_merged[df_merged['Producto'] == producto_seleccionado]

with st.form(key='mercados_form'):
    st.markdown(f'<div class="section-title">\U0001F30E Mercados recomendados para {producto_seleccionado}</div>', unsafe_allow_html=True)
    st.dataframe(df_producto[['País', 'Afinidad', 'Acuerdo Comercial']])

    fig = px.bar(df_producto, x='País', y='Afinidad', color='Acuerdo Comercial',
                 title=f"Afinidad de los mercados para {producto_seleccionado}",
                 color_discrete_map={'Sí': 'green', 'No': 'gray'})
    st.plotly_chart(fig)

    st.subheader("\U0001F4CD Mapa Interactivo - Facilidad para hacer negocios")
    df_producto_map = mercados_df[mercados_df['País'].isin(df_producto['País'])]

    if 'Latitud' in df_producto_map.columns and 'Longitud' in df_producto_map.columns:
        fig_map = px.scatter_geo(df_producto_map,
                                 lat="Latitud", lon="Longitud",
                                 size="Facilidad Negocios (WB 2019)",
                                 hover_name="País",
                                 size_max=50,
                                 title=f"Facilidad para hacer negocios en los mercados recomendados",
                                 color="Facilidad Negocios (WB 2019)",
                                 color_continuous_scale="Viridis")
        st.plotly_chart(fig_map)
    else:
        st.error("Faltan columnas de Latitud y Longitud para el mapa.")

    submit_button = st.form_submit_button("Ver Recomendaciones")

    if submit_button:
        st.markdown("""
        ### Recomendaciones:
        Mercados con alta afinidad y presencia de acuerdos comerciales:
        """)
        st.write(df_producto[['País', 'Afinidad', 'Acuerdo Comercial']].sort_values(by='Afinidad', ascending=False))

    st.subheader("\U0001F504 Personaliza tu Recomendación")
    slider = st.slider("Afinidad mínima para recomendar", 0, 100, 50)
    filtrado = df_producto[df_producto['Afinidad'] >= slider]
    st.write(f"\U0001F6CD Mercados con afinidad mayor a {slider}:")
    st.dataframe(filtrado[['País', 'Afinidad', 'Acuerdo Comercial']])

# Mostrar mercados completos
st.markdown('<div class="section-title">\U0001F4DD Información completa sobre los mercados</div>', unsafe_allow_html=True)
st.write("Información detallada sobre todos los mercados disponibles:")
st.dataframe(mercados_df)
