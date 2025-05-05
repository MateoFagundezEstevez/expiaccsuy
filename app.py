import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import streamlit as st
import pydeck as pdk

# Cargar los datos desde los archivos
afinidad_df = pd.read_csv('afinidad_producto_país.csv')
mercados_df = pd.read_csv('mercados.csv')

# Función para calcular la afinidad del producto con los mercados
def calcular_afinidad(row, mercados_df, ponderaciones):
    # Normalizar las métricas del país
    scaler = MinMaxScaler()
    mercados_df[['Facilidad Negocios (WB 2019)', 'PIB per cápita (USD)', 'Crecimiento Anual PIB (%)',
                 'Tamaño del Mercado Total (Millones USD)', 'Población (Millones)', 'Logística (LPI 2023)',
                 'Crecimiento Importaciones (%)', 'Sofisticación Exportaciones (Score)', 'Población Urbana (%)',
                 'Infraestructura Portuaria (LPI 2023)', 'Penetración Internet (%)']] = scaler.fit_transform(
        mercados_df[['Facilidad Negocios (WB 2019)', 'PIB per cápita (USD)', 'Crecimiento Anual PIB (%)',
                     'Tamaño del Mercado Total (Millones USD)', 'Población (Millones)', 'Logística (LPI 2023)',
                     'Crecimiento Importaciones (%)', 'Sofisticación Exportaciones (Score)', 'Población Urbana (%)',
                     'Infraestructura Portuaria (LPI 2023)', 'Penetración Internet (%)']])

    # Calcular el puntaje de afinidad para cada país
    afinidad = []
    for idx, mercado in mercados_df.iterrows():
        puntaje = 0
        for col, peso in ponderaciones.items():
            puntaje += mercado[col] * peso
        afinidad.append(puntaje)
    
    mercados_df['Puntaje'] = afinidad
    return mercados_df

# Función para recomendar los mejores mercados
def recomendar_mercados(afinidad_producto, mercados_df, extra_global=0):
    # Obtener las ponderaciones del producto seleccionado
    ponderaciones = {
        'Facilidad Negocios (WB 2019)': 0.2,
        'PIB per cápita (USD)': 0.1,
        'Crecimiento Anual PIB (%)': 0.1,
        'Tamaño del Mercado Total (Millones USD)': 0.15,
        'Población (Millones)': 0.05,
        'Logística (LPI 2023)': 0.1,
        'Crecimiento Importaciones (%)': 0.05,
        'Sofisticación Exportaciones (Score)': 0.05,
        'Población Urbana (%)': 0.05,
        'Infraestructura Portuaria (LPI 2023)': 0.05,
        'Penetración Internet (%)': 0.1
    }

    # Filtrar los datos por producto
    afinidad_producto = afinidad_producto[afinidad_producto['Producto'] == afinidad_producto['Producto'].iloc[0]]
    
    # Aplicar la función para calcular afinidad
    mercados_df = calcular_afinidad(afinidad_producto, mercados_df, ponderaciones)

    # Ordenar los países por el puntaje de afinidad
    df_recomendado = mercados_df.sort_values(by='Puntaje', ascending=False)

    # Seleccionar los primeros mercados de Latinoamérica
    df_latam = df_recomendado[df_recomendado['País'].isin(['Argentina', 'Brasil', 'México', 'Chile', 'Perú', 'Colombia', 'Ecuador', 'Venezuela', 'Bolivia', 'Paraguay', 'Cuba'])]
    
    # Si se desea incluir mercados globales
    if extra_global > 0:
        df_global = df_recomendado[~df_recomendado['País'].isin(df_latam['País'])]
        df_global = df_global.head(extra_global)
        df_recomendado = pd.concat([df_latam, df_global])

    # Obtener los fundamentos
    fundamentos = []
    for idx, row in df_recomendado.iterrows():
        fundamento = f"**{row['País']}**: Puntaje de afinidad: {round(row['Puntaje'], 2)}. "
        fundamentos.append(fundamento)
    
    return df_recomendado, fundamentos

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
