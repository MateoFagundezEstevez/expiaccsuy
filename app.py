import streamlit as st
import pandas as pd
import numpy as np

# Cargar los datos de los CSV (ya están subidos en Streamlit Cloud)
afinidad_df = pd.read_csv("afinidad_producto_país.csv", encoding="ISO-8859-1")
mercados_df = pd.read_csv("mercados.csv", encoding="ISO-8859-1")
acuerdos_df = pd.read_csv("acuerdos_comerciales.csv")

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

# Función para mostrar los acuerdos comerciales
def mostrar_acuerdos_comerciales(pais_seleccionado):
    # Filtrar por el país seleccionado
    acuerdos_pais = acuerdos_df[acuerdos_df['País'] == pais_seleccionado]
    
    if not acuerdos_pais.empty:
        for _, row in acuerdos_pais.iterrows():
            st.subheader(f"Acuerdo Comercial con {row['País']}")
            st.write(f"**Acuerdo:** {row['Acuerdo Comercial']}")
            st.write(f"**Descripción:** {row['Descripción']}")
            st.write(f"**Vigencia:** {row['Vigencia']}")
            st.write(f"[Enlace al Acuerdo]({row['Enlace']})")
            st.write(f"**Notas importantes:** {row['Notas importantes']}")
            st.write(f"**Categorías negociadas:** {row['Categorías negociadas']}")
    else:
        st.write("No se encontraron acuerdos comerciales para este país.")

# Interfaz de usuario
st.set_page_config(page_title="Recomendador de Mercados de Exportación", page_icon="🌍")

# Cargar el logo de la Cámara de Comercio y Servicios del Uruguay
logo_url = "https://www.ccsuy.org.uy/wp-content/uploads/2020/09/camara-comercio-servicios-uruguay-logo.png"
st.image(logo_url, use_column_width=True)

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
categoria = st.selectbox("Selecciona la categoría de tu producto", afinidad_df['Categoria'].unique())

# Filtrar por categoría
producto_filtrado = afinidad_df[afinidad_df['Categoria'] == categoria]
producto = st.selectbox("Selecciona tu producto", producto_filtrado['Producto'].unique())

# Botón para obtener la recomendación
if st.button("Obtener recomendaciones"):
    # Filtrar datos del producto
    afinidad_producto = producto_filtrado[producto_filtrado['Producto'] == producto]
    
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

    # Mostrar los acuerdos comerciales del país recomendado
    st.subheader("Acuerdos Comerciales")
    mostrar_acuerdos_comerciales(df_recomendado['País'].iloc[0])  # Mostrar acuerdos del primer mercado recomendado

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
