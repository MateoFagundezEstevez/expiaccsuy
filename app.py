import streamlit as st
import pandas as pd
import folium
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from geopy.distance import geodesic
import matplotlib.pyplot as plt
import plotly.express as px

# Cargar los archivos CSV con codificación 'ISO-8859-1' para evitar errores de codificación
mercados_df = pd.read_csv('mercados.csv', encoding='ISO-8859-1')
afinidad_df = pd.read_csv('afinidad_producto_país.csv', encoding='ISO-8859-1')

# Mapeo de las métricas en los archivos CSV
mercados_df['Facilidad Negocios'] = mercados_df['Facilidad Negocios (WB 2019)']
mercados_df['PIB per cápita (USD)'] = mercados_df['PIB per cápita (USD)']
mercados_df['Crecimiento Anual PIB'] = mercados_df['Crecimiento Anual PIB (%)']
mercados_df['Tamaño del Mercado'] = mercados_df['Tamaño del Mercado Total (Millones USD)']
mercados_df['Población'] = mercados_df['Población (Millones)']
mercados_df['Logística'] = mercados_df['Logística (LPI 2023)']
mercados_df['Crecimiento Importaciones'] = mercados_df['Crecimiento Importaciones (%)']
mercados_df['Sofisticación Exportaciones'] = mercados_df['Sofisticación Exportaciones (Score)']
mercados_df['Población Urbana'] = mercados_df['Población Urbana (%)']
mercados_df['Infraestructura Portuaria'] = mercados_df['Infraestructura Portuaria (LPI 2023)']
mercados_df['Distancia a Uruguay'] = mercados_df['Distancia a Uruguay (km)']

# Función para calcular la afinidad de un producto en un mercado
def calcular_afinidad(producto, mercado):
    # Combinar los datos de afinidad y mercados
    afinidad_producto = afinidad_df[afinidad_df['Producto'] == producto]
    mercado_datos = mercados_df[mercados_df['País'] == mercado].iloc[0]
    
    if afinidad_producto.empty:
        return 0
    
    afinidad = afinidad_producto[mercado].values[0]
    
    # Normalizar y ponderar los valores
    scaler = MinMaxScaler()
    scaler.fit(mercados_df[['Facilidad Negocios', 'PIB per cápita (USD)', 'Crecimiento Anual PIB', 
                            'Tamaño del Mercado', 'Población', 'Logística', 'Crecimiento Importaciones', 
                            'Sofisticación Exportaciones', 'Población Urbana', 'Infraestructura Portuaria']])
    mercado_normalizado = scaler.transform(mercado_datos[['Facilidad Negocios', 'PIB per cápita (USD)', 'Crecimiento Anual PIB', 
                                                         'Tamaño del Mercado', 'Población', 'Logística', 'Crecimiento Importaciones', 
                                                         'Sofisticación Exportaciones', 'Población Urbana', 'Infraestructura Portuaria']].values.reshape(1, -1))
    
    # Ponderación de afinidad
    peso_afinidad = 0.3
    peso_mercado = 0.7
    
    afinidad_ponderada = afinidad * peso_afinidad
    mercado_ponderado = np.dot(mercado_normalizado, np.array([peso_mercado]))
    
    return afinidad_ponderada + mercado_ponderado[0]

# Función para calcular la distancia geográfica a Uruguay
def calcular_distancia(lat, lon):
    uruguay_coords = (-32.5228, -55.7652)  # Coordenadas de Uruguay
    return geodesic(uruguay_coords, (lat, lon)).kilometers

# Función para crear un mapa interactivo de los mercados
def crear_mapa():
    # Centro del mapa (aproximadamente en el centro de América Latina)
    m = folium.Map(location=[-15.7942, -47.9292], zoom_start=3)
    
    # Agregar marcadores para cada mercado
    for index, row in mercados_df.iterrows():
        folium.Marker([row['Latitud'], row['Longitud']], popup=row['País']).add_to(m)
    
    return m

# Interfaz de usuario
st.title("Recomendación de Mercados de Exportación")
st.write("Explora los mercados más atractivos para exportar productos desde Uruguay.")

# Selección de producto
producto = st.selectbox("Selecciona un producto:", afinidad_df['Producto'].unique())

# Cálculo de afinidad para todos los mercados
mercados_df['Afinidad'] = mercados_df['País'].apply(lambda x: calcular_afinidad(producto, x))

# Selección de mercado recomendado
mercado_recomendado = mercados_df.loc[mercados_df['Afinidad'].idxmax()]

# Mostrar la recomendación
st.subheader(f"Mercado recomendado: {mercado_recomendado['País']}")
st.write(f"Afinidad estimada: {mercado_recomendado['Afinidad']:.2f}")
st.write(f"Distancia a Uruguay: {mercado_recomendado['Distancia a Uruguay']:.2f} km")

# Mostrar mapa interactivo
st.subheader("Mapa de Mercados")
mapa = crear_mapa()
st.write(mapa)

# Mostrar gráficos de análisis
st.subheader("Análisis de Mercados")

# Gráfico de barras de afinidad por mercado
fig, ax = plt.subplots(figsize=(10, 6))
mercados_df.plot(kind='bar', x='País', y='Afinidad', ax=ax)
ax.set_title('Afinidad de Mercados por Producto')
ax.set_ylabel('Afinidad')
ax.set_xlabel('Mercado')
st.pyplot(fig)

# Gráfico de dispersión de PIB vs Población
fig2 = px.scatter(mercados_df, x='PIB per cápita', y='Población', color='País', 
                  title='PIB per cápita vs Población por Mercado')
st.plotly_chart(fig2)
