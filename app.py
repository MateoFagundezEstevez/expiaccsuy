import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Cargar los archivos CSV
afinidad_df = pd.read_csv("afinidad_producto_país.csv")
mercados_df = pd.read_csv("mercados.csv")
acuerdos_df = pd.read_csv("acuerdos_comerciales.csv")

# Función para calcular la afinidad ajustada
def calcular_afinidad(producto, mercados_df, afinidad_df, acuerdos_df):
    # Filtrar afinidad para el producto específico
    afinidad_producto = afinidad_df[afinidad_df['Producto'] == producto]
    
    # Fusionar con los datos de mercados
    df_afinidad = pd.merge(afinidad_producto, mercados_df, on='País')
    
    # Agregar información sobre acuerdos comerciales
    df_afinidad = pd.merge(df_afinidad, acuerdos_df[['País', 'Acuerdo Comercial']], on='País', how='left')

    # Ajustar afinidad según acuerdos comerciales
    df_afinidad['Puntaje_Ajustado'] = df_afinidad['Afinidad'] * df_afinidad['Acuerdo Comercial'].apply(lambda x: 1.1 if pd.notna(x) else 1)
    
    # Ordenar los países por el puntaje ajustado
    df_afinidad = df_afinidad.sort_values(by='Puntaje_Ajustado', ascending=False)
    
    return df_afinidad[['País', 'Puntaje_Ajustado']]

# Interfaz de usuario en Streamlit
st.title("Recomendador de Mercados de Exportación")
producto = st.selectbox("Selecciona el Producto", afinidad_df['Producto'].unique())

# Mostrar los resultados y mapa
if producto:
    df_recomendaciones = calcular_afinidad(producto, mercados_df, afinidad_df, acuerdos_df)
    st.write("Recomendación de mercados para el producto:", producto)
    st.dataframe(df_recomendaciones)
    
    # Crear un mapa centrado en el continente
    mapa = folium.Map(location=[-33.8688, -56.1913], zoom_start=3)  # Latitud y longitud aproximada de Uruguay
    
    # Añadir los países recomendados al mapa
    for index, row in df_recomendaciones.iterrows():
        pais = row['País']
        lat = mercados_df[mercados_df['País'] == pais]['Latitud'].values[0]
        lon = mercados_df[mercados_df['País'] == pais]['Longitud'].values[0]
        
        # Añadir marcador al mapa
        folium.Marker(
            [lat, lon],
            popup=f"{pais}: {row['Puntaje_Ajustado']:.2f}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(mapa)
    
    # Mostrar el mapa en Streamlit
    st_folium(mapa, width=700, height=500)
