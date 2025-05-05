import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

# Intentar cargar los datos con distintas codificaciones y delimitadores
try:
    # Intentar cargar con codificación UTF-8 y delimitador por defecto (coma)
    mercados_df = pd.read_csv("mercados.csv", encoding="utf-8")
except UnicodeDecodeError:
    # Si hay error de codificación, intentar con Latin1
    mercados_df = pd.read_csv("mercados.csv", encoding="latin1")
except Exception as e:
    st.error(f"Error al cargar el archivo mercados.csv: {e}")

# Si el archivo no tiene el delimitador por coma, intentar con punto y coma
if mercados_df.empty:
    try:
        mercados_df = pd.read_csv("mercados.csv", encoding="utf-8", sep=";")
    except Exception as e:
        st.error(f"Error al cargar el archivo mercados.csv con punto y coma: {e}")

# Verificar si el DataFrame tiene contenido
if mercados_df.empty:
    st.error("El archivo mercados.csv está vacío o tiene un formato incorrecto.")

# Mostrar una muestra de los datos cargados para verificar
st.write(mercados_df.head())

# Lista de países de Latinoamérica
latinoamerica = [
    "Argentina", "Brasil", "Paraguay", "Chile", "Bolivia", "Perú", "Colombia", "Ecuador", 
    "México", "Panamá", "Costa Rica", "República Dominicana", "Guatemala", "El Salvador", 
    "Honduras", "Nicaragua", "Venezuela", "Uruguay", "Cuba", "Haití", "Puerto Rico", "Belice", 
    "Jamaica", "Trinidad y Tobago", "Barbados", "Guyana", "Surinam"
]

# Función para recomendar mercados
def recomendar_mercados(afinidad_producto, mercados_df, extra_global=0):
    mercados_df['Región'] = mercados_df['País'].apply(lambda x: 'Latinoamérica' if x in latinoamerica else 'Resto del Mundo')
    df_completo = pd.merge(afinidad_producto[['País', 'Afinidad']], mercados_df, on='País', how='inner')

    def calcular_puntaje(row):
        if row['Región'] == 'Latinoamérica':
            return (
                0.6 * row['Afinidad'] +
                0.15 * row['Demanda esperada'] +
                0.1 * row['Facilidad para hacer negocios'] +
                0.15 * row['Estabilidad política']
            )
        else:
            return (
                0.4 * row['Afinidad'] +
                0.25 * row['Demanda esperada'] +
                0.2 * row['Facilidad para hacer negocios'] +
                0.15 * row['Estabilidad política']
            )
    
    df_completo['Puntaje'] = df_completo.apply(calcular_puntaje, axis=1)

    top_latam = df_completo[df_completo['Región'] == 'Latinoamérica'].sort_values(by='Puntaje', ascending=False).head(3)
    top_global = df_completo[df_completo['Región'] == 'Resto del Mundo'].sort_values(by='Puntaje', ascending=False).head(2 + extra_global)

    df_recomendado = pd.concat([top_latam, top_global])

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
    
    return df_recomendado[['País', 'Región', 'Puntaje', 'Latitud', 'Longitud']], recomendaciones

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

