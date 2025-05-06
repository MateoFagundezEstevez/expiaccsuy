import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Cargar los archivos CSV con los datos
mercados_df = pd.read_csv('mercados.csv')
afinidad_df = pd.read_csv('afinidad_producto_país.csv')

# Agregar la nueva columna de acuerdos comerciales al dataframe
acuerdos_comerciales_df = pd.read_csv('acuerdos_comerciales.csv')

# Estilo CSS para personalizar el logo y las secciones
st.markdown("""
    <style>
        /* Estilo del logo, títulos y botones */
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

# Logo centrado y grande
from PIL import Image
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

# Usar un formulario para manejar la interacción
with st.form(key='mercados_form'):
    st.markdown('<div class="section-title">🌎 Mercados recomendados para {}</div>'.format(producto_seleccionado), unsafe_allow_html=True)
    st.dataframe(df_producto[['País', 'Afinidad']])

    # Filtros de afinidad y acuerdos comerciales
    st.subheader("🔄 Personaliza tu Recomendación")
    slider = st.slider("Ajusta la Afinidad mínima para la recomendación", 0, 100, 50)
    mercados_filtrados = df_producto[df_producto['Afinidad'] >= slider]

    # Mostrar solo los mercados con acuerdo comercial
    st.checkbox("Mostrar solo mercados con acuerdo comercial", key="acuerdo_comercial")

    if st.session_state.get("acuerdo_comercial", False):
        # Verificamos que las columnas 'Acuerdo Comercial' y 'Descripción del Acuerdo' estén presentes
        if 'Acuerdo Comercial' in acuerdos_comerciales_df.columns and 'Descripción del Acuerdo' in acuerdos_comerciales_df.columns:
            mercados_filtrados = mercados_filtrados.merge(acuerdos_comerciales_df[acuerdos_comerciales_df['Acuerdo Comercial'] == 'Sí'], on="País")
        else:
            st.warning("No se encontraron las columnas de acuerdo comercial o descripción del acuerdo en los datos.")
    
    # Verificar si las columnas necesarias están presentes antes de intentar acceder a ellas
    if 'Acuerdo Comercial' in mercados_filtrados.columns and 'Descripción del Acuerdo' in mercados_filtrados.columns:
        st.write(f"🛍️ Mercados con afinidad mayor a {slider}:")
        st.dataframe(mercados_filtrados[['País', 'Afinidad', 'Acuerdo Comercial', 'Descripción del Acuerdo']])
    else:
        st.write(f"🛍️ Mercados con afinidad mayor a {slider}, pero sin acuerdo comercial o descripción del acuerdo disponibles.")
        st.dataframe(mercados_filtrados[['País', 'Afinidad']])

    # Mostrar un gráfico interactivo de los mercados recomendados
    fig = px.bar(mercados_filtrados, x='País', y='Afinidad', title=f"Afinidad de los mercados para {producto_seleccionado}")
    st.plotly_chart(fig)

    # Botón de recomendación - el botón de 'submit' está en el formulario
    submit_button = st.form_submit_button("Ver Recomendaciones")
    
    if submit_button:
        st.markdown("""
        ### Recomendaciones:
        Los siguientes mercados tienen una alta afinidad para el producto seleccionado, junto con acuerdos comerciales vigentes.
        Los mercados con mayor puntaje de afinidad son los más recomendados.
        """)
        if 'Acuerdo Comercial' in mercados_filtrados.columns and 'Descripción del Acuerdo' in mercados_filtrados.columns:
            st.write(mercados_filtrados[['País', 'Afinidad', 'Acuerdo Comercial', 'Descripción del Acuerdo']].sort_values(by='Afinidad', ascending=False))
        else:
            st.write(mercados_filtrados[['País', 'Afinidad']].sort_values(by='Afinidad', ascending=False))

# Mostrar todos los mercados
st.markdown('<div class="section-title">📝 Información completa sobre los mercados</div>', unsafe_allow_html=True)
st.write("""
A continuación se muestra la información detallada sobre todos los mercados disponibles:
""")
st.dataframe(mercados_df)
