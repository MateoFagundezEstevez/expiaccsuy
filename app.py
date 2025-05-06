import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from PIL import Image

# Cargar los archivos CSV con los datos
mercados_df = pd.read_csv('mercados.csv')
afinidad_df = pd.read_csv('afinidad_producto_país.csv')
acuerdos_comerciales_df = pd.read_csv('acuerdos_comerciales.csv', encoding='latin1')

# Mostrar columnas de los DataFrames para depuración (esto lo haremos opcional para el usuario)
if st.checkbox("Mostrar columnas de los DataFrames"):
    st.write("Columnas de 'mercados_df':", mercados_df.columns)
    st.write("Columnas de 'afinidad_df':", afinidad_df.columns)
    st.write("Columnas de 'acuerdos_comerciales_df':", acuerdos_comerciales_df.columns)

# Estilo CSS personalizado
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

# Logo centrado\col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    logo = Image.open("logo_ccsuy.png")
    st.image(logo, width=400)

# Título de la aplicación
st.title("\U0001F30D Bot de Recomendación de Mercados de Exportación")

# Descripción de la herramienta
st.markdown("""
<div class="section">
    <p class="section-description">
        Bienvenido al **Bot de Recomendación de Mercados de Exportación**. 
        Este bot le ayudará a encontrar los mercados más adecuados para exportar sus productos, basándose en una serie de indicadores clave de cada país. 
        Seleccione un producto y vea los mercados recomendados. \U0001F680
    </p>
</div>
""", unsafe_allow_html=True)

# Selección de Producto
productos = afinidad_df['Producto'].unique()
producto_seleccionado = st.selectbox("\U0001F50D Elija un Producto", productos, index=0)

# Filtrar los datos según el producto seleccionado
df_producto = afinidad_df[afinidad_df['Producto'] == producto_seleccionado]

# Slider para ajustar la afinidad mínima
slider = st.slider("Ajuste la Afinidad mínima para la recomendación", 0, 100, 50)

# Filtro de mercados por afinidad
mercados_filtrados = df_producto[df_producto['Afinidad'] >= slider]

# Checkbox para filtrar por acuerdo comercial
mostrar_acuerdo = st.checkbox("Mostrar solo mercados con acuerdo comercial")

# Aplicar el filtro de acuerdo comercial si corresponde
if mostrar_acuerdo:
    mercados_filtrados = pd.merge(mercados_filtrados, acuerdos_comerciales_df[['País', 'Acuerdo Comercial', 'Descripción del Acuerdo']], on='País', how='left')

# Agregar continente desde mercados_df
mercados_completos = pd.merge(mercados_filtrados, mercados_df[['País', 'Continente']], on='País', how='left')

# Seleccionar los 5 mejores mercados recomendados, asegurando al menos 3 de América
mercados_america = mercados_completos[mercados_completos['Continente'] == 'América'].sort_values(by='Afinidad', ascending=False)
mercados_otro = mercados_completos[mercados_completos['Continente'] != 'América'].sort_values(by='Afinidad', ascending=False)
top_america = mercados_america.head(3)
top_otro = mercados_otro.head(2)
mercados_recomendados = pd.concat([top_america, top_otro])

st.markdown(f"### \U0001F30D Mercados recomendados para {producto_seleccionado} (mínimo 3 en América)")

# Mostrar recomendaciones con justificación
for index, row in mercados_recomendados.iterrows():
    st.write(f"**Recomendación:** {row['País']} ({row['Continente']})")

    justificacion = f"Alta afinidad (**{row['Afinidad']}**) del producto con este mercado."

    if mostrar_acuerdo and 'Acuerdo Comercial' in row and pd.notnull(row['Acuerdo Comercial']):
        justificacion += f" Cuenta con un acuerdo comercial (**{row['Acuerdo Comercial']}**) que puede facilitar el ingreso."

    if row['Continente'] == 'América':
        justificacion += " Al estar en América, se favorecen los lazos comerciales y logísticos con Uruguay."
    else:
        justificacion += " Aunque fuera del continente, el mercado muestra gran interés en este tipo de producto."

    st.write(justificacion)

# Gráfico de barras
fig = px.bar(mercados_recomendados, x='País', y='Afinidad', title=f"Afinidad de los 5 principales mercados para {producto_seleccionado}")
st.plotly_chart(fig)

# Mapa de Facilidad para Hacer Negocios
st.subheader("\U0001F4CD Mapa de Facilidad para Hacer Negocios")
df_producto_map = mercados_df[mercados_df['País'].isin(mercados_recomendados['País'])]

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
    st.error("El archivo de datos no contiene las columnas de Latitud y Longitud necesarias para mostrar el mapa.")

# Mostrar todos los mercados disponibles
st.markdown('<div class="section-title">\U0001F4DD Información completa sobre los mercados</div>', unsafe_allow_html=True)
st.write("""
A continuación se muestra la información detallada sobre todos los mercados disponibles:
""")

mercados_sin_latitud = mercados_df.drop(columns=['Latitud', 'Longitud'], errors='ignore')
st.dataframe(mercados_sin_latitud)
