import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from PIL import Image

# Cargar los archivos CSV con los datos
mercados_df = pd.read_csv('mercados.csv')
afinidad_df = pd.read_csv('afinidad_producto_país.csv')

# Cargar archivo de acuerdos comerciales (nuevo archivo CSV)
acuerdos_df = pd.read_csv('acuerdos_comerciales.csv')

# Merge de los datos de acuerdos comerciales con los mercados
mercados_df = mercados_df.merge(acuerdos_df, on='País', how='left')

# Estilo CSS para personalizar el logo y las secciones
st.markdown("""
    <style>
        /* Centrar el logo y hacerlo más grande */
        .logo-container {
            text-align: center;
        }
        .logo-container img {
            width: 400px;  /* Aproximadamente 10 cm */
        }

        /* Colores personalizados para las secciones */
        .section-title {
            color: #003B5C;  /* Un color oscuro azul, por ejemplo */
            font-size: 24px;
            font-weight: bold;
        }

        .section-description {
            color: #9E2A2F;  /* Color rojo oscuro */
            font-size: 16px;
        }

        .section {
            background-color: #E8F4F9;  /* Fondo de sección en azul claro */
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
            background-color: #9E2A2F;  /* Rojo oscuro */
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
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    logo = Image.open("logo_ccsuy.png")
    st.image(logo, width=400)

# Título de la aplicación
st.title("🌍 Bot de Recomendación de Mercados de Exportación")

# Opción para desplegar/ocultar las instrucciones
with st.expander("📄 Ver Instrucciones", expanded=False):
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
        Bienvenido al **Bot de Recomendación de Mercados de Exportación**. 
        Este bot le ayudará a encontrar los mercados más adecuados para exportar sus productos, basándose en una serie de indicadores clave de cada país. 
        Seleccione un producto y vea los mercados recomendados. 🚀
    </p>
</div>
""", unsafe_allow_html=True)

# Selección de Producto
productos = afinidad_df['Producto'].unique()
producto_seleccionado = st.selectbox("🔍 Elija un Producto", productos)

# Filtrar los datos según el producto seleccionado
df_producto = afinidad_df[afinidad_df['Producto'] == producto_seleccionado]

# Ponderaciones de los factores (por defecto todas con el mismo peso)
ponderaciones_default = {
    'afinidad': 0.25,
    'facilidad_negocios': 0.25,
    'demanda': 0.25,
    'acuerdo_comercial': 0.25
}

# Interfaz para que el usuario ajuste las ponderaciones
st.subheader("🔄 Ajuste las Ponderaciones")
afinidad_ponderacion = st.slider("🔸 Ponderación de Afinidad", 0.0, 1.0, ponderaciones_default['afinidad'], 0.01)
facilidad_negocios_ponderacion = st.slider("🔸 Ponderación de Facilidad para hacer negocios", 0.0, 1.0, ponderaciones_default['facilidad_negocios'], 0.01)
demanda_ponderacion = st.slider("🔸 Ponderación de Demanda Esperada", 0.0, 1.0, ponderaciones_default['demanda'], 0.01)
acuerdo_comercial_ponderacion = st.slider("🔸 Ponderación de Acuerdo Comercial", 0.0, 1.0, ponderaciones_default['acuerdo_comercial'], 0.01)

# Asegurarse de que las ponderaciones sumen 1
total_ponderacion = afinidad_ponderacion + facilidad_negocios_ponderacion + demanda_ponderacion + acuerdo_comercial_ponderacion
if total_ponderacion != 1.0:
    st.warning(f"Las ponderaciones no suman 1. Se ajustará automáticamente: {total_ponderacion:.2f}")
    # Reajustar las ponderaciones
    afinidad_ponderacion /= total_ponderacion
    facilidad_negocios_ponderacion /= total_ponderacion
    demanda_ponderacion /= total_ponderacion
    acuerdo_comercial_ponderacion /= total_ponderacion

# Mostrar las ponderaciones elegidas
st.markdown(f"""
    <div class="section">
        <b>Resumen de las Ponderaciones:</b><br>
        Afinidad: {afinidad_ponderacion:.2f} <br>
        Facilidad de Negocios: {facilidad_negocios_ponderacion:.2f} <br>
        Demanda Esperada: {demanda_ponderacion:.2f} <br>
        Acuerdo Comercial: {acuerdo_comercial_ponderacion:.2f} <br>
    </div>
""", unsafe_allow_html=True)

# Función para calcular el score ponderado
def calcular_score(row, ponderaciones):
    score = (row['Afinidad'] * ponderaciones['afinidad'] +
             row['Facilidad Negocios (WB 2019)'] * ponderaciones['facilidad_negocios'] +
             row['Demanda Esperada'] * ponderaciones['demanda'] +
             (5 if row['Acuerdo Comercial'] == 'Sí' else 0) * ponderaciones['acuerdo_comercial'])
    return score

# Calcular el score ponderado para cada país
df_producto['Score Ponderado'] = df_producto.apply(calcular_score, axis=1, ponderaciones=ponderaciones_default)

# Ordenar los resultados por el score ponderado
df_producto = df_producto.sort_values(by='Score Ponderado', ascending=False)

# Mostrar las recomendaciones
st.subheader(f"📊 Mercados recomendados para {producto_seleccionado}")
st.dataframe(df_producto[['País', 'Score Ponderado', 'Afinidad', 'Facilidad Negocios (WB 2019)', 'Demanda Esperada', 'Acuerdo Comercial']])

# Mostrar gráfico interactivo de la recomendación ponderada
fig = px.bar(df_producto, x='País', y='Score Ponderado', title=f"Ranking de Mercados para {producto_seleccionado}")
st.plotly_chart(fig)

# Mostrar un mapa interactivo de los mercados recomendados
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
                             size_max=50,  # Reducir el tamaño máximo de los globos
                             title=f"Facilidad para hacer negocios en los mercados recomendados para {producto_seleccionado}",
                             color="Facilidad Negocios (WB 2019)",
                             color_continuous_scale="Viridis")
    # Mostrar el mapa interactivo
    st.plotly_chart(fig_map)
else:
    st.error("El archivo de datos no contiene las columnas de Latitud y Longitud necesarias para mostrar el mapa.")
    
# Agregar algún cuadro interactivo (ejemplo con Slider)
st.subheader("🔄 Personaliza tu Recomendación")
slider = st.slider("Ajusta la Afinidad mínima para la recomendación", 0, 100, 50)
mercados_filtrados = df_producto[df_producto['Afinidad'] >= slider]

st.write(f"🛍️ Mercados con afinidad mayor a {slider}:")
st.dataframe(mercados_filtrados[['País', 'Afinidad']])

# Mostrar todas las columnas de mercados.csv
st.markdown('<div class="section-title">📝 Información completa sobre los mercados</div>', unsafe_allow_html=True)
st.write("""
A continuación se muestra la información detallada sobre todos los mercados disponibles:
""")

# Hacer que la tabla de 'mercados_df' sea más interactiva
st.dataframe(mercados_df)
