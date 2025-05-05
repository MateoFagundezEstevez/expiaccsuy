import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import pydeck as pdk

st.set_page_config(page_title="Explorador de Mercados", layout="wide")

# Cargar archivo de mercados
mercados_df = pd.read_csv("mercados.csv")

# Variables a usar con su dirección (1: mejor más alto, -1: mejor más bajo)
variables = {
    'Facilidad Negocios (WB 2019)': 1,
    'PIB per cápita (USD)': 1,
    'Crecimiento Anual PIB (%)': 1,
    'Tamaño del Mercado Total (Millones USD)': 1,
    'Población (Millones)': 1,
    'Logística (LPI 2023)': 1,
    'Infraestructura Portuaria (LPI 2023)': 1,
    'Sofisticación Exportaciones (Score)': 1,
    'Distancia a Uruguay (km)': -1
}

# Normalización y cálculo de puntaje
scaler = MinMaxScaler()
df = mercados_df.copy()

for col, direction in variables.items():
    norm = scaler.fit_transform(df[[col]])
    df[col + "_norm"] = norm * direction

df["Puntaje Oportunidad"] = df[[col + "_norm" for col in variables]].sum(axis=1)

# Ordenar por puntaje
df_sorted = df.sort_values(by="Puntaje Oportunidad", ascending=False)

# Título
st.title("🌎 Recomendador de Mercados de Exportación")
st.markdown("Este análisis se basa exclusivamente en variables estructurales de cada país.")

# Mostrar tabla
st.subheader("🔝 Top 10 Mercados Recomendados")
st.dataframe(df_sorted[['País', 'Puntaje Oportunidad'] + list(variables.keys())].head(10), use_container_width=True)

# Mapa interactivo
st.subheader("🗺️ Mapa de Oportunidad de Mercado")
st.pydeck_chart(pdk.Deck(
    initial_view_state=pdk.ViewState(
        latitude=-15, longitude=-60, zoom=2, pitch=0
    ),
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=df_sorted,
            get_position='[Longitud, Latitud]',
            get_color='[255, 140, 0, 160]',
            get_radius='Puntaje Oportunidad * 30000',
            pickable=True,
        )
    ],
    tooltip={"text": "{País}\nPuntaje: {Puntaje Oportunidad}"}
))
