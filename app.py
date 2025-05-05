import streamlit as st
import pandas as pd
import numpy as np

# Cargar los datos localmente
afinidad_df = pd.read_csv("afinidad_producto_país.csv", encoding="ISO-8859-1")
mercados_df = pd.read_csv("mercados.csv", encoding="ISO-8859-1")

# Definir la función principal
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
    def calcular_puntaje(row):
        if row['Región'] == 'Latinoamérica':
            return (
                0.6 * row['Afinidad'] +
                0.15 * row['Tamaño del Mercado Total (Millones USD)'] +
                0.1 * row['Facilidad Negocios (WB 2019)'] +
                0.15 * row['Crecimiento Anual PIB (%)']
            )
        else:
            return (
                0.4 * row['Afinidad'] +
                0.25 * row['Tamaño del Mercado Total (Millones USD)'] +
                0.2 * row['Facilidad Negocios (WB 2019)'] +
                0.15 * row['Crecimiento Anual PIB (%)']
            )
    
    df_completo['Puntaje'] = df_completo.apply(calcular_puntaje, axis=1)

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

El cálculo de afinidad por producto se basa en datos históricos de comercio entre Uruguay y los países. Esto permite determinar qué tan bien un producto uruguayo se adapta a las necesidades de un mercado específico, lo cual es clave para identificar mercados potencialmente rentables.

Para cada producto, se utiliza un puntaje de afinidad que se combina con otros indicadores para determinar qué mercados son los más adecuados para exportar.

### Indicadores Utilizados

La recomendación de mercados se realiza tomando en cuenta los siguientes indicadores:

- **Afinidad del Producto**: Puntaje que refleja la afinidad histórica entre el producto y el mercado.
- **Demanda Esperada**: Proyección de la demanda o consumo del producto en el mercado destino.
- **Facilidad para Hacer Negocios**: Índice global que mide cuán fácil es hacer negocios en un país (según el Banco Mundial).
- **Beneficios Arancelarios**: Preferencias arancelarias entre Uruguay y el país destino, que facilitan el comercio.
- **Estabilidad Política**: Indicador de la estabilidad política en cada país (según fuentes como el Banco Mundial o Economist Intelligence Unit).
- **Tamaño del Mercado Total**: Estimación del tamaño del mercado para productos similares en millones de USD.
- **Crecimiento Anual del PIB**: Proyección de crecimiento económico del país en el corto y mediano plazo.

### Lógica de Recomendación

1. **Cálculo de Puntajes**: Los puntajes se calculan a partir de una combinación ponderada de estos indicadores. Los países de Latinoamérica tienen un mayor peso en la afinidad, mientras que los mercados fuera de Latinoamérica se priorizan en otros indicadores como el tamaño del mercado y el crecimiento económico.
   
2. **Selección de Mercados**: Se seleccionan los mejores mercados dentro de Latinoamérica y el resto del mundo en función del puntaje final. Los mercados se ordenan de mayor a menor puntaje, y se muestran los mejores según la cantidad seleccionada por el usuario.

3. **Personalización de Resultados**: El usuario puede ver más mercados globales adicionales ajustando un control deslizante, lo que permite explorar más opciones fuera de Latinoamérica.

### Fuentes de Información

Los datos utilizados en esta herramienta provienen de diversas fuentes confiables y actualizadas, que incluyen:

- **Banco Mundial**: Información sobre facilidad para hacer negocios, estabilidad política, etc.
- **Banco Interamericano de Desarrollo (BID)**: Datos sobre el crecimiento económico y otros indicadores clave.
- **OMC (Organización Mundial del Comercio)**: Información sobre comercio internacional y acuerdos preferenciales.
- **Trademap (ITC - Centro de Comercio Internacional)**: Datos sobre el comercio internacional y exportaciones.
- **Cámara de Comercio y Servicios del Uruguay**: Información consolidada sobre acuerdos comerciales y relaciones internacionales.

### Recomendaciones

Al obtener las recomendaciones, los usuarios verán los mercados sugeridos junto con una descripción detallada de los indicadores que contribuyeron a la recomendación. Estos fundamentos proporcionan un análisis completo de las razones por las que un mercado fue seleccionado.

## Uso de la Herramienta

### 1. Selección de Producto

El primer paso es elegir el producto que deseas exportar desde un listado disponible. Esto determinará el cálculo de afinidad para ese producto en particular.

### 2. Obtener Recomendaciones

Haz clic en el botón **"Obtener recomendaciones"** para que la herramienta te muestre los mercados recomendados. Los mercados se clasificarán primero por los mejores puntajes en **Latinoamérica**, seguidos de los mercados globales con mejor puntaje.

### 3. Más Mercados Globales

Si deseas explorar más mercados fuera de Latinoamérica, puedes usar el control deslizante para ajustar cuántos mercados adicionales del resto del mundo deseas ver.

### 4. Tabla de Puntajes

En la sección **"Tabla de Puntajes"**, podrás ver los puntajes calculados para cada país y cómo se comparan los mercados recomendados.

## Configuración

- **Lenguaje de la Aplicación**: Español
- **Estructura de la Aplicación**: Basada en Streamlit
- **Formato de Entrada**: Archivos CSV para los datos de afinidad y mercados

## Instalación

Si deseas instalar y ejecutar esta herramienta localmente, puedes seguir los siguientes pasos:

1. Clona este repositorio.
2. Instala las dependencias necesarias:

    ```bash
    pip install -r requirements.txt
    ```

3. Ejecuta la aplicación:

    ```bash
    streamlit run app.py
    ```

## Contacto

Si tienes preguntas o comentarios, no dudes en ponerte en contacto con nosotros a través de [correo electrónico o enlaces de contacto].
""", unsafe_allow_html=True)


)
# Selección de producto
producto = st.selectbox("Selecciona tu producto", afinidad_df['Producto'].unique())

# Recomendación principal
if st.button("Obtener recomendaciones"):
    afinidad_producto = afinidad_df[afinidad_df['Producto'] == producto]
    df_recomendado, fundamentos = recomendar_mercados(afinidad_producto, mercados_df)

    st.subheader("🌟 Mercados recomendados (con prioridad LATAM)")
    for i, (mercado, fundamento) in enumerate(zip(df_recomendado['País'], fundamentos)):
        st.markdown(f"**{i+1}. {mercado}**")
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
