import pandas as pd
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from geopy.distance import geodesic

# Cargar los archivos CSV
mercados_df = pd.read_csv("mercados.csv", encoding="latin1")
acuerdos_df = pd.read_csv("acuerdos_comerciales.csv", encoding="latin1")

# Función para calcular el puntaje de cada país
def calcular_puntaje(row):
    return (
        0.3 * row['Facilidad Negocios (WB 2019)'] +
        0.2 * row['PIB per cápita (USD)'] + 
        0.1 * row['Crecimiento Anual PIB (%)'] +
        0.15 * row['Tamaño del Mercado Total (Millones USD)'] +
        0.1 * row['Logística (LPI 2023)'] +
        0.05 * row['Crecimiento Importaciones (%)'] +
        0.05 * row['Sofisticación Exportaciones (Score)'] +
        0.05 * row['Infraestructura Portuaria (LPI 2023)'] +
        0.05 * row['Distancia a Uruguay (km)']
    )

# Función para recomendar mercados basados en la afinidad del producto y los mercados disponibles
def recomendar_mercados(afinidad_producto, mercados_df):
    # Calcular puntajes para cada país
    df_completo = mercados_df.copy()
    df_completo['Puntaje'] = df_completo.apply(calcular_puntaje, axis=1)
    
    # Ordenar países por puntaje (del más alto al más bajo)
    df_completo = df_completo.sort_values(by='Puntaje', ascending=False)
    
    # Filtrar los 10 países con los mejores puntajes
    df_recomendado = df_completo.head(10)
    
    # Extract the relevant market data for the report
    fundamentos = {
        "Puntajes": df_recomendado[['País', 'Puntaje']],
        "Otros Datos": df_recomendado[['País', 'Facilidad Negocios (WB 2019)', 'PIB per cápita (USD)', 'Crecimiento Anual PIB (%)', 
                                       'Tamaño del Mercado Total (Millones USD)', 'Logística (LPI 2023)', 'Crecimiento Importaciones (%)', 
                                       'Sofisticación Exportaciones (Score)', 'Infraestructura Portuaria (LPI 2023)', 'Distancia a Uruguay (km)']]
    }

    return df_recomendado, fundamentos

# Interfaz de usuario en Streamlit
st.title('Recomendador de Mercados de Exportación')
st.write("Ingrese la afinidad del producto para obtener recomendaciones de mercados:")

# Asumiendo que 'afinidad_producto' es un diccionario o un conjunto de parámetros para calcular la afinidad
afinidad_producto = {
    # Aquí colocarías los parámetros para el cálculo de afinidad
}

# Obtener las recomendaciones de mercados
df_recomendado, fundamentos = recomendar_mercados(afinidad_producto, mercados_df)

# Mostrar los resultados
st.write("Los 10 mejores mercados recomendados:")
st.dataframe(df_recomendado)

# Mostrar fundamentos detrás de las recomendaciones
st.write("Fundamentos de las recomendaciones:")
st.write(fundamentos["Puntajes"])
st.write(fundamentos["Otros Datos"])

# Mostrar acuerdos comerciales asociados
acuerdos_cols = ['País', 'Acuerdo Comercial', 'Descripción', 'Vigencia', 'Enlace', 'Notas importantes', 'Categorías negociadas']
acuerdos_info = acuerdos_df[acuerdos_cols].drop_duplicates()
st.write("Acuerdos comerciales vigentes:")
st.dataframe(acuerdos_info)

# Mostrar el mapa interactivo con los países recomendados
st.write("Mapa interactivo de los mercados recomendados:")

# Crear un mapa de Folium
mapa = folium.Map(location=[-32.5228, -55.7658], zoom_start=3)  # Coordenadas de Uruguay

# Agregar un marcador por cada país recomendado
marker_cluster = MarkerCluster().add_to(mapa)
for _, row in df_recomendado.iterrows():
    # Añadir un marcador para cada país recomendado
    folium.Marker(
        location=[row['Latitud'], row['Longitud']],
        popup=f"{row['País']}<br>Puntaje: {row['Puntaje']}",
        icon=folium.Icon(color='blue')
    ).add_to(marker_cluster)

# Mostrar el mapa en la app
st.components.v1.html(mapa._repr_html_(), height=500)

# Si el usuario selecciona un país, mostrar más detalles
pais_seleccionado = st.selectbox('Seleccionar un país para más detalles:', df_recomendado['País'])
if pais_seleccionado:
    st.write(f"Detalles para {pais_seleccionado}:")
    pais_info = df_recomendado[df_recomendado['País'] == pais_seleccionado]
    st.write(pais_info)
    
    # Mostrar los acuerdos comerciales para el país seleccionado
    acuerdos_pais = acuerdos_info[acuerdos_info['País'] == pais_seleccionado]
    if not acuerdos_pais.empty:
        st.write(f"Acuerdos comerciales de {pais_seleccionado}:")
        st.dataframe(acuerdos_pais)
    else:
        st.write(f"No hay acuerdos comerciales disponibles para {pais_seleccionado}.")
