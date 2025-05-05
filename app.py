# app.py
import streamlit as st
import pandas as pd
from rapidfuzz import process

# Cargar base de datos NCM (ejemplo simplificado)
df_ncm = pd.read_csv("ncm.csv")  # columnas: codigo, descripcion

# Base de recomendaciones por NCM (puede estar en otro archivo)
recomendaciones_ncm = {
    "20091100": ["Brasil", "Chile", "Estados Unidos"],
    "22029000": ["Paraguay", "México", "España"],
    # agregar más según sea necesario
}

st.set_page_config(page_title="Selector de Mercados", layout="wide")
st.title("🌍 Plataforma de Exportación para Uruguay")

# 1. Ingreso del producto
descripcion_producto = st.text_input("Describa su producto para exportar:")

codigo_ncm_sugerido = ""
if descripcion_producto:
    mejor_match = process.extractOne(descripcion_producto, df_ncm['descripcion'])
    if mejor_match:
        codigo_ncm_sugerido = df_ncm.loc[df_ncm['descripcion'] == mejor_match[0], 'codigo'].values[0]
        st.success(f"📦 Código NCM sugerido: {codigo_ncm_sugerido} – {mejor_match[0]}")

        # 2. Sugerencia de países
        paises_sugeridos = recomendaciones_ncm.get(codigo_ncm_sugerido, [])
        if paises_sugeridos:
            st.markdown("**🌐 Mercados recomendados:**")
            for p in paises_sugeridos:
                st.write(f"- {p}")
        else:
            st.info("No hay recomendaciones precargadas para este NCM. Puedes ingresar tus propios países.")

# 3. Ingreso de datos de mercado
st.subheader("📊 Evaluación de Mercados")
datos_csv = st.text_area("Pegue aquí los datos de los países (CSV):",
"""pais,facilidad_negocios,demanda,beneficios_arancelarios,estabilidad_politica
Brasil,60,90,85,65
Chile,80,70,90,85
Estados Unidos,75,95,80,70""")

# 4. Ajuste de pesos
st.sidebar.header("⚖️ Ajuste de pesos")
pesos = {
    'facilidad_negocios': st.sidebar.slider("Facilidad de negocios", 0.0, 1.0, 0.25),
    'demanda': st.sidebar.slider("Demanda", 0.0, 1.0, 0.25),
    'beneficios_arancelarios': st.sidebar.slider("Beneficios arancelarios", 0.0, 1.0, 0.25),
    'estabilidad_politica': st.sidebar.slider("Estabilidad política", 0.0, 1.0, 0.25)
}

# Normalización de pesos
suma_pesos = sum(pesos.values())
if suma_pesos == 0:
    st.error("Los pesos no pueden ser todos cero.")
else:
    pesos = {k: v/suma_pesos for k, v in pesos.items()}

# 5. Cálculo del ranking
def evaluar_mercado(row, pesos):
    return sum([row[k] * pesos[k] for k in pesos])

try:
    df_mercados = pd.read_csv(pd.compat.StringIO(datos_csv))
    df_mercados['score'] = df_mercados.apply(lambda row: evaluar_mercado(row, pesos), axis=1)
    df_ordenado = df_mercados.sort_values("score", ascending=False).reset_index(drop=True)

    st.success(f"🏆 Mejor mercado: {df_ordenado.loc[0, 'pais']} (score: {round(df_ordenado.loc[0, 'score'], 2)})")
    st.dataframe(df_ordenado)

    # 6. Gráfico (opcional)
    st.bar_chart(df_ordenado.set_index("pais")["score"])
except Exception as e:
    st.error(f"Error al procesar los datos: {e}")

# Instrucciones de uso
st.markdown("""
---
### 📌 Instrucciones para ejecutar la app:

1. Instalá las dependencias necesarias:
```bash
pip install streamlit pandas rapidfuzz
```

2. Guardá este archivo como `app.py` y asegurate de tener `ncm.csv` con columnas `codigo` y `descripcion`.

3. Ejecutá la app con:
```bash
streamlit run app.py
```

4. Podés subirla a [Streamlit Cloud](https://streamlit.io/cloud) para compartirla gratis.
""")
