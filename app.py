import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

# Cargar los datos
afinidad_df = pd.read_csv('afinidad_producto_país.csv', encoding='latin1')
mercados_df = pd.read_csv('mercados.csv', encoding='ISO-8859-1')

# Función para recomendar los mejores mercados
def recomendar_mercados(afinidad_producto, mercados_df):
    latinoamerica = [
        "Argentina", "Brasil", "Paraguay", "Chile", "Bolivia", "Perú", "Colombia", "Ecuador", 
        "México", "Panamá", "Costa Rica", "República Dominicana", "Guatemala", "El Salvador", 
        "Honduras", "Nicaragua", "Venezuela", "Uruguay", "Cuba", "Haití", "Puerto Rico", "Belice", 
        "Jamaica", "Trinidad y Tobago", "Barbados", "Guyana", "Surinam"
    ]
    mercados_df['Región'] = mercados_df['País'].apply(lambda x: 'Latinoamérica' if x in latinoamerica else 'Global')

    # Combinar los datos de afinidad con los del mercado
    df_completo = pd.merge(afinidad_producto[['País', 'Afinidad']], mercados_df, on='País', how='inner')

    # Calcular puntaje ponderado (puedes ajustar los pesos)
    def calcular_puntaje(row):
        return (
            0.25 * row["Afinidad"] +
            0.10 * row["Facilidad Negocios (WB 2019)"] +
            0.10 * row["PIB per cápita (USD)"] +
            0.10 * row["Crecimiento Anual PIB (%)"] +
            0.10 * row["Tamaño del Mercado Total (Millones USD)"] +
            0.10 * row["Crecimiento Importaciones (%)"] +
            0.10 * row["Logística (LPI 2023)"] +
            0.05 * row["Sofisticación Exportaciones (Score)"] +
            0.05 * row["Infraestructura Portuaria (LPI 2023)"] +
            0.05 * row["Población Urbana (%)"] -
            0.10 * row["Distancia a Uruguay (km)"]
        )
    
    df_completo['Puntaje'] = df_completo.apply(calcular_puntaje, axis=1)
    df_recomendado = df_completo.sort_values(by='Puntaje', ascending=False).head(5)

    recomendaciones = []
    for _, row in df_recomendado.iterrows():
        fundamento = (
            f"**Mercado recomendado: {row['País']}** 🌟\n\n"
            f"- **Afinidad del producto con el mercado**: {row['Afinidad']}\n"
            f"- **PIB per cápita**: {row['PIB per cápita (USD)']} USD\n"
            f"- **Crecimiento del PIB**: {row['Crecimiento Anual PIB (%)']}%\n"
            f"- **Crecimiento de importaciones**: {row['Crecimiento Importaciones (%)']}%\n"
            f"- **Facilidad para hacer negocios (WB 2019)**: {row['Facilidad Negocios (WB 2019)']}\n"
            f"- **Logística (LPI 2023)**: {row['Logística (LPI 2023)']}\n"
            f"- **Sofisticación exportadora**: {row['Sofisticación Exportaciones (Score)']}\n"
            f"- **Distancia a Uruguay**: {row['Distancia a Uruguay (km)']} km\n\n"
            "🔎 Este mercado muestra condiciones altamente favorables para la exportación de este producto."
        )
        recomendaciones.append(fundamento)
    
    return df_recomendado, recomendaciones

# Interfaz
st.set_page_config(page_title="Recomendador de Mercados de Exportación", page_icon="🌍")
logo_url = "https://www.ccsuy.org.uy/wp-content/uploads/2020/09/camara-comercio-servicios-uruguay-logo.png"
st.image(logo_url, use_column_width=True)

st.markdown("<h1 style='color: #3E8E41;'>Bienvenido al Recomendador de Mercados de Exportación 🌎</h1>", unsafe_allow_html=True)
st.markdown("🚀 **Elige tu producto y descubre los mejores mercados para exportarlo.**")

# Selección
categoria = st.selectbox("Selecciona la categoría de tu producto", afinidad_df['Categoria'].unique())
producto_filtrado = afinidad_df[afinidad_df['Categoria'] == categoria]
producto = st.selectbox("Selecciona tu producto", producto_filtrado['Producto'].unique())

# Resultado
if st.button("Obtener recomendaciones"):
    afinidad_producto = producto_filtrado[producto_filtrado['Producto'] == producto]
    df_recomendado, fundamentos = recomendar_mercados(afinidad_producto, mercados_df)

    st.subheader("Top 5 Mercados recomendados para tu producto:")
    for i, (mercado, fundamento) in enumerate(zip(df_recomendado['País'], fundamentos)):
        st.markdown(f"**{i+1}. {mercado}**")
        st.markdown(fundamento)
        st.markdown("---")

    st.subheader("Detalles de los mercados recomendados")
    st.dataframe(df_recomendado[[
        "País", "Puntaje", "Afinidad", "PIB per cápita (USD)", "Crecimiento Anual PIB (%)",
        "Crecimiento Importaciones (%)", "Facilidad Negocios (WB 2019)", "Logística (LPI 2023)",
        "Sofisticación Exportaciones (Score)", "Distancia a Uruguay (km)"
    ]])

    # Mapa interactivo
    st.subheader("Mapa interactivo de los 5 principales mercados")
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_recomendado,
        get_position='[Longitud, Latitud]',
        get_radius=500000,
        get_color=[0, 128, 255],
        pickable=True,
    )
    view_state = pdk.ViewState(
        latitude=df_recomendado["Latitud"].mean(),
        longitude=df_recomendado["Longitud"].mean(),
        zoom=2,
        pitch=0,
    )
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=view_state,
        layers=[layer],
        tooltip={"text": "{País}\nPuntaje: {Puntaje}"}
    ))

# Estilo
st.markdown("""
    <style>
        .stButton > button {
            background-color: #3E8E41;
            color: white;
            font-size: 16px;
        }
        .stButton > button:hover {
            background-color: #45a049;
        }
    </style>
""", unsafe_allow_html=True)
