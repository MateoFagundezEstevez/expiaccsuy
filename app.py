import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Ruta de los archivos CSV ya subidos
afinidad_file_path = "afinidad_producto_país.csv"
mercados_file_path = "mercados.csv"

def load_csv_file(file_path):
    try:
        # Intentamos con diferentes codificaciones
        try:
            return pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                return pd.read_csv(file_path, encoding='ISO-8859-1')
            except UnicodeDecodeError:
                return pd.read_csv(file_path, encoding='latin1')
    except Exception as e:
        st.error(f"Ocurrió un error al cargar el archivo {file_path}: {e}")
        return None

# Cargar los archivos CSV directamente desde las rutas
afinidad_df = load_csv_file(afinidad_file_path)
mercados_df = load_csv_file(mercados_file_path)

# Verificación de la carga de datos
if afinidad_df is not None:
    st.write("### Datos de 'afinidad_producto_país.csv':")
    st.write(afinidad_df)

if mercados_df is not None:
    st.write("### Datos de 'mercados.csv':")
    st.write(mercados_df)

# Interfaz para seleccionar el producto
producto_seleccionado = st.selectbox('Selecciona un Producto:', afinidad_df['Producto'].unique())

# Filtrar los datos de afinidad por el producto seleccionado
afinidad_producto = afinidad_df[afinidad_df['Producto'] == producto_seleccionado]

# Mostrar la afinidad del producto en diferentes países
st.write(f"### Afinidad del Producto '{producto_seleccionado}' en los países:")
st.write(afinidad_producto[['País', 'Afinidad']])

# Interfaz para seleccionar el país
pais_seleccionado = st.selectbox('Selecciona un País:', mercados_df['País'].unique())

# Filtrar los datos de mercado por el país seleccionado
mercado_pais = mercados_df[mercados_df['País'] == pais_seleccionado]

# Mostrar las características del país seleccionado
st.write(f"### Características del mercado en {pais_seleccionado}:")
st.write(mercado_pais)

# Visualización: Gráfico de afinidad vs demanda esperada
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=afinidad_df, x='Afinidad', y='Demanda esperada', hue='País', ax=ax)
ax.set_title(f"Afinidad vs Demanda Esperada para Producto: {producto_seleccionado}")
st.pyplot(fig)

# Visualización: Gráfico de características del país seleccionado
fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(x=mercado_pais.columns[1:], y=mercado_pais.iloc[0, 1:], ax=ax)
ax.set_title(f"Características de Mercado en {pais_seleccionado}")
ax.set_ylabel('Valor')
st.pyplot(fig)

# Análisis final
if afinidad_producto.empty or mercado_pais.empty:
    st.write("No hay datos disponibles para el producto o país seleccionados.")
else:
    st.write(f"### Análisis de mercado para el producto '{producto_seleccionado}' en {pais_seleccionado}:")
    st.write(f"**Afinidad en el país seleccionado:** {afinidad_producto['Afinidad'].values[0]}")
    st.write(f"**Demanda esperada en el país seleccionado:** {mercado_pais['Demanda esperada'].values[0]}")
    st.write(f"**Facilidad para hacer negocios en {pais_seleccionado}:** {mercado_pais['Facilidad para hacer negocios'].values[0]}")
    st.write(f"**Beneficios arancelarios en {pais_seleccionado}:** {mercado_pais['Beneficios arancelarios'].values[0]}")
    st.write(f"**Estabilidad política en {pais_seleccionado}:** {mercado_pais['Estabilidad política'].values[0]}")
