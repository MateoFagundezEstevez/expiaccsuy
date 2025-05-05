# app.py
import streamlit as st
import pandas as pd
import chardet

st.set_page_config(page_title="Recomendador de Mercados", layout="centered")

st.title("🌍 Recomendador de Mercados para Exportadores Uruguayos")

# Función para detectar codificación de un archivo
def detectar_codificacion(filepath):
    with open(filepath, 'rb') as f:
        resultado = chardet.detect(f.read())
    return resultado['encoding']

# Cargar archivos
@st.cache_data
def cargar_datos():
    # Detectar codificación del archivo afinidad
    encoding_afinidad = detectar_codificacion("/mnt/data/afinidad_producto_país.csv")

    mercados = pd.read_csv("/mnt/data/mercados.csv")  # Asumimos UTF-8 correcto
    afinidad = pd.read_csv("/mnt/data/afinidad_producto_país.csv", encoding=encoding_afinidad)
    
    return mercados, afinidad

mercados_df, afinidad_df = cargar_datos()

# Interfaz para ingresar producto
producto = st.text_input("Ingrese el nombre del producto que desea exportar:", "")

if producto:
    producto_filtrado = afinidad_df[afinidad_df['Producto'].str.lower() == producto.lower()]

    if producto_filtrado.empty:
        st.warning("⚠️ No se encontró afinidad para ese producto.")
    else:
        # Unir afinidad con datos de mercado
        datos_combinados = pd.merge(producto_filtrado, mercados_df, on="País", how="inner")

        # Crear una puntuación compuesta (puedes ajustar los pesos)
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
                "Facilidad para hacer negocios", "Beneficios arancelarios", "Estabilidad política"
            ]].reset_index(drop=True)
        )
else:
    st.info("Ingrese un producto para ver recomendaciones.")

