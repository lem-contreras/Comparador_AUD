"""
parser.py
---------
Extracción y normalización de nombres de programas desde la columna 'Programa'.
Elimina horarios, EMS, duraciones y cualquier metadata adicional.
"""

import re
import pandas as pd
from typing import Dict, List, Tuple, Optional


# Patrones regex para eliminar metadata de los nombres de programa
# Ejemplos a eliminar:
#   "12:30:01 - 15:09:05"
#   "(EMS = 1141933715 - 02:39:04)"
#   "SIMULCAST 12:30:01"  → solo el horario, no "SIMULCAST"

PATTERNS_TO_REMOVE = [
    r'\s*\d{1,2}:\d{2}:\d{2}\s*-\s*\d{1,2}:\d{2}:\d{2}.*',   # HH:MM:SS - HH:MM:SS y todo lo que sigue
    r'\s*\(\s*EMS\s*=.*?\)',                                      # (EMS = ...)
    r'\s+\d{1,2}:\d{2}:\d{2}\s*$',                              # horario suelto al final
    r'\s*-\s*\d{2}:\d{2}:\d{2}\s*$',                            # - HH:MM:SS al final
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in PATTERNS_TO_REMOVE]


def extract_program_name(raw_name: str) -> str:
    """
    Extrae el nombre limpio del programa eliminando horarios, EMS y metadata.

    Ejemplo:
        Input:  "FSI. MEXICO VS. SUDAFRICA SIMULCAST 12:30:01 - 15:09:05 (EMS = 1141933715 - 02:39:04)"
        Output: "FSI. MEXICO VS. SUDAFRICA SIMULCAST"

    Args:
        raw_name: Nombre crudo del programa desde el Excel.

    Returns:
        Nombre limpio del programa.
    """
    if not isinstance(raw_name, str):
        return ""

    cleaned = raw_name.strip()

    # Aplicar cada patrón de limpieza en orden
    for pattern in COMPILED_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    return cleaned.strip()


def get_all_programs(canales: Dict[str, pd.DataFrame]) -> Dict[str, List[str]]:
    """
    Obtiene todos los programas únicos de cada canal con sus nombres limpios.

    Returns:
        Diccionario {canal: [lista de programas limpios únicos]}
    """
    programas_por_canal = {}

    for canal, df in canales.items():
        if "Programa" not in df.columns:
            programas_por_canal[canal] = []
            continue

        nombres_limpios = (
            df["Programa"]
            .dropna()
            .astype(str)
            .apply(extract_program_name)
            .unique()
            .tolist()
        )
        # Filtrar cadenas vacías
        programas_por_canal[canal] = [n for n in nombres_limpios if n]

    return programas_por_canal


def get_unified_program_list(canales: Dict[str, pd.DataFrame]) -> List[str]:
    """
    Genera una lista unificada y ordenada de todos los programas
    disponibles en todos los canales combinados.
    """
    todos = set()
    for canal, df in canales.items():
        if "Programa" not in df.columns:
            continue
        nombres = (
            df["Programa"]
            .dropna()
            .astype(str)
            .apply(extract_program_name)
        )
        todos.update(n for n in nombres if n)

    return sorted(list(todos))


def filter_by_program(
    df: pd.DataFrame,
    program_name: str
) -> pd.DataFrame:
    """
    Filtra el DataFrame para mostrar solo los registros del programa seleccionado.
    Usa el nombre limpio para hacer el match (sin horarios ni EMS).

    Args:
        df: DataFrame del canal.
        program_name: Nombre limpio del programa a buscar.

    Returns:
        DataFrame filtrado.
    """
    if "Programa" not in df.columns:
        return pd.DataFrame()

    mask = (
        df["Programa"]
        .fillna("")
        .astype(str)
        .apply(extract_program_name)
        .str.upper()
        == program_name.upper()
    )

    return df[mask].copy()


def detect_program_name_inconsistencies(
    canales: Dict[str, pd.DataFrame],
    program_name: str
) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Detecta si el nombre del programa varía entre canales para el mismo programa seleccionado.

    Returns:
        Tuple (hay_inconsistencias: bool, variantes: Dict[canal, [nombres_encontrados]])
    """
    variantes = {}

    for canal, df in canales.items():
        if "Programa" not in df.columns:
            continue

        nombres_raw = (
            df["Programa"]
            .fillna("")
            .astype(str)
        )

        nombres_limpios = nombres_raw.apply(extract_program_name)

        # Filtrar los que coinciden con el programa buscado
        mask = nombres_limpios.str.upper() == program_name.upper()
        nombres_originales = nombres_raw[mask].unique().tolist()

        if nombres_originales:
            variantes[canal] = nombres_originales

    # Hay inconsistencia si los nombres originales (antes de limpiar) difieren entre canales
    todos_los_nombres = set()
    for nombres in variantes.values():
        todos_los_nombres.update(nombres)

    hay_inconsistencias = len(todos_los_nombres) > 1

    return hay_inconsistencias, variantes


def add_clean_program_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega columna 'Programa Limpio' al DataFrame para búsquedas eficientes.
    """
    if "Programa" in df.columns:
        df = df.copy()
        df["Programa Limpio"] = (
            df["Programa"]
            .fillna("")
            .astype(str)
            .apply(extract_program_name)
        )
    return df
