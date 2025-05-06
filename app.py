import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Cargar los archivos CSV con los datos
mercados_df = pd.read_csv('mercados.csv')
afinidad_df = pd.read_csv('afinidad_producto_país.csv')
acuerdos_df = pd.read_csv('acuerdos_comerciales.csv')

# Fusionar acuerdos comerciales con los datos de afinidad
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

# Logo centrado y grande
from PIL import Image
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    logo = Image.open("logo_ccsuy.png")
    st.image(logo, width=400)

# Título de la aplicación
st.title("🌍 Bot de Recomendación de Mercados de Exportación")

# Instrucciones desplegables
with st.expander("📄 Ver Instrucciones", expanded=False):
    try:
        with open("README.md", "r", encoding="utf-8") as file:
            readme_content = file.read()
        st.markdown(f'<div class="expander-content">{readme_content}</div>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("El archivo README.md no se encuentra disponible.")

# Descripción
st.markdown("""
<div class="section">
    <p class="section-description">
        Bienvenido al **Bot de Recomendación de Mercados de Exportación**. 
        Este bot le ayudará a encontrar los mercados más adecuados para exportar sus productos, basándose en una serie de indicadores clave de cada país. 
        Seleccione un producto y vea los mercados recomendados. 🚀
    </p>
</div>
""", unsafe_allow_html=True)

# Selección de Producto
productos = afinidad_df['Producto'].unique()
producto_seleccionado = st.selectbox("🔍 Elija un Producto", productos)

# Filtrar por producto
df_producto = afinidad_df[afinidad_df['Producto'] == producto_seleccionado]

# Formulario para mostrar resultados
with st.form(key='mercados_form'):
    st.markdown(f'<div class="section-title">🌎 Mercados recomendados para {producto_seleccionado}</div>', unsafe_allow_html=True)

    # Mostrar tabla con acuerdos
    st.dataframe(df_producto[['País', 'Afinidad', 'Acuerdo Comercial (Sí/No)', 'Descripción del Acuerdo']])

    # Gráfico de barras
    fig = px.bar(df_producto, x='País', y='Afinidad', color='Acuerdo Comercial (Sí/No)',
                 title=f"Afinidad de los mercados para {producto_seleccionado}")
    st.plotly_chart(fig)

    # Mapa interactivo
    st.subheader("📍 Mapa Interactivo de los Mercados - Facilidad para hacer negocios")
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
        st.error("El archivo de datos no contiene columnas de Latitud y Longitud necesarias para el mapa.")

    # Botón
    submit_button = st.form_submit_button("Ver Recomendaciones")
    if submit_button:
        st.markdown("### Recomendaciones ordenadas por afinidad:")
        st.write(df_producto[['País', 'Afinidad', 'Acuerdo Comercial (Sí/No)', 'Descripción del Acuerdo']].sort_values(by='Afinidad', ascending=False))

    # Filtro adicional por afinidad
    st.subheader("🔄 Personaliza tu Recomendación")
    slider = st.slider("Ajusta la Afinidad mínima para la recomendación", 0, 100, 50)
    mercados_filtrados = df_producto[df_producto['Afinidad'] >= slider]
    st.write(f"🛍️ Mercados con afinidad mayor a {slider}:")
    st.dataframe(mercados_filtrados[['País', 'Afinidad', 'Acuerdo Comercial (Sí/No)', 'Descripción del Acuerdo']])

# Mostrar todos los datos
st.markdown('<div class="section-title">📝 Información completa sobre los mercados</div>', unsafe_allow_html=True)
st.write("A continuación se muestra la información detallada sobre todos los mercados disponibles:")
st.dataframe(mercados_df)
