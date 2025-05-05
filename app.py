import streamlit as st
import pandas as pd
import numpy as np

# Cargar los datos de los CSV (ya están subidos en Streamlit Cloud)
afinidad_df = pd.read_csv("afinidad_producto_país.csv", encoding="ISO-8859-1")
mercados_df = pd.read_csv("mercados.csv", encoding="ISO-8859-1")

# Función para recomendar los mejores mercados
def recomendar_mercados(afinidad_producto, mercados_df):
    # Crear una columna adicional para identificar la región
    latinoamerica = [
        "Argentina", "Brasil", "Paraguay", "Chile", "Bolivia", "Perú", "Colombia", "Ecuador", 
        "México", "Panamá", "Costa Rica", "República Dominicana", "Guatemala", "El Salvador", 
        "Honduras", "Nicaragua", "Venezuela", "Uruguay", "Cuba", "Haití", "Puerto Rico", "Belice", 
        "Jamaica", "Trinidad y Tobago", "Barbados", "Guyana", "Surinam"
    ]
    
    # Agregar columna de región
    mercados_df['Región'] = mercados_df['País'].apply(lambda x: 'Latinoamérica' if x in latinoamerica else 'Global')

    # Merge para combinar los datos de afinidad y mercado
    df_completo = pd.merge(afinidad_producto[['País', 'Afinidad']], mercados_df, on='País', how='inner')

    # Ajustar las ponderaciones según la región
    def calcular_puntaje(row):
        if row['Región'] == 'Latinoamérica':
            return (
                0.6 * row['Afinidad'] +  # Mayor peso a la afinidad para Latinoamérica
                0.15 * row['Demanda esperada'] +
                0.1 * row['Facilidad para hacer negocios'] +
                0.15 * row['Estabilidad política']
            )
        else:
            return (
                0.4 * row['Afinidad'] +  # Menor peso a la afinidad para mercados globales
                0.25 * row['Demanda esperada'] +
                0.2 * row['Facilidad para hacer negocios'] +
                0.15 * row['Estabilidad política']
            )
    
    # Aplicar la función de puntaje
    df_completo['Puntaje'] = df_completo.apply(calcular_puntaje, axis=1)

    # Ordenar los mercados por puntaje y seleccionar los 5 mejores
    df_recomendado = df_completo.sort_values(by='Puntaje', ascending=False).head(5)

    # Generar los fundamentos
    recomendaciones = []
    for index, row in df_recomendado.iterrows():
        fundamento = (
            f"**Mercado recomendado: {row['País']}** 🌟\n\n"
            f"- **Afinidad del producto con el mercado**: {row['Afinidad']}\n"
            f"- **Demanda esperada**: {row['Demanda esperada']}\n"
            f"- **Facilidad para hacer negocios**: {row['Facilidad para hacer negocios']}\n"
            f"- **Beneficios arancelarios**: {row['Beneficios arancelarios']}\n"
            f"- **Estabilidad política**: {row['Estabilidad política']}\n\n"
            "En base a estos indicadores, se recomienda este mercado debido a su alto nivel de afinidad con el producto seleccionado, su "
            "alta demanda esperada, y sus condiciones favorables para hacer negocios. Además, ofrece beneficios arancelarios competitivos "
            "y una estabilidad política que lo convierte en una opción segura para la exportación. 🚀"
        )
        recomendaciones.append(fundamento)
    
    return df_recomendado[['País', 'Puntaje']], recomendaciones

# Interfaz de usuario
st.set_page_config(page_title="Recomendador de Mercados de Exportación", page_icon="🌍")

# Cargar el logo de la Cámara de Comercio y Servicios del Uruguay desde el archivo local
st.image("logo_ccsuy.png", use_container_width=True)

# Título principal
st.markdown("<h1 style='color: #3E8E41;'>Bienvenido al Recomendador de Mercados de Exportación 🌎</h1>", unsafe_allow_html=True)

# Subtítulo con instrucciones
st.markdown(
    """
    🚀 **Elige tu producto y descubre los mejores mercados para exportarlo.** 
    En esta herramienta, te recomendaremos los 5 mercados con mayor potencial de exportación para tu producto, basándonos en diversos indicadores.
    """
)

# Selección de producto
producto = st.selectbox("Selecciona tu producto", afinidad_df['Producto'].unique())

# Botón para obtener la recomendación
if st.button("Obtener recomendaciones"):
    # Filtrar datos del producto
    afinidad_producto = afinidad_df[afinidad_df['Producto'] == producto]
    
    # Obtener las recomendaciones de mercado
    df_recomendado, fundamentos = recomendar_mercados(afinidad_producto, mercados_df)
    
    # Mostrar resultados
    st.subheader("Top 5 Mercados recomendados para tu producto:")
    
    for i, (mercado, fundamento) in enumerate(zip(df_recomendado['País'], fundamentos)):
        # Añadir colores y formato
        st.markdown(f"**{i+1}. {mercado}**")
        st.markdown(fundamento)
        st.markdown("---")

    # Mostrar los resultados en formato tabla
    st.subheader("Detalles de los mercados recomendados")
    st.dataframe(df_recomendado)

# Estilo con colores y emojis para la interfaz
st.markdown(""" 
    <style> 
        .stButton > button { 
            background-color: #3E8E41; 
            color: white; 
            font-size: 16px; 
        } 
        .stButton > button:hover { 
            background-color: #45a049; 
        } 
    </style> 
""", unsafe_allow_html=True)
