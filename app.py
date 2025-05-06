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
# Selección de producto
# -------------------------
st.sidebar.header("🔧 Filtros")
producto_seleccionado = st.sidebar.selectbox("Seleccione un producto", afinidad_df['Producto'].unique())

# -------------------------
# Ponderación de factores reales
# -------------------------
st.sidebar.subheader("⚖️ Ponderación de indicadores")
pesos = {
    'Afinidad': st.sidebar.slider("Afinidad", 0, 100, 30),
    'Facilidad Negocios (WB 2019)': st.sidebar.slider("Facilidad para hacer negocios", 0, 100, 20),
    'PIB per cápita (USD)': st.sidebar.slider("PIB per cápita", 0, 100, 15),
    'Crecimiento Anual PIB (%)': st.sidebar.slider("Crecimiento del PIB", 0, 100, 10),
    'Tamaño del Mercado Total (Millones USD)': st.sidebar.slider("Tamaño del mercado", 0, 100, 10),
    'Logística (LPI 2023)': st.sidebar.slider("Logística", 0, 100, 5),
    'Infraestructura Portuaria (LPI 2023)': st.sidebar.slider("Infraestructura portuaria", 0, 100, 5),
    'Distancia a Uruguay (km)': st.sidebar.slider("Distancia (penaliza)", 0, 100, 5)
}
total_peso = sum(pesos.values())

# -------------------------
# Procesamiento de datos
# -------------------------
df_prod = afinidad_df[afinidad_df['Producto'] == producto_seleccionado]
df_merged = df_prod.merge(mercados_df, on='País')

# Invertir la distancia (penaliza en lugar de sumar)
df_merged['Distancia Invertida'] = 1 / (df_merged['Distancia a Uruguay (km)'] + 1)

# Calcular Score
df_merged['Score'] = (
    (pesos['Afinidad'] / total_peso) * df_merged['Afinidad'] +
    (pesos['Facilidad Negocios (WB 2019)'] / total_peso) * df_merged['Facilidad Negocios (WB 2019)'] +
    (pesos['PIB per cápita (USD)'] / total_peso) * df_merged['PIB per cápita (USD)'] +
    (pesos['Crecimiento Anual PIB (%)'] / total_peso) * df_merged['Crecimiento Anual PIB (%)'] +
    (pesos['Tamaño del Mercado Total (Millones USD)'] / total_peso) * df_merged['Tamaño del Mercado Total (Millones USD)'] +
    (pesos['Logística (LPI 2023)'] / total_peso) * df_merged['Logística (LPI 2023)'] +
    (pesos['Infraestructura Portuaria (LPI 2023)'] / total_peso) * df_merged['Infraestructura Portuaria (LPI 2023)'] +
    (pesos['Distancia a Uruguay (km)'] / total_peso) * df_merged['Distancia Invertida']
)

# -------------------------
# Resultados
# -------------------------
st.markdown(f'<div class="section-title">🌎 Recomendaciones para "{producto_seleccionado}"</div>', unsafe_allow_html=True)
st.dataframe(df_merged[['País', 'Score'] + list(pesos.keys())].sort_values(by='Score', ascending=False), use_container_width=True)

# Gráfico
fig = px.bar(df_merged.sort_values(by='Score'), x='Score', y='País', orientation='h', 
             title="Ranking de países recomendados", color='Score', color_continuous_scale='Blues')
st.plotly_chart(fig)

# -------------------------
# Mapa
# -------------------------
st.subheader("📍 Mapa de mercados sugeridos")
fig_map = px.scatter_geo(df_merged,
                         lat="Latitud", lon="Longitud",
                         size="Score", hover_name="País",
                         color="Score", color_continuous_scale="Viridis",
                         projection="natural earth",
                         title="Ubicación de los mercados recomendados")
st.plotly_chart(fig_map)

# -------------------------
# Ficha detallada
# -------------------------
st.subheader("🔎 Información detallada por país")
selected_pais = st.selectbox("Seleccione un país para ver detalles", df_merged['País'].unique())
ficha = df_merged[df_merged['País'] == selected_pais].iloc[0]
st.write(f"**Score total:** {ficha['Score']:.2f}")
for k in pesos:
    st.write(f"**{k}:** {ficha.get(k, 'N/A')}")

# -------------------------
# Tabla completa
# -------------------------
st.markdown('<div class="section-title">📝 Información completa de mercados</div>', unsafe_allow_html=True)
st.dataframe(mercados_df, use_container_width=True)
