import streamlit as st
import pandas as pd
import numpy as np

# Cargar los datos localmente
afinidad_df = pd.read_csv("afinidad_producto_país.csv", encoding="ISO-8859-1")
mercados_df = pd.read_csv("mercados.csv", encoding="ISO-8859-1")

# Definir la función principal
def recomendar_mercados(afinidad_producto, mercados_df, extra_global=0):
    # Lista de países de Latinoamérica
    latinoamerica = [
        "Argentina", "Brasil", "Paraguay", "Chile", "Bolivia", "Perú", "Colombia", "Ecuador", 
        "México", "Panamá", "Costa Rica", "República Dominicana", "Guatemala", "El Salvador", 
        "Honduras", "Nicaragua", "Venezuela", "Uruguay", "Cuba", "Haití", "Puerto Rico", "Belice", 
        "Jamaica", "Trinidad y Tobago", "Barbados", "Guyana", "Surinam"
    ]

    # Clasificar región
    mercados_df['Región'] = mercados_df['País'].apply(lambda x: 'Latinoamérica' if x in latinoamerica else 'Resto del Mundo')

    # Unir datasets
    df_completo = pd.merge(afinidad_producto[['País', 'Afinidad']], mercados_df, on='País', how='inner')

    # Calcular puntajes ponderados
    def calcular_puntaje(row):
        if row['Región'] == 'Latinoamérica':
            return (
                0.6 * row['Afinidad'] +
                0.15 * row['Tamaño del Mercado Total (Millones USD)'] +
                0.1 * row['Facilidad Negocios (WB 2019)'] +
                0.15 * row['Crecimiento Anual PIB (%)']
            )
        else:
            return (
                0.4 * row['Afinidad'] +
                0.25 * row['Tamaño del Mercado Total (Millones USD)'] +
                0.2 * row['Facilidad Negocios (WB 2019)'] +
                0.15 * row['Crecimiento Anual PIB (%)']
            )
    
    df_completo['Puntaje'] = df_completo.apply(calcular_puntaje, axis=1)

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
            f"- **Tamaño del Mercado Total**: {row['Tamaño del Mercado Total (Millones USD)']}\n"
            f"- **Facilidad para hacer negocios**: {row['Facilidad Negocios (WB 2019)']}\n"
            f"- **Crecimiento Anual PIB**: {row['Crecimiento Anual PIB (%)']}\n\n"
            "✅ Este mercado presenta condiciones favorables para exportar tu producto, considerando su afinidad, tamaño de mercado y crecimiento económico."
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
    - **Tamaño del Mercado Total** (en millones de USD).
    - **Facilidad para hacer negocios** (índices globales como el Doing Business).
    - **Crecimiento Anual del PIB** (proyección de crecimiento económico).

    Los mercados se priorizan primero en **Latinoamérica** (mayor cercanía y afinidad cultural), y luego se muestran las mejores opciones del **resto del mundo**.

    Los datos fueron extraídos y consolidados desde fuentes como:
    - Banco Mundial
    - Banco Interamericano de Desarrollo (BID)
    - OMC
    - Trademap (ITC)
    - Cámara de Comercio y Servicios del Uruguay

    👇 Elegí tu producto y explorá las recomendaciones.
    """)

# Selección de producto
producto = st.selectbox("Selecciona tu producto", afinidad_df['Producto'].unique())

# Recomendación principal
if st.button("Obtener recomendaciones"):
    afinidad_producto = afinidad_df[afinidad_df['Producto'] == producto]
    df_recomendado, fundamentos = recomendar_mercados(afinidad_producto, mercados_df)

    st.subheader("🌟 Mercados recomendados (con prioridad LATAM)")
    for i, (mercado, fundamento) in enumerate(zip(df_recomendado['País'], fundamentos)):
        st.markdown(f"**{i+1}. {mercado}**")
        st.markdown(fundamento)
        st.markdown("---")
    
    st.subheader("📊 Tabla de puntajes")
    st.dataframe(df_recomendado)

    # Expandible para más mercados globales
    with st.expander("🔍 Ver más mercados del Resto del Mundo (opcional)"):
        extra_count = st.slider("¿Cuántos mercados adicionales del mundo quieres ver?", min_value=1, max_value=10, value=3)
        df_ext, fundamentos_ext = recomendar_mercados(afinidad_producto, mercados_df, extra_global=extra_count)
        nuevos_globales = df_ext[~df_ext['País'].isin(df_recomendado['País']) & (df_ext['Región'] == "Resto del Mundo")]

        for i, row in nuevos_globales.iterrows():
            st.markdown(f"**🌐 {row['País']}** - Puntaje: {round(row['Puntaje'], 2)}")
        st.dataframe(nuevos_globales)

# Estilos
st.markdown(""" 
    <style> 
        .stButton > button { background-color: #3E8E41; color: white; font-size: 16px; } 
        .stButton > button:hover { background-color: #45a049; } 
    </style> 
""", unsafe_allow_html=True)
