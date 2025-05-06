import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from PIL import Image

# Cargar los archivos CSV con los datos
mercados_df = pd.read_csv('mercados.csv')
afinidad_df = pd.read_csv('afinidad_producto_país.csv')
acuerdos_df = pd.read_csv('acuerdos_comerciales.csv')

# Renombrar la columna para uniformizar
acuerdos_df.rename(columns={'Acuerdo Comercial': 'Acuerdo Comercial (Sí/No)'}, inplace=True)

# Unir afinidad con acuerdos comerciales
afinidad_df = afinidad_df.merge(acuerdos_df, on='País', how='left')

# Estilo CSS para personalizar el logo y las secciones
st.markdown("""
    <style>
        .logo-container {
            text-align: center;
        }
        .logo-container img {
            width: 400px;
        }
        .section-title {
            color: #003B5C;
            font-size: 24px;
            font-weight: bold;
        }
        .section-description {
            color: #9E2A2F;
            font-size: 16px;
        }
        .section {
            background-color: #E8F4F9;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 10px;
        }
        .expander-title {
            font-size: 20px;
            color: #003B5C;
        }
        .expander-content {
            font-size: 14px;
            color: #4A4A4A;
        }
        .button {
            background-color: #9E2A2F;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 5px;
        }
        .button:hover {
            background-color: #C84B53;
        }
    </style>
""", unsafe_allow_html=True)

# Logo centrado
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    logo = Image.open("logo_ccsuy.png")
    st.image(logo, width=400)

# Título de la app
st.title("\U0001F30D Bot de Recomendación de Mercados de Exportación")

# Instrucciones
with st.expander("\U0001F4C4 Ver Instrucciones", expanded=False):
    try:
        with open("README.md", "r", encoding="utf-8") as file:
            readme_content = file.read()
        st.markdown(f'<div class="expander-content">{readme_content}</div>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("El archivo README.md no se encuentra disponible.")

# Descripción de la herramienta
st.markdown("""
<div class="section">
    <p class="section-description">
        Bienvenido al <strong>Bot de Recomendación de Mercados de Exportación</strong>. 
        Este bot le ayudará a encontrar los mercados más adecuados para exportar sus productos, basándose en indicadores clave como afinidad del producto, facilidad de negocios y existencia de acuerdos comerciales.\n
        Seleccione un producto y vea los mercados recomendados. 🚀
    </p>
</div>
""", unsafe_allow_html=True)

# Selección de producto
productos = afinidad_df['Producto'].unique()
producto_seleccionado = st.selectbox("\U0001F50D Elija un Producto", productos)

# Filtrar por producto
df_producto = afinidad_df[afinidad_df['Producto'] == producto_seleccionado]

# Formulario
with st.form(key='mercados_form'):
    st.markdown(f'<div class="section-title">\U0001F30E Mercados recomendados para {producto_seleccionado}</div>', unsafe_allow_html=True)
    st.dataframe(df_producto[['País', 'Afinidad', 'Acuerdo Comercial (Sí/No)', 'Descripción del Acuerdo']])

    # Gráfico de afinidad
    fig = px.bar(df_producto, x='País', y='Afinidad', title=f"Afinidad de los mercados para {producto_seleccionado}")
    st.plotly_chart(fig)

    # Mapa de facilidad de negocios
    st.subheader("\U0001F4CD Mapa Interactivo de los Mercados - Facilidad para hacer negocios")
    df_producto_map = mercados_df[mercados_df['País'].isin(df_producto['País'])]

    if 'Latitud' in df_producto_map.columns and 'Longitud' in df_producto_map.columns:
        fig_map = px.scatter_geo(df_producto_map,
                                 lat="Latitud",
                                 lon="Longitud",
                                 size="Facilidad Negocios (WB 2019)",
                                 hover_name="País",
                                 size_max=50,
                                 title=f"Facilidad para hacer negocios en los mercados recomendados para {producto_seleccionado}",
                                 color="Facilidad Negocios (WB 2019)",
                                 color_continuous_scale="Viridis")
        st.plotly_chart(fig_map)
    else:
        st.error("El archivo de datos no contiene columnas de latitud y longitud necesarias.")

    submit_button = st.form_submit_button("Ver Recomendaciones")

    if submit_button:
        st.markdown("""
        ### Recomendaciones:
        Los siguientes mercados tienen alta afinidad para el producto seleccionado y pueden beneficiarse de acuerdos comerciales.
        """)
        st.write(df_producto[['País', 'Afinidad', 'Acuerdo Comercial (Sí/No)', 'Descripción del Acuerdo']].sort_values(by='Afinidad', ascending=False))

    st.subheader("\U0001F501 Personaliza tu Recomendación")
    slider = st.slider("Ajusta la Afinidad mínima para la recomendación", 0, 100, 50)
    mercados_filtrados = df_producto[df_producto['Afinidad'] >= slider]
    st.write(f"\U0001F6CD️ Mercados con afinidad mayor a {slider}:")
    st.dataframe(mercados_filtrados[['País', 'Afinidad', 'Acuerdo Comercial (Sí/No)', 'Descripción del Acuerdo']])

# Info completa de mercados
st.markdown('<div class="section-title">\U0001F4DD Información completa sobre los mercados</div>', unsafe_allow_html=True)
st.write("""
A continuación se muestra la información detallada sobre todos los mercados disponibles:
""")
st.dataframe(mercados_df)
