import streamlit as st
import pandas as pd
import pydeck as pdk

# Cargar los datos localmente
afinidad_df = pd.read_csv("afinidad_producto_país.csv", encoding="ISO-8859-1")
mercados_df = pd.read_csv("mercados.csv", encoding="ISO-8859-1")
acuerdos_df = pd.read_csv("acuerdos_comerciales.csv", encoding="ISO-8859-1")

# Filtrar las columnas de acuerdos comerciales
acuerdos_cols = ['País', 'Acuerdo Comercial', 'Descripción', 'Vigencia', 'Enlace', 'Notas importantes', 'Categorías negociadas']
acuerdos_info = acuerdos_df[acuerdos_cols].drop_duplicates()

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
                0.15 * row['Crecimiento Importaciones (%)'] +
                0.1 * row['Facilidad Negocios (WB 2019)'] +
                0.15 * row['PIB per cápita (USD)']
            )
        else:
            return (
                0.4 * row['Afinidad'] +
                0.25 * row['Crecimiento Importaciones (%)'] +
                0.2 * row['Facilidad Negocios (WB 2019)'] +
                0.15 * row['PIB per cápita (USD)']
            )
    
    df_completo['Puntaje'] = df_completo.apply(calcular_puntaje, axis=1)

    top_latam = df_completo[df_completo['Región'] == 'Latinoamérica'].sort_values(by='Puntaje', ascending=False).head(3)
    top_global = df_completo[df_completo['Región'] == 'Resto del Mundo'].sort_values(by='Puntaje', ascending=False).head(2 + extra_global)

    df_recomendado = pd.concat([top_latam, top_global])

    recomendaciones = []
    for index, row in df_recomendado.iterrows():
        acuerdos_pais = acuerdos_info[acuerdos_info['País'] == row['País']]
        acuerdos_texto = ""
        if not acuerdos_pais.empty:
            acuerdos_texto = "\n\n**Acuerdos Comerciales:**\n"
            for _, ac in acuerdos_pais.iterrows():
                acuerdos_texto += f"- **{ac['Acuerdo Comercial']}**: {ac['Descripción']} (Vigencia: {ac['Vigencia']}) - [Ver más]({ac['Enlace']})\n"
        
        fundamento = (
            f"**🌍 Mercado recomendado: {row['País']} ({row['Región']})**\n\n"
            f"- **Afinidad del producto**: {row['Afinidad']}\n"
            f"- **Crecimiento Importaciones**: {row['Crecimiento Importaciones (%)']}%\n"
            f"- **Facilidad para hacer negocios**: {row['Facilidad Negocios (WB 2019)']}\n"
            f"- **PIB per cápita**: {row['PIB per cápita (USD)']}\n\n"
            f"{acuerdos_texto}\n"
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
    st.markdown("""Esta aplicación te ayuda a identificar los mejores mercados para exportar productos uruguayos. Se basa en indicadores como: 
    - **Afinidad** del producto con cada país.
    - **Crecimiento de las importaciones**.
    - **Facilidad para hacer negocios**.
    - **PIB per cápita**.
    - **Acuerdos comerciales** existentes.
    👇 Elegí tu producto y explorá las recomendaciones.""")

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
