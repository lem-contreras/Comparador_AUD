"""
loader.py
---------
Carga y cacheo de archivos Excel de monitoreo televisivo.
Optimizado para archivos de gran volumen (100k+ registros).
"""

import pandas as pd
import streamlit as st
from typing import Dict, List
import io

# Columnas obligatorias que debe contener cada archivo
REQUIRED_COLUMNS = {
    "Programa", "Spot Id", "Inicio", "Final", "Duración",
    "Tipo Bloque", "Compañía", "Marca", "SubMarca", "Producto",
    "Campaña", "Posición", "Spot", "Tipo", "Fecha"
}

# Mapeo de tipos de bloque normalizados
TIPO_BLOQUE_MAP = {
    "carrier": "Tanda Publicitaria",
    "break": "Tanda Publicitaria",
    "accion especial": "Accion especial",
    "acción especial": "Accion especial",
    "programa": "Programa",
}


@st.cache_data(show_spinner=False)
def load_excel_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """
    Carga un archivo Excel desde bytes y lo retorna como DataFrame.
    Usa cache de Streamlit para evitar recargas innecesarias.

    Args:
        file_bytes: Contenido del archivo en bytes.
        filename: Nombre del archivo (usado para el cache key).

    Returns:
        DataFrame con los datos del archivo.
    """
    try:
        df = pd.read_excel(
            io.BytesIO(file_bytes),
            engine="openpyxl",
            dtype=str  # Leer todo como string para evitar conversiones erróneas
        )
        # Normalizar nombres de columnas: strip de espacios
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        raise ValueError(f"Error al leer '{filename}': {e}")


def validate_columns(df: pd.DataFrame, filename: str) -> List[str]:
    """
    Valida que el DataFrame contenga las columnas obligatorias.

    Returns:
        Lista de columnas faltantes (vacía si todo está bien).
    """
    existing = set(df.columns)
    missing = REQUIRED_COLUMNS - existing
    return list(missing)


def normalize_tipo_bloque(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza la columna 'Tipo Bloque' para unificar variantes textuales.
    Carrier y Break → 'Tanda Publicitaria'
    """
    if "Tipo Bloque" in df.columns:
        df = df.copy()
        df["Tipo Bloque Norm"] = (
            df["Tipo Bloque"]
            .fillna("")
            .str.strip()
            .str.lower()
            .map(TIPO_BLOQUE_MAP)
            .fillna(df["Tipo Bloque"].str.strip())
        )
    return df


def process_uploaded_files(uploaded_files) -> Dict[str, pd.DataFrame]:
    """
    Procesa todos los archivos subidos por el usuario.

    Args:
        uploaded_files: Lista de archivos cargados por st.file_uploader.

    Returns:
        Diccionario {nombre_canal: DataFrame}
    """
    canales = {}
    errores = []
    advertencias = []

    progress_bar = st.progress(0, text="Iniciando carga de archivos...")

    for i, uploaded_file in enumerate(uploaded_files):
        canal_name = uploaded_file.name.replace(".xlsx", "").replace(".xls", "").strip()
        progress_text = f"Cargando: {canal_name} ({i+1}/{len(uploaded_files)})"
        progress_bar.progress((i) / len(uploaded_files), text=progress_text)

        try:
            file_bytes = uploaded_file.read()
            df = load_excel_file(file_bytes, uploaded_file.name)

            # Validar columnas
            missing = validate_columns(df, canal_name)
            if missing:
                advertencias.append(
                    f"⚠️ **{canal_name}**: columnas faltantes: `{', '.join(missing)}`"
                )

            # Normalizar Tipo Bloque
            df = normalize_tipo_bloque(df)

            # Convertir columnas de tiempo si existen
            for col in ["Inicio", "Final", "Duración"]:
                if col in df.columns:
                    df[col] = df[col].fillna("").astype(str).str.strip()

            canales[canal_name] = df

        except ValueError as e:
            errores.append(str(e))

    progress_bar.progress(1.0, text="✅ Carga completa")

    # Mostrar advertencias y errores
    for warn in advertencias:
        st.warning(warn)
    for err in errores:
        st.error(err)

    return canales
