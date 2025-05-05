import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler

# Cargar archivos
mercados_df = pd.read_csv('mercados.csv')
afinidad_df = pd.read_csv('afinidad_producto_país.csv')

# Variables seleccionadas de mercados.csv para el cálculo de la afinidad
indicadores = [
    'Tamaño del Mercado Total (Millones USD)', 
    'Crecimiento Anual PIB (%)', 
    'Crecimiento Importaciones (%)', 
    'Facilidad Negocios (WB 2019)', 
    'Logística (LPI 2023)', 
    'Distancia a Uruguay (km)'
]

# Ponderaciones de los indicadores
pesos = {
    'Tamaño del Mercado Total (Millones USD)': 0.30,
    'Crecimiento Anual PIB (%)': 0.15,
    'Crecimiento Importaciones (%)': 0.15,
    'Facilidad Negocios (WB 2019)': 0.15,
    'Logística (LPI 2023)': 0.15,
    'Distancia a Uruguay (km)': 0.10
}

# Normalizar los indicadores
scaler = MinMaxScaler()
df = mercados_df.copy()

for col in indicadores:
    if col == 'Distancia a Uruguay (km)':
        # Normalización inversa para la distancia (menos distancia mejor)
        df[col + '_norm'] = 1 - scaler.fit_transform(df[[col]])
    else:
        df[col + '_norm'] = scaler.fit_transform(df[[col]])

# Calcular la afinidad
df['Afinidad_base'] = sum(df[ind + '_norm'] * pesos[ind] for ind in indicadores)

# Añadir una variación aleatoria a la afinidad (entre -5 y 5)
np.random.seed(42)  # Para reproducibilidad
df['Afinidad'] = df['Afinidad_base'] + np.random.uniform(-5, 5, len(df))

# Escalar la afinidad entre 0 y 100
df['Afinidad'] = df['Afinidad'].clip(0, 100)

# Unir los datos de afinidad calculada con el dataset original de afinidad por producto
df_final = pd.merge(afinidad_df, df[['País', 'Afinidad']], on='País', how='left')

# Interfaz de usuario con Streamlit
st.title("Recomendador de Mercado de Exportación")
st.sidebar.header("Selecciona un Producto")

# Selección del Producto
producto_seleccionado = st.sidebar.selectbox('Selecciona un Producto', afinidad_df['Producto'].unique())

# Filtrar los datos por el producto seleccionado
df_producto = df_final[df_final['Producto'] == producto_seleccionado]

# Mostrar tabla con afinidad calculada para el producto
st.write(f"**Afinidad para el producto '{producto_seleccionado}'**")
st.dataframe(df_producto[['País', 'Afinidad']])

# Crear el mapa interactivo usando Plotly
fig = px.choropleth(
    df_producto,
    locations="País",
    locationmode="country names",
    color="Afinidad",
    color_continuous_scale=px.colors.sequential.Plasma,
    labels={"Afinidad": "Afinidad Calculada"},
    title=f"Afinidad de Mercado para el Producto '{producto_seleccionado}'"
)

# Mostrar el mapa interactivo
st.plotly_chart(fig)

# Mostrar los resultados más relevantes
st.sidebar.header("Resultados Relevantes")
top_resultados = df_producto.sort_values(by='Afinidad', ascending=False).head(10)
st.sidebar.write(top_resultados[['País', 'Afinidad']])
