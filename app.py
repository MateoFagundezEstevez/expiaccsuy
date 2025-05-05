import streamlit as st
import pandas as pd
import numpy as np

# Cargar los datos localmente
afinidad_df = pd.read_csv("afinidad_producto_país.csv", encoding="ISO-8859-1")
mercados_df = pd.read_csv("mercados.csv", encoding="ISO-8859-1")

# Definir la función principal para calcular la afinidad
def calcular_afinidad(pais, afinidad_producto, mercados_df):
    # Obtener las métricas del país
    pais_data = mercados_df[mercados_df['País'] == pais].iloc[0]
    
    # Definir los indicadores clave
    indicadores = {
        'Facilidad para hacer negocios': pais_data['Facilidad Negocios (WB 2019)'],
        'Tamaño del Mercado Total (Millones USD)': pais_data['Tamaño del Mercado Total (Millones USD)'],
        'Crecimiento Anual PIB (%)': pais_data['Crecimiento Anual PIB (%)'],
        'Crecimiento Importaciones (%)': pais_data['Crecimiento Importaciones (%)'],
        'Performance Logística (LPI 2023)': pais_data['Logística (LPI 2023)'],
        'Distancia a Uruguay (km)': pais_data['Distancia a Uruguay (km)']
    }

    # Normalizar las métricas
    max_values = {
        'Facilidad para hacer negocios': mercados_df['Facilidad Negocios (WB 2019)'].max(),
        'Tamaño del Mercado Total (Millones USD)': mercados_df['Tamaño del Mercado Total (Millones USD)'].max(),
        'Crecimiento Anual PIB (%)': mercados_df['Crecimiento Anual PIB (%)'].max(),
        'Crecimiento Importaciones (%)': mercados_df['Crecimiento Importaciones (%)'].max(),
        'Performance Logística (LPI 2023)': mercados_df['Logística (LPI 2023)'].max(),
        'Distancia a Uruguay (km)': mercados_df['Distancia a Uruguay (km)'].max()
    }

    min_values = {
        'Facilidad para hacer negocios': mercados_df['Facilidad Negocios (WB 2019)'].min(),
        'Tamaño del Mercado Total (Millones USD)': mercados_df['Tamaño del Mercado Total (Millones USD)'].min(),
        'Crecimiento Anual PIB (%)': mercados_df['Crecimiento Anual PIB (%)'].min(),
        'Crecimiento Importaciones (%)': mercados_df['Crecimiento Importaciones (%)'].min(),
        'Performance Logística (LPI 2023)': mercados_df['Logística (LPI 2023)'].min(),
        'Distancia a Uruguay (km)': mercados_df['Distancia a Uruguay (km)'].min()
    }

    # Normalizar cada indicador
    for indicador, valor in indicadores.items():
        if indicador == 'Distancia a Uruguay (km)':
            indicadores[indicador] = 1 - (valor - min_values[indicador]) / (max_values[indicador] - min_values[indicador])
        else:
            indicadores[indicador] = (valor - min_values[indicador]) / (max_values[indicador] - min_values[indicador])

    # Ponderar las métricas
    pesos = {
        'Facilidad para hacer negocios': 0.2,
        'Tamaño del Mercado Total (Millones USD)': 0.3,
        'Crecimiento Anual PIB (%)': 0.2,
        'Crecimiento Importaciones (%)': 0.1,
        'Performance Logística (LPI 2023)': 0.1,
        'Distancia a Uruguay (km)': 0.1
    }

    puntaje_base = sum(indicadores[indicador] * pesos[indicador] for indicador in indicadores)

    # Añadir variación por producto (simulada)
    variacion_producto = np.random.uniform(-0.05, 0.05)  # Ajuste aleatorio entre -5% y +5%
    puntaje_final = puntaje_base + variacion_producto

    # Escalar el puntaje final a un rango de 0 a 100
    puntaje_final = max(0, min(100, puntaje_final * 100))  # Escalar y limitar el puntaje

    return puntaje_final

# Función principal para recomendar mercados
def recomendar_mercados(afinidad_producto, mercados_df, extra_global=0):
    # Lista de países de Latinoamérica
    latinoamerica = [
        "Argentina", "Brasil", "Paraguay", "Chile", "Bolivia", "Perú", "Colombia", "Ecuador", 
        "México", "Panamá", "Costa Rica", "República Dominicana", "Guatemala", "El Salvador", 
        "Honduras", "Nicaragua", "Venezuela", "Uruguay", "Cuba", "Haití", "Puerto Rico", "Belice", 
        "Jamaica", "Trinidad y Tobago", "Barbados", "Guyana", "Surinam"
    ]

    # Clasificar región
    mercados_df['Región'] = mercados_df['País'].apply(lambda x: 'Latinoamérica' if x in latinoamerica else 'Resto del Mundo')

    # Unir datasets
    df_completo = pd.merge(afinidad_producto[['País', 'Afinidad']], mercados_df, on='País', how='inner')

    # Calcular puntajes ponderados
    df_completo['Puntaje'] = df_completo['País'].apply(lambda x: calcular_afinidad(x, afinidad_producto, mercados_df))

    # Seleccionar mercados recomendados
    top_latam = df_completo[df_completo['Región'] == 'Latinoamérica'].sort_values(by='Puntaje', ascending=False).head(3)
    top_global = df_completo[df_completo['Región'] == 'Resto del Mundo'].sort_values(by='Puntaje', ascending=False).head(2 + extra_global)

    df_recomendado = pd.concat([top_latam, top_global])

    # Fundamentos
    recomendaciones = []
    for index, row in df_recomendado.iterrows():
        fundamento = (
            f"**🌍 Mercado recomendado: {row['País']} ({row['Región']})**\n\n"
            f"- **Afinidad del producto**: {row['Afinidad']}\n"
            f"- **Tamaño del Mercado Total**: {row['Tamaño del Mercado Total (Millones USD)']}\n"
            f"- **Facilidad para hacer negocios**: {row['Facilidad Negocios (WB 2019)']}\n"
            f"- **Crecimiento Anual PIB**: {row['Crecimiento Anual PIB (%)']}\n\n"
            "✅ Este mercado presenta condiciones favorables para exportar tu producto, considerando su afinidad, tamaño de mercado y crecimiento económico."
        )
        recomendaciones.append(fundamento)
    
    return df_recomendado[['País', 'Región', 'Puntaje']], recomendaciones

# Configuración de la app
st.set_page_config(page_title="Recomendador de Mercados", page_icon="🌎")

# Logo
st.image("logo_ccsuy.png", use_container_width=True)

# Título e instrucciones
st.markdown("<h1 style='color: #3E8E41;'>Bienvenido al Recomendador de Mercados de Exportación 🌎</h1>", unsafe_allow_html=True)
st.markdown("🚀 Selecciona tu producto y descubre los mejores mercados para exportarlo. Priorizamos Latinoamérica, pero puedes explorar también el resto del mundo.")
with st.expander("ℹ️ ¿Cómo funciona esta herramienta?"):
    st.markdown("""
    # Recomendador de Mercados de Exportación 🌎

    ## Descripción

    Este es un **Recomendador de Mercados de Exportación** diseñado para ayudar a los exportadores uruguayos a identificar los mejores mercados para sus productos. La herramienta está basada en indicadores clave que incluyen la **afinidad del producto**, el **tamaño del mercado**, la **facilidad para hacer negocios** y el **crecimiento económico** de los países. 

    La recomendación de mercados se prioriza primero para **Latinoamérica** (debido a la cercanía geográfica y la afinidad cultural), seguida de las mejores opciones del **resto del mundo**.

    ## ¿Cómo Funciona?

    ### Cálculo de Afinidad por Producto

    La afinidad es un puntaje de potencial estimado que se calcula para cada combinación posible de Producto y País de destino. Se basa en una selección de características clave que posee ese país, ponderadas según su relevancia para la oportunidad de exportación.

    El proceso de cálculo para obtener el puntaje de afinidad de un Producto en un País es el siguiente:

    1. **Obtener las Métricas del País**: Se toman los valores específicos que tiene ese país para indicadores como Facilidad para hacer negocios, Tamaño del Mercado, Crecimiento del PIB, entre otros.
    2. **Normalizar las Métricas**: Se convierten a una escala común (por ejemplo, de 0 a 1) para permitir su comparación.
    3. **Ponderar las Métricas**: Cada puntaje normalizado se multiplica por un peso predefinido.
    4. **Sumar los Puntajes Ponderados**: Se obtiene un puntaje base, que representa la evaluación general del potencial de mercado.
    5. **Añadir Variación por Producto (Simulada)**: Se ajusta el puntaje para reflejar variabilidad específica del producto.
    6. **Escalar y Limitar el Puntaje Final**: El puntaje final se ajusta para asegurar que no exceda el máximo ni sea menor que el mínimo.

    Con base en estos cálculos, podrás explorar las mejores opciones para tu producto y encontrar mercados con mayores oportunidades de exportación.
    """)

# Implementación de la selección de productos y países
# Definir los productos disponibles
productos = afinidad_df['Producto'].unique()

# Seleccionar el producto
producto_seleccionado = st.selectbox("Selecciona tu Producto", productos)

# Botón para obtener recomendaciones
if st.button("Obtener Recomendaciones de Mercados"):
    afinidad_producto = afinidad_df[afinidad_df['Producto'] == producto_seleccionado]
    recomendacion, fundamentos = recomendar_mercados(afinidad_producto, mercados_df)
    
    st.write("### Mercados Recomendados:")
    st.dataframe(recomendacion)
    
    st.write("### Fundamentos para la recomendación:")
    for fundamento in fundamentos:
        st.markdown(fundamento)
        st.markdown("---")
    
    st.subheader("📊 Tabla de puntajes")
    st.dataframe(df_recomendado)

    # Expandible para más mercados globales
    with st.expander("🔍 Ver más mercados del Resto del Mundo (opcional)"):
        extra_count = st.slider("¿Cuántos mercados adicionales del mundo quieres ver?", min_value=1, max_value=10, value=3)
        df_ext, fundamentos_ext = recomendar_mercados(afinidad_producto, mercados_df, extra_global=extra_count)
        nuevos_globales = df_ext[~df_ext['País'].isin(df_recomendado['País']) & (df_ext['Región'] == "Resto del Mundo")]

        for i, row in nuevos_globales.iterrows():
            st.markdown(f"**🌐 {row['País']}** - Puntaje: {round(row['Puntaje'], 2)}")
        st.dataframe(nuevos_globales)

# Estilos
st.markdown(""" 
    <style> 
        .stButton > button { background-color: #3E8E41; color: white; font-size: 16px; } 
        .stButton > button:hover { background-color: #45a049; } 
    </style> 
""", unsafe_allow_html=True)
