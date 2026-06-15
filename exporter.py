"""
exporter.py
-----------
Exportación de resultados a Excel (.xlsx) y CSV.
Genera archivos de diferencias detectadas con formato profesional.
"""

import pandas as pd
import io
from typing import Dict, Optional
from datetime import datetime


def df_to_excel_bytes(
    dataframes: Dict[str, pd.DataFrame],
    sheet_names: Optional[Dict[str, str]] = None
) -> bytes:
    """
    Convierte múltiples DataFrames a un archivo Excel con múltiples hojas.

    Args:
        dataframes: {key: DataFrame} donde key es el nombre de la hoja.
        sheet_names: Mapeo opcional de renombrado de hojas.

    Returns:
        Bytes del archivo Excel generado.
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_key, df in dataframes.items():
            sheet_name = sheet_names.get(sheet_key, sheet_key) if sheet_names else sheet_key
            # Excel limita nombres de hoja a 31 caracteres
            sheet_name = sheet_name[:31]

            if df.empty:
                # Escribir hoja vacía con mensaje
                pd.DataFrame({"Info": ["Sin datos para esta sección"]}).to_excel(
                    writer, sheet_name=sheet_name, index=False
                )
            else:
                # Filtrar columnas internas (prefijo _)
                cols_visibles = [c for c in df.columns if not c.startswith("_")]
                df[cols_visibles].to_excel(writer, sheet_name=sheet_name, index=False)

    return output.getvalue()


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """
    Convierte un DataFrame a bytes CSV (UTF-8 con BOM para compatibilidad Excel).
    """
    cols_visibles = [c for c in df.columns if not c.startswith("_")]
    return df[cols_visibles].to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def build_export_filename(
    base: str,
    program_name: str,
    extension: str = "xlsx"
) -> str:
    """
    Genera un nombre de archivo de exportación con timestamp.

    Ejemplo: "acciones_FSI_MEXICO_VS_SUDAFRICA_20240615_1430.xlsx"
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    safe_program = program_name.replace(" ", "_").replace(".", "")[:40]
    return f"{base}_{safe_program}_{ts}.{extension}"


def prepare_differences_export(
    comparison_df: pd.DataFrame,
    canales: list
) -> pd.DataFrame:
    """
    Filtra y prepara solo las filas con diferencias (parciales o faltantes)
    para el reporte de diferencias detectadas.
    """
    if comparison_df.empty:
        return pd.DataFrame()

    from comparator import STATUS_ALL

    # Solo filas que NO están en todos los canales
    if "Estado" in comparison_df.columns:
        diff_df = comparison_df[comparison_df["Estado"] != STATUS_ALL].copy()
    else:
        diff_df = comparison_df.copy()

    # Filtrar columnas internas
    cols_visibles = [c for c in diff_df.columns if not c.startswith("_")]
    return diff_df[cols_visibles]
