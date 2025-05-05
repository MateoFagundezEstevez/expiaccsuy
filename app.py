import streamlit as st
import pandas as pd

# Leer los datos de mercados
df = pd.read_csv('mercados.csv')

# Descripción de la app
st.title("Identificación del Mejor Mercado para Exportar")
st.write("Selecciona las características del producto y ajusta los puntajes para obtener el mejor mercado")

# Sliders para los parámetros con rango de 0 a 100
facilidad_negocios = st.slider('Facilidad para hacer negocios', 0, 100, 50)
demanda = st.slider('Demanda', 0, 100, 50)
beneficios_arancelarios = st.slider('Beneficios arancelarios', 0, 100, 50)
estabilidad_politica = st.slider('Estabilidad política', 0, 100, 50)

# Cálculo del puntaje total por país
df['Puntaje Total'] = (df['Facilidad para hacer negocios'] * 0.25) + \
                       (df['Demanda'] * 0.25) + \
                       (df['Beneficios arancelarios'] * 0.25) + \
                       (df['Estabilidad política'] * 0.25)

# Mostrar el ranking completo de países ordenado por puntaje total
df_sorted = df[['País', 'Facilidad para hacer negocios', 'Demanda', 'Beneficios arancelarios',
                'Estabilidad política', 'Puntaje Total']].sort_values(by='Puntaje Total', ascending=False)

# Mostrar los resultados
st.write('Ranking de países sugeridos:')
st.dataframe(df_sorted)

# Mostrar las recomendaciones
top_5_markets = df_sorted.head(5)
st.write("Los 5 mejores mercados para exportar son:")
st.dataframe(top_5_markets[['País', 'Puntaje Total']])
