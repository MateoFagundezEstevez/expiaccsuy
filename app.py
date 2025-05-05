import pandas as pd
import streamlit as st
import random
import folium
from folium.plugins import MarkerCluster

# Cargar los archivos CSV
mercados = pd.read_csv('mercados.csv')
afinidad_producto_pais = pd.read_csv('afinidad_producto_pais.csv')

# Función para normalizar un valor en un rango [0, 1]
def normalizar(valor, min_val, max_val, inverso=False):
    if inverso:
        return 1 - (valor - min_val) / (max_val - min_val)
    else:
        return (valor - min_val) / (max_val - min_val)

# Función para calcular la afinidad ponderada considerando todas las métricas
def calcular_afinidad(pais, producto, mercados, afinidad_producto_pais):
    # Filtrar los datos del mercado
    mercado = mercados[mercados['País'] == pais].iloc[0]
    
    # Filtrar las métricas específicas para el producto
    afinidad = afinidad_producto_pais[(afinidad_producto_pais['Producto'] == producto) & 
                                      (afinidad_producto_pais['País'] == pais)].iloc[0]
    
    # Normalizar las métricas
    facilidad_negocios = normalizar(mercado['Facilidad Negocios (WB 2019)'], mercados['Facilidad Negocios (WB 2019)'].min(), mercados['Facilidad Negocios (WB 2019)'].max())
    tamano_mercado = normalizar(mercado['Tamaño del Mercado Total (Millones USD)'], mercados['Tamaño del Mercado Total (Millones USD)'].min(), mercados['Tamaño del Mercado Total (Millones USD)'].max())
    crecimiento_pib = normalizar(mercado['Crecimiento Anual PIB (%)'], mercados['Crecimiento Anual PIB (%)'].min(), mercados['Crecimiento Anual PIB (%)'].max())
    crecimiento_importaciones = normalizar(mercado['Crecimiento Importaciones (%)'], mercados['Crecimiento Importaciones (%)'].min(), mercados['Crecimiento Importaciones (%)'].max())
    logistica = normalizar(mercado['Logística (LPI 2023)'], mercados['Logística (LPI 2023)'].min(), mercados['Logística (LPI 2023)'].max())
    distancia = normalizar(mercado['Distancia a Uruguay (km)'], mercados['Distancia a Uruguay (km)'].min(), mercados['Distancia a Uruguay (km)'].max(), inverso=True)
    
    # Incluir la afinidad (producto)
    afinidad_producto = afinidad['Afinidad']  # La afinidad ya está calculada para cada producto
    
    # Ponderación de las métricas
    peso_facilidad_negocios = 0.15
    peso_tamano_mercado = 0.2
    peso_crecimiento_pib = 0.1
    peso_crecimiento_importaciones = 0.1
    peso_logistica = 0.1
    peso_distancia = 0.1
    peso_afinidad_producto = 0.25  # Afinidad como una variable adicional con su propio peso
    
    puntaje_base = (facilidad_negocios * peso_facilidad_negocios +
                    tamano_mercado * peso_tamano_mercado +
                    crecimiento_pib * peso_crecimiento_pib +
                    crecimiento_importaciones * peso_crecimiento_importaciones +
                    logistica * peso_logistica +
                    distancia * peso_distancia +
                    afinidad_producto * peso_afinidad_producto)
    
    # Escalar el puntaje final (de 0 a 100)
    puntaje_final = min(max(puntaje_base * 100, 0), 100)
    
    return puntaje_final

# Función para recomendar mercados para un producto
def recomendar_mercados(producto, mercados, afinidad_producto_pais):
    recomendaciones = []
    
    # Para cada país, calcular la afinidad ponderada
    for pais in mercados['País']:
        afinidad = calcular_afinidad(pais, producto, mercados, afinidad_producto_pais)
        recomendaciones.append({'País': pais, 'Afinidad': afinidad})
    
    # Convertir la lista de recomendaciones en un DataFrame
    df_recomendado = pd.DataFrame(recomendaciones)
    
    # Ordenar los países por afinidad (de mayor a menor)
    df_recomendado = df_recomendado.sort_values(by='Afinidad', ascending=False)
    
    return df_recomendado

# Función para crear el mapa con los países recomendados
def crear_mapa(df_recomendado, mercados):
    # Crear un mapa centrado en América Latina
    mapa = folium.Map(location=[-20, -60], zoom_start=3)
    
    # Crear un grupo de marcadores para las recomendaciones
    marker_cluster = MarkerCluster().add_to(mapa)
    
    # Añadir marcadores para los países recomendados
    for _, row in df_recomendado.iterrows():
        pais = row['País']
        latitud = mercados[mercados['País'] == pais]['Latitud'].values[0]
        longitud = mercados[mercados['País'] == pais]['Longitud'].values[0]
        folium.Marker([latitud, longitud], popup=f"{pais}: {row['Afinidad']}").add_to(marker_cluster)
    
    return mapa

# Título y descripción de la aplicación
st.title("Recomendador de Mercados de Exportación")
st.write("""
Este es un sistema que recomienda mercados internacionales para la exportación de productos, basado en una serie de métricas de países y productos.
""")

st.write("""
## ¿Cómo funciona la aplicación?

La recomendación de mercados se calcula tomando en cuenta varias métricas clave de cada país y de los productos seleccionados. Estas métricas son ponderadas en función de su relevancia para la oportunidad de exportación, de la siguiente manera:

1. **Facilidad para hacer negocios**: Basado en el índice del Banco Mundial (WB 2019), mide cuán fácil es hacer negocios en un país.
2. **Tamaño del mercado**: Medido a través del PIB total del país.
3. **Crecimiento anual del PIB**: Representa el porcentaje de crecimiento de la economía de un país.
4. **Crecimiento anual de las importaciones**: Indica el aumento de las importaciones en ese país.
5. **Performance logística**: Basado en el índice de desempeño logístico (LPI 2023), mide la calidad de la infraestructura logística del país.
6. **Distancia geográfica**: La distancia en kilómetros desde Uruguay al país en cuestión. Las distancias más cortas reciben un puntaje más alto.
7. **Afinidad del producto**: Cada producto tiene un puntaje de afinidad calculado específicamente para cada país, basado en sus características.

### Ponderación de las métricas:
Cada una de estas métricas tiene un peso asignado que refleja su importancia en la recomendación de exportación:

- **Facilidad para hacer negocios**: 15%
- **Tamaño del mercado**: 20%
- **Crecimiento anual del PIB**: 10%
- **Crecimiento anual de las importaciones**: 10%
- **Performance logística**: 10%
- **Distancia**: 10%
- **Afinidad del producto**: 25%

Cada métrica se normaliza en una escala de 0 a 1 para hacerla comparable, y luego se pondera según su peso. Finalmente, todas las métricas ponderadas se suman para generar un puntaje final que se ajusta a un rango de 0 a 100. Los países con los puntajes más altos son los recomendados para la exportación del producto seleccionado.
""")

# Ingresar el producto
producto = st.selectbox("Selecciona un Producto", afinidad_producto_pais['Producto'].unique())

# Obtener las recomendaciones
df_recomendado = recomendar_mercados(producto, mercados, afinidad_producto_pais)

# Mostrar las recomendaciones
if df_recomendado is not None and not df_recomendado.empty:
    st.dataframe(df_recomendado)
    
    # Crear y mostrar el mapa interactivo con los países recomendados
    mapa = crear_mapa(df_recomendado, mercados)
    st.write(mapa)
else:
    st.error("No se encontraron datos para mostrar.")
