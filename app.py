import streamlit as st
import pandas as pd
import numpy as np
import re
import io
import sys
from pathlib import Path
import logging
from typing import Dict, List, Optional, Set, Tuple, Union
import traceback
# Importar ParserError para manejo de errores en pandas
from pandas.errors import ParserError

# --- Setup Logging ---
# Configura el nivel de logging para que se muestren los mensajes en la consola de Streamlit Cloud
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configure Error Capture for Debugging ---
class StreamCapture:
    """Captura stdout a un buffer en memoria para depuración."""
    def __init__(self):
        self.logs = io.StringIO()
        self.old_stdout = sys.stdout

    def start(self):
        """Inicia la captura de stdout."""
        sys.stdout = self.logs

    def stop(self):
        """Detiene la captura de stdout y restaura el stdout original."""
        sys.stdout = self.old_stdout

    def get_logs(self):
        """Obtiene los logs capturados como una cadena."""
        return self.logs.getvalue()

# Instancia el capturador de logs
log_capture = StreamCapture()

# --- Application Constants ---
# Define los archivos de datos que la aplicación espera y sus posibles nombres/columnas
DATA_FILES = {
    # Archivo de afinidad producto-país (calculado previamente)
    "product_country_affinity": {
        "filename_variations": ["data/afinidad_producto_pais.csv", "afinidad_producto_país.csv", "afinidad_producto_pais.csv.csv", "afinidad_producto_país.csv.csv", "afinidad_producto_pais", "afinidad_producto_país"],
        "default_columns": ['Producto', 'País', 'Afinidad']
    },
    # Archivo consolidado de métricas de país (tu nueva tabla de mercados)
    "consolidated_country_metrics": {
        "filename_variations": ["data/mercados.csv", "mercados.csv", "data/country_metrics.csv", "country_metrics.csv"],
         # Asegúrate que estos nombres de columna coincidan EXACTAMENTE con el encabezado de tu archivo mercados.csv
         "default_columns": ['País', 'Facilidad Negocios (WB 2019)', 'Latitud', 'Longitud', 'PIB per cápita (USD)', 'Crecimiento Anual PIB (%)', 'Tamaño del Mercado Total (Millones USD)', 'Población (Millones)', 'Logística (LPI 2023)', 'Crecimiento Importaciones (%)', 'Sofisticación Exportaciones (Score)', 'Población Urbana (%)', 'Infraestructura Portuaria (LPI 2023)', 'Distancia a Uruguay (km)']
    },
    # Archivo de acuerdos comerciales (opcional, si se usa en fundamentos o info adicional)
    "commercial_agreements": {
        "filename_variations": ["data/acuerdos_comerciales.csv", "acuerdos_comerciales.csv"],
        "default_columns": ['country', 'agreement_name', 'beneficiary_country', 'product_coverage', 'preferential_tariff_reduction']
    },
    # Puedes añadir otros archivos originales si los necesitas (ej: demanda, aranceles por NCM)
    # pero si la afinidad ya los resume, quizás no sea necesario cargarlos en main
}

# Mapeos estándar de columnas para manejar variaciones en los archivos de datos del usuario
STANDARD_COLUMN_MAPPINGS = {
    'país': ['País', 'pais', 'país', 'country', 'nation', 'nacion', 'nation_name', 'country_name'],
    'producto': ['Producto', 'producto', 'product_name'],
    'afinidad': ['Afinidad', 'afinidad', 'affinity_score', 'score'],
    # Columnas del nuevo mercados.csv - Asegúrate que estos mapeos cubran variaciones si las hay
    'facilidad negocios (wb 2019)': ['Facilidad Negocios (WB 2019)', 'facilidad negocios', 'eodb_score'],
    'latitud': ['Latitud', 'latitud'],
    'longitud': ['Longitud', 'longitud'],
    'pib per cápita (usd)': ['PIB per cápita (USD)', 'pib per capita', 'gdp per capita'],
    'crecimiento anual pib (%)': ['Crecimiento Anual PIB (%)', 'crecimiento pib', 'gdp growth'],
    'tamaño del mercado total (millones usd)': ['Tamaño del Mercado Total (Millones USD)', 'tamaño mercado', 'total market size', 'gdp_total'],
    'población (millones)': ['Población (Millones)', 'poblacion', 'population'],
    'logística (lpi 2023)': ['Logística (LPI 2023)', 'logistica', 'lpi score'],
    'crecimiento importaciones (%)': ['Crecimiento Importaciones (%)', 'crecimiento importaciones', 'import growth'],
    'sofisticación exportaciones (score)': ['Sofisticación Exportaciones (Score)', 'sofisticacion exportaciones', 'export sophistication'],
    'población urbana (%)': ['Población Urbana (%)', 'poblacion urbana', 'urban population'],
    'infraestructura portuaria (lpi 2023)': ['Infraestructura Portuaria (LPI 2023)', 'infraestructura portuaria', 'port infrastructure'],
    'distancia a uruguay (km)': ['Distancia a Uruguay (km)', 'distancia uruguay', 'distance to uruguay'],
    # Columnas de acuerdos si se usan
    'agreement_name': ['agreement_name', 'nombre_acuerdo', 'acuerdo'],
    'beneficiary_country': ['beneficiary_country', 'pais_beneficiario', 'beneficiario'],
    'product_coverage': ['product_coverage', 'cobertura_producto', 'productos_cubiertos'],
    'preferential_tariff_reduction': ['preferential_tariff_reduction', 'reduccion_arancelaria', 'reduccion_preferencial']
}

# Lista común de países (para detección y clasificación regional)
COMMON_COUNTRIES = [
    "Argentina", "Brasil", "Paraguay", "Chile", "Bolivia", "Perú", "Colombia", "Ecuador",
    "México", "Panamá", "Costa Rica", "República Dominicana", "Guatemala", "El Salvador",
    "Honduras", "Nicaragua", "Venezuela", "Uruguay", "Cuba", "Haití", "Puerto Rico", "Belice",
    "Jamaica", "Trinidad y Tobago", "Barbados", "Guyana", "Surinam", # Latinoamérica y Caribe
    "Estados Unidos", "Canadá", # Norteamérica
    "Países Bajos", "Alemania", "España", "Italia", "Francia", "Bélgica", "Reino Unido", "Suiza", "Portugal", "Polonia", # Europa
    "China", "Japón", "Corea del Sur", "India", "Singapur", "Hong Kong", # Asia
    "Emiratos Árabes Unidos", # Medio Oriente
    "Sudáfrica", "Nigeria", "Egipto", "Argelia", # África
    "Australia", "Nueva Zelanda" # Oceanía
]


# --- Page Configuration ---
def setup_page():
    """Configura la página de Streamlit."""
    try:
        st.set_page_config(
            page_title="Recomendador de Mercados de Exportación",
            page_icon="🌎",
            layout="wide"
        )
        return True
    except Exception as e:
        st.error(f"Error en la configuración inicial de la página: {str(e)}")
        logger.error(f"Error in initial setup: {str(e)}")
        return False

# --- Setup Debugging Sidebar ---
def setup_debug_sidebar():
    """Configura la barra lateral de depuración."""
    with st.sidebar:
        st.subheader("Opciones de Depuración")
        # Usamos un key único para el checkbox
        show_debug = st.checkbox("Mostrar información de depuración", value=False, key='show_debug_checkbox')

        debug_expander = None
        if show_debug:
            st.info("La información de depuración se mostrará abajo.")
            debug_expander = st.expander("Registros de Depuración", expanded=True) # Expandido por defecto si está activo

    return show_debug, debug_expander

# --- Data Loading Functions ---
@st.cache_data
def load_data(filename: str) -> Optional[pd.DataFrame]:
    """
    Intenta cargar un archivo CSV con múltiples codificaciones.
    """
    try:
        # Lista de codificaciones comunes a intentar
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']

        # Intenta cargar con diferentes codificaciones
        for encoding in encodings:
            try:
                # Usar low_memory=False para evitar advertencias de tipos mixtos en columnas grandes
                df = pd.read_csv(filename, encoding=encoding, low_memory=False)
                logger.info(f"Successfully loaded {filename} with encoding {encoding}")
                return df
            except (UnicodeDecodeError, ParserError) as e:
                 # Captura errores específicos de codificación o parsing y prueba la siguiente
                 logger.warning(f"Failed to load {filename} with encoding {encoding} ({type(e).__name__}: {str(e)}). Trying next.")
                 continue
            except Exception as e:
                 # Captura cualquier otro error inesperado durante la lectura y prueba la siguiente
                 logger.warning(f"Failed to load {filename} with encoding {encoding} ({type(e).__name__}: {str(e)}). Trying next.")
                 continue

        # Si llegamos aquí, ninguna codificación funcionó o hubo un error de parsing persistente
        logger.error(f"Failed to load {filename}: No suitable encoding found or parsing error after trying all options.")
        return None
    except Exception as e:
        # Captura cualquier otro error inesperado durante el proceso de carga
        logger.error(f"General error during load_data for {filename}: {type(e).__name__}: {str(e)}")
        return None

def try_load_with_variations(base_name: str, show_debug: bool, debug_expander: Optional[st.expander]) -> pd.DataFrame:
    """
    Intenta cargar un archivo con diferentes variaciones de nombre y estandariza las columnas.
    """
    file_info = DATA_FILES.get(base_name, {})
    # Si no se encuentra información para base_name, usa un nombre por defecto y columnas vacías
    variations = file_info.get("filename_variations", [f"{base_name}.csv"])
    default_columns = file_info.get("default_columns", [])

    loaded_df = None
    successful_filename = None # Rastrea el nombre de archivo que funcionó

    for variant in variations:
        if show_debug and debug_expander:
             with debug_expander:
                 st.text(f"Attempting to load: {variant}")

        # Construye la ruta del archivo usando pathlib para manejo robusto de rutas
        file_path = Path(variant)
        if file_path.exists():
             # Pasa la ruta como cadena a load_data (compatibilidad con pandas < 1.3)
             df = load_data(str(file_path))
             if df is not None:
                 loaded_df = df
                 successful_filename = str(file_path) # Almacena el nombre de archivo exitoso
                 if show_debug and debug_expander:
                      with debug_expander:
                          st.text(f"✅ File loaded successfully: {variant}")
                 break # Detiene después de la primera carga exitosa
        else:
             if show_debug and debug_expander:
                  with debug_expander:
                      st.text(f"File not found: {variant}")

    if loaded_df is None:
        logger.error(f"Could not load any variation for base name '{base_name}'. Tried: {variations}")
        # Crea un DataFrame vacío con las columnas por defecto si la carga falla
        df = pd.DataFrame(columns=default_columns)
        # Asegura que las columnas estén estandarizadas incluso en un DF vacío
        df = standardize_columns(df, STANDARD_COLUMN_MAPPINGS)
        # Añade un nombre para propósitos de depuración
        df.name = f"Empty DF for {base_name} (Load Failed)"
        return df

    # Limpia y estandariza los nombres de columna después de una carga exitosa
    loaded_df.columns = [col.strip().lower() for col in loaded_df.columns]
    loaded_df = standardize_columns(loaded_df, STANDARD_COLUMN_MAPPINGS)
    # Añade el nombre del archivo exitoso al dataframe para rastreo
    loaded_df.name = successful_filename

    # Asegúrate de que las columnas numéricas esperadas sean numéricas, coercing errors
    numeric_cols_to_convert = [
        'afinidad', 'facilidad negocios (wb 2019)', 'latitud', 'longitud',
        'pib per cápita (usd)', 'crecimiento anual pib (%)',
        'tamaño del mercado total (millones usd)', 'población (millones)',
        'logística (lpi 2023)', 'crecimiento importaciones (%)',
        'sofisticación exportaciones (score)', 'población urbana (%)',
        'infraestructura portuaria (lpi 2023)', 'distancia a uruguay (km)'
        # Añade aquí otras columnas numéricas esperadas de tus archivos
    ]
    for col in numeric_cols_to_convert:
        if col in loaded_df.columns:
            loaded_df[col] = pd.to_numeric(loaded_df[col], errors='coerce')
            # Opcional: Llenar NaNs con 0 o otro valor si es apropiado para el cálculo downstream
            # Si la fórmula de afinidad maneja NaNs usando 0.5 neutral, no necesitas llenar aquí
            # loaded_df[col] = loaded_df[col].fillna(0) # Ejemplo

    return loaded_df

# standardize_columns function (slightly improved)
def standardize_columns(df: pd.DataFrame, standard_mappings: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Standardiza nombres de columna según un mapeo predefinido.
    Maneja insensibilidad a mayúsculas/minúsculas y elimina espacios.
    Asegura que las columnas esperadas estén presentes.
    """
    # Crea un mapeo de las columnas actuales (limpias) a sus nombres originales (limpios)
    current_cols_clean_to_original_clean = {col.strip().lower(): col.strip().lower() for col in df.columns}
    col_map = {}

    # Itera sobre los mapeos estándar para encontrar coincidencias en las columnas actuales
    for standard_col, possible_names in standard_mappings.items():
        for possible_name in possible_names:
            possible_name_clean = possible_name.strip().lower()
            if possible_name_clean in current_cols_clean_to_original_clean:
                original_col_clean_name = current_cols_clean_to_original_clean[possible_name_clean]
                # Si la columna limpia original aún no ha sido mapeada a un estándar
                # (esto previene que una columna original coincida con múltiples estándares si sus nombres posibles se solapan)
                if original_col_clean_name not in [v.strip().lower() for v in col_map.keys()]:
                     # Encuentra el nombre original exacto en el dataframe para renombrar
                     exact_original_col_name = [col for col in df.columns if col.strip().lower() == original_col_clean_name][0]
                     col_map[exact_original_col_name] = standard_col
                     break # Pasa al siguiente nombre estándar una vez encontrada una coincidencia


    # Renombra columnas usando el mapa creado.
    # Las columnas no en col_map mantendrán su nombre original (limpio: stripped + lower)
    df = df.rename(columns=col_map)

    # Asegura que todas las columnas estándar esperadas estén presentes, añadiendo NaN si faltan
    source_base_name = None
    # Intenta inferir el base_name del archivo original para saber qué columnas *esperar*
    if df.name and isinstance(df.name, str):
         for base_name, info in DATA_FILES.items():
             # Comprueba si alguna variación de nombre coincide con el nombre del archivo que se cargó
             if any(str(Path(var).name).lower() in str(Path(df.name).name).lower() for var in info.get('filename_variations', [])):
                 source_base_name = base_name
                 break
    # Si no se pudo inferir, omite añadir columnas faltantes basadas en default_columns

    if source_base_name and DATA_FILES[source_base_name].get('default_columns'):
        expected_standard_cols = DATA_FILES[source_base_name]['default_columns']
        # Convierte los nombres de columna esperados a sus versiones estandarizadas
        expected_standardized = set()
        for expected_col in expected_standard_cols:
            # Busca su mapeo estándar, si no lo encuentra, usa el nombre esperado en minúsculas (limpio)
            mapped_name = next((standard_col for standard_col, possible_names in standard_mappings.items()
                                 if expected_col.strip().lower() in [p.strip().lower() for p in possible_names]), expected_col.strip().lower())
            expected_standardized.add(mapped_name)


        # Añade columnas faltantes
        for col in expected_standardized:
            if col not in df.columns:
                 df[col] = np.nan # Añade columnas faltantes con NaN

    return df


# --- Recommendation Function (Adapted for new data) ---

# Define the new weights for recommendation based on the NEW mercado.csv columns and Afinidad
# Estos pesos son ejemplos, ajusta según tu lógica de negocio
RECOMMENDATION_WEIGHTS_LATAM = {
    'afinidad': 0.50, # La afinidad pre-calculada sigue siendo un factor importante
    'tamaño del mercado total (millones usd)': 0.20,
    'crecimiento anual pib (%)': 0.10,
    'facilidad negocios (wb 2019)': 0.10,
    'logística (lpi 2023)': 0.10,
    # Puedes añadir otros indicadores de tu mercados.csv aquí con sus pesos correspondientes
    # 'crecimiento importaciones (%)': 0.05,
    # 'distancia a uruguay (km)': 0.05, # Asegurarse de la normalización inversa si se añade
}

RECOMMENDATION_WEIGHTS_GLOBAL = {
    'afinidad': 0.40, # Menos énfasis en afinidad, más en otros factores quizás
    'tamaño del mercado total (millones usd)': 0.25,
    'crecimiento anual pib (%)': 0.15,
    'facilidad negocios (wb 2019)': 0.10,
    'logística (lpi 2023)': 0.10,
    # Puedes añadir otros indicadores aquí
}

# Asegurarse que los pesos sumen 1.0 en cada diccionario
def normalize_weights(weights):
    total_weight = sum(weights.values())
    if total_weight == 0: return {k: 0 for k in weights}
    return {k: v / total_weight for k, v in weights.items()}

RECOMMENDATION_WEIGHTS_LATAM_NORMALIZED = normalize_weights(RECOMMENDATION_WEIGHTS_LATAM)
RECOMMENDATION_WEIGHTS_GLOBAL_NORMALIZED = normalize_weights(RECOMMENDATION_WEIGHTS_GLOBAL)


def recomendar_mercados(afinidad_df: pd.DataFrame, mercados_df: pd.DataFrame, producto_seleccionado: str, extra_global: int = 0) -> Tuple[pd.DataFrame, List[str]]:
    """
    Recomienda mercados basado en afinidad pre-calculada y otros indicadores de mercado,
    usando la nueva estructura de mercados_df.

    Args:
        afinidad_df: DataFrame con columnas 'producto', 'país', 'afinidad' (completo o filtrado).
        mercados_df: DataFrame con columnas 'país', 'facilidad negocios (wb 2019)',
                     'tamaño del mercado total (millones usd)', etc. (tu nueva tabla).
        producto_seleccionado: El nombre del producto para el cual se buscan recomendaciones.
        extra_global: Número de mercados globales adicionales a recomendar.

    Returns:
        Tuple: DataFrame de mercados recomendados (con puntaje) y lista de fundamentos.
    """
    # Filtrar afinidad_df para el producto seleccionado (se hace aquí dentro para consistencia)
    afinidad_producto = afinidad_df[afinidad_df['producto'] == producto_seleccionado].copy()

    if afinidad_producto.empty:
        logger.warning(f"No hay datos de afinidad para el producto seleccionado: {producto_seleccionado}")
        return pd.DataFrame(), []

    # Asegurar que las columnas clave existen y tienen el nombre estandarizado
    required_afinidad_cols = ['país', 'afinidad']
    required_mercados_cols = ['país'] + list(RECOMMENDATION_WEIGHTS_LATAM.keys() - {'afinidad'}) # Necesita país y los indicadores con peso (excepto afinidad)

    if not all(col in afinidad_producto.columns for col in required_afinidad_cols):
        st.error(f"Error interno: afinidad_producto_filtrado no tiene las columnas requeridas: {required_afinidad_cols}")
        logger.error(f"Filtered Afinidad DF missing columns: {afinidad_producto.columns}. Required: {required_afinidad_cols}")
        return pd.DataFrame(), []

    if not all(col in mercados_df.columns for col in required_mercados_cols):
         st.error(f"Error interno: mercados_df no tiene las columnas requeridas para el cálculo: {required_mercados_cols}")
         logger.error(f"Mercados DF missing columns for calculation: {mercados_df.columns}. Required: {required_mercados_cols}")
         return pd.DataFrame(), []

    # Unir datasets (usando el nombre estandarizado 'país')
    # Usamos left join desde afinidad_producto para incluir todos los países con afinidad para este producto
    df_completo = pd.merge(afinidad_producto[['país', 'afinidad']],
                           mercados_df, on='país', how='left')

    # Eliminar filas donde no se pudo hacer el merge (países con afinidad pero no en mercados_df)
    # Opcional: puedes decidir mantenerlas y que sus métricas sean NaN (puntaje neutral)
    df_completo.dropna(subset=list(RECOMMENDATION_WEIGHTS_LATAM.keys() - {'afinidad'}), how='all', inplace=True)
    if df_completo.empty:
         st.warning(f"Después de unir con los datos de país, no quedan datos válidos para {producto_seleccionado}.")
         return pd.DataFrame(), []


    # Lista de países de Latinoamérica (usando el nombre estandarizado 'país' en minúsculas)
    latinoamerica_lower = {p.lower() for p in COMMON_COUNTRIES[:27]} # Los primeros 27 de COMMON_COUNTRIES

    # Clasificar región (usando el nombre estandarizado 'país' en minúsculas para la comparación)
    df_completo['Región'] = df_completo['país'].apply(lambda x: 'Latinoamérica' if str(x).lower() in latinoamerica_lower else 'Resto del Mundo')


    # --- Calcular puntajes ponderados usando los nuevos indicadores y pesos ---
    # Calcular los valores min/max para la normalización SOBRE EL DATAFRAME COMPLETO MERGEADO
    # Esto asegura que la normalización sea consistente a través de todos los países en el análisis actual
    metrics_to_normalize = list(RECOMMENDATION_WEIGHTS_LATAM.keys()) # Normalizar todos los que tienen peso

    min_max_values = {}
    for metric in metrics_to_normalize:
        if metric in df_completo.columns:
            # Asegurarse que la columna es numérica, coercing errors a NaN
            df_completo[metric] = pd.to_numeric(df_completo[metric], errors='coerce')
            # Eliminar NaNs temporales para calcular min/max
            temp_series = df_completo[metric].dropna()
            if not temp_series.empty:
                 min_val = temp_series.min()
                 max_val = temp_series.max()
                 min_max_values[metric] = {'min': min_val, 'max': max_val, 'range': max_val - min_val}
                 # Handle specific inverse normalization logic for distance
                 if metric == 'distancia a uruguay (km)':
                     min_max_values[metric]['is_higher_better'] = False
                 else:
                     min_max_values[metric]['is_higher_better'] = True

                 if show_debug and debug_expander:
                      with debug_expander:
                          st.text(f"Normalization range for '{metric}': Min={min_val}, Max={max_val}, Range={min_max_values[metric]['range']}, HigherBetter={min_max_values[metric]['is_higher_better']}")

            else:
                 logger.warning(f"Metric '{metric}' has no non-NaN values. Cannot normalize. Will use neutral score.")
                 min_max_values[metric] = {'min': 0, 'max': 1, 'range': 1, 'is_higher_better': True} # Default to avoid errors


    def calcular_puntaje(row):
        try:
            # Obtener los pesos apropiados según la región
            weights = RECOMMENDATION_WEIGHTS_LATAM_NORMALIZED if row['Región'] == 'Latinoamérica' else RECOMMENDATION_WEIGHTS_GLOBAL_NORMALIZED

            weighted_sum = 0
            for metric, weight in weights.items():
                 if metric in row and pd.notna(row[metric]): # Check if metric exists and has a value in this row
                     value = float(row[metric])

                     if metric in min_max_values: # Check if we have normalization info for this metric
                         norm_info = min_max_values[metric]
                         min_val = norm_info['min']
                         max_val = norm_info['max']
                         value_range = norm_info['range']
                         is_higher_better = norm_info['is_higher_better']

                         if value_range != 0:
                              # Standard min-max normalization to 0-1
                              norm_value = (value - min_val) / value_range
                              if not is_higher_better: # Inverse normalization
                                   norm_value = 1.0 - norm_value
                         else:
                              norm_value = 0.5 # Neutral if no variation in data

                         # Clamp normalized value between 0 and 1
                         norm_value = max(0.0, min(1.0, norm_value))

                         weighted_sum += norm_value * weight

                     elif weight > 0: # Metric has weight but no normalization info (e.g., not in metrics_to_normalize or no non-NaNs)
                          # Use a neutral normalized score (0.5) for metrics with weight but no valid data/norm info
                          weighted_sum += 0.5 * weight
                          # logger.warning(f"Metric '{metric}' weighted but no valid norm data for country {row['país']}. Using neutral.")


                 elif weight > 0: # Metric has weight but is missing (NaN) in this specific row
                     # Use a neutral normalized score (0.5) for missing data
                     weighted_sum += 0.5 * weight
                     # logger.warning(f"Metric '{metric}' weighted but missing for country {row['país']}. Using neutral.")


            # Final score is the weighted sum scaled to 0-100
            final_score = weighted_sum * 100.0

            # Ensure final score is within 0-100 range
            final_score = max(0.0, min(100.0, final_score))

            return final_score

        except Exception as e:
            logger.error(f"Error calculating puntaje for country {row.get('país', 'N/A')}: {type(e).__name__}: {str(e)}. Row data: {row.to_dict()}")
            return 0.0 # Return 0 in case of error


    # Aplicar la nueva función de puntuación
    df_completo['Puntaje'] = df_completo.apply(calcular_puntaje, axis=1)

    # --- Seleccionar mercados recomendados ---
    # Asegurar que 'Puntaje' sea numérico antes de ordenar
    df_completo['Puntaje'] = pd.to_numeric(df_completo['Puntaje'], errors='coerce')
    # Eliminar filas con Puntaje NaN si las hay (de países con datos críticos faltantes)
    df_completo.dropna(subset=['Puntaje'], inplace=True)


    # Filtrar y ordenar
    # Asegúrate de que hay suficientes filas para seleccionar los top N
    top_latam_count = min(3, df_completo[df_completo['Región'] == 'Latinoamérica'].shape[0])
    top_global_base_count = min(2, df_completo[df_completo['Región'] == 'Resto del Mundo'].shape[0])

    top_latam = df_completo[df_completo['Región'] == 'Latinoamérica'].sort_values(by='Puntaje', ascending=False).head(top_latam_count).copy()
    top_global_base = df_completo[df_completo['Región'] == 'Resto del Mundo'].sort_values(by='Puntaje', ascending=False).head(top_global_base_count).copy() # Base 2 global

    # Concatenar los top LATAM y los top Global base
    df_recomendado_base = pd.concat([top_latam, top_global_base])

    # Seleccionar mercados globales adicionales si extra_global > 0
    df_recomendado = df_recomendado_base.copy() # Empezamos con la base
    if extra_global > 0:
        # Excluir los países ya seleccionados en la base recomendación
        excluded_countries_lower = {str(p).lower() for p in df_recomendado_base['país'].unique()}
        additional_global_count = min(extra_global, df_completo[
            (df_completo['Región'] == 'Resto del Mundo') &
            (~df_completo['país'].astype(str).str.lower().isin(excluded_countries_lower))
        ].shape[0])

        if additional_global_count > 0:
             additional_global = df_completo[
                 (df_completo['Región'] == 'Resto del Mundo') &
                 (~df_completo['país'].astype(str).str.lower().isin(excluded_countries_lower))
             ].sort_values(by='Puntaje', ascending=False).head(additional_global_count).copy()

             # Concatenar con la base recomendación
             df_recomendado = pd.concat([df_recomendado_base, additional_global])


    # --- Fundamentos ---
    recomendaciones = []
    # Columnas relevantes del nuevo mercados_df para incluir en fundamentos (usando nombres estandarizados)
    fundamento_cols = [
        'afinidad',
        'tamaño del mercado total (millones usd)',
        'crecimiento anual pib (%)',
        'facilidad negocios (wb 2019)',
        'logística (lpi 2023)',
        'distancia a uruguay (km)',
        # Añadir otras columnas de tu nuevo mercados_df si quieres que aparezcan en fundamentos
        'pib per cápita (usd)',
        'crecimiento importaciones (%)',
        'sofisticación exportaciones (score)',
        'población urbana (%)',
        'infraestructura portuaria (lpi 2023)',
        # Omitida si se eliminó 'protección propiedad intelectual (score)'
    ]

    # Formatear valores para mejor visualización en fundamentos
    def format_value_for_fundamento(col_name, value):
        if pd.isna(value):
            return "N/A"
        # Formateo basado en el nombre estandarizado de la columna
        if col_name in ['tamaño del mercado total (millones usd)', 'pib per cápita (usd)']:
             return f"${value:,.0f}" # Formato moneda sin decimales
        elif col_name in ['crecimiento anual pib (%)', 'crecimiento importaciones (%)', 'población urbana (%)']:
             return f"{value:.1f}%" # Formato porcentaje con 1 decimal
        elif col_name in ['logística (lpi 2023)', 'infraestructura portuaria (lpi 2023)', 'sofisticación exportaciones (score)', 'afinidad', 'facilidad negocios (wb 2019)']:
             return f"{value:.1f}" # Score con 1 decimal
        elif col_name == 'distancia a uruguay (km)':
             return f"{value:,.0f} km" # Distancia en km sin decimales
        else:
            return str(value) # Valor por defecto como cadena

    # Renombrar columnas estandarizadas a nombres legibles para fundamentos
    fundamento_col_names = {
        'afinidad': 'Afinidad calculada (0-100)',
        'tamaño del mercado total (millones usd)': 'Tamaño Mercado Total (PIB)',
        'crecimiento anual pib (%)': 'Crecimiento Anual PIB',
        'facilidad negocios (wb 2019)': 'Facilidad para hacer Negocios (WB 2019)',
        'logística (lpi 2023)': 'Logística (LPI 2023 Score)',
        'distancia a uruguay (km)': 'Distancia desde Uruguay',
        'pib per cápita (usd)': 'PIB per Cápita',
        'crecimiento importaciones (%)': 'Crecimiento Importaciones (General)',
        'sofisticación exportaciones (score)': 'Sofisticación Exportaciones',
        'población urbana (%)': 'Población Urbana',
        'infraestructura portuaria (lpi 2023)': 'Infraestructura Portuaria (LPI 2023 Score)',
        # Si incluyes Protección Propiedad Intelectual de nuevo, añade su nombre aquí
        # 'protección propiedad intelectual (score)': 'Protección Propiedad Intelectual',
    }


    for index, row in df_recomendado.iterrows():
        fundamento_text = f"**🌍 Mercado recomendado: {row['país']} ({row['Región']})**\n\n"
        fundamento_text += f"- **Puntaje de Recomendación Calculado**: {row['Puntaje']:.2f}\n" # Añadir el puntaje final redondeado

        # Iterar sobre las columnas deseadas para fundamentos
        for col in fundamento_cols:
            # Asegurarse que la columna exista en el dataframe antes de intentar acceder a ella
            if col in row.index:
                 display_name = fundamento_col_names.get(col, col.title()) # Usar nombre legible o capitalizar
                 formatted_value = format_value_for_fundamento(col, row[col])
                 fundamento_text += f"- **{display_name}**: {formatted_value}\n"
            else:
                 logger.warning(f"Columna '{col}' no encontrada en el dataframe para fundamentos del país {row['país']}.")
                 # Opcional: añadir una línea al fundamento indicando dato faltante si es relevante
                 # display_name = fundamento_col_names.get(col, col.title())
                 # fundamento_text += f"- **{display_name}**: Dato no disponible\n"


        fundamento_text += "\n✅ Este mercado presenta un buen potencial estimado para exportar tu producto, basado en un análisis ponderado de sus métricas clave."
        recomendaciones.append(fundamento_text)

    # Renombrar columnas en el dataframe recomendado para la tabla de display final en la UI
    # Solo incluimos las columnas que queremos mostrar en la tabla principal
    display_cols_mapping = {
        'país': 'País',
        'Región': 'Región',
        'Puntaje': 'Puntaje Calculado' # Nombre visible en la tabla
    }
    # Asegurarse que las columnas existan antes de renombrar
    cols_to_display = [col for col in display_cols_mapping.keys() if col in df_recomendado.columns]
    df_recomendado_display = df_recomendado[cols_to_display].rename(columns=display_cols_mapping)


    return df_recomendado_display, recomendaciones

# --- Main Application Function ---
def main():
    """Función principal de la aplicación."""
    # Configura la página
    if not setup_page():
        return

    # Configura la barra lateral de depuración
    show_debug, debug_expander = setup_debug_sidebar()

    # Contenido principal
    # Logo (Asegúrate que logo_ccsuy.png esté en el mismo directorio o en data/)
    try:
        st.image("logo_ccsuy.png", use_container_width=True)
    except FileNotFoundError:
        st.warning("Logo 'logo_ccsuy.png' no encontrado. Asegúrate de que esté en el directorio correcto o en la carpeta 'data/'.") # Mensaje actualizado

    st.markdown("<h1 style='color: #3E8E41;'>Bienvenido al Recomendador de Mercados de Exportación 🌎</h1>", unsafe_allow_html=True)
    st.markdown("🚀 Selecciona tu producto y descubre los mejores mercados para exportarlo. Priorizamos Latinoamérica, pero puedes explorar también el resto del mundo.")
    with st.expander("ℹ️ ¿Cómo funciona esta herramienta?"):
        st.markdown("""
        Esta aplicación te ayuda a identificar mercados potenciales para productos uruguayos.  
        El análisis se basa en un **puntaje calculado** que combina:

        - La **Afinidad** pre-calculada del producto con cada país (idealmente basada en datos de comercio histórico y otros factores).
        - **Indicadores clave del país** obtenidos de fuentes como el Banco Mundial y el FMI, incluyendo:
            - Facilidad para hacer Negocios
            - Tamaño Total del Mercado (PIB)
            - Crecimiento Económico (PIB)
            - Performance Logística e Infraestructura Portuaria
            - Crecimiento de Importaciones
            - Sofisticación de Exportaciones
            - Población y Población Urbana
            - Distancia Geográfica desde Uruguay

        Los mercados se presentan priorizando las opciones con mayor puntaje en **Latinoamérica**, y luego se muestran las mejores opciones del **resto del mundo**.

        La información se obtiene de archivos de datos locales (`afinidad_producto_pais.csv`, `mercados.csv`, etc.) que deben estar en el mismo directorio que la aplicación o en una subcarpeta `data/`.

        👇 Elegí tu producto y explorá las recomendaciones.
        """)


    # --- Load DataFrames ---
    # Usa st.spinner para mostrar que se están cargando los datos
    with st.spinner("Cargando datos..."):
        # Aseguramos que el capturador de logs esté activo durante la carga
        log_capture.start()
        try:
            # Cargar archivo de afinidad usando la carga robusta
            afinidad_df = try_load_with_variations("product_country_affinity", show_debug, debug_expander)
            # Cargar archivo consolidado de métricas de país usando la carga robusta
            mercados_df = try_load_with_variations("consolidated_country_metrics", show_debug, debug_expander)
            # Cargar acuerdos (opcional)
            acuerdos_df = try_load_with_variations("commercial_agreements", show_debug, debug_expander)
        finally:
             # Detenemos la captura de logs de carga
             log_capture.stop()


    # Verificar estado de carga de los DataFrames esenciales
    essential_dfs_loaded = not afinidad_df.empty and not mercados_df.empty

    status_text = st.empty() # Placeholder para el mensaje de estado
    if essential_dfs_loaded:
        status_text.success("✅ Archivos de datos esenciales cargados exitosamente.")
        # Añadir la marca de verificación de la versión correcta solo si carga esencial tuvo éxito
        st.info("✅ Aplicación ejecutando la versión con carga de datos robusta y esencial cargado.")
    else:
        # Identificar qué archivos esenciales fallaron para un mensaje más útil
        failed_essentials = []
        if afinidad_df.empty: failed_essentials.append("Afinidad Producto-País")
        if mercados_df.empty: failed_essentials.append("Métricas Consolidadas del País")
        status_text.error(f"Archivos esenciales no cargados: {', '.join(failed_essentials)}. La aplicación no puede funcionar sin ellos.")

        # Mostrar logs de depuración inmediatamente si falló la carga esencial y el debug está activo
        if show_debug and debug_expander:
             with debug_expander:
                 st.text("--- Captured Logs during Essential Load ---")
                 st.text(log_capture.get_logs())
             st.warning("Active 'Mostrar información de depuración' en la barra lateral para ver los detalles del error de carga.")

        return # Detiene la ejecución si faltan datos esenciales


    # --- UI para la Selección de Producto ---

    # Asegurarse que la columna 'producto' exista y sea única en afinidad_df para el selectbox
    if not afinidad_df.empty and 'producto' in afinidad_df.columns:
         productos_disponibles = afinidad_df['producto'].dropna().unique().tolist()
         if productos_disponibles:
            # Ordenar productos alfabéticamente para el selectbox
            productos_disponibles.sort()
            producto_seleccionado = st.selectbox("Selecciona tu producto", productos_disponibles, key='product_selectbox')
         else:
            st.warning("No se encontraron productos válidos en el archivo de afinidad.")
            producto_seleccionado = None
    else:
        st.warning("Archivo de afinidad no cargado o sin columna 'producto'. No se puede seleccionar un producto.")
        producto_seleccionado = None


    # Botón de recomendación
    if producto_seleccionado: # Habilita el botón solo si hay un producto seleccionado
        if st.button("Obtener recomendaciones", key='get_recommendations_button'):
            st.markdown("---")

            # Iniciar captura de logs para la lógica de recomendación
            log_capture.start()
            try:
                # Llamar a la función de recomendación con los dataframes cargados y el producto
                # Pasar ambos DFs, la función hará el merge internamente
                df_recomendado, fundamentos = recomendar_mercados(afinidad_df, mercados_df, producto_seleccionado)

                if df_recomendado.empty:
                     st.warning(f"No se pudieron generar recomendaciones para el producto '{producto_seleccionado}'. Esto puede deberse a falta de datos de país o errores en el cálculo.")
                else:
                     # --- Mostrar resultados ---
                     st.subheader(f"🌟 Mercados recomendados para {producto_seleccionado} (con prioridad LATAM)")

                     # Mostrar el DataFrame principal de recomendaciones
                     # Usamos hide_index=True para no mostrar el índice de pandas
                     st.dataframe(df_recomendado, hide_index=True)

                     # Mostrar fundamentos
                     st.subheader("Fundamentos de la Recomendación")
                     # Usar un key único para cada expander dentro del bucle
                     for i, fundamento in enumerate(fundamentos):
                        # Buscar el nombre del país en el fundamento para el título del expander
                        match = re.search(r'🌍 Mercado recomendado: (.+?) \(', fundamento)
                        country_name_for_expander = match.group(1) if match else f"Recomendación {i+1}"

                        with st.expander(f"Ver detalles para {country_name_for_expander}", key=f'fundamento_expander_{i}'):
                             st.markdown(fundamento)


                     # Expandible para más mercados globales
                     st.markdown("---") # Separador antes del expander opcional
                     with st.expander("🔍 Ver más mercados del Resto del Mundo (opcional)", key='more_global_expander'):
                         # Usar un key único para el slider
                         extra_count = st.slider("¿Cuántos mercados adicionales del mundo quieres ver?", min_value=1, max_value=10, value=3, key='extra_global_slider')

                         # Llamar a la función nuevamente para obtener la lista extendida, pasando el producto
                         df_ext, fundamentos_ext = recomendar_mercados(afinidad_df, mercados_df, producto_seleccionado, extra_global=extra_count)

                         # Encontrar los nuevos mercados globales en la lista extendida que NO estaban en la recomendación base
                         # Asegurarse de usar minúsculas para la comparación
                         base_recommended_countries_lower = {str(p).lower() for p in df_recomendado['País'].unique()}
                         nuevos_globales = df_ext[
                             (df_ext['Región'] == "Resto del Mundo") &
                             (~df_ext['País'].astype(str).str.lower().isin(base_recommended_countries_lower))
                         ].copy() # Trabajar sobre una copia

                         if not nuevos_globales.empty:
                              st.subheader("Mercados Adicionales del Resto del Mundo")
                              # Mostrar solo País y Puntaje para la tabla adicional
                              st.dataframe(nuevos_globales[['País', 'Puntaje Calculado']], hide_index=True)
                              # Opcional: añadir fundamentos expandibles para estos también si lo deseas

                         else:
                              st.info("No se encontraron mercados adicionales en el Resto del Mundo con el criterio seleccionado.")


            except Exception as e:
                st.error(f"Ocurrió un error durante el análisis y recomendación: {str(e)}")
                logger.error(f"Error during recommendation process: {traceback.format_exc()}")
                if show_debug and debug_expander:
                    with debug_expander:
                        st.text(f"Detailed error during Recommendation: {traceback.format_exc()}")

            finally:
                 # Detener la captura de logs de recomendación
                 log_capture.stop()


    # --- Debug Information Display (at the end) ---
    # Asegurar que los logs del final se muestren
    if show_debug and debug_expander:
         with debug_expander:
             st.text("--- Logs al Final de la Ejecución (Si los hay) ---")
             st.text(log_capture.get_logs())


    # Display footer or additional info
    st.markdown("---")
    st.markdown("Este bot utiliza datos de mercados consolidados y afinidad calculada para sugerir mercados.")
    st.markdown("Asegúrese de que los archivos `afinidad_producto_pais.csv` y `mercados.csv` estén correctamente nombrados, formateados (CSV delimitado por comas) y ubicados (en el mismo directorio que `app.py` o en una subcarpeta `data/`).")
    st.markdown("Desarrollado por [Tu Nombre/Organización]")


# --- Run the application ---
if __name__ == "__main__":
    # El script comienza su ejecución aquí
    main()
