import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from PIL import Image

# Configuración general
st.set_page_config(page_title="Bot de Recomendación de Mercados", layout="wide")

# Cargar los datos
mercados_df = pd.read_csv("mercados.csv")
afinidad_df = pd.read_csv("afinidad_producto_pais.csv")
acuerdos_df = pd.read_csv("acuerdos_comerciales.csv", encoding="utf-8", quotechar='"')

# Preprocesamiento
acuerdos_df["Acuerdo Comercial"] = acuerdos_df["Acuerdo Comercial"].map({"Sí": 1, "No": 0})
df = pd.merge(afinidad_df, mercados_df, on="País", how="left")
df = pd.merge(df, acuerdos_df, on="País", how="left")

# Mostrar logo
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    logo = Image.open("logo_ccsuy.png")
    st.image(logo, width=400)

# Título y descripción
st.title("🌍 Bot de Recomendación de Mercados de Exportación")

st.markdown("""
Este bot te ayuda a identificar mercados recomendados para exportar productos uruguayos, basándose en:
- Afinidad histórica del producto en ese mercado
- Facilidad para hacer negocios
- Nivel de demanda estimada
- Existencia de acuerdos comerciales
""")

# Selección de producto
productos = df["Producto"].unique()
producto = st.selectbox("🔍 Selecciona un producto", productos)

df_producto = df[df["Producto"] == producto]

# Ponderación de criterios
st.markdown("### ⚖️ Asigna importancia a cada criterio (suma 100)")
col1, col2, col3, col4 = st.columns(4)
peso_afinidad = col1.slider("Afinidad", 0, 100, 30)
peso_facilidad = col2.slider("Facilidad Negocios", 0, 100, 30)
peso_demanda = col3.slider("Demanda", 0, 100, 30)
peso_acuerdo = col4.slider("Acuerdo Comercial", 0, 100, 10)

peso_total = peso_afinidad + peso_facilidad + peso_demanda + peso_acuerdo
if peso_total != 100:
    st.warning("⚠️ La suma de los pesos debe ser 100.")
    st.stop()

# Normalización de columnas relevantes
df_producto["Afinidad_norm"] = df_producto["Afinidad"] / df_producto["Afinidad"].max()
df_producto["Facilidad_norm"] = df_producto["Facilidad para hacer negocios"] / df_producto["Facilidad para hacer negocios"].max()
df_producto["Demanda_norm"] = df_producto["Demanda esperada"] / df_producto["Demanda esperada"].max()

# Score ponderado
df_producto["Score"] = (
    df_producto["Afinidad_norm"] * peso_afinidad +
    df_producto["Facilidad_norm"] * peso_facilidad +
    df_producto["Demanda_norm"] * peso_demanda +
    df_producto["Acuerdo Comercial"] * peso_acuerdo
) / 100

# Mostrar resultados
st.markdown("### 📊 Mercados recomendados")
st.dataframe(df_producto[["País", "Score", "Afinidad", "Facilidad para hacer negocios", "Demanda esperada", "Acuerdo Comercial", "Descripción Acuerdo"]].sort_values(by="Score", ascending=False))

# Gráfico de barras
fig = px.bar(df_producto.sort_values(by="Score", ascending=False).head(15),
             x="País", y="Score", color="Score", title="Top 15 mercados recomendados")
st.plotly_chart(fig)

# Mapa de ubicación
st.markdown("### 🗺️ Mapa de mercados recomendados")
if "Latitud" in df_producto.columns and "Longitud" in df_producto.columns:
    fig_map = px.scatter_geo(df_producto,
                             lat="Latitud", lon="Longitud",
                             hover_name="País", size="Score",
                             color="Score", color_continuous_scale="Blues",
                             title=f"Ubicación geográfica de los mercados recomendados")
    st.plotly_chart(fig_map)
else:
    st.warning("🌐 No se encontraron coordenadas geográficas para mostrar el mapa.")

# Footer
st.markdown("---")
st.caption("Desarrollado por CCSUY · Datos ficticios de ejemplo")
