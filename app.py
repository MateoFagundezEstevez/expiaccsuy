import streamlit as st
import pandas as pd
import plotly.express as px

# Cargar los archivos CSV con los datos
mercados_df = pd.read_csv('mercados.csv')
afinidad_df = pd.read_csv('afinidad_producto_país.csv')

# Título e imagen
st.image('logo_ccsuy.png', width=200)  # Logo de la Cámara de Comercio y Servicios
st.title("🌍 Bot de Recomendación de Mercados de Exportación")

# Descripción
st.markdown("""
Bienvenido al **Bot de Recomendación de Mercados de Exportación**. 
Este bot le ayudará a encontrar los mercados más adecuados para exportar sus productos, basándose en una serie de indicadores clave de cada país. 
Seleccione un producto y vea los mercados recomendados. 🚀
""")

# Selección de Producto
productos = afinidad_df['Producto'].unique()
producto_seleccionado = st.selectbox("🔍 Elija un Producto", productos)

# Filtrar los datos según el producto seleccionado
df_producto = afinidad_df[afinidad_df['Producto'] == producto_seleccionado]

# Mostrar la tabla con los mercados recomendados
st.subheader(f"🌎 Mercados recomendados para {producto_seleccionado}")
st.dataframe(df_producto[['País', 'Afinidad']])

# Mostrar un gráfico interactivo de los mercados recomendados
fig = px.bar(df_producto, x='País', y='Afinidad', title=f"Afinidad de los mercados para {producto_seleccionado}")
st.plotly_chart(fig)

# Mostrar un mapa interactivo de los países recomendados
st.subheader("📍 Mapa Interactivo de los Mercados")
fig_map = px.scatter_geo(df_producto, locations="País", size="Afinidad", hover_name="País", size_max=30, title=f"Mercados recomendados para {producto_seleccionado}")
fig_map.update_layout(
    geo=dict(showcoastlines=True, coastlinecolor="Black", projection_type="natural earth", visible=True)
)
st.plotly_chart(fig_map)

# Mostrar un disclaimer para la prioridad de los mercados latinoamericanos
st.markdown("""
#### ⚠️ **Disclaimer**:
Los primeros 5 mercados recomendados se priorizan para los países de Latinoamérica antes de mostrar otros mercados de otras regiones.
""")

# Agregar el cuadro de personalización de recomendación
st.subheader("🔄 Personaliza tu Recomendación")
slider = st.slider("Ajusta la Afinidad mínima para la recomendación", 0, 100, 50)
mercados_filtrados = df_producto[df_producto['Afinidad'] >= slider]

st.write(f"🛍️ Mercados con afinidad mayor a {slider}:")
st.dataframe(mercados_filtrados[['País', 'Afinidad']])

# Mostrar recomendación de los primeros 5 mercados de Latinoamérica
latam_df = df_producto[df_producto['País'].isin(['Argentina', 'Brasil', 'México', 'Chile', 'Perú', 'Colombia', 'Ecuador', 'Paraguay', 'Bolivia', 'Venezuela', 'Cuba', 'Uruguay', 'Guatemala', 'Costa Rica', 'Panamá', 'Honduras', 'El Salvador', 'Nicaragua', 'República Dominicana'])]
latam_top_5 = latam_df.sort_values(by='Afinidad', ascending=False).head(5)
st.subheader("🛒 Top 5 mercados recomendados en Latinoamérica:")
st.dataframe(latam_top_5[['País', 'Afinidad']])

# Agregar botón para mostrar todos los mercados recomendados
if st.button('Mostrar todos los mercados recomendados'):
    st.subheader(f"🌍 Todos los mercados recomendados para {producto_seleccionado}:")
    st.write(df_producto[['País', 'Afinidad']].sort_values(by='Afinidad', ascending=False))

# Mensaje final
st.markdown("""
Gracias por usar nuestro **Bot de Recomendación de Mercados de Exportación**. 
¡Esperamos que esta herramienta te ayude a tomar decisiones informadas sobre tus exportaciones! 🌍
""")
