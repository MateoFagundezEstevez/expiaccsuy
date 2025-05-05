import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
import folium
from folium.plugins import MarkerCluster

# Cargar los archivos CSV
mercados_df = pd.read_csv('mercados.csv')
afinidad_df = pd.read_csv('afinidad_producto_país.csv')

# Escalado de las variables numéricas
scaler = MinMaxScaler()
mercados_df[['Facilidad Negocios (WB 2019)', 'PIB per cápita (USD)', 'Crecimiento Anual PIB (%)', 
             'Tamaño del Mercado Total (Millones USD)', 'Población (Millones)', 'Logística (LPI 2023)', 
             'Crecimiento Importaciones (%)', 'Sofisticación Exportaciones (Score)', 
             'Población Urbana (%)', 'Infraestructura Portuaria (LPI 2023)', 'Penetración Internet (%)', 
             'Distancia a Uruguay (km)']] = scaler.fit_transform(mercados_df[['Facilidad Negocios (WB 2019)', 'PIB per cápita (USD)', 'Crecimiento Anual PIB (%)', 
             'Tamaño del Mercado Total (Millones USD)', 'Población (Millones)', 'Logística (LPI 2023)', 
             'Crecimiento Importaciones (%)', 'Sofisticación Exportaciones (Score)', 
             'Población Urbana (%)', 'Infraestructura Portuaria (LPI 2023)', 'Penetración Internet (%)', 
             'Distancia a Uruguay (km)']])

# Interfaz de usuario
st.title("Recomendador de Mercados para Exportación")

# Selección del producto
producto = st.selectbox("Selecciona un Producto", afinidad_df['Producto'].unique())

# Filtrar los datos de afinidad por producto seleccionado
afinidad_producto = afinidad_df[afinidad_df['Producto'] == producto]

# Merge de datos para obtener afinidad con las variables de mercados
mercados_con_afinidad = pd.merge(mercados_df, afinidad_producto, on="País", how="inner")
mercados_con_afinidad['Puntaje Afinidad'] = mercados_con_afinidad['Afinidad']  # Usar el puntaje de afinidad

# Ordenar por afinidad
mercados_con_afinidad = mercados_con_afinidad.sort_values(by='Puntaje Afinidad', ascending=False)

# Mostrar recomendaciones
st.write("### Mercados recomendados según afinidad:")
st.dataframe(mercados_con_afinidad[['País', 'Puntaje Afinidad', 'Facilidad Negocios (WB 2019)', 'PIB per cápita (USD)', 'Crecimiento Anual PIB (%)']])

# Visualización del puntaje de afinidad en un gráfico de barras
fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(x='Puntaje Afinidad', y='País', data=mercados_con_afinidad.head(10), ax=ax)
ax.set_title(f"Top 10 países recomendados para la exportación de {producto}")
st.pyplot(fig)

# Crear un mapa interactivo con los países recomendados
st.write("### Mapa interactivo de los países recomendados")

# Crear un mapa base centrado en Uruguay
m = folium.Map(location=[-32.5, -55.5], zoom_start=2)

# Crear un MarkerCluster para los países recomendados
marker_cluster = MarkerCluster().add_to(m)

# Añadir los países recomendados al mapa
for index, row in mercados_con_afinidad.head(10).iterrows():
    folium.Marker(
        location=[row['Latitud'], row['Longitud']],
        popup=f"{row['País']}: Afinidad {row['Puntaje Afinidad']:.2f}",
    ).add_to(marker_cluster)

# Mostrar el mapa
st.write("Mapa interactivo de los países recomendados:")
st.dataframe(m)

# Mostrar información adicional
st.write("""
    La aplicación ha calculado el puntaje de afinidad basado en múltiples factores económicos y logísticos, 
    y recomienda los países con mayor potencial para exportar tu producto.
""")

# Gráfico de dispersión para visualizar la relación entre el PIB per cápita y la facilidad de negocios
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(x='PIB per cápita (USD)', y='Facilidad Negocios (WB 2019)', data=mercados_con_afinidad, hue='Puntaje Afinidad', palette="viridis", ax=ax)
ax.set_title(f"Relación entre PIB per cápita y Facilidad de Negocios para la exportación de {producto}")
st.pyplot(fig)

# Calcular y mostrar la recomendación de países más cercanos en términos de distancia
mercados_con_afinidad['Distancia Relativa'] = mercados_con_afinidad['Distancia a Uruguay (km)'].apply(lambda x: 1 - (x / mercados_con_afinidad['Distancia a Uruguay (km)'].max()))
mercados_con_afinidad['Puntaje Final'] = mercados_con_afinidad['Puntaje Afinidad'] + mercados_con_afinidad['Distancia Relativa']
mercados_con_afinidad = mercados_con_afinidad.sort_values(by='Puntaje Final', ascending=False)

# Mostrar los mercados con el puntaje final más alto
st.write("### Mercados recomendados considerando afinidad y proximidad a Uruguay:")
st.dataframe(mercados_con_afinidad[['País', 'Puntaje Final', 'Puntaje Afinidad', 'Distancia a Uruguay (km)']])

# Mostrar el mapa actualizado
m = folium.Map(location=[-32.5, -55.5], zoom_start=2)
marker_cluster = MarkerCluster().add_to(m)
for index, row in mercados_con_afinidad.head(10).iterrows():
    folium.Marker(
        location=[row['Latitud'], row['Longitud']],
        popup=f"{row['País']}: Puntaje Final {row['Puntaje Final']:.2f}",
    ).add_to(marker_cluster)

st.write("### Mapa interactivo de los países con mayor puntaje final:")
st.dataframe(m)

