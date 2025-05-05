import streamlit as st
import pandas as pd

# Cargar los archivos CSV
afinidad_df = pd.read_csv("afinidad_producto_país.csv")
mercados_df = pd.read_csv("mercados.csv")

# Mostrar el logo de la Cámara de Comercio y Servicios de Uruguay
st.image("logo_ccsuy.png", width=200)

# Título de la aplicación
st.title("Sistema de Recomendación de Mercados de Exportación")

# Introducción
st.markdown("Bienvenido a la plataforma de recomendaciones de mercados de exportación.")
st.markdown("Selecciona el producto que deseas exportar y te recomendaremos los mejores mercados.")

# Desplegar el selectbox para elegir el producto
producto = st.selectbox("Selecciona el producto", afinidad_df['Producto'].unique())

# Filtrar los países con mayor afinidad para el producto seleccionado
afinidad_producto = afinidad_df[afinidad_df['Producto'] == producto]

# Ordenar los países por afinidad en orden descendente
afinidad_producto = afinidad_producto.sort_values(by='Afinidad', ascending=False)

# Mostrar los 5 mejores países
top_5_paises = afinidad_producto.head(5)

# Mostrar las recomendaciones de países con su afinidad
st.subheader("Los 5 mejores mercados de exportación para tu producto son:")

for idx, row in top_5_paises.iterrows():
    st.write(f"**{row['País']}** - Afinidad: {row['Afinidad']}")

# Sugerencia opcional para ver la información del archivo CSV
st.checkbox("Ver detalles del CSV de afinidad", key="mostrar_csv_afinidad")

if st.session_state.mostrar_csv_afinidad:
    st.write(afinidad_df)

# Lógica para mostrar la información de los mercados (opcional)
st.checkbox("Ver detalles de los mercados", key="mostrar_csv_mercados")

if st.session_state.mostrar_csv_mercados:
    st.write(mercados_df)

# Mostrar los 5 mejores mercados según los índices de los CSV de mercados
st.subheader("Recomendaciones globales de mercados")

# Ponderación de los mejores mercados en Latinoamérica primero
mercados_df = mercados_df.sort_values(by=["Facilidad para hacer negocios", "Demanda esperada", "Beneficios arancelarios", "Estabilidad política"], ascending=False)
top_5_mercados = mercados_df.head(5)

# Mostrar los 5 mejores mercados
for idx, row in top_5_mercados.iterrows():
    st.write(f"**{row['País']}** - Facilidad para hacer negocios: {row['Facilidad para hacer negocios']}, Demanda esperada: {row['Demanda esperada']}, Beneficios arancelarios: {row['Beneficios arancelarios']}, Estabilidad política: {row['Estabilidad política']}")
