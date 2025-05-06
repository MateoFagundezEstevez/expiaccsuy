import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Cargar los archivos CSV con los datos
mercados_df = pd.read_csv('mercados.csv')
afinidad_df = pd.read_csv('afinidad_producto_país.csv')
acuerdos_comerciales_df = pd.read_csv('acuerdos_comerciales.csv', encoding='latin1')

# Mostrar columnas de los DataFrames para depuración (esto lo haremos opcional para el usuario)
if st.checkbox("Mostrar columnas de los DataFrames"):
    st.write("Columnas de 'mercados_df':", mercados_df.columns)
    st.write("Columnas de 'afinidad_df':", afinidad_df.columns)
    st.write("Columnas de 'acuerdos_comerciales_df':", acuerdos_comerciales_df.columns)

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
producto_seleccionado = st.selectbox("🔍 Elija un Producto", productos, index=0)

# Filtrar los datos según el producto seleccionado
df_producto = afinidad_df[afinidad_df['Producto'] == producto_seleccionado]

# Slider para ajustar la afinidad mínima
slider = st.slider("Ajuste la Afinidad mínima para la recomendación", 0, 100, 50)

# Filtro de mercados por afinidad
mercados_filtrados = df_producto[df_producto['Afinidad'] >= slider]

# Checkbox para filtrar por acuerdo comercial
mostrar_acuerdo = st.checkbox("Mostrar solo mercados con acuerdo comercial")

# Si se selecciona el checkbox, aplicar el filtro de acuerdo comercial
if mostrar_acuerdo:
    # Realizar la fusión con los datos de acuerdos comerciales
    mercados_filtrados = pd.merge(mercados_filtrados, acuerdos_comerciales_df[['País', 'Acuerdo Comercial', 'Descripción del Acuerdo']], on='País', how='left')

# Ordenar los mercados filtrados por afinidad de mayor a menor
mercados_filtrados = mercados_filtrados.sort_values(by='Afinidad', ascending=False)

# Mostrar los mercados recomendados si existen
if not mercados_filtrados.empty:
    st.markdown(f"### 🌍 Mercados recomendados para {producto_seleccionado} con afinidad superior a {slider}")

# Obtener lista de países por continente si aún no existe
if 'Continente' not in mercados_df.columns:
    st.warning("Falta la columna 'Continente' en el archivo 'mercados.csv'. Para aplicar esta lógica, necesitás clasificar los países por continente.")
else:
    # Unir datos de mercados_df al dataframe filtrado para usar el continente
    mercados_filtrados = pd.merge(mercados_filtrados, mercados_df[['País', 'Continente', 'Facilidad para hacer negocios']], on='País', how='left')

    # Asegurar al menos 3 de América entre los 5 mejores
    mercados_america = mercados_filtrados[mercados_filtrados['Continente'] == 'América'].sort_values(by='Afinidad', ascending=False).head(3)
    restantes = mercados_filtrados[~mercados_filtrados['País'].isin(mercados_america['País'])].sort_values(by='Afinidad', ascending=False).head(2)
    
    top_mercados = pd.concat([mercados_america, restantes]).sort_values(by='Afinidad', ascending=False).head(5)

    st.markdown(f"### 🌎 Top 5 Mercados Recomendados para **{producto_seleccionado}** (con al menos 3 de América)")

    for _, row in top_mercados.iterrows():
        st.markdown(f"#### ✅ {row['País']}")

        razones = [
            f"- **Alta afinidad**: {row['Afinidad']} puntos, lo que indica coincidencia entre demanda y oferta del producto.",
            f"- **Facilidad para hacer negocios**: {row['Facilidad para hacer negocios']} según WB (2019)."
        ]

        if mostrar_acuerdo and pd.notnull(row.get('Acuerdo Comercial')):
            razones.append(f"- **Acuerdo vigente**: {row['Acuerdo Comercial']}. {row.get('Descripción del Acuerdo', '')}")
        else:
            razones.append("- **Sin acuerdo comercial preferencial vigente** con Uruguay.")

        estrategia = f"**Recomendación estratégica:** Se sugiere explorar este mercado por su perfil compatible y las condiciones institucionales. Identificar canales de distribución y validar requisitos específicos de acceso."

        st.markdown("\n".join(razones))
        st.markdown(estrategia)

else:
    st.warning("No se encontraron mercados con la afinidad seleccionada o los filtros aplicados.")

# Mapa interactivo de la facilidad para hacer negocios
st.subheader("📍 Mapa de Facilidad para Hacer Negocios")

# Asegurarse de que la columna "Facilidad Negocios (WB 2019)" esté en el DataFrame
df_producto_map = mercados_df[mercados_df['País'].isin(mercados_filtrados['País'])]

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
    st.plotly_chart(fig_map)
else:
    st.error("El archivo de datos no contiene las columnas de Latitud y Longitud necesarias para mostrar el mapa.")

# Mostrar todos los mercados disponibles (sin latitud y longitud)
st.markdown('<div class="section-title">📝 Información completa sobre los mercados</div>', unsafe_allow_html=True)
st.write("""
A continuación se muestra la información detallada sobre todos los mercados disponibles:
""")

# Eliminar las columnas 'Latitud' y 'Longitud' antes de mostrar los datos
mercados_sin_latitud = mercados_df.drop(columns=['Latitud', 'Longitud'], errors='ignore')
st.dataframe(mercados_sin_latitud)
