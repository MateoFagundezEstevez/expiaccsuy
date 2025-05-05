import streamlit as st
import pandas as pd

def load_csv_file(uploaded_file):
    try:
        # Intentamos con utf-8
        return pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            # Intentamos con ISO-8859-1
            return pd.read_csv(uploaded_file, encoding='ISO-8859-1')
        except UnicodeDecodeError:
            # Intentamos con latin1
            return pd.read_csv(uploaded_file, encoding='latin1')

# Subir los archivos CSV desde la interfaz de Streamlit
uploaded_afinidad = st.file_uploader("Sube el archivo 'afinidad_producto_país.csv'", type=["csv"])
uploaded_mercados = st.file_uploader("Sube el archivo 'mercados.csv'", type=["csv"])

# Verifica si los archivos han sido subidos
if uploaded_afinidad is not None:
    afinidad_df = load_csv_file(uploaded_afinidad)
    st.write("Datos de 'afinidad_producto_país.csv':")
    st.write(afinidad_df)

if uploaded_mercados is not None:
    mercados_df = load_csv_file(uploaded_mercados)
    st.write("Datos de 'mercados.csv':")
    st.write(mercados_df)
import matplotlib.pyplot as plt
import seaborn as sns

# Cargar los archivos CSV
afinidad_df = pd.read_csv("afinidad_producto_país.csv")
mercados_df = pd.read_csv("mercados.csv")

# Función para calcular el puntaje final para cada país basado en los criterios
def calcular_puntaje(df_afinidad, df_mercado, producto):
    # Obtener la afinidad del producto con cada país
    afinidad = df_afinidad[df_afinidad['Producto'] == producto]
    
    # Si no se encuentra el producto, retornar un mensaje
    if afinidad.empty:
        return "Producto no encontrado"
    
    # Merge entre los dataframes de afinidad y mercados
    df_merge = pd.merge(afinidad, df_mercado, on="País", how="left")
    
    # Normalización de las columnas para facilitar el cálculo del puntaje
    df_merge['Puntaje Afinidad'] = df_merge['Afinidad'] * 0.2
    df_merge['Puntaje Facilidad'] = df_merge['Facilidad para hacer negocios'] * 0.2
    df_merge['Puntaje Demanda'] = df_merge['Demanda esperada'] * 0.2
    df_merge['Puntaje Aranceles'] = df_merge['Beneficios arancelarios'] * 0.2
    df_merge['Puntaje Estabilidad'] = df_merge['Estabilidad política'] * 0.2
    
    # Calcular el puntaje total
    df_merge['Puntaje Total'] = (df_merge['Puntaje Afinidad'] + 
                                 df_merge['Puntaje Facilidad'] + 
                                 df_merge['Puntaje Demanda'] + 
                                 df_merge['Puntaje Aranceles'] + 
                                 df_merge['Puntaje Estabilidad'])
    
    # Ordenar los países por puntaje
    df_merge_sorted = df_merge.sort_values(by="Puntaje Total", ascending=False)
    
    return df_merge_sorted[['País', 'Puntaje Total', 'Puntaje Afinidad', 'Puntaje Facilidad', 'Puntaje Demanda', 'Puntaje Aranceles', 'Puntaje Estabilidad']].head(10)

# Interfaz de Streamlit
st.title('Recomendación de mercado para exportadores')
st.markdown("""
    Esta aplicación ayuda a los exportadores a encontrar los mejores mercados según la afinidad de su producto con diferentes países y criterios clave como:
    - Facilidad para hacer negocios
    - Demanda esperada
    - Beneficios arancelarios
    - Estabilidad política
    Elija un producto y obtenga los países recomendados.
""")

# Selector de producto con descripción
producto = st.selectbox(
    "Seleccione un producto", 
    afinidad_df['Producto'].unique(),
    help="Seleccione el producto que desea exportar para ver los países más recomendados."
)

# Botón para generar la recomendación
if st.button("Generar recomendación"):
    recomendacion = calcular_puntaje(afinidad_df, mercados_df, producto)
    
    if isinstance(recomendacion, str):  # En caso de que no se encuentre el producto
        st.error(recomendacion)
    else:
        st.subheader(f"Los mejores mercados recomendados para el producto '{producto}'")
        
        # Mostrar tabla de recomendación
        st.dataframe(recomendacion)
        
        # Gráfico de puntajes
        st.subheader('Visualización de puntajes por país')
        
        # Crear un gráfico de barras para los puntajes totales
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x='Puntaje Total', y='País', data=recomendacion, palette='viridis', ax=ax)
        ax.set_title('Puntaje Total de los países recomendados', fontsize=16)
        ax.set_xlabel('Puntaje Total', fontsize=12)
        ax.set_ylabel('País', fontsize=12)
        st.pyplot(fig)

        # Gráfico de desgloses por criterios
        st.subheader('Desglose de puntajes por criterio')
        
        # Crear un gráfico de barras para cada criterio
        fig, ax = plt.subplots(figsize=(10, 6))
        recomendacion.set_index('País').drop(columns='Puntaje Total').plot(kind='barh', stacked=True, ax=ax, colormap='Set3')
        ax.set_title(f'Desglose de puntajes para el producto {producto}', fontsize=16)
        ax.set_xlabel('Puntaje', fontsize=12)
        ax.set_ylabel('País', fontsize=12)
        st.pyplot(fig)
        
        st.markdown("""
            **Interpretación:**
            - Los países con mayor puntaje total son los más recomendados.
            - Los gráficos muestran cómo cada país se desempeña en los distintos criterios evaluados.
        """)

