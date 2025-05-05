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
    "product_demand": {
        "filename_variations": ["data/product_demand.csv", "product_demand.csv", "product_demand.csv.csv", "product_demand"],
        "default_columns": ['country', 'ncm', 'import_value_usd']
    },
    "tariffs_exemptions": {
        "filename_variations": ["data/tariffs_exemptions.csv", "tariffs_exemptions.csv", "tariffs_exemptions.csv.csv", "tariffs_exemptions"],
        "default_columns": ['country', 'ncm', 'general_tariff', 'preferential_tariff']
    },
    "ease_of_doing_business": {
        "filename_variations": ["data/ease_of_doing_business.csv", "ease_of_doing_business.csv", "ease_of_doing_business.csv.csv", "ease_of_doing_business"]
        , "default_columns": ['country', 'eodb_score']
    },
    "economic_complexity_index": {
        "filename_variations": ["data/economic_complexity_index.csv", "economic_complexity_index.csv", "economic_complexity_index.csv.csv", "economic_complexity_index"]
        , "default_columns": ['country', 'eci_value']
    },
    # === Nuevo archivo para acuerdos comerciales ===
    "commercial_agreements": {
        "filename_variations": ["data/acuerdos_comerciales.csv", "acuerdos_comerciales.csv"],
        "default_columns": ['country', 'agreement_name', 'beneficiary_country', 'product_coverage', 'preferential_tariff_reduction'] # Columnas de ejemplo, ajusta según tu archivo real
    }
    # ===============================================
}

# Standard column mappings to handle variations in user data files
STANDARD_COLUMN_MAPPINGS = {
    'country': ['country', 'pais', 'país', 'nation', 'nacion', 'nation_name', 'country_name'],
    'ncm': ['ncm', 'codigo_ncm', 'código_ncm', 'code', 'product_code', 'hs_code', 'codigo_hs'],
    'import_value_usd': ['import_value_usd', 'valor_importacion', 'import_value', 'value', 'valor', 'trade_value_usd'],
    'general_tariff': ['general_tariff', 'arancel_general', 'tariff', 'arancel'],
    'preferential_tariff': ['preferential_tariff', 'arancel_preferencial', 'preferential'],
    'eodb_score': ['eodb_score', 'eodb', 'doing_business', 'ease_of_business'],
    'eci_value': ['eci_value', 'eci', 'complexity_index', 'indice_complejidad'],
    # === Mapeos de columnas para acuerdos comerciales ===
    'agreement_name': ['agreement_name', 'nombre_acuerdo', 'acuerdo'],
    'beneficiary_country': ['beneficiary_country', 'pais_beneficiario', 'beneficiario'],
    'product_coverage': ['product_coverage', 'cobertura_producto', 'productos_cubiertos'],
    'preferential_tariff_reduction': ['preferential_tariff_reduction', 'reduccion_arancelaria', 'reduccion_preferencial']
    # Agrega otros mapeos si tu archivo de acuerdos tiene columnas diferentes
    # =====================================================
}

# Common countries list for fallback detection (extended list)
COMMON_COUNTRIES = [
    "brasil", "argentina", "china", "estados unidos", "eeuu", "usa", 
    "méxico", "mexico", "canada", "canadá", "japón", "japon", "alemania", 
    "francia", "italia", "españa", "espana", "chile", "colombia", 
    "perú", "peru", "uruguay", "paraguay", "reino unido", "australia", 
    "india", "rusia", "sudáfrica", "sudafrica", "portugal", "holanda",
    "países bajos", "paises bajos", "bélgica", "belgica", "suiza", "corea del sur",
    "singapur", "malasia", "tailandia", "vietnam", "indonesia", "filipinas",
    "bolivia", "ecuador", "panamá", "panama", "costa rica", "república dominicana",
    "guatemala", "el salvador", "honduras", "nicaragua", "cuba", "haití", "haiti",
    "puerto rico", "belice", "jamaica", "trinidad y tobago", "barbados", "guyana", "surinam"
]

# Score weights for recommendation calculation (can be adjusted)
SCORE_WEIGHTS = {
    'demand': 0.4,     # 40% weight for demand (import_value_usd)
    'tariff': 0.3,     # 30% weight for tariffs (preferential_tariff mostly)
    'eodb': 0.2,       # 20% weight for ease of doing business
    'eci': 0.1         # 10% weight for economic complexity index
    # Si agregas nuevas métricas (ej: estabilidad política), deberás añadirlas aquí y ajustar los pesos
}

# --- Page Configuration ---
def setup_page():
    """Configure the Streamlit page settings."""
    try:
        st.set_page_config(
            page_title="Export Market Recommendation System",
            page_icon="🌍",
            layout="wide"
        )
        return True
    except Exception as e:
        st.error(f"Error in initial setup: {str(e)}")
        logger.error(f"Error in initial setup: {str(e)}")
        return False

# --- Setup Debugging Sidebar ---
def setup_debug_sidebar():
    """Configure the debugging sidebar."""
    with st.sidebar:
        st.subheader("Debugging Options")
        show_debug = st.checkbox("Show debug information", value=False)

        debug_expander = None
        if show_debug:
            st.info("Debug information will be shown below")
            debug_expander = st.expander("Debug Logs")

    return show_debug, debug_expander

# --- Data Loading Functions ---
@st.cache_data
def load_data(filename: str) -> Optional[pd.DataFrame]:
    """
    Attempt to load a CSV file with multiple encodings.

    Args:
        filename: Path to the file to load

    Returns:
        DataFrame if successful, None otherwise
    """
    try:
        # List of encodings to try - common ones first
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']

        # Try loading with different encodings
        for encoding in encodings:
            try:
                # Use low_memory=False to potentially avoid mixed type warnings
                df = pd.read_csv(filename, encoding=encoding, low_memory=False)
                logger.info(f"Successfully loaded {filename} with encoding {encoding}")

                # Column cleaning happens after successful load in try_load_with_variations

                return df
            except UnicodeDecodeError:
                # This is the specific error we're trying to catch and retry on
                logger.warning(f"Failed to load {filename} with encoding {encoding} (UnicodeDecodeError). Trying next encoding.")
                continue # Try the next encoding
            except Exception as e:
                 # Catch other potential read_csv errors (e.g., parser errors)
                 logger.warning(f"Failed to load {filename} with encoding {encoding} ({type(e).__name__}: {str(e)}). Trying next encoding.")
                 continue


        # If we reach here, no encoding worked
        logger.error(f"Failed to load {filename}: No suitable encoding found after trying {encodings}")
        return None
    except Exception as e:
        # Catch any other unexpected errors during the process
        logger.error(f"General error during load_data for {filename}: {type(e).__name__}: {str(e)}")
        return None

def try_load_with_variations(base_name: str, show_debug: bool, debug_expander: Optional[st.expander]) -> pd.DataFrame:
    """
    Attempt to load a file with different name variations and standardize columns.

    Args:
        base_name: Base name of the file to load (key in DATA_FILES)
        show_debug: Whether to show debug information
        debug_expander: Expander to show debug information in

    Returns:
        DataFrame with the data or empty DataFrame with expected columns if loading fails
    """
    file_info = DATA_FILES.get(base_name, {})
    variations = file_info.get("filename_variations", [f"{base_name}.csv"])
    # Use default_columns here to ensure even empty DFs have the right cols for standardization
    default_columns = file_info.get("default_columns", [])

    loaded_df = None
    for variant in variations:
        if show_debug and debug_expander:
             with debug_expander:
                 st.text(f"Attempting to load: {variant}")

        file_path = Path(variant)
        if file_path.exists():
             # Pass the specific filename variant to load_data
             df = load_data(str(file_path)) # Use str(file_path) to be compatible with older pandas
             if df is not None:
                 loaded_df = df
                 if show_debug and debug_expander:
                      with debug_expander:
                          st.text(f"✅ File loaded successfully: {variant}")
                 break # Stop after the first successful load
        else:
             if show_debug and debug_expander:
                  with debug_expander:
                      st.text(f"File not found: {variant}")


    if loaded_df is None:
        logger.warning(f"Could not load any variation for base name '{base_name}'. Tried: {variations}")
        # Create empty DataFrame with default columns and standardize them
        df = pd.DataFrame(columns=default_columns)
        # Ensure columns are standardized even on empty df to maintain structure
        df = standardize_columns(df, STANDARD_COLUMN_MAPPINGS)
        return df

    # Clean column names after successful load
    loaded_df.columns = [col.strip().lower() for col in loaded_df.columns]

    # Standardize columns after successful load and cleaning
    loaded_df = standardize_columns(loaded_df, STANDARD_COLUMN_MAPPINGS)
    return loaded_df


def standardize_columns(df: pd.DataFrame, standard_mappings: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Standardize column names according to a predefined mapping.
    Handles case-insensitivity and stripping whitespace.

    Args:
        df: DataFrame to standardize
        standard_mappings: Mapping of standard column names to possible variations

    Returns:
        DataFrame with standardized column names. If a standard column
        is not found in the variations, it remains unchanged if present,
        or is effectively ignored if not present.
    """
    if df.empty:
        # For an empty DataFrame, ensure the column names are the standard ones
        # if default_columns was used during creation.
        # This check is already partly handled by try_load_with_variations,
        # but ensures consistency.
        current_cols_lower = [col.lower() for col in df.columns]
        standardized_empty_cols = []
        for standard_col, possible_names in standard_mappings.items():
            if standard_col.lower() in current_cols_lower:
                 standardized_empty_cols.append(standard_col)
            else:
                 # If the standard column wasn't in the default columns either,
                 # we can't add it meaningfully to an empty DF based on input.
                 # We only standardize names that were *intended* to be there.
                 pass # Keep only columns that were in the original (empty) df

        # If the original empty df had columns not in standard_mappings, keep them too?
        # The current logic in try_load_with_variations creates an empty df
        # with default_columns, then standardizes. So all columns *should*
        # be standard columns if they match. Let's stick to mapping found variations.
        # A simpler approach for empty DF is just to ensure the names are lowercase
        # if they were already cleaned. Standardizing maps *existing* columns.
        return df # Return cleaned (lowercased) empty df


    # Create a mapping from current lowercased columns to the desired standard name
    col_map = {}
    current_cols_lower = [col.lower() for col in df.columns]

    for standard_col, possible_names in standard_mappings.items():
        for possible_name in possible_names:
            possible_name_lower = possible_name.lower()
            if possible_name_lower in current_cols_lower and possible_name_lower not in col_map:
                 # Map the *first* matching input column name (case-insensitive)
                 # to the standard column name.
                 # Find the original column name (preserving original capitalization if needed later, though we lowercased headers already)
                 original_col_name = df.columns[current_cols_lower.index(possible_name_lower)]
                 col_map[original_col_name] = standard_col
                 # Optimization: if a standard_col is mapped, no need to check its other possible names for this df
                 break # Move to the next standard_col

    # Rename columns using the created map
    # Columns not in col_map will keep their original (lowercased) names
    df = df.rename(columns=col_map)

    # Ensure all standard columns expected for *this type* of data are present,
    # adding them with NaN if they weren't in the original file. This helps downstream.
    # Find which data file this dataframe came from based on filename variations
    source_file_info = next((info for name, info in DATA_FILES.items()
                             for var in info.get('filename_variations', [])
                             if df.name and str(Path(var).name) in str(Path(df.name).name)), None)

    if source_file_info and source_file_info.get('default_columns'):
        expected_standard_cols = source_file_info['default_columns']
        for col in expected_standard_cols:
            if col not in df.columns:
                 df[col] = np.nan # Add missing expected columns

    return df


# --- Entity Recognition and Detection Functions ---
@st.cache_resource
def load_entity_extractor():
    """
    Load a Named Entity Recognition (NER) model.

    Returns:
        NER pipeline if successful and transformers is installed, None otherwise
    """
    try:
        logger.info("Attempting to load NER model")

        # Check if transformers is installed
        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
            logger.info("✅ transformers library found")
        except ImportError:
            logger.warning("transformers library not found. NER detection will be disabled.")
            # Use st.toast or st.info for less intrusive messages than st.warning here
            st.info("Para mejorar la detección de países, instale la librería `transformers` (`pip install transformers`). La detección se limitará a una lista común y países cargados.")
            return None

        try:
            # Try using a lightweight model
            model_name = "dslim/bert-base-NER"

            # Load model and tokenizer explicitly
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForTokenClassification.from_pretrained(model_name)

            # Create NER pipeline
            ner_pipeline = pipeline(
                "ner",
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="simple" # Use simple strategy to merge consecutive tokens of the same entity
            )

            logger.info("✅ NER model loaded successfully")
            return ner_pipeline
        except Exception as e:
            # Return None to use alternative method if model loading fails
            logger.warning(f"Failed to load NER model: {str(e)}")
            st.warning(f"No se pudo cargar el modelo de NER. La detección de países se limitará a una lista común y países cargados. Error: {type(e).__name__}: {e}")
            return None

    except Exception as e:
        # Catch any other unexpected errors during the process
        logger.error(f"General error during load_entity_extractor: {type(e).__name__}: {str(e)}")
        st.error(f"Error inesperado al cargar el modelo de NER: {e}")
        return None

def detect_ncm(text: str) -> Optional[str]:
    """
    Look for an NCM code in the text (4, 6, or 8 digits).

    Args:
        text: Text to search for NCM codes

    Returns:
        First valid NCM code found (as a string) or None
    """
    # Look for sequences of exactly 4, 6, or 8 digits at word boundaries
    ncm_patterns = re.findall(r'\b\d{4}\b|\b\d{6}\b|\b\d{8}\b', text)

    # In a real application, you might want to validate these against a list of known NCM prefixes.
    # For now, we'll just return the first one found.
    if ncm_patterns:
        logger.info(f"Detected potential NCMs: {ncm_patterns}")
        # Return the first potential NCM found
        return ncm_patterns[0]
    else:
        return None


def detect_countries(text: str, entity_extractor=None, all_countries: Set[str] = None) -> List[str]:
    """
    Detect country names in text using NER if available,
    or a predefined list and loaded data countries as fallback.

    Args:
        text: Text to search for countries
        entity_extractor: NER model pipeline to use (or None)
        all_countries: Set of known country names (lowercase strings) from loaded data

    Returns:
        List of unique countries found (Title cased)
    """
    text_lower = text.lower()
    found_countries_lower = set() # Use a set of lowercase names to avoid duplicates

    # Try with NER first if available and model loaded successfully
    if entity_extractor:
        try:
            entities = entity_extractor(text)
            ner_countries = [entity['word'].strip().lower() for entity in entities if entity['entity_group'] == 'LOC']
            found_countries_lower.update(ner_countries)
            if ner_countries:
                 logger.info(f"NER detected potential countries (lower): {ner_countries}")
        except Exception as e:
            logger.warning(f"NER detection failed: {type(e).__name__}: {str(e)}")
            # Continue to fallback if NER fails

    # Fallback method with country list
    # Check common countries first (lowercase the common list for comparison)
    common_countries_lower = {c.lower() for c in COMMON_COUNTRIES}
    for country_lower in common_countries_lower:
        # Use regex word boundary to avoid matching "us" in "house"
        if re.search(r'\b' + re.escape(country_lower) + r'\b', text_lower):
            found_countries_lower.add(country_lower)


    # Check countries from loaded data (all_countries is already lowercase)
    if all_countries:
        for country_lower in all_countries:
            # Ensure the country name is a string before lowercasing
            country_lower_str = str(country_lower).lower()
            if re.search(r'\b' + re.escape(country_lower_str) + r'\b', text_lower):
                 found_countries_lower.add(country_lower_str)

    # Convert the set of lowercase country names back to Title Case list
    # We might need a mapping if the original data uses specific capitalization,
    # but Title case is a reasonable default presentation.
    # For now, just converting the found lowercase names to title case.
    # A more advanced approach would be to map back to original casing from loaded data.
    # Using a simple mapping for common variations for better presentation:
    title_cased_mapping = {c.lower(): c for c in COMMON_COUNTRIES} # Start with common ones
    if all_countries:
        # Add countries from loaded data, using their original casing if available
        title_cased_mapping.update({str(c).lower(): str(c) for c in all_countries if pd.notna(c)})


    found_countries_title = sorted(list({title_cased_mapping.get(c, c.title()) for c in found_countries_lower}))

    logger.info(f"Detected countries (Title Case): {found_countries_title}")

    return found_countries_title


# --- Recommendation and Scoring Functions ---
def calculate_score(row: pd.Series, product_demand_df: pd.DataFrame, eci_df: pd.DataFrame) -> float:
    """
    Calculate a recommendation score based on different metrics.

    Args:
        row: Row with country data (should contain at least 'country' column)
        product_demand_df: DataFrame with product demand data (for normalization context)
        eci_df: DataFrame with economic complexity data (for normalization context)

    Returns:
        Recommendation score between 0 and 1
    """
    try:
        # Initialize score components
        demand_score = 0.0
        tariff_score = 0.5  # Default neutral value (50% tariff)
        eodb_score = 0.5    # Default neutral value (50/100 EODB)
        eci_score = 0.5     # Default neutral value (mid-range ECI)

        # Calculate demand score (imports)
        # Ensure column exists and value is not NaN or None
        if 'import_value_usd' in row and pd.notna(row['import_value_usd']):
            import_val = float(row['import_value_usd'])
            # Normalize by the maximum value in the DataFrame, avoiding division by zero
            max_import = product_demand_df['import_value_usd'].max() if not product_demand_df.empty and 'import_value_usd' in product_demand_df and product_demand_df['import_value_usd'].max() > 0 else 1.0
            demand_score = import_val / max_import
            # Clamp score between 0 and 1
            demand_score = max(0.0, min(1.0, demand_score))


        # Calculate tariff score (lower tariff = better score)
        # Prefer preferential tariff over general tariff
        tariff_val = None
        if 'preferential_tariff' in row and pd.notna(row['preferential_tariff']):
             try:
                tariff_val = float(row['preferential_tariff'])
             except (ValueError, TypeError):
                 logger.warning(f"Invalid preferential_tariff value for {row.get('country', 'N/A')}: {row['preferential_tariff']}")
                 pass # tariff_val remains None

        if tariff_val is None and 'general_tariff' in row and pd.notna(row['general_tariff']):
             try:
                tariff_val = float(row['general_tariff'])
             except (ValueError, TypeError):
                 logger.warning(f"Invalid general_tariff value for {row.get('country', 'N/A')}: {row['general_tariff']}")
                 pass # tariff_val remains None


        if tariff_val is not None:
             # Assume tariff is a percentage. Cap tariff at 100% for normalization sanity.
             normalized_tariff = min(tariff_val, 100.0) / 100.0
             # Score is inverse of normalized tariff (0% tariff -> score 1, 100% tariff -> score 0)
             tariff_score = 1.0 - normalized_tariff
             # Clamp score between 0 and 1
             tariff_score = max(0.0, min(1.0, tariff_score))


        # Calculate ease of doing business score (higher score = better)
        if 'eodb_score' in row and pd.notna(row['eodb_score']):
            try:
                # Assuming EODB is on a 0-100 scale
                eodb_val = float(row['eodb_score'])
                eodb_score = eodb_val / 100.0 # Normalize to 0-1
                # Clamp score between 0 and 1
                eodb_score = max(0.0, min(1.0, eodb_score))
            except (ValueError, TypeError):
                 logger.warning(f"Invalid eodb_score value for {row.get('country', 'N/A')}: {row['eodb_score']}")
                 pass # eodb_score remains default 0.5


        # Calculate economic complexity score (higher score = better)
        if 'eci_value' in row and pd.notna(row['eci_value']):
            try:
                eci_val = float(row['eci_value'])
                # Normalize ECI between 0 and 1 based on min/max in the dataset
                # Provide fallback defaults if ECI data is empty or has no range
                eci_min = eci_df['eci_value'].min() if not eci_df.empty and 'eci_value' in eci_df and pd.notna(eci_df['eci_value'].min()) else -2.0 # Use a reasonable default min
                eci_max = eci_df['eci_value'].max() if not eci_df.empty and 'eci_value' in eci_df and pd.notna(eci_df['eci_value'].max()) else 2.0 # Use a reasonable default max

                if eci_max - eci_min != 0:
                    eci_score = (eci_val - eci_min) / (eci_max - eci_min)
                    # Clamp score between 0 and 1
                    eci_score = max(0.0, min(1.0, eci_score))
                else:
                    eci_score = 0.5 # Neutral if range is zero
            except (ValueError, TypeError):
                 logger.warning(f"Invalid eci_value value for {row.get('country', 'N/A')}: {row['eci_value']}")
                 pass # eci_score remains default 0.5


        # Calculate final weighted score
        final_score = (
            demand_score * SCORE_WEIGHTS.get('demand', 0.0) +
            tariff_score * SCORE_WEIGHTS.get('tariff', 0.0) +
            eodb_score * SCORE_WEIGHTS.get('eodb', 0.0) +
            eci_score * SCORE_WEIGHTS.get('eci', 0.0)
            # Add new metrics here if added to SCORE_WEIGHTS
        )

        # Ensure final score is within 0-1 range
        final_score = max(0.0, min(1.0, final_score))

        return final_score
    except Exception as e:
        logger.error(f"Error calculating score for country {row.get('country', 'N/A')}: {type(e).__name__}: {str(e)}")
        # Log the specific row data that caused the error (sensitive data might need masking)
        # logger.debug(f"Row data causing error: {row.to_dict()}") # Use debug level if needed
        return 0.0  # Return 0 in case of error


def format_display_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Format DataFrame for display with proper formatting for each column type.

    Args:
        df: DataFrame to format

    Returns:
        Formatted DataFrame for display
    """
    display_df = df.copy()

    # Format numeric columns if they exist
    numeric_cols_to_format = {
        'import_value_usd': lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A", # Format as currency, no decimals for large values
        'general_tariff': lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A",
        'preferential_tariff': lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A",
        'eodb_score': lambda x: f"{x:.1f}/100" if pd.notna(x) else "N/A",
        'eci_value': lambda x: f"{x:.2f}" if pd.notna(x) else "N/A",
        'score': lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A" # Score is 0-1, display as percentage
    }

    for col, formatter in numeric_cols_to_format.items():
        if col in display_df.columns:
            # Ensure the column is numeric before applying formatters
            # Avoids errors if standardization failed or data is messy
            try:
                 display_df[col] = pd.to_numeric(display_df[col], errors='coerce')
                 display_df[col] = display_df[col].apply(formatter)
            except Exception as e:
                 logger.warning(f"Could not format column '{col}' for display: {e}")
                 display_df[col] = display_df[col].astype(str) # Fallback to string representation


    # Rename columns for better visualization in Spanish
    display_df = display_df.rename(columns={
        'country': 'País',
        'ncm': 'Código NCM',
        'import_value_usd': 'Valor Importación (USD)',
        'general_tariff': 'Arancel General',
        'preferential_tariff': 'Arancel Preferencial',
        'eodb_score': 'Facilidad Negocios (0-100)',
        'eci_value': 'Índice Complejidad',
        'score': 'Puntuación Total (%)'
        # Add renames for any new columns from acuerdos_comerciales if you display them
        # 'agreement_name': 'Acuerdo Comercial',
        # 'beneficiary_country': 'País Beneficiario', # Might not need if already filtered by country
        # 'product_coverage': 'Cobertura de Productos',
        # 'preferential_tariff_reduction': 'Reducción Arancelaria (%)'
    })

    return display_df

def process_ncm_recommendation(ncm_found: str, product_demand_df: pd.DataFrame,
                               tariffs_exemptions_df: pd.DataFrame, eodb_df: pd.DataFrame,
                               eci_df: pd.DataFrame, acuerdos_df: pd.DataFrame, # Pass acuerdos_df here
                               show_debug: bool, debug_expander: Optional[st.expander]) -> None:
    """
    Process NCM code and display recommendations based on available data.

    Args:
        ncm_found: NCM code to analyze
        product_demand_df: DataFrame with product demand data
        tariffs_exemptions_df: DataFrame with tariff data
        eodb_df: DataFrame with ease of doing business data
        eci_df: DataFrame with economic complexity data
        acuerdos_df: DataFrame with commercial agreements data
        show_debug: Whether to show debug information
        debug_expander: Expander to show debug information in
    """
    st.subheader(f"Análisis para el código NCM: {ncm_found}")

    try:
        # Filter data by NCM (ensure 'ncm' column exists and is string type for robust matching)
        demand_filtered = pd.DataFrame()
        if not product_demand_df.empty and 'ncm' in product_demand_df.columns:
             product_demand_df['ncm_str'] = product_demand_df['ncm'].astype(str).str.strip()
             demand_filtered = product_demand_df[product_demand_df['ncm_str'] == str(ncm_found).strip()].copy()
             demand_filtered = demand_filtered.drop(columns=['ncm_str'])


        tariffs_filtered = pd.DataFrame()
        if not tariffs_exemptions_df.empty and 'ncm' in tariffs_exemptions_df.columns:
             tariffs_exemptions_df['ncm_str'] = tariffs_exemptions_df['ncm'].astype(str).str.strip()
             tariffs_filtered = tariffs_exemptions_df[tariffs_exemptions_df['ncm_str'] == str(ncm_found).strip()].copy()
             tariffs_filtered = tariffs_filtered.drop(columns=['ncm_str'])


        # Check if we have enough NCM-specific data
        if demand_filtered.empty and tariffs_filtered.empty:
            st.warning(f"No se encontraron datos de demanda o aranceles para el código NCM {ncm_found}. No se pueden generar recomendaciones específicas por NCM.")
            return

        # Build results DataFrame starting with NCM-specific data (demand or tariffs)
        if not demand_filtered.empty or not tariffs_filtered.empty:
             # Use an outer merge to include countries present in either NCM-filtered dataframe
             results_df = pd.merge(
                 demand_filtered[['country', 'import_value_usd']] if not demand_filtered.empty else pd.DataFrame(columns=['country', 'import_value_usd']),
                 tariffs_filtered[['country', 'general_tariff', 'preferential_tariff']] if not tariffs_filtered.empty else pd.DataFrame(columns=['country', 'general_tariff', 'preferential_tariff']),
                 on='country',
                 how='outer'
             )
        else:
             # Should not happen based on the check above, but as a safeguard
             st.warning("No data available for this NCM after filtering.")
             return

        # Ensure 'country' column is handled correctly for subsequent merges
        if 'country' not in results_df.columns:
             st.error("Error interno: La columna 'country' no se encontró después de filtrar los datos por NCM.")
             if show_debug and debug_expander:
                  with debug_expander:
                       st.text("Results DF columns:")
                       st.text(results_df.columns.tolist())
             return # Cannot proceed without country column


        # Add general country data (Ease of Business, ECI) if available
        # Use lowercase country names for robust merging
        if not eodb_df.empty and 'country' in eodb_df.columns:
             eodb_for_merge = eodb_df[['country', 'eodb_score']].copy()
             eodb_for_merge['country_lower'] = eodb_for_merge['country'].astype(str).str.lower()
             results_df['country_lower'] = results_df['country'].astype(str).str.lower()
             results_df = pd.merge(results_df, eodb_for_merge[['country_lower', 'eodb_score']], on='country_lower', how='left')
             results_df = results_df.drop(columns=['country_lower']) # Drop temp column
             # No need to drop from eodb_df as it's cached


        if not eci_df.empty and 'country' in eci_df.columns:
             eci_for_merge = eci_df[['country', 'eci_value']].copy()
             eci_for_merge['country_lower'] = eci_for_merge['country'].astype(str).str.lower()
             if 'country_lower' not in results_df.columns: # Add if not already added by eodb merge
                 results_df['country_lower'] = results_df['country'].astype(str).str.lower()
             results_df = pd.merge(results_df, eci_for_merge[['country_lower', 'eci_value']], on='country_lower', how='left')
             results_df = results_df.drop(columns=['country_lower']) # Drop temp column


        # Add the NCM column to the results for clarity in the final table
        # Ensure it's added only once and correctly
        if 'ncm' not in results_df.columns:
             results_df['ncm'] = ncm_found
        # If it was already merged (e.g., from tariffs_filtered), ensure consistency if possible
        # (This part can get complex if NCM values in tariffs_filtered might differ, but for a single NCM query it should be okay)


        # --- Optional: Integrate Commercial Agreements Data ---
        # This is just an example of how you *could* integrate it.
        # You would need to define how agreements affect the score or display.
        # For now, let's just show if a country has relevant agreements for this NCM.
        if not acuerdos_df.empty and 'country' in acuerdos_df.columns and 'beneficiary_country' in acuerdos_df.columns and 'product_coverage' in acuerdos_df.columns:
            # Assuming acuerdos_df has columns 'country' (exporter), 'beneficiary_country' (importer), 'product_coverage' (NCMs or categories)
            # Filter agreements where the user's country is the exporter and the result country is the beneficiary
            # And where the agreement covers the queried NCM (this matching logic needs careful design)
            # Simplified example: just check if the country is a beneficiary in ANY agreement in the loaded data
            beneficiary_countries_in_agreements = acuerdos_df['beneficiary_country'].astype(str).str.lower().unique()

            results_df['country_lower'] = results_df['country'].astype(str).str.lower()
            results_df['Has Agreement Info'] = results_df['country_lower'].apply(
                 lambda x: x in beneficiary_countries_in_agreements
            )
            results_df = results_df.drop(columns=['country_lower'])

            # You could potentially adjust the tariff score here based on specific agreement reductions
            # or add a bonus to the final score if an agreement covers the NCM.
            # This requires more complex logic depending on your data structure and rules.
        # ------------------------------------------------------


        # Calculate scores for each country that has data after merges
        if not results_df.empty:
            with st.spinner("Calculando puntuaciones de recomendación..."):
                 # Drop rows where the country is NaN (can happen with outer merges if source data is messy)
                 results_df.dropna(subset=['country'], inplace=True)

                 results_df['score'] = results_df.apply(
                     lambda row: calculate_score(row, product_demand_df, eci_df), # Pass global DFs for normalization context
                     axis=1
                 )

            # Sort by score and select the best
            top_markets = results_df.sort_values(by='score', ascending=False).head(10).reset_index(drop=True) # Show top 10

            # Display recommended markets
            if not top_markets.empty:
                st.subheader("🏆 Mercados recomendados:")

                # Format and display results table
                display_df = format_display_dataframe(top_markets)
                st.dataframe(display_df, hide_index=True) # Hide index for cleaner display

                # Display score chart
                st.subheader("📊 Comparación de mercados (Puntuación Total)")
                if len(top_markets) > 0:
                    chart_data = top_markets[['País', 'Puntuación Total (%)']].copy() # Use display names for chart
                    # Convert score percentage back to numeric for chart sorting if needed, or just use raw score column before formatting
                    # Let's use the raw score column before formatting for consistency with sorting
                    chart_data['score'] = top_markets['score']
                    chart_data = chart_data.sort_values(by='score', ascending=True)
                    chart_data = chart_data.rename(columns={'País': 'index'}).set_index('index')
                    st.bar_chart(chart_data['Puntuación Total (%)'], height=400)

            else:
                 st.info("No se encontraron mercados relevantes con datos suficientes para este NCM después del cálculo.")

        else:
            st.warning("Datos insuficientes para generar recomendaciones después de combinar la información.")
    except Exception as e:
        st.error(f"Error al procesar los datos del NCM: {str(e)}")
        logger.error(f"Error processing NCM recommendation: {traceback.format_exc()}")
        if show_debug and debug_expander:
            with debug_expander:
                st.text(f"Detailed error: {traceback.format_exc()}")


def process_country_information(countries_found: List[str], product_demand_df: pd.DataFrame,
                               tariffs_exemptions_df: pd.DataFrame, eodb_df: pd.DataFrame,
                               eci_df: pd.DataFrame, acuerdos_df: pd.DataFrame, # Pass acuerdos_df here
                               show_debug: bool, debug_expander: Optional[st.expander]) -> None:
    """
    Process country information and display details for detected countries.

    Args:
        countries_found: List of countries (Title cased) to analyze
        product_demand_df: DataFrame with product demand data
        tariffs_exemptions_df: DataFrame with tariff data
        eodb_df: DataFrame with ease of doing business data
        eci_df: DataFrame with economic complexity data
        acuerdos_df: DataFrame with commercial agreements data
        show_debug: Whether to show debug information
        debug_expander: Expander to show debug information in
    """
    if not countries_found:
        return # Do nothing if no countries were found

    st.markdown("---")
    st.subheader("Información por país(es) detectado(s)")

    # Create tabs for each country
    # Ensure country names are strings for tab creation
    country_tabs = st.tabs([f"{str(country)}" for country in countries_found])

    for i, country in enumerate(countries_found):
        with country_tabs[i]:
            st.markdown(f"### Detalles para {country}")
            try:
                # Find specific country data (case-insensitive comparison using lowercased string column)
                country_lower_str = str(country).lower()

                country_eodb = eodb_df[eodb_df['country'].astype(str).str.lower() == country_lower_str] if not eodb_df.empty and 'country' in eodb_df.columns else pd.DataFrame()
                country_eci = eci_df[eci_df['country'].astype(str).str.lower() == country_lower_str] if not eci_df.empty and 'country' in eci_df.columns else pd.DataFrame()
                country_tariffs = tariffs_exemptions_df[tariffs_exemptions_df['country'].astype(str).str.lower() == country_lower_str] if not tariffs_exemptions_df.empty and 'country' in tariffs_exemptions_df.columns else pd.DataFrame()
                country_demand = product_demand_df[product_demand_df['country'].astype(str).str.lower() == country_lower_str] if not product_demand_df.empty and 'country' in product_demand_df.columns else pd.DataFrame()
                # === Find agreements for this country ===
                country_agreements = acuerdos_df[acuerdos_df['beneficiary_country'].astype(str).str.lower() == country_lower_str] if not acuerdos_df.empty and 'beneficiary_country' in acuerdos_df.columns else pd.DataFrame()
                # ======================================


                # Display main metrics (EODB, ECI)
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📈 Facilidad para hacer negocios")
                    # Check if dataframe is not empty, column exists, and value is not NaN
                    if not country_eodb.empty and 'eodb_score' in country_eodb.columns and pd.notna(country_eodb['eodb_score'].iloc[0]):
                        # Use .iloc[0] to get the value from the first row of the filtered DataFrame
                        try:
                            eodb_value = float(country_eodb['eodb_score'].iloc[0])
                            st.metric("Puntuación EODB", f"{eodb_value:.1f}/100")

                            # Add interpretation
                            if eodb_value >= 80:
                                st.success("Excelente facilidad para hacer negocios")
                            elif eodb_value >= 60:
                                st.info("Buena facilidad para hacer negocios")
                            else:
                                st.warning("Ambiente de negocios más desafiante")
                        except (ValueError, TypeError):
                             st.write("Dato de Puntuación EODB inválido")
                             logger.warning(f"Invalid EODB value for {country}: {country_eodb['eodb_score'].iloc[0]}")
                    else:
                        st.write("No hay datos de Facilidad para hacer Negocios disponibles")

                with col2:
                    st.subheader("🧩 Complejidad económica")
                    if not country_eci.empty and 'eci_value' in country_eci.columns and pd.notna(country_eci['eci_value'].iloc[0]):
                        try:
                            eci_value = float(country_eci['eci_value'].iloc[0])
                            st.metric("Índice ECI", f"{eci_value:.2f}")

                            # Add interpretation
                            if eci_value > 1:
                                st.success("Economía altamente compleja y diversificada")
                            elif eci_value > 0:
                                st.info("Economía moderadamente diversificada")
                            else:
                                st.warning("Economía menos diversificada")
                        except (ValueError, TypeError):
                             st.write("Dato de Índice ECI inválido")
                             logger.warning(f"Invalid ECI value for {country}: {country_eci['eci_value'].iloc[0]}")
                    else:
                        st.write("No hay datos de Índice de Complejidad Económica disponibles")

                # --- Display Commercial Agreements ---
                st.subheader("🤝 Acuerdos Comerciales con Uruguay")
                if not country_agreements.empty:
                    # Assuming your acuerdos_comerciales.csv has columns like 'agreement_name', 'product_coverage', 'preferential_tariff_reduction'
                    # Select and display relevant columns
                    display_cols = [col for col in ['agreement_name', 'product_coverage', 'preferential_tariff_reduction'] if col in country_agreements.columns]
                    if display_cols:
                        # Format reduction percentage if it exists
                        if 'preferential_tariff_reduction' in display_cols:
                            country_agreements_display = country_agreements[display_cols].copy()
                            country_agreements_display['preferential_tariff_reduction'] = country_agreements_display['preferential_tariff_reduction'].apply(
                                lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
                            )
                        else:
                            country_agreements_display = country_agreements[display_cols].copy()

                        # Rename columns for display
                        country_agreements_display = country_agreements_display.rename(columns={
                            'agreement_name': 'Nombre del Acuerdo',
                            'product_coverage': 'Cobertura de Productos',
                            'preferential_tariff_reduction': 'Reducción Arancelaria Preferencial (%)'
                        })
                        st.dataframe(country_agreements_display, hide_index=True)
                    else:
                         st.write("El archivo de acuerdos no contiene las columnas esperadas para mostrar detalles.")
                         if show_debug and debug_expander:
                             with debug_expander:
                                 st.text("Acuerdos DF columns:")
                                 st.text(acuerdos_df.columns.tolist())
                else:
                    st.write("No hay datos de acuerdos comerciales disponibles para este país en los archivos cargados.")
                # -------------------------------------


                # Show tariff information (General/Preferential for NCMs in data)
                st.subheader("💰 Aranceles por NCM (ejemplos de datos cargados)")
                if not country_tariffs.empty:
                    # Show only relevant columns and NCMs present in the filtered data
                    display_cols = ['ncm', 'general_tariff', 'preferential_tariff']
                    display_cols = [col for col in display_cols if col in country_tariffs.columns]

                    if display_cols:
                        # Sort by NCM code
                        sorted_tariffs = country_tariffs.sort_values(by='ncm')
                         # Format for display
                        formatted_tariffs = sorted_tariffs[display_cols].copy()
                        if 'general_tariff' in formatted_tariffs.columns:
                             formatted_tariffs['general_tariff'] = formatted_tariffs['general_tariff'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
                        if 'preferential_tariff' in formatted_tariffs.columns:
                             formatted_tariffs['preferential_tariff'] = formatted_tariffs['preferential_tariff'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
                        formatted_tariffs = formatted_tariffs.rename(columns={'ncm': 'Código NCM', 'general_tariff': 'Arancel General', 'preferential_tariff': 'Arancel Preferencial'})

                        st.dataframe(formatted_tariffs, hide_index=True)
                    else:
                        st.write("No hay columnas de aranceles disponibles en los datos cargados.")
                else:
                    st.write("No hay datos de aranceles disponibles para este país en los archivos cargados.")


                # Show product demand information (Top NCMs imported)
                st.subheader("📊 Demanda de productos (NCMs importados con mayor valor en datos cargados)")
                if not country_demand.empty:
                    # Show only relevant columns and NCMs present in the filtered data
                    display_cols = ['ncm', 'import_value_usd']
                    display_cols = [col for col in display_cols if col in country_demand.columns]

                    if display_cols:
                        # Sort by import value descending and show top 10
                        sort_col = 'import_value_usd' if 'import_value_usd' in country_demand.columns else display_cols[0]
                        sorted_demand = country_demand.sort_values(
                            by=sort_col,
                            ascending=False
                        ).head(10)

                        # Format values for display
                        formatted_demand = sorted_demand.copy()
                        if 'import_value_usd' in formatted_demand.columns:
                            formatted_demand['import_value_usd'] = formatted_demand['import_value_usd'].apply(
                                lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A" # Format as currency, no decimals
                            )

                        # Rename columns for display
                        display_demand = formatted_demand.rename(columns={
                            'ncm': 'Código NCM',
                            'import_value_usd': 'Valor Importación (USD)'
                        })

                        st.dataframe(display_demand, hide_index=True)
                    else:
                        st.write("No hay columnas de demanda disponibles en los datos cargados.")
                else:
                    st.write("No hay datos de demanda disponibles para este país en los archivos cargados.")

            except Exception as e:
                st.error(f"Error al procesar los datos del país {country}: {str(e)}")
                logger.error(f"Error processing country {country}: {traceback.format_exc()}")
                if show_debug and debug_expander:
                     with debug_expander:
                          st.text(f"Detailed error: {traceback.format_exc()}")

def main():
    """Main application function."""
    # Setup page
    if not setup_page():
        return

    # Setup debugging sidebar
    show_debug, debug_expander = setup_debug_sidebar()

    # Main content
    st.title("🌍 Bot Inteligente para Recomendación de Mercados de Exportación")
    st.markdown("Ingrese un código NCM o una descripción de su producto y le sugeriremos mercados potenciales.")
    st.markdown("---") # Separator

    # Load NER model
    # Load NER model once and pass it
    ner_model = load_entity_extractor()

    # Load all DataFrames
    # Using st.spinner for data loading feedback
    with st.spinner("Cargando datos..."):
        product_demand_df = try_load_with_variations("product_demand", show_debug, debug_expander)
        tariffs_exemptions_df = try_load_with_variations("tariffs_exemptions", show_debug, debug_expander)
        eodb_df = try_load_with_variations("ease_of_doing_business", show_debug, debug_expander)
        eci_df = try_load_with_variations("economic_complexity_index", show_debug, debug_expander)
        # === Cargar el nuevo archivo de acuerdos comerciales ===
        acuerdos_df = try_load_with_variations("commercial_agreements", show_debug, debug_expander)
        # =====================================================


    # Verify data loading status and provide feedback
    loaded_dfs_status = {
        "Demanda de Productos": not product_demand_df.empty,
        "Aranceles y Exenciones": not tariffs_exemptions_df.empty,
        "Facilidad para hacer Negocios": not eodb_df.empty,
        "Índice de Complejidad Económica": not eci_df.empty,
        "Acuerdos Comerciales": not acuerdos_df.empty # Incluir estado del nuevo archivo
    }

    # Display loading status
    status_text = st.empty() # Placeholder for status message
    if all(loaded_dfs_status.values()):
        status_text.success("✅ Todos los archivos de datos cargados exitosamente.")
    else:
        failed_files = [name for name, loaded in loaded_dfs_status.items() if not loaded]
        if failed_files:
            status_text.warning(f"No se pudieron cargar los siguientes archivos: {', '.join(failed_files)}")
            status_text.info("La aplicación funcionará con capacidades limitadas usando los datos disponibles.")
        else:
             # This case implies some files might be empty but loaded without error
             status_text.info("Archivos cargados. Algunos archivos pueden estar vacíos.")


    # Extract all countries for better detection (case-insensitive set)
    # Include countries from the new agreements file as well
    all_countries = set()
    for df in [product_demand_df, tariffs_exemptions_df, eodb_df, eci_df]:
        if not df.empty and 'country' in df.columns:
            # Convert country column to string and lowercase before adding to set
            all_countries.update(df['country'].dropna().astype(str).str.lower().unique())

    # Include beneficiary countries from the agreements file
    if not acuerdos_df.empty and 'beneficiary_country' in acuerdos_df.columns:
         all_countries.update(acuerdos_df['beneficiary_country'].dropna().astype(str).str.lower().unique())
    # Include exporter countries from the agreements file if they are distinct from beneficiary
    if not acuerdos_df.empty and 'country' in acuerdos_df.columns: # Assuming 'country' column in acuerdos is the exporter
         all_countries.update(acuerdos_df['country'].dropna().astype(str).str.lower().unique())


    # UI for user query
    st.subheader("Consulta")

    # Add predefined examples
    examples = [
        "Exportar carne bovina (020230) a Brasil",
        "Quiero exportar manzanas (080810) a Estados Unidos",
        "Analizar el mercado de China", # Example querying a country
        "Aranceles para 020230 en Argentina", # Example combining NCM and Country
        "Información sobre acuerdos con México" # Example querying for agreements (will show in country info)
    ]

    # Create container for example buttons
    st.markdown("O pruebe con uno de estos ejemplos:")
    # Determine how many columns are needed based on the number of examples
    num_example_cols = min(len(examples), 5) # Limit example columns to max 5 for smaller screens
    example_cols = st.columns(num_example_cols)

    # State variable to hold the query from examples
    if 'query' not in st.session_state:
        st.session_state.query = ""

    # Add buttons to columns
    for i, example_text in enumerate(examples):
        with example_cols[i % num_example_cols]: # Cycle through columns
            if st.button(example_text):
                st.session_state.query = example_text # Update session state when button is clicked

    # Main text input for user query, pre-filled if an example was clicked
    user_query = st.text_input("Ingrese su código NCM, descripción del producto, o nombre del país:", key='query') # Use the session state key

    # Analyze button
    analyze_button = st.button("Analizar")

    # --- Processing Logic ---
    if analyze_button and user_query:
        log_capture.start() # Start capturing logs for debugging
        st.markdown("---")
        # Use st.container to group results if needed, though subheaders work well

        try:
            # 1. Detect NCM and Countries from the query
            # Clean the user query string
            cleaned_query = user_query.strip()
            ncm_found = detect_ncm(cleaned_query)
            # Pass loaded NER model and all countries to detection function
            countries_found = detect_countries(cleaned_query, entity_extractor=ner_model, all_countries=all_countries)

            if show_debug and debug_expander:
                with debug_expander:
                    st.text(f"Detected NCM: {ncm_found}")
                    st.text(f"Detected Countries: {countries_found}")

            # 2. Process based on detected entities
            processed_ncm = False
            processed_countries = False

            # If an NCM is found, process NCM recommendation
            if ncm_found:
                 # Check if product demand or tariffs data is available for NCM processing
                 if not product_demand_df.empty or not tariffs_exemptions_df.empty:
                      process_ncm_recommendation(
                          ncm_found,
                          product_demand_df,
                          tariffs_exemptions_df,
                          eodb_df,
                          eci_df,
                          acuerdos_df, # Pass acuerdos_df
                          show_debug,
                          debug_expander
                      )
                      processed_ncm = True
                 else:
                      st.warning("Datos de demanda o aranceles no disponibles para procesar la recomendación por NCM.")


            # If countries are found, process country-specific information
            # This can run in addition to NCM recommendation if both are detected
            if countries_found:
                 # Check if any country-specific data is available
                 if not eodb_df.empty or not eci_df.empty or not tariffs_exemptions_df.empty or not product_demand_df.empty or not acuerdos_df.empty:
                     process_country_information(
                          countries_found,
                          product_demand_df,
                          tariffs_exemptions_df,
                          eodb_df,
                          eci_df,
                          acuerdos_df, # Pass acuerdos_df
                          show_debug,
                          debug_expander
                      )
                     processed_countries = True
                 else:
                      st.warning("Datos específicos de país no disponibles para mostrar información detallada.")


            if not processed_ncm and not processed_countries:
                st.warning("No se detectó ningún código NCM o nombre de país en su consulta. Por favor, ingrese un código NCM (4, 6 u 8 dígitos) o un nombre de país.")

        except Exception as e:
            st.error(f"Ocurrió un error durante el análisis: {str(e)}")
            logger.error(f"Error during main processing: {traceback.format_exc()}")
            if show_debug and debug_expander:
                with debug_expander:
                    st.text(f"Detailed error: {traceback.format_exc()}")

        finally:
            log_capture.stop() # Stop capturing logs
            if show_debug and debug_expander:
                with debug_expander:
                    st.text("--- Captured Logs ---")
                    st.text(log_capture.get_logs())


    # Display footer or additional info
    st.markdown("---")
    st.markdown("Este bot utiliza datos de demanda de importaciones, aranceles, facilidad para hacer negocios e índice de complejidad económica, y potencialmente información de acuerdos comerciales, para sugerir mercados.")
    st.markdown("Desarrollado por [Tu Nombre/Organización]") # Replace with actual developer info


# --- Run the application ---
if __name__ == "__main__":
    main()
