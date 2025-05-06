import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# -------------------------
# Cargar datos con caché
# -------------------------
@st.cache_data
def cargar_datos():
    mercados_df = pd.read_csv('mercados.csv')
    mercados_df.columns = mercados_df.columns.str.strip()
    afinidad_df = pd.read_csv('afinidad_producto_país.csv')
    afinidad_df.columns = afinidad_df.columns.str.strip()
    afinidad_df['Producto'] = afinidad_df['Producto'].astype(str).str.strip()
    return mercados_df, afinidad_df

mercados_df, afinidad_df = cargar_datos()

# -------------------------
# Estilos personalizados
# -------------------------
st.markdown("""
    <style>
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
    </style>
""", unsafe_allow_html=True)

# -------------------------
# Logo y título
# -------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    logo = Image.open("logo_ccsuy.png")
    st.image(logo, width=300)

st.title("🌍 Bot de Recomendación de Mercados de Exportación")

# -------------------------
# Instrucciones
# -------------------------
with st.expander("📄 Ver Instrucciones", expanded=False):
    try:
        with open("README.md", "r", encoding="utf-8") as file:
            st.markdown(file.read())
    except FileNotFoundError:
        st.error("El archivo README.md no se encuentra disponible.")

# -------------------------
# Selección de producto y filtros globales
# -------------------------
st.sidebar.header("🔧 Filtros")
productos_disponibles = afinidad_df['Producto'].dropna().unique()
producto_seleccionado = st.sidebar.selectbox("Seleccione un producto", productos_disponibles)

# Filtro por continente si existe
if 'Continente' not in mercados_df.columns:
    continentes = mercados_df['País'].unique()
    df_continente = mercados_df
else:
    continentes = st.sidebar.multiselect("Filtrar por continente", mercados_df['Continente'].dropna().unique(), default=mercados_df['Continente'].dropna().unique())
    df_continente = mercados_df[mercados_df['Continente'].isin(continentes)]

# -------------------------
# Ponderación de factores
# -------------------------
st.sidebar.subheader("⚖️ Ponderación de factores")
pesos = {
    'Afinidad': st.sidebar.slider("Afinidad", 0, 100, 50),
    'PIB per cápita (USD)': st.sidebar.slider("PIB per cápita", 0, 100, 15),
    'Crecimiento Anual PIB (%)': st.sidebar.slider("Crecimiento PIB", 0, 100, 10),
    'Crecimiento Importaciones (%)': st.sidebar.slider("Crecimiento Importaciones", 0, 100, 10),
    'Logística (LPI 2023)': st.sidebar.slider("Logística (LPI)", 0, 100, 10),
    'Infraestructura Portuaria (LPI 2023)': st.sidebar.slider("Infraestructura Portuaria", 0, 100, 5),
    'Distancia a Uruguay (km)': st.sidebar.slider("Distancia a Uruguay", 0, 100, 0)  # penalización inversa
}
total_peso = sum(pesos.values())

# -------------------------
# Procesamiento de datos
# -------------------------
df_prod = afinidad_df[afinidad_df['Producto'] == producto_seleccionado]
df_merged = df_prod.merge(df_continente, on='País')

# Invertir valores donde se penaliza (por ejemplo, distancia)
df_merged['Distancia a Uruguay (km)'] = df_merged['Distancia a Uruguay (km)'].max() - df_merged['Distancia a Uruguay (km)']

for k in pesos:
    if k not in df_merged.columns:
        df_merged[k] = 0

df_merged['Score'] = sum((pesos[k] / total_peso) * df_merged[k] for k in pesos)

# -------------------------
# Resultados y visualización
# -------------------------
st.markdown(f'<div class="section-title">🌎 Recomendaciones para "{producto_seleccionado}"</div>', unsafe_allow_html=True)

st.dataframe(df_merged[['País', 'Score'] + list(pesos.keys())].sort_values(by='Score', ascending=False), use_container_width=True)

fig = px.bar(df_merged.sort_values(by='Score'), x='Score', y='País', orientation='h', 
             title="Ranking de países recomendados", color='Score', color_continuous_scale='Blues')
st.plotly_chart(fig)

# -------------------------
# Mapa geográfico
# -------------------------
st.subheader("📍 Mapa de mercados sugeridos")

# Asegurar que los datos de latitud, longitud y score sean numéricos
df_merged['Latitud'] = pd.to_numeric(df_merged['Latitud'], errors='coerce')
df_merged['Longitud'] = pd.to_numeric(df_merged['Longitud'], errors='coerce')
df_merged['Score'] = pd.to_numeric(df_merged['Score'], errors='coerce')

g
eo_data = df_merged.dropna(subset=['Latitud', 'Longitud', 'Score'])

if not geo_data.empty:
    try:
        fig_map = px.scatter_geo(geo_data,
                                 lat="Latitud", lon="Longitud",
                                 size="Score", hover_name="País",
                                 color="Score", color_continuous_scale="Viridis",
                                 projection="natural earth",
                                 title="Ubicación de los mercados recomendados")
        st.plotly_chart(fig_map)
    except Exception as e:
        st.error(f"❌ Error al generar el mapa: {e}")
else:
    st.warning("⚠️ No se encontraron coordenadas válidas para mostrar el mapa.")

# -------------------------
# Ficha de país seleccionado (opcional)
# -------------------------
st.subheader("🔎 Información detallada por país")
if not df_merged.empty:
    selected_pais = st.selectbox("Seleccione un país para ver detalles", df_merged['País'].unique())
    ficha = df_merged[df_merged['País'] == selected_pais].iloc[0]
    st.write(f"**Score total:** {ficha['Score']:.2f}")
    for k in pesos:
        st.write(f"**{k}:** {ficha[k]}")

# -------------------------
# Información completa
# -------------------------
st.markdown('<div class="section-title">📝 Información completa de mercados</div>', unsafe_allow_html=True)
st.dataframe(mercados_df, use_container_width=True)

