import streamlit as st
import pandas as pd

# Leer el archivo CSV con los mercados y puntajes
mercados_df = pd.read_csv('mercados.csv')

# Función para calcular el puntaje total de cada país
def calcular_puntaje(pais, facilidad, demanda, beneficios, estabilidad):
    # Ponderar los puntajes (ajustar los pesos si es necesario)
    puntaje_total = (facilidad * 0.25) + (demanda * 0.35) + (beneficios * 0.2) + (estabilidad * 0.2)
    return puntaje_total

# Función para recomendar los mejores mercados
def recomendar_mercados(facilidad, demanda, beneficios, estabilidad, num_recomendados=5):
    # Crear una columna con los puntajes de cada país
    mercados_df['Puntaje'] = mercados_df.apply(
        lambda row: calcular_puntaje(row['Pais'], facilidad, demanda, beneficios, estabilidad), axis=1
    )
    
    # Ordenar los países por puntaje, de mayor a menor
    mercados_df_sorted = mercados_df.sort_values(by='Puntaje', ascending=False)
    
    # Tomar los mejores 'num_recomendados' países
    mejores_mercados = mercados_df_sorted.head(num_recomendados)
    
    return mejores_mercados

# Función para mostrar recomendaciones con comentarios
def mostrar_recomendaciones(mercados):
    for index, row in mercados.iterrows():
        st.write(f"**{row['Pais']}**")
        st.write(f"**Puntaje Total**: {row['Puntaje']:.2f}")
        
        # Generar el feedback basado en el puntaje
        if row['Puntaje'] > 80:
            st.write(f"  → **Excelente opción**: {row['Pais']} tiene una alta facilidad para hacer negocios, demanda fuerte y una buena estabilidad política.")
        elif row['Puntaje'] > 70:
            st.write(f"  → **Buena opción**: {row['Pais']} ofrece una demanda interesante y beneficios arancelarios aceptables.")
        elif row['Puntaje'] > 60:
            st.write(f"  → **Moderada opción**: {row['Pais']} presenta un entorno favorable pero con algunos desafíos en la estabilidad política o beneficios arancelarios.")
        else:
            st.write(f"  → **Considerar con cautela**: {row['Pais']} podría tener barreras políticas o regulatorias que hacen que el entorno de negocios sea menos favorable.")
        
        st.write("---")

# Streamlit UI
st.title("Recomendador de Mercados para Exportadores Uruguayos")

# Inputs del usuario
descripcion_producto = st.text_input("Descripción del Producto")
facilidad_input = st.slider("Facilidad para hacer negocios (0 a 100)", 0, 100, 70)
demanda_input = st.slider("Demanda esperada (0 a 100)", 0, 100, 70)
beneficios_input = st.slider("Beneficios arancelarios (0 a 100)", 0, 100, 70)
estabilidad_input = st.slider("Estabilidad política (0 a 100)", 0, 100, 70)

if st.button("Recomendar Mercados"):
    # Llamar a la función que recomienda los mercados
    mejores_mercados = recomendar_mercados(facilidad_input, demanda_input, beneficios_input, estabilidad_input)

    # Mostrar las recomendaciones con comentarios
    st.subheader("Los 5 mejores mercados recomendados:")
    mostrar_recomendaciones(mejores_mercados)
