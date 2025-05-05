import pandas as pd
import streamlit as st
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler

# Cargar los archivos CSV y limpiar los nombres de las columnas
mercados_df = pd.read_csv('mercados.csv', encoding='utf-8')
afinidad_df = pd.read_csv('afinidad_producto_país.csv', encoding='utf-8')

# Limpiar nombres de columnas para evitar problemas de espacios o caracteres invisibles
mercados_df.columns = mercados_df.columns.str.strip()
afinidad_df.columns = afinidad_df.columns.str.strip()

# Título de la aplicación
st.title("Recomendación de Mercados de Exportación")

# Descripción de la app
st.markdown("""
    Esta aplicación ayuda a identificar los mejores mercados de exportación para un producto en función de diversas variables como el PIB per cápita, la facilidad para hacer negocios, la logística, y la afinidad por producto. 
    Los datos de los países están basados en diferentes indicadores económicos y comerciales.
""")

# Mostrar las primeras filas de los dataframes para revisar los datos cargados
st.write("Mercados DataFrame:")
st.write(mercados_df.head())
st.write("Afinidad DataFrame:")
st.write(afinidad_df.head())

# Verificar si la columna 'PIB per cápita (USD)' existe en mercados_df
if 'PIB per cápita (USD)' in mercados_df.columns:
    st.write("La columna 'PIB per cápita (USD)' está presente.")
else:
    st.write("La columna 'PIB per cápita (USD)' NO está presente.")

# Crear una columna extra para PIB per cápita si es necesario
mercados_df['PIB per cápita'] = mercados_df['PIB per cápita (USD)']  # Verificar si el nombre de la columna es correcto

# Preprocesamiento para combinar las variables y calcular un puntaje
scaler = MinMaxScaler()

# Normalizar las variables numéricas en el DataFrame
mercados_df[['PIB per cápita', 'Facilidad Negocios (WB 2019)', 'Logística (LPI 2023)', 'Tamaño del Mercado Total (Millones USD)', 'Población (Millones)']] = scaler.fit_transform(
    mercados_df[['PIB per cápita', 'Facilidad Negocios (WB 2019)', 'Logística (LPI 2023)', 'Tamaño del Mercado Total (Millones USD)', 'Población (Millones)']]
)

# Selección del producto para recomendar mercados
producto = st.selectbox(
    "Selecciona el producto para el cual deseas recomendaciones:",
    afinidad_df['Producto'].unique()
)

# Filtrar el DataFrame de afinidad para el producto seleccionado
afinidad_producto = afinidad_df[afinidad_df['Producto'] == producto]

# Normalizar la columna 'Afinidad' para que se integre correctamente con las otras variables
afinidad_df['Afinidad Normalizada'] = scaler.fit_transform(afinidad_df[['Afinidad']])

# Combinar los DataFrames de mercados y afinidad por país
mercados_afinidad = pd.merge(mercados_df, afinidad_producto[['País', 'Afinidad Normalizada']], on='País')

# Calcular un puntaje ponderado para cada país
mercados_afinidad['Puntaje'] = (
    0.2 * mercados_afinidad['PIB per cápita'] +
    0.2 * mercados_afinidad['Facilidad Negocios (WB 2019)'] +
    0.2 * mercados_afinidad['Logística (LPI 2023)'] +
    0.2 * mercados_afinidad['Tamaño del Mercado Total (Millones USD)'] +
    0.2 * mercados_afinidad['Afinidad Normalizada']
)

# Ordenar los países según el puntaje
mercados_afinidad = mercados_afinidad.sort_values(by='Puntaje', ascending=False)

# Mostrar los mercados recomendados
st.write(f"Mercados recomendados para {producto}:")
st.write(mercados_afinidad[['País', 'Puntaje', 'PIB per cápita', 'Facilidad Negocios (WB 2019)', 'Logística (LPI 2023)', 'Tamaño del Mercado Total (Millones USD)']])

# Mapa interactivo
fig = px.scatter_geo(mercados_afinidad,
                     locations='País',
                     size='Población (Millones)',
                     hover_name='País',
                     size_max=100,
                     projection='natural earth',
                     title="Mapa de Países por Tamaño de Población")
st.plotly_chart(fig)

# Mostrar las 5 mejores recomendaciones de mercados
top_mercados = mercados_afinidad.head(5)
st.write("Top 5 mercados recomendados:")
st.write(top_mercados[['País', 'Puntaje', 'PIB per cápita', 'Facilidad Negocios (WB 2019)', 'Logística (LPI 2023)', 'Tamaño del Mercado Total (Millones USD)']])

# Generar un gráfico de barras con el puntaje para cada mercado
fig2 = px.bar(mercados_afinidad,
              x='País',
              y='Puntaje',
              title=f"Puntaje de Mercados para {producto}",
              labels={'Puntaje': 'Puntaje de Recomendación', 'País': 'País'})
st.plotly_chart(fig2)

# Detalles sobre las recomendaciones
st.markdown("""
    ### Otros Indicadores Clave:
    - PIB per cápita
    - Facilidad para hacer negocios
    - Logística
    - Tamaño del mercado
    - Afinidad por producto
""")
