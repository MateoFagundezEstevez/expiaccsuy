import pandas as pd
import plotly.express as px
import streamlit as st

# Título de la aplicación
st.title("Recomendación de Mercados de Exportación")

# Agregar el logo de la Cámara de Comercio y Servicios
# Si la imagen está en la misma carpeta que el script, solo debes poner el nombre del archivo.
st.image("logo_ccsuy.png", use_column_width=True)

# Cargar los archivos CSV de mercados y afinidad
try:
    mercados_df = pd.read_csv('mercados.csv', encoding='utf-8')
    afinidad_df = pd.read_csv('afinidad_producto_país.csv', encoding='utf-8')
except Exception as e:
    st.error(f"Error al cargar los archivos CSV: {e}")

# Limpiar los nombres de las columnas (espacios adicionales, mayúsculas/minúsculas inconsistentes)
mercados_df.columns = mercados_df.columns.str.strip()
afinidad_df.columns = afinidad_df.columns.str.strip()

# Verificar que los archivos tengan las columnas necesarias
required_mercados_columns = ['País', 'Tamaño del Mercado Total (Millones USD)', 'Facilidad Negocios (WB 2019)', 
                             'Latitud', 'Longitud', 'PIB per cápita (USD)', 'Crecimiento Anual PIB (%)', 
                             'Logística (LPI 2023)', 'Crecimiento Importaciones (%)', 'Sofisticación Exportaciones (Score)', 
                             'Población Urbana (%)', 'Infraestructura Portuaria (LPI 2023)', 'Distancia a Uruguay (km)']

required_afinidad_columns = ['Producto', 'País', 'Afinidad']

# Verificar que los DataFrames contengan las columnas necesarias
if all(col in mercados_df.columns for col in required_mercados_columns):
    st.write("Datos de mercados cargados correctamente.")
else:
    st.error(f"Faltan columnas necesarias en 'mercados.csv'. Asegúrate de tener las siguientes columnas: {required_mercados_columns}")

if all(col in afinidad_df.columns for col in required_afinidad_columns):
    st.write("Datos de afinidad cargados correctamente.")
else:
    st.error(f"Faltan columnas necesarias en 'afinidad_producto_país.csv'. Asegúrate de tener las siguientes columnas: {required_afinidad_columns}")

# Crear el selectbox para elegir el producto
producto_seleccionado = st.selectbox('Selecciona un producto', afinidad_df['Producto'].unique())

if producto_seleccionado:
    df_producto = afinidad_df[afinidad_df['Producto'] == producto_seleccionado]
    
    # Verificar si el producto seleccionado tiene los datos necesarios
    if 'País' in df_producto.columns and 'Afinidad' in df_producto.columns:
        st.write(f"Recomendaciones de mercados para {producto_seleccionado}:")
        st.dataframe(df_producto[['País', 'Afinidad']])
    else:
        st.write(f"Las columnas 'País' y 'Afinidad' no están presentes para el producto {producto_seleccionado}.")
else:
    st.write("Por favor, selecciona un producto para ver los mercados recomendados.")

# Crear un mapa interactivo con Plotly
fig = px.scatter_geo(mercados_df,
                     locations='País',
                     locationmode='country names',
                     size='Tamaño del Mercado Total (Millones USD)',
                     color='Facilidad Negocios (WB 2019)',
                     hover_name='País',
                     size_max=100,
                     template='plotly',
                     title='Mapa de Mercados Internacionales')

st.plotly_chart(fig)

# Opción para ver la tabla completa de mercados
if st.checkbox("Ver datos completos de mercados"):
    st.dataframe(mercados_df)

# Funcionalidad extra: Visualización de un gráfico de los 10 países con mayor tamaño de mercado
top_10_mercados = mercados_df.nlargest(10, 'Tamaño del Mercado Total (Millones USD)')

fig_top_10 = px.bar(top_10_mercados, 
                    x='País', 
                    y='Tamaño del Mercado Total (Millones USD)', 
                    title='Top 10 de Mercados por Tamaño de Mercado Total',
                    labels={'Tamaño del Mercado Total (Millones USD)': 'Tamaño del Mercado (Millones USD)', 'País': 'País'})
st.plotly_chart(fig_top_10)
