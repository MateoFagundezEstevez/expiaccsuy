import pandas as pd
import streamlit as st

# Leer el archivo CSV (con la codificación detectada)
df = pd.read_csv('mercados.csv', encoding='ISO-8859-1')

# Verificar las columnas del DataFrame para depurar posibles problemas de nombres
st.write("Columnas disponibles en el DataFrame:", df.columns)

# Limpiar los nombres de las columnas para eliminar espacios extras
df.columns = df.columns.str.strip()

# Verificar si las columnas necesarias están presentes
required_columns = ['Facilidad para hacer negocios', 'Demanda esperada', 'Beneficios arancelarios', 'Estabilidad política']
missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    st.error(f"Faltan las siguientes columnas en el archivo CSV: {', '.join(missing_columns)}")
else:
    # Si las columnas están presentes, proceder con el cálculo

    # Solicitar al usuario los pesos para los indicadores
    facilidades_peso = st.slider('Peso para Facilidad para hacer negocios', 0, 100, 25)
    demanda_peso = st.slider('Peso para Demanda esperada', 0, 100, 25)
    aranceles_peso = st.slider('Peso para Beneficios arancelarios', 0, 100, 25)
    estabilidad_peso = st.slider('Peso para Estabilidad política', 0, 100, 25)

    # Asegurarse de que los pesos sumen 100
    total_weight = facilidades_peso + demanda_peso + aranceles_peso + estabilidad_peso
    if total_weight != 100:
        st.warning("La suma de los pesos no es 100. Los valores ajustados para asegurar la suma a 100.")

        # Normalizar los pesos para que sumen 100
        total = facilidades_peso + demanda_peso + aranceles_peso + estabilidad_peso
        facilidades_peso = facilidades_peso / total * 100
        demanda_peso = demanda_peso / total * 100
        aranceles_peso = aranceles_peso / total * 100
        estabilidad_peso = estabilidad_peso / total * 100

    # Calcular los puntajes ponderados para cada país
    df['Puntaje'] = (
        (df['Facilidad para hacer negocios'] * facilidades_peso / 100) +
        (df['Demanda esperada'] * demanda_peso / 100) +
        (df['Beneficios arancelarios'] * aranceles_peso / 100) +
        (df['Estabilidad política'] * estabilidad_peso / 100)
    )

    # Ordenar los países según el puntaje
    df_sorted = df.sort_values(by='Puntaje', ascending=False)

    # Mostrar los 5 mejores mercados
    st.write("Los mejores mercados según la evaluación son:")
    st.write(df_sorted.head(5))

    # Mostrar el ranking completo
    st.write("Ranking completo de mercados:")
    st.write(df_sorted)

    # Mostrar un gráfico de barras con los puntajes
    st.bar_chart(df_sorted[['Puntaje']])

