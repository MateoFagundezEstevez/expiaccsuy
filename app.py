import streamlit as st
import pandas as pd

st.set_page_config(page_title="Recomendador de Mercados", layout="centered")
st.title("🌍 Recomendador de Mercados para Exportadores Uruguayos")

@st.cache_data
def cargar_datos():
    mercados = pd.read_csv("mercados.csv")
    afinidad = pd.read_csv("afinidad_producto_país.csv", encoding="latin1")  # <= Cambio clave aquí
    return mercados, afinidad

mercados_df, afinidad_df = cargar_datos()

producto = st.text_input("Ingrese el nombre del producto que desea exportar:")

if producto:
    producto_filtrado = afinidad_df[afinidad_df['Producto'].str.lower() == producto.lower()]

    if producto_filtrado.empty:
        st.warning("⚠️ No se encontró afinidad para ese producto.")
    else:
        datos_combinados = pd.merge(producto_filtrado, mercados_df, on="País", how="inner")

        datos_combinados["Puntaje Total"] = (
            datos_combinados["Afinidad"] * 0.4 +
            datos_combinados["Demanda esperada"] * 0.3 +
            datos_combinados["Facilidad para hacer negocios"] * 0.2 +
            datos_combinados["Beneficios arancelarios"] * 0.05 +
            datos_combinados["Estabilidad política"] * 0.05
        )

        datos_ordenados = datos_combinados.sort_values(by="Puntaje Total", ascending=False)

        st.success(f"🌟 Ranking de países recomendados para exportar '{producto}':")
        st.dataframe(
            datos_ordenados[[
                "País", "Puntaje Total", "Afinidad", "Demanda esperada",
                "Facilidad para hacer negocios",
