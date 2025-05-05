import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from sklearn.preprocessing import MinMaxScaler

# Cargar los datos localmente
afinidad_df = pd.read_csv("afinidad_producto_país.csv", encoding="ISO-8859-1")
mercados_df = pd.read_csv("mercados.csv", encoding="ISO-8859-1")

# Lista de países de Latinoamérica
latinoamerica = [
    "Argentina", "Brasil", "Paraguay", "Chile", "Bolivia", "Perú", "Colombia", "Ecuador", 
    "México", "Panamá", "Costa Rica", "República Dominicana", "Guatemala", "El Salvador", 
    "Honduras", "Nicaragua", "Venezuela", "Uruguay", "Cuba", "Haití", "Puerto Rico", "Belice", 
    "Jamaica", "Trinidad y Tobago", "Barbados", "Guyana", "Surinam"
]

# Función para normalizar las variables
def normalizar_variables(df):
    scaler = MinMaxScaler()
    variables = ['Facilidad Negocios (WB 2019)', 'Tamaño del Mercado Total (Millones USD)', 
                 'Crecimiento Anual PIB (%)', 'Crecimiento Importaciones (%)', 'Logística (LPI 2023)', 
                 'Distancia a Uruguay (km)']
    df[variables] = scaler.fit_transform(df[variables])
    return df

# Función para recomendar mercados
def recomendar_mercados(afinidad_producto, mercados_df, extra_global=0):
    # Normalizar las variables
    mercados_df = normalizar_variables(mercados_df)

    # Añadir la región (Latinoamérica o Resto del Mundo)
    mercados_df['Región'] = mercados_df['País'].apply(lambda x: 'Latinoamérica' if x in latinoamerica else 'Resto del Mundo')
    
    # Fusionar los datos de afinidad con los de mercados
    df_completo = pd.merge(afinidad_producto[['País', 'Afinidad']], mercados_df, on='País', how='inner')

    # Función para calcular el puntaje ponderado
    def calcular_puntaje(row):
        # Ponderación para Latinoamérica y Resto del Mundo
        if row['Región'] == 'Latinoamérica':
            puntaje = (
                0.15 * row['Afinidad'] +
                0.25 * row['Facilidad Negocios (WB 2019)'] +
                0.25 * row['Tamaño del Mercado Total (Millones USD)'] +
                0.15 * row['Crecimiento Anual PIB (%)'] +
                0.1 * row['Crecimiento Importaciones (%)'] +
                0.05 * row['Logística (LPI 2023)'] +
                0.05 * (1 - row['Distancia a Uruguay (km)'])  # Invertir distancia (menor distancia, mayor puntaje)
            )
        else:
            puntaje = (
                0.1 * row['Afinidad'] +
                0.2 * row['Facilidad Negocios (WB 2019)'] +
                0.3 * row['Tamaño del Mercado Total (Millones USD)'] +
                0.2 * row['Crecimiento Anual PIB (%)'] +
                0.1 * row['Crecimiento Importaciones (%)'] +
                0.05 * row['Logística (LPI 2023)'] +
                0.05 * (1 - row['Distancia a Uruguay (km)'])  # Invertir distancia (menor distancia, mayor puntaje)
            )
        return puntaje
    
    # Calcular el puntaje para cada mercado
    df_completo['Puntaje'] = df_completo.apply(calcular_puntaje, axis=1)

    # Ordenar por puntaje y seleccionar los mejores mercados
    top_latam = df_completo[df_completo['Región'] == 'Latinoamérica'].sort_values(by='Puntaje', ascending=False).head(3)
    top_global = df_completo[df_completo['Región'] == 'Resto del Mundo'].sort_values(by='Puntaje', ascending=False).head(2 + extra_global)

    # Concatenar los mejores mercados
    df_recomendado = pd.concat([top_latam, top_global])

    # Generar las recomendaciones
    recomendaciones = []
    for index, row in df_recomendado.iterrows():
        fundamento = (
            f"**🌍 Mercado recomendado: {row['País']} ({row['Región']})**\n\n"
            f"- **Afinidad del producto**: {row['Afinidad']}\n"
            f"- **Facilidad para hacer negocios**: {row['Facilidad Negocios (WB 2019)']}\n"
            f"- **Tamaño del mercado (PIB)**: {row['Tamaño del Mercado Total (Millones USD)']}\n"
            f"- **Crecimiento PIB**: {row['Crecimiento Anual PIB (%)']}%\n"
            f"- **Crecimiento Importaciones**: {row['Crecimiento Importaciones (%)']}%\n"
            f"- **Logística (LPI 2023)**: {row['Logística (LPI 2023)']}\n"
            f"- **Distancia a Uruguay**: {round(row['Distancia a Uruguay (km)'], 2)} km\n\n"
            f"✅ Este mercado presenta condiciones favorables para exportar tu producto, considerando su afinidad, demanda y entorno económico y político."
        )
        recomendaciones.append(fundamento)

    return df_recomendado[['País', 'Región', 'Puntaje']], recomendaciones

# Configuración de la app
st.set_page_config(page_title="Recomendador de Mercados", page_icon="🌎")
st.image("logo_ccsuy.png", use_container_width=True)

st.markdown("<h1 style='color: #3E8E41;'>Bienvenido al Recomendador de Mercados de Exportación 🌎</h1>", unsafe_allow_html=True)
st.markdown("🚀 Selecciona tu producto y descubre los mejores mercados para exportarlo. Priorizamos Latinoamérica, pero puedes explorar también el resto del mundo.")
with st.expander("ℹ️ ¿Cómo funciona esta herramienta?"):
    st.markdown("""
    Esta aplicación te ayuda a identificar los mejores mercados para exportar productos uruguayos.  
    Se basa en indicadores como:

    - **Afinidad** del producto con cada país.
    - **Demanda esperada**.
    - **Facilidad para hacer negocios**.
    - **Beneficios arancelarios**.
    - **Estabilidad política**.

    👇 Elegí tu producto y explorá las recomendaciones.
    """)

producto = st.selectbox("Selecciona tu producto", afinidad_df['Producto'].unique())

if st.button("Obtener recomendaciones"):
    afinidad_producto = afinidad_df[afinidad_df['Producto'] == producto]
    df_recomendado, fundamentos = recomendar_mercados(afinidad_producto, mercados_df)

    st.subheader("🌟 Mercados recomendados")
    for i, (mercado, fundamento) in enumerate(zip(df_recomendado['País'], fundamentos)):
        st.markdown(f"**{i+1}. {mercado}**")
        st.markdown(fundamento)
        st.markdown("---")
    
    st.subheader("📊 Tabla de puntajes")
    st.dataframe(df_recomendado)

    # Mapa interactivo con pydeck
    st.subheader("🗺️ Mapa de mercados recomendados")

    df_mapa = df_recomendado.dropna(subset=["Latitud", "Longitud"]).copy()

    # Escalar puntaje a color RGB: más puntaje = más verde
    def puntaje_a_color(puntaje):
        if puntaje >= 85:
            return [0, 200, 0, 160]    # Verde intenso
        elif puntaje >= 70:
            return [100, 200, 0, 160]  # Verde-lima
        elif puntaje >= 60:
            return [200, 200, 0, 160]  # Amarillo
        else:
            return [200, 100, 0, 160]  # Naranja

    df_mapa["color"] = df_mapa["Puntaje"].apply(puntaje_a_color)

    mapa = pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(
            latitude=df_mapa["Latitud"].mean(),
            longitude=df_mapa["Longitud"].mean(),
            zoom=1.5,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=df_mapa,
                get_position='[Longitud, Latitud]',
                get_color='color',
                get_radius=80000,
                pickable=True,
            ),
            pdk.Layer(
                "TextLayer",
                data=df_mapa,
                get_position='[Longitud, Latitud]',
                get_text='País',
                get_size=12,
                get_color=[0, 0, 0],
                get_alignment_baseline="'bottom'"
            )
        ],
    )

    st.pydeck_chart(mapa)
