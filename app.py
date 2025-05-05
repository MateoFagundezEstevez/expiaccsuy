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

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configure Error Capture for Debugging ---
class StreamCapture:
    """Captures stdout to an in-memory buffer for debugging."""
    def __init__(self):
        self.logs = io.StringIO()
        self.old_stdout = sys.stdout

    def start(self):
        """Starts capturing stdout."""
        sys.stdout = self.logs

    def stop(self):
        """Stops capturing stdout and restores original stdout."""
        sys.stdout = self.old_stdout

    def get_logs(self):
        """Gets the captured logs as a string."""
        return self.logs.getvalue()

# Instantiate the log capturer
log_capture = StreamCapture()

# --- Application Constants ---
# Define the data files the application expects and their possible names/columns
DATA_FILES = {
    # Eliminamos los archivos originales que ya no usaremos directamente para afinidad
    # pero mantenemos el de acuerdos si es relevante para los fundamentos
    "commercial_agreements": {
        "filename_variations": ["data/acuerdos_comerciales.csv", "acuerdos_comerciales.csv"],
        "default_columns": ['country', 'agreement_name', 'beneficiary_country', 'product_coverage', 'preferential_tariff_reduction']
    },
    # Archivo de afinidad producto-país (calculado previamente)
    "product_country_affinity": {
        "filename_variations": ["data/afinidad_producto_pais.csv", "afinidad_producto_país.csv", "afinidad_producto_pais.csv.csv", "afinidad_producto_país.csv.csv", "afinidad_producto_pais", "afinidad_producto_país"],
        "default_columns": ['Producto', 'País', 'Afinidad']
    },
    # Archivo consolidado de métricas de país (tu nueva tabla)
    "consolidated_country_metrics": {
        "filename_variations": ["data/mercados.csv", "mercados.csv", "data/country_metrics.csv", "country_metrics.csv"],
        "default_columns": ['País', 'Facilidad Negocios (WB 2019)', 'Latitud', 'Longitud', 'PIB per cápita (USD)', 'Crecimiento Anual PIB (%)', 'Tamaño del Mercado Total (Millones USD)', 'Población (Millones)', 'Logística (LPI 2023)', 'Crecimiento Importaciones (%)', 'Sofisticación Exportaciones (Score)', 'Población Urbana (%)', 'Infraestructura Portuaria (LPI 2023)', 'Distancia a Uruguay (km)']
    }
}

# Standard column mappings to handle variations in user data files
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

# Common countries list for fallback detection (extendida si es necesario)
COMMON_COUNTRIES = [
    "brasil", "argentina", "china", "estados unidos", "eeuu", "usa",
    "méxico", "mexico", "canada", "canadá", "japón", "japon", "alemania",
    "francia", "italia", "españa", "espana", "chile", "colombia",
    "perú", "peru", "uruguay", "paraguay", "reino unido", "australia",
    "india", "rusia", "sudáfrica", "sudafrica", "portugal", "holanda",
    "países bajos", "paises bajos", "bélgica", "belgica", "suiza", "corea del sur",
    "singapur", "bolivia", "ecuador", "panamá", "panama", "costa rica",
    "república dominicana", "guatemala", "el salvador", "honduras", "nicaragua",
    "venezuela", "cuba", "haití", "haiti", "puerto rico", "belice", "jamaica",
    "trinidad y tobago", "barbados", "guyana", "surinam", "argelia", "egipto",
    "nigeria", "polonia", "nueva zelanda", "emiratos árabes unidos", "hong kong"
]


# --- Page Configuration ---
def setup_page():
    """Configure the Streamlit page settings."""
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
    """Configure the debugging sidebar."""
    with st.sidebar:
        st.subheader("Opciones de Depuración")
        show_debug = st.checkbox("Mostrar información de depuración", value=False)

        debug_expander = None
        if show_debug:
            st.info("La información de depuración se mostrará abajo.")
            debug_expander = st.expander("Registros de Depuración")

    return show_debug, debug_expander

# --- Data Loading Functions (Integrated) ---
# load_data function remains the same as in the previous robust code block
@st.cache_data
def load_data(filename: str) -> Optional[pd.DataFrame]:
    """
    Attempt to load a CSV file with multiple encodings.
    """
    try:
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
        for encoding in encodings:
            try:
                df = pd.read_csv(filename, encoding=encoding, low_memory=False)
                logger.info(f"Successfully loaded {filename} with encoding {encoding}")
                return df
            except (UnicodeDecodeError, ParserError): # Added ParserError for robustness
                logger.warning(f"Failed to load {filename} with encoding {encoding}. Trying next.")
                continue
            except Exception as e:
                 logger.warning(f"Failed to load {filename} with encoding {encoding} ({type(e).__name__}: {str(e)}). Trying next.")
                 continue

        logger.error(f"Failed to load {filename}: No suitable encoding found or parsing error.")
        return None
    except Exception as e:
        logger.error(f"General error during load_data for {filename}: {type(e).__name__}: {str(e)}")
        return None

# try_load_with_variations function remains the same as in the previous robust code block
def try_load_with_variations(base_name: str, show_debug: bool, debug_expander: Optional[st.expander]) -> pd.DataFrame:
    """
    Attempt to load a file with different name variations and standardize columns.
    """
    file_info = DATA_FILES.get(base_name, {})
    variations = file_info.get("filename_variations", [f"{base_name}.csv"])
    default_columns = file_info.get("default_columns", [])

    loaded_df = None
    successful_filename = None

    for variant in variations:
        if show_debug and debug_expander:
             with debug_expander:
                 st.text(f"Attempting to load: {variant}")

        file_path = Path(variant)
        if file_path.exists():
             df = load_data(str(file_path))
             if df is not None:
                 loaded_df = df
                 successful_filename = str(file_path)
                 if show_debug and debug_expander:
                      with debug_expander:
                          st.text(f"✅ File loaded successfully: {variant}")
                 break
        else:
             if show_debug and debug_expander:
                  with debug_expander:
                      st.text(f"File not found: {variant}")

    if loaded_df is None:
        logger.warning(f"Could not load any variation for base name '{base_name}'. Tried: {variations}")
        df = pd.DataFrame(columns=default_columns)
        df = standardize_columns(df, STANDARD_COLUMN_MAPPINGS) # Standardize empty DF too
        df.name = f"Empty DF for {base_name} (Load Failed)"
        return df

    loaded_df.columns = [col.strip().lower() for col in loaded_df.columns]
    loaded_df = standardize_columns(loaded_df, STANDARD_COLUMN_MAPPINGS)
    loaded_df.name = successful_filename
    return loaded_df

# standardize_columns function remains the same as in the previous robust code block
def standardize_columns(df: pd.DataFrame, standard_mappings: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Standardize column names according to a predefined mapping.
    """
    # Ensure current columns are stripped and lowercased for matching
    current_cols_mapping = {col.strip().lower(): col for col in df.columns}
    col_map = {}

    for standard_col, possible_names in standard_mappings.items():
        for possible_name in possible_names:
            possible_name_lower = possible_name.strip().lower()
            if possible_name_lower in current_cols_mapping:
                original_col_name = current_cols_mapping[possible_name_lower]
                if original_col_name not in col_map: # Map original name to standard name only once
                    col_map[original_col_name] = standard_col
                    break # Move to the next standard_col

    # Rename columns using the created map
    df = df.rename(columns=col_map)

    # Ensure all expected standard columns are present
    source_base_name = None
    # Infer source base name from df.name or column structure if df.name is not set
    if df.name and isinstance(df.name, str):
         for base_name, info in DATA_FILES.items():
             # Simple check: if any variation name is part of the df.name
             if any(var.lower() in df.name.lower() for var in info.get('filename_variations', [])):
                 source_base_name = base_name
                 break
         # If df.name didn't work, try matching columns to default columns
         if source_base_name is None:
             current_standardized_cols = set(df.columns)
             for base_name, info in DATA_FILES.items():
                 expected_standard_cols = set(info.get('default_columns', []))
                 # If a significant portion of expected columns are in the df
                 if len(expected_standard_cols.intersection(current_standardized_cols)) > len(expected_standard_cols) * 0.5 and len(expected_standard_cols) > 0:
                      source_base_name = base_name
                      break


    if source_base_name and DATA_FILES[source_base_name].get('default_columns'):
        expected_standard_cols = DATA_FILES[source_base_name]['default_columns']
        # Convert expected columns to the standardized names they *should* map to
        expected_standardized = set()
        for expected_col in expected_standard_cols:
            # Find the standard name it maps to, or use itself if no mapping found in the main map
            mapped_name = next((standard_col for standard_col, possible_names in standard_mappings.items()
                                 if expected_col.strip().lower() in [p.strip().lower() for p in possible_names]), expected_col.strip().lower())
            expected_standardized.add(mapped_name)


        for col in expected_standardized:
            if col not in df.columns:
                 df[col] = np.nan # Add missing expected columns

    return df


# --- Recommendation Function (Adapted for new data) ---

# Define the new weights for recommendation based on the NEW mercado.csv columns and Afinidad
# These are examples, adjust based on desired business logic
RECOMMENDATION_WEIGHTS_LATAM = {
    'afinidad': 0.50, # Keep affinity high
    'tamaño del mercado total (millones usd)': 0.20,
    'crecimiento anual pib (%)': 0.10,
    'facilidad negocios (wb 2019)': 0.10,
    'logística (lpi 2023)': 0.10,
    # Note: Other metrics from new mercados.csv like Distancia, Pop Urbana, etc.,
    # are implicitly considered in the Afinidad score or omitted here for simplicity.
}

RECOMMENDATION_WEIGHTS_GLOBAL = {
    'afinidad': 0.40, # Slightly less emphasis on affinity
    'tamaño del mercado total (millones usd)': 0.25,
    'crecimiento anual pib (%)': 0.15,
    'facilidad negocios (wb 2019)': 0.10,
    'logística (lpi 2023)': 0.10,
}


def recomendar_mercados(afinidad_df: pd.DataFrame, mercados_df: pd.DataFrame, extra_global: int = 0) -> Tuple[pd.DataFrame, List[str]]:
    """
    Recomienda mercados basado en afinidad pre-calculada y otros indicadores de mercado,
    usando la nueva estructura de mercados_df.

    Args:
        afinidad_df: DataFrame con columnas 'Producto', 'País', 'Afinidad'.
        mercados_df: DataFrame con columnas 'País', 'Facilidad Negocios (WB 2019)',
                     'Tamaño del Mercado Total (Millones USD)', etc. (tu nueva tabla).
        extra_global: Número de mercados globales adicionales a recomendar.

    Returns:
        Tuple: DataFrame de mercados recomendados y lista de fundamentos.
    """
    # Asegurar que las columnas clave existen y tienen el nombre estandarizado
    required_afinidad_cols = ['producto', 'país', 'afinidad']
    required_mercados_cols = ['país', 'facilidad negocios (wb 2019)',
                              'tamaño del mercado total (millones usd)', 'crecimiento anual pib (%)',
                              'logística (lpi 2023)'] # Indicadores usados en el cálculo + país clave

    if not all(col in afinidad_df.columns for col in required_afinidad_cols):
        st.error(f"Error: afinidad_df no tiene las columnas requeridas: {required_afinidad_cols}")
        logger.error(f"Afinidad DF missing columns: {afinidad_df.columns}")
        return pd.DataFrame(), []

    if not all(col in mercados_df.columns for col in required_mercados_cols):
         st.error(f"Error: mercados_df no tiene las columnas requeridas para el cálculo: {required_mercados_cols}")
         logger.error(f"Mercados DF missing columns: {mercados_df.columns}")
         return pd.DataFrame(), []

    # Seleccionar un producto (ya se hizo fuera de la función principal en el selectbox)
    # La función recibe el afinidad_df filtrado para el producto seleccionado
    afinidad_producto = afinidad_df.copy() # Trabajar sobre una copia

    # Unir datasets (usando el nombre estandarizado 'país')
    # Usar how='left' desde afinidad_producto para mantener todos los países con afinidad
    # y how='inner' si solo quieres países que están en ambos (menos recomendado si afinidad tiene más países)
    # Usemos left para no perder países de afinidad si faltan en mercados_df (se tratarán como datos faltantes con 0.5 normalizado)
    df_completo = pd.merge(afinidad_producto[['país', 'afinidad']],
                           mercados_df, on='país', how='left')


    # Lista de países de Latinoamérica (mantener la misma lógica original del usuario)
    latinoamerica_lower = {p.lower() for p in [
        "Argentina", "Brasil", "Paraguay", "Chile", "Bolivia", "Perú", "Colombia", "Ecuador",
        "México", "Panamá", "Costa Rica", "República Dominicana", "Guatemala", "El Salvador",
        "Honduras", "Nicaragua", "Venezuela", "Uruguay", "Cuba", "Haití", "Puerto Rico", "Belice",
        "Jamaica", "Trinidad y Tobago", "Barbados", "Guyana", "Surinam"
    ]}

    # Clasificar región (usando el nombre estandarizado 'país' en minúsculas para la comparación)
    df_completo['Región'] = df_completo['país'].apply(lambda x: 'Latinoamérica' if str(x).lower() in latinoamerica_lower else 'Resto del Mundo')


    # --- Calcular puntajes ponderados usando los nuevos indicadores y pesos ---
    # Primero, calcular los valores min/max para la normalización SOBRE EL DATAFRAME COMPLETO MERGEADO
    # Esto asegura que la normalización sea consistente a través de todos los países en el análisis actual
    metrics_to_normalize = {
        'tamaño del mercado total (millones usd)': True, # True = higher is better
        'crecimiento anual pib (%)': True,
        'facilidad negocios (wb 2019)': True,
        'logística (lpi 2023)': True,
        # 'afinidad': True # Afinidad ya está en 0-100, se puede usar directamente o normalizar
        # 'distancia a uruguay (km)': False # False = lower is better (if used in scoring)
    }

    # Calcular min/max y rangos
    min_max_values = {}
    for metric, is_higher_better in metrics_to_normalize.items():
        if metric in df_completo.columns:
            # Convert to numeric, coercing errors to NaN
            df_completo[metric] = pd.to_numeric(df_completo[metric], errors='coerce')
            min_val = df_completo[metric].min()
            max_val = df_completo[metric].max()
            min_max_values[metric] = {'min': min_val, 'max': max_val, 'range': max_val - min_val}
            if show_debug and debug_expander:
                 with debug_expander:
                     st.text(f"Normalization range for '{metric}': Min={min_val}, Max={max_val}")
        else:
            logger.warning(f"Metric '{metric}' not found in merged dataframe. Cannot normalize/use in scoring.")
            min_max_values[metric] = {'min': 0, 'max': 1, 'range': 1} # Default to avoid division by zero


    def calcular_puntaje(row):
        try:
            # Get the appropriate weights based on region
            weights = RECOMMENDATION_WEIGHTS_LATAM if row['Región'] == 'Latinoamérica' else RECOMMENDATION_WEIGHTS_GLOBAL

            weighted_sum = 0
            # Afinidad is often already 0-100, treat it as a base score or normalize relative to its own range in this df
            # Let's normalize Afinidad relative to its range in the merged df too for consistency
            afinidad_min = df_completo['afinidad'].min() if pd.notna(df_completo['afinidad'].min()) else 0
            afinidad_max = df_completo['afinidad'].max() if pd.notna(df_completo['afinidad'].max()) else 1
            afinidad_range = afinidad_max - afinidad_min
            afinidad_norm = (row['afinidad'] - afinidad_min) / afinidad_range if afinidad_range != 0 else 0.5
            afinidad_norm = max(0.0, min(1.0, afinidad_norm)) # Clamp

            # Start with the weighted affinity
            weighted_sum += afinidad_norm * weights.get('afinidad', 0) # Use 0 weight if not found

            # Add weighted normalized scores for other metrics
            for metric, weight in weights.items():
                 if metric == 'afinidad': continue # Skip afinidad here

                 if metric in row and pd.notna(row[metric]) and metric in metrics_to_normalize: # Check if metric exists and was in normalize list
                     value = float(row[metric])
                     norm_info = min_max_values.get(metric, {'min': 0, 'max': 1, 'range': 1})
                     min_val = norm_info['min']
                     max_val = norm_info['max']
                     value_range = norm_info['range']

                     if value_range != 0:
                          # Standard normalization (higher is better)
                          norm_value = (value - min_val) / value_range
                     else:
                          norm_value = 0.5 # Neutral if no variation in data

                     norm_value = max(0.0, min(1.0, norm_value)) # Clamp

                     weighted_sum += norm_value * weight

                 elif metric in weights: # If metric has weight but is missing in data or not for normalization
                     # Use a neutral normalized score (0.5) for missing or non-normalized metrics with weights
                     weighted_sum += 0.5 * weight
                     # logger.warning(f"Metric '{metric}' weighted but not available/normalized for country {row['país']}. Using neutral.")


            # Final score is the weighted sum scaled (already using normalized 0-1 values, so just scale by 100)
            final_score = weighted_sum * 100.0

            # Ensure final score is within 0-100 range
            final_score = max(0.0, min(100.0, final_score))

            return final_score

        except Exception as e:
            logger.error(f"Error calculating puntaje for country {row.get('país', 'N/A')}: {type(e).__name__}: {str(e)}")
            return 0.0


    # Apply the new scoring function
    df_completo['Puntaje'] = df_completo.apply(calcular_puntaje, axis=1)

    # --- Seleccionar mercados recomendados ---
    # Asegurar que 'Puntaje' sea numérico antes de ordenar
    df_completo['Puntaje'] = pd.to_numeric(df_completo['Puntaje'], errors='coerce')

    # Filtrar y ordenar
    top_latam = df_completo[df_completo['Región'] == 'Latinoamérica'].sort_values(by='Puntaje', ascending=False).head(3).copy()
    top_global_base = df_completo[df_completo['Región'] == 'Resto del Mundo'].sort_values(by='Puntaje', ascending=False).head(2).copy() # Base 2 global

    # Concatenar los top 3 LATAM y los top 2 Global base
    df_recomendado_base = pd.concat([top_latam, top_global_base])

    # Seleccionar mercados globales adicionales si extra_global > 0
    if extra_global > 0:
        # Excluir los países ya seleccionados en la base recomendación
        excluded_countries_lower = {str(p).lower() for p in df_recomendado_base['país'].unique()}
        additional_global = df_completo[
            (df_completo['Región'] == 'Resto del Mundo') &
            (~df_completo['país'].astype(str).str.lower().isin(excluded_countries_lower))
        ].sort_values(by='Puntaje', ascending=False).head(extra_global).copy()

        # Concatenar con la base recomendación
        df_recomendado = pd.concat([df_recomendado_base, additional_global])
    else:
        df_recomendado = df_recomendado_base.copy() # No additional globals


    # --- Fundamentos ---
    recomendaciones = []
    # Columnas relevantes del nuevo mercados_df para incluir en fundamentos (usando nombres estandarizados)
    fundamento_cols = [
        'afinidad',
        'tamaño del mercado total (millones usd)',
        'crecimiento anual pib (%)',
        'facilidad negocios (wb 2019)',
        'logística (lpi 2023)',
        'distancia a uruguay (km)', # También relevante aunque no esté en el score directo
        # Añadir otras columnas de tu nuevo mercados_df si quieres que aparezcan en fundamentos
        'pib per cápita (usd)',
        'crecimiento importaciones (%)',
        'sofisticación exportaciones (score)',
        'población urbana (%)',
        'infraestructura portuaria (lpi 2023)',
        # 'protección propiedad intelectual (score)' # Omitida si se eliminó
    ]

    # Formatear columnas para mejor visualización en fundamentos
    def format_value_for_fundamento(col_name, value):
        if pd.isna(value):
            return "N/A"
        if col_name in ['tamaño del mercado total (millones usd)', 'pib per cápita (usd)']:
             return f"${value:,.0f}" # Formato moneda
        elif col_name in ['crecimiento anual pib (%)', 'crecimiento importaciones (%)', 'población urbana (%)']:
             return f"{value:.1f}%" # Formato porcentaje
        elif col_name in ['logística (lpi 2023)', 'infraestructura portuaria (lpi 2023)', 'sofisticación exportaciones (score)']:
             return f"{value:.2f}" # Score con decimales
        elif col_name == 'distancia a uruguay (km)':
             return f"{value:,.0f} km" # Distancia en km
        elif col_name == 'afinidad':
             return f"{value:.1f}" # Afinidad con 1 decimal
        elif col_name == 'facilidad negocios (wb 2019)':
             return f"{value:.1f}" # Facilidad negocios con 1 decimal
        else:
            return str(value)

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
        'protección propiedad intelectual (score)': 'Protección Propiedad Intelectual',
    }


    for index, row in df_recomendado.iterrows():
        fundamento_text = f"**🌍 Mercado recomendado: {row['país']} ({row['Región']})**\n\n"
        fundamento_text += f"- **Puntaje de Recomendación Calculado**: {row['Puntaje']:.2f}\n" # Añadir el puntaje final

        for col in fundamento_cols:
            if col in row.index:
                 display_name = fundamento_col_names.get(col, col.title()) # Usar nombre legible o capitalizar
                 formatted_value = format_value_for_fundamento(col, row[col])
                 fundamento_text += f"- **{display_name}**: {formatted_value}\n"


        fundamento_text += "\n✅ Este mercado presenta un buen potencial estimado para exportar tu producto, basado en un análisis ponderado de sus métricas clave."
        recomendaciones.append(fundamento_text)

    # Renombrar columnas en el dataframe recomendado para la tabla de display final
    df_recomendado_display = df_recomendado.rename(columns={
        'país': 'País',
        'Región': 'Región',
        'Puntaje': 'Puntaje Calculado',
        # Puedes añadir renombres para las columnas de fundamento si quieres mostrarlas en la tabla principal
        # 'afinidad': 'Afinidad',
        # 'tamaño del mercado total (millones usd)': 'Tamaño Mercado'
        # etc.
    })


    return df_recomendado_display, recomendaciones

# --- Main Application Function ---
def main():
    """Main application function."""
    # Configure page
    if not setup_page():
        return

    # Setup debugging sidebar
    show_debug, debug_expander = setup_debug_sidebar()

    # Main content
    # Logo (Asegúrate que logo_ccsuy.png esté en el mismo directorio o en data/)
    try:
        st.image("logo_ccsuy.png", use_container_width=True)
    except FileNotFoundError:
        st.warning("Logo 'logo_ccsuy.png' no encontrado. Asegúrate de que esté en el directorio correcto.")

    st.markdown("<h1 style='color: #3E8E41;'>Bienvenido al Recomendador de Mercados de Exportación 🌎</h1>", unsafe_allow_html=True)
    st.markdown("🚀 Selecciona tu producto y descubre los mejores mercados para exportarlo. Priorizamos Latinoamérica, pero puedes explorar también el resto del mundo.")
    with st.expander("ℹ️ ¿Cómo funciona esta herramienta?"):
        st.markdown("""
        Esta aplicación te ayuda a identificar mercados potenciales para productos uruguayos.  
        El análisis se basa en un **puntaje calculado** que combina:

        - La **Afinidad** pre-calculada del producto con cada país.
        - **Indicadores clave del país** como el Tamaño Total del Mercado (PIB), Crecimiento Económico, Facilidad para hacer Negocios y Performance Logística.

        Los mercados se presentan priorizando las opciones en **Latinoamérica**, y luego se muestran las mejores opciones del **resto del mundo**.

        La información se obtiene de archivos de datos locales que consolidan métricas de fuentes como el Banco Mundial, FMI y análisis de afinidad.

        👇 Elegí tu producto y explorá las recomendaciones.
        """)


    # --- Load DataFrames ---
    log_capture.start() # Start capturing logs for debugging
    with st.spinner("Cargando datos..."):
        # Cargar archivo de afinidad
        afinidad_df = try_load_with_variations("product_country_affinity", show_debug, debug_expander)
        # Cargar archivo consolidado de métricas de país
        mercados_df = try_load_with_variations("consolidated_country_metrics", show_debug, debug_expander)
        # Cargar acuerdos (opcional para fundamentos si se adaptan)
        acuerdos_df = try_load_with_variations("commercial_agreements", show_debug, debug_expander)

    # Verify data loading status
    loaded_dfs_status = {
        "Afinidad Producto-País": not afinidad_df.empty,
        "Métricas Consolidadas del País": not mercados_df.empty,
        "Acuerdos Comerciales": not acuerdos_df.empty # Status for agreements file
    }

    status_text = st.empty() # Placeholder for status message
    if all(loaded_dfs_status.values()):
        status_text.success("✅ Todos los archivos de datos cargados exitosamente.")
    else:
        failed_files = [name for name, loaded in loaded_dfs_status.items() if not loaded]
        if failed_files:
            status_text.warning(f"No se pudieron cargar los siguientes archivos: {', '.join(failed_files)}")
            status_text.info("La aplicación funcionará con capacidades limitadas usando los datos disponibles.")
        # Check if essential files are loaded for core functionality
        if not loaded_dfs_status["Afinidad Producto-País"] or not loaded_dfs_status["Métricas Consolidadas del País"]:
             st.error("Archivos esenciales (Afinidad y Métricas de País) no cargados. La aplicación no puede funcionar.")
             log_capture.stop()
             if show_debug and debug_expander:
                 with debug_expander:
                     st.text("--- Captured Logs ---")
                     st.text(log_capture.get_logs())
             return # Stop execution if essential data is missing


    # --- UI for Recommendation ---

    # Asegurarse que la columna 'producto' exista y sea única en afinidad_df para el selectbox
    if not afinidad_df.empty and 'producto' in afinidad_df.columns:
         productos_disponibles = afinidad_df['producto'].dropna().unique().tolist()
         if productos_disponibles:
            producto_seleccionado = st.selectbox("Selecciona tu producto", productos_disponibles)
         else:
            st.warning("No se encontraron productos válidos en el archivo de afinidad.")
            producto_seleccionado = None
    else:
        st.warning("Archivo de afinidad no cargado o sin columna 'producto'. No se puede seleccionar un producto.")
        producto_seleccionado = None


    # Botón de recomendación
    if producto_seleccionado and st.button("Obtener recomendaciones"):
        st.markdown("---")

        try:
            # Filtrar afinidad_df para el producto seleccionado
            afinidad_producto_filtrado = afinidad_df[afinidad_df['producto'] == producto_seleccionado].copy()

            if afinidad_producto_filtrado.empty:
                 st.warning(f"No se encontraron datos de afinidad para el producto '{producto_seleccionado}'.")
            else:
                 # Llamar a la función de recomendación con los dataframes cargados
                 # Pasar ambos DFs, la función hará el merge internamente
                 df_recomendado, fundamentos = recomendar_mercados(afinidad_producto_filtrado, mercados_df)

                 # --- Mostrar resultados ---
                 st.subheader("🌟 Mercados recomendados (con prioridad LATAM)")

                 # Mostrar el DataFrame principal de recomendaciones
                 st.dataframe(df_recomendado.rename(columns={'Puntaje Calculado': 'Puntaje'}), hide_index=True) # Rename for display table

                 # Mostrar fundamentos
                 st.subheader("Fundamentos de la Recomendación")
                 for i, fundamento in enumerate(fundamentos):
                    # Buscar el nombre del país en el fundamento para el título del expander
                    match = re.search(r'🌍 Mercado recomendado: (.+?) \(', fundamento)
                    country_name_for_expander = match.group(1) if match else f"Recomendación {i+1}"

                    with st.expander(f"Ver detalles para {country_name_for_expander}"):
                         st.markdown(fundamento)
                    # st.markdown("---") # Optional separator between expanders


                 # Expandible para más mercados globales
                 st.markdown("---")
                 with st.expander("🔍 Ver más mercados del Resto del Mundo (opcional)"):
                     # Usar un key único para el slider si está dentro de un expander o if block
                     extra_count = st.slider("¿Cuántos mercados adicionales del mundo quieres ver?", min_value=1, max_value=10, value=3, key='extra_global_slider')

                     # Volver a obtener afinidad_producto_filtrado ya que el slider puede cambiar el estado
                     afinidad_producto_filtrado_ext = afinidad_df[afinidad_df['producto'] == producto_seleccionado].copy()

                     # Llamar a la función nuevamente para obtener la lista extendida
                     df_ext, fundamentos_ext = recomendar_mercados(afinidad_producto_filtrado_ext, mercados_df, extra_global=extra_count)

                     # Encontrar los nuevos mercados globales en la lista extendida que NO estaban en la recomendación base
                     base_recommended_countries_lower = {str(p).lower() for p in df_recomendado['País'].unique()}
                     nuevos_globales = df_ext[
                         (df_ext['Región'] == "Resto del Mundo") &
                         (~df_ext['País'].astype(str).str.lower().isin(base_recommended_countries_lower))
                     ]

                     if not nuevos_globales.empty:
                          st.subheader("Mercados Adicionales del Resto del Mundo")
                          # Mostrar solo País y Puntaje para la tabla adicional
                          st.dataframe(nuevos_globales[['País', 'Puntaje Calculado']].rename(columns={'Puntaje Calculado': 'Puntaje'}), hide_index=True)
                          # Puedes añadir fundamentos expandibles para estos también si lo deseas

                     else:
                          st.info("No se encontraron mercados adicionales en el Resto del Mundo con el criterio seleccionado.")


        except Exception as e:
            st.error(f"Ocurrió un error durante el análisis y recomendación: {str(e)}")
            logger.error(f"Error during recommendation process: {traceback.format_exc()}")
            if show_debug and debug_expander:
                with debug_expander:
                    st.text(f"Detailed error: {traceback.format_exc()}")


    # --- Debug Information Display (at the end) ---
    log_capture.stop() # Ensure logging is stopped before displaying
    if show_debug and debug_expander:
        with debug_expander:
            st.text("--- Captured Logs ---")
            st.text(log_capture.get_logs())


    # Display footer or additional info
    st.markdown("---")
    st.markdown("Este bot utiliza datos de mercados consolidados y afinidad calculada para sugerir mercados. Asegúrese de que los archivos `afinidad_producto_pais.csv` y `mercados.csv` estén correctamente nombrados y ubicados.")
    st.markdown("Desarrollado por [Tu Nombre/Organización]")


# --- Run the application ---
if __name__ == "__main__":
    main()
