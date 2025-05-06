import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from PIL import Image

# Cargar datos
mercados_df = pd.read_csv('mercados.csv', encoding='latin1')
afinidad_df = pd.read_csv('afinidad_producto_país.csv')
acuerdos_df = pd.read_csv('acuerdos_comerciales.csv', encoding='latin1')

# Logo
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    logo = Image.open("logo_ccsuy.png")
    st.image(logo, width=400)

st.title("🌍 Bot de Recomendación de Mercados de Exportación")

# Instrucciones y descripción
st.markdown("""
Bienvenido al **Bot de Recomendación de Mercados de Exportación**.  
Esta herramienta identifica los mejores mercados para exportar productos uruguayos, priorizando América Latina y considerando afinidad, acuerdos comerciales y facilidad para hacer negocios.
""")

# Selección de producto
productos = afinidad_df['Producto'].unique()
producto_seleccionado = st.selectbox("🔍 Elija un Producto", productos)

# Filtro de acuerdo comercial
solo_con_acuerdo = st.checkbox("🔒 Solo países con acuerdo comercial con Uruguay")

# Preparar datos
df_producto = afinidad_df[afinidad_df['Producto'] == producto_seleccionado]
df_producto = df_producto.merge(acuerdos_df[['País', 'Acuerdo Comercial']], on='País', how='left')
df_producto = df_producto.merge(mercados_df, on='País', how='left')
df_producto = df_producto.merge(mercados_df[['País', 'Continente']], on='País', how='left')

# Aplicar filtro de acuerdo comercial
if solo_con_acuerdo:
    df_producto = df_producto[df_producto['Acuerdo Comercial'] == 'Sí']

# Afinidad ajustada con bonus
df_producto['Afinidad Ajustada'] = df_producto.apply(
    lambda row: row['Afinidad'] + 5 if row['Acuerdo Comercial'] == 'Sí' else row['Afinidad'],
    axis=1
)

# Asignar prioridad a las regiones dentro de América
region_order = {
    'América Central': 1,
    'América del Sur': 2,
    'América del Norte': 3,
}

df_producto['Región_Prioridad'] = df_producto['Continente'].map(region_order)

# Separar países latinoamericanos
latam = df_producto[df_producto['Continente'] == 'América Latina']
resto = df_producto[df_producto['Continente'] != 'América Latina']

# Seleccionar top 5 LatAm (priorizando América Central > Sur > Norte) y top 2 globales
top_latam = latam.sort_values(by=['Región_Prioridad', 'Afinidad Ajustada'], ascending=[True, False]).head(5)
top_global = resto.sort_values(by='Afinidad Ajustada', ascending=False).head(2)

# Combinar resultados
top_recomendados = pd.concat([top_latam, top_global])

# Mostrar tabla
st.subheader("🧭 Recomendaciones Prioritarias")
st.dataframe(top_recomendados[['País', 'Afinidad Ajustada', 'Acuerdo Comercial', 'Facilidad Negocios (WB 2019)', 'Demanda Esperada']])

# Mostrar gráfico
fig = px.bar(top_recomendados, x='País', y='Afinidad Ajustada', color='Continente', title="Ranking de Mercados Recomendados")
st.plotly_chart(fig)

# Generar recomendaciones breves
st.subheader("📝 Recomendaciones Estratégicas")

for _, row in top_recomendados.iterrows():
    nombre = row['País']
    acuerdo = "cuenta con un acuerdo comercial" if row['Acuerdo Comercial'] == "Sí" else "no cuenta con un acuerdo preferencial"
    demanda = row['Demanda Esperada']
    facilidad = row['Facilidad Negocios (WB 2019)']

    recomendacion = (
        f"**{nombre}** es un mercado atractivo para exportar {producto_seleccionado}. "
        f"Este país {acuerdo} con Uruguay, lo que influye en los costos y condiciones de acceso. "
        f"Su nivel de demanda esperada ({demanda}) sugiere un mercado con oportunidades relevantes, "
        f"y su puntuación de {facilidad} en facilidad para hacer negocios lo posiciona como un entorno "
        f"moderadamente accesible para empresas uruguayas. Se recomienda investigar barreras no arancelarias "
        f"y regulaciones específicas del sector antes de avanzar con estrategias comerciales más profundas."
    )

    st.markdown(f"#### {nombre}")
    st.markdown(recomendacion)
