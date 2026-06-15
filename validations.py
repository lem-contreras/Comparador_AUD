"""
validations.py
--------------
Validaciones de consistencia entre archivos de monitoreo televisivo.
Detecta inconsistencias de nombres, columnas faltantes y anomalías.
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional


def validate_program_consistency(
    canales_data: Dict[str, pd.DataFrame],
    program_name: str
) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Verifica que todos los canales tengan el mismo nombre de programa
    (antes de la limpieza de horarios).

    Returns:
        (hay_inconsistencias, {canal: [nombres_crudos_encontrados]})
    """
    from parser import extract_program_name

    variantes_crudas = {}

    for canal, df in canales_data.items():
        if "Programa" not in df.columns:
            continue

        # Buscar nombres que coincidan con el programa limpio
        nombres_raw = df["Programa"].dropna().astype(str)
        nombres_limpios = nombres_raw.apply(extract_program_name)

        mask = nombres_limpios.str.upper() == program_name.upper()
        nombres_originales = nombres_raw[mask].unique().tolist()

        if nombres_originales:
            variantes_crudas[canal] = nombres_originales

    # Recolectar todos los nombres únicos crudos entre canales
    todos = set()
    for nombres in variantes_crudas.values():
        todos.update(nombres)

    hay_inconsistencias = len(todos) > 1
    return hay_inconsistencias, variantes_crudas


def validate_required_columns(
    df: pd.DataFrame,
    canal: str,
    required: set
) -> List[str]:
    """
    Verifica que el DataFrame tenga todas las columnas requeridas.

    Returns:
        Lista de columnas faltantes.
    """
    missing = required - set(df.columns)
    return list(missing)


def detect_empty_canales(
    canales_data: Dict[str, pd.DataFrame],
    program_name: str
) -> List[str]:
    """
    Detecta canales que no tienen datos para el programa seleccionado.

    Returns:
        Lista de nombres de canales sin datos del programa.
    """
    from parser import filter_by_program

    vacios = []
    for canal, df in canales_data.items():
        filtered = filter_by_program(df, program_name)
        if filtered.empty:
            vacios.append(canal)

    return vacios


def validate_date_consistency(
    canales_data: Dict[str, pd.DataFrame]
) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Verifica que todos los canales tengan la misma fecha de emisión.

    Returns:
        (hay_inconsistencias, {canal: [fechas_encontradas]})
    """
    fechas_por_canal = {}

    for canal, df in canales_data.items():
        if "Fecha" not in df.columns:
            continue

        fechas = df["Fecha"].dropna().astype(str).unique().tolist()
        fechas_por_canal[canal] = fechas

    # Verificar unicidad de fechas globales
    todas = set()
    for f in fechas_por_canal.values():
        todas.update(f)

    hay_inconsistencias = len(todas) > 1
    return hay_inconsistencias, fechas_por_canal


def get_canal_summary_stats(
    df: pd.DataFrame,
    canal: str,
    program_name: str
) -> Dict:
    """
    Genera estadísticas resumidas de un canal para el programa dado.

    Returns:
        Diccionario con conteos de registros por tipo de bloque.
    """
    from parser import filter_by_program

    filtered = filter_by_program(df, program_name)

    if filtered.empty or "Tipo Bloque Norm" not in filtered.columns:
        return {
            "canal": canal,
            "total_registros": 0,
            "acciones_especiales": 0,
            "tandas": 0,
            "programa": 0
        }

    tipo_norm = filtered["Tipo Bloque Norm"].str.strip().str.lower()

    return {
        "canal": canal,
        "total_registros": len(filtered),
        "acciones_especiales": (tipo_norm == "accion especial").sum(),
        "tandas": (tipo_norm == "tanda publicitaria").sum(),
        "programa": (tipo_norm == "programa").sum()
    }
