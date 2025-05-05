import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster

# Cargar los datos localmente
afinidad_df = pd.read_csv("afinidad_producto_país.csv", encoding="ISO-8859-1")
mercados_df = pd.read_csv("mercados.csv", encoding="ISO-8859-1")

# Definir la función principal con los nuevos filtros
def recomendar_mercados(afinidad_producto, mercados_df, extra_global=0, prioridad_emergentes=False, distancia_maxima=10000, facilidades_exportacion=True):
    # Lista de países de Latinoamérica
    latinoamerica = [
        "Argentina", "Brasil", "Paraguay", "Chile", "Bolivia", "Perú", "Colombia", "Ecuador", 
        "México", "Panamá", "Costa Rica", "República Dominicana", "Guatemala", "El Salvador", 
        "Honduras", "Nicaragua", "Venezuela", "Uruguay", "Cuba", "Haití", "Puerto Rico", "Belice", 
        "Jamaica", "Trinidad y Tobago", "Barbados", "Guyana", "Surinam"
    ]
    
    # Clasificar región
    mercados_df['Región'] = mercados_df['País'].apply(lambda x: 'Latinoamérica' if x in latinoamerica else 'Resto del Mundo')

    # Identificar mercados emergentes
    emergentes = ["Brasil", "México", "Perú", "Colombia", "Chile", "Argentina"]  # Ejemplo de emergentes, puedes ajustarlo

    # Unir datasets
    df_completo = pd.merge(afinidad_producto[['País', 'Afinidad']], mercados_df, on='País', how='inner')

    # Calcular puntajes ponderados con filtros aplicados
    def calcular_puntaje(row):
        puntaje_base = (
            0.6 * row['Afinidad'] +
            0.15 * row['Demanda esperada'] +
            0.1 * row['Facilidad para hacer negocios'] +
            0.15 * row['Estabilidad política']
        )
        
        if prioridad_emergentes and row['País'] in emergentes:
            puntaje_base *= 1.2  # Aumentar peso de los mercados emergentes
        
        if facilidades_exportacion:
            puntaje_base += 0.1 * row['Facilidad para hacer negocios']  # Aumentar puntaje si es prioritario

        return puntaje_base

    df_completo['Puntaje'] = df_completo.apply(calcular_puntaje, axis=1)

    # Filtro por distancia
    if distancia_maxima > 0:
        df_completo['Distancia'] = df_completo['País'].apply(lambda x: np.random.randint(1000, 12000))  # Esto es un ejemplo, debes tener datos reales
        df_completo = df_completo[df_completo['Distancia'] <= distancia_maxima]
    
    # Seleccionar mercados recomendados
    top_latam = df_completo[df_completo['Región'] == 'Latinoamérica'].sort_values(by='Puntaje', ascending=False).head(3)
    top_global = df_completo[df_completo['Región'] == 'Resto del Mundo'].sort_values(by='Puntaje', ascending=False).head(2 + extra_global)

    df_recomendado = pd.concat([top_latam, top_global])

    # Fundamentos
    recomendaciones = []
    for index, row in df_recomendado.iterrows():
        fundamento = (
            f"**🌍 Mercado recomendado: {row['País']} ({row['Región']})**\n\n"
            f"- **Afinidad del producto**: {row['Afinidad']}\n"
            f"- **Demanda esperada**: {row['Demanda esperada']}\n"
            f"- **Facilidad para hacer negocios**: {row['Facilidad para hacer negocios']}\n"
            f"- **Beneficios arancelarios**: {row['Beneficios arancelarios']}\n"
            f"- **Estabilidad política**: {row['Estabilidad política']}\n\n"
            "✅ Este mercado presenta condiciones favorables para exportar tu producto, considerando su afinidad, demanda y entorno económico y político."
        )
        recomendaciones.append(fundamento)
    
    return df_recomendado[['País', 'Región', 'Puntaje']], recomendaciones

# Configuración de la app
st.set_page_config(page_title="Recomendador de Mercados", page_icon="🌎")

# Logo
st.image("logo_ccsuy.png", use_container_width=True)

# Título e instrucciones
st.markdown("<h1 style='color: #3E8E41;'>Bienvenido al Recomendador de Mercados de Exportación 🌎</h1>", unsafe_allow_html=True)
st.markdown("🚀 Selecciona tu producto y descubre los mejores mercados para exportarlo. Priorizamos Latinoamérica, pero puedes explorar también el resto del mundo.")
with st.expander("ℹ️ ¿Cómo funciona esta herramienta?"):
    st.markdown("""
    Esta aplicación te ayuda a identificar los mejores mercados para exportar productos uruguayos.  
    Se basa en indicadores como:

    - **Afinidad** del producto con cada país (según comercio histórico).
    - **Demanda esperada** (proyección de consumo/importación).
    - **Facilidad para hacer negocios** (índices globales como el Doing Business).
    - **Beneficios arancelarios** (preferencias vigentes entre Uruguay y el país destino).
    - **Estabilidad política** (datos de organismos internacionales como el Banco Mundial o Economist Intelligence Unit).
    """)

# Filtros de preferencia
prioridad_emergentes = st.checkbox("Priorizar mercados emergentes")
distancia_maxima = st.slider("Máxima distancia de exportación (km)", 0, 20000, 10000)
facilidades_exportacion = st.checkbox("Dar prioridad a la facilidad de exportación")

# Selección de producto
producto = st.selectbox("Selecciona tu producto", afinidad_df['Producto'].unique())

# Recomendación principal
if st.button("Obtener recomendaciones"):
    afinidad_producto = afinidad_df[afinidad_df['Producto'] == producto]
    df_recomendado, fundamentos = recomendar_mercados(afinidad_producto, mercados_df, prioridad_emergentes=prioridad_emergentes, distancia_maxima=distancia_maxima, facilidades_exportacion=facilidades_exportacion)

    st.subheader("🌟 Mercados recomendados")
    for i, (mercado, fundamento) in enumerate(zip(df_recomendado['País'], fundamentos)):
        st.markdown(f"**{i+1}. {mercado}**")
        st.markdown(fundamento)
        st.markdown("---")
    
    st.subheader("📊 Tabla de puntajes")
    st.dataframe(df_recomendado)

# Visualización en Mapa
st.subheader("🗺️ Visualización Interactiva en Mapa")
mapa = folium.Map(location=[0, 0], zoom_start=2)
marker_cluster = MarkerCluster().add_to(mapa)

# Agregar marcadores al mapa
for _, row in df_recomendado.iterrows():
    folium.Marker([np.random.uniform(-60, 60), np.random.uniform(-180, 180)], popup=row['País']).add_to(marker_cluster)

st.markdown(mapa._repr_html_(), unsafe_allow_html=True)

# Estilos
st.markdown(""" 
    <style> 
        .stButton > button { background-color: #3E8E41; color: white; font-size: 16px; } 
        .stButton > button:hover { background-color: #45a049; } 
    </style> 
""", unsafe_allow_html=True)
