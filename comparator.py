"""
comparator.py
-------------
Motor de comparación multicanal para spots, acciones especiales y tandas.
Implementa lógica de semaforización: verde/amarillo/rojo.
Optimizado con operaciones vectorizadas de Pandas.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple

# ─── Constantes de estado ────────────────────────────────────────────────────

STATUS_ALL     = "✅ En todos"      # Verde: existe en todos los canales
STATUS_PARTIAL = "⚠️ Parcial"       # Amarillo: existe en algunos canales
STATUS_MISSING = "❌ Faltante"      # Rojo: falta en algún canal

# ─── Colores de semaforización ───────────────────────────────────────────────

COLOR_MAP = {
    STATUS_ALL:     "#1a7a4a",   # Verde corporativo
    STATUS_PARTIAL: "#b8860b",   # Amarillo/dorado
    STATUS_MISSING: "#c0392b",   # Rojo
}

BG_COLOR_MAP = {
    STATUS_ALL:     "#d4edda",
    STATUS_PARTIAL: "#fff3cd",
    STATUS_MISSING: "#f8d7da",
}


# ─── Funciones de comparación ────────────────────────────────────────────────

def compare_spots(
    canales_data: Dict[str, pd.DataFrame],
    tipo_bloque_norm: str,
    excluir_autopromos: Dict[str, bool] = None,
    key_column: str = "Spot Id"
) -> pd.DataFrame:
    """
    Compara spots entre todos los canales para un tipo de bloque dado.
    Perdona e identifica visualmente los autopromos excluidos.
    """
    if excluir_autopromos is None:
        excluir_autopromos = {}

    canal_names = list(canales_data.keys())
    spots_por_canal: Dict[str, pd.DataFrame] = {}

    for canal, df in canales_data.items():
        if "Tipo Bloque Norm" not in df.columns:
            spots_por_canal[canal] = pd.DataFrame()
            continue

        mask = df["Tipo Bloque Norm"].str.strip().str.lower() == tipo_bloque_norm.lower()
        spots_por_canal[canal] = df[mask].copy()

    # Obtener universo total de IDs y detectar cuáles son Autopromos
    all_ids = set()
    autopromo_ids = set()

    for canal, df in spots_por_canal.items():
        if not df.empty and key_column in df.columns:
            all_ids.update(df[key_column].dropna().astype(str).unique())
            # Detectar si es autopromo en cualquier canal
            if "Producto" in df.columns:
                mask_auto = df["Producto"].fillna("").str.strip().str.lower() == "autopromo"
                autos = df[mask_auto][key_column].dropna().astype(str).unique()
                autopromo_ids.update(autos)

    if not all_ids:
        return pd.DataFrame()

    rows = []
    for spot_id in sorted(all_ids):
        row = {"Spot Id": spot_id}
        is_autopromo = spot_id in autopromo_ids

        canal_count = 0
        required_count = len(canal_names)
        ignored_everywhere = True

        for canal in canal_names:
            df_canal = spots_por_canal.get(canal, pd.DataFrame())
            has_spot = False
            
            if not df_canal.empty and key_column in df_canal.columns:
                matches = df_canal[df_canal[key_column].astype(str) == spot_id]
                if not matches.empty:
                    has_spot = True
                    # Enriquecer datos con el primer match encontrado
                    if "_Spot" not in row:
                        first = matches.iloc[0]
                        for col in ["Inicio", "Duración", "Spot", "Posición", "Compañía", "Marca", "SubMarca", "Producto", "Producto", "Campaña"]:
                            if col in first.index and f"_{col}" not in row:
                                row[f"_{col}"] = first[col]

            # ¿El usuario pidió excluir autopromos en ESTE canal y el spot es un autopromo?
            is_excluded_in_canal = is_autopromo and excluir_autopromos.get(canal, False)

            if has_spot:
                if is_excluded_in_canal:
                    row[canal] = "⚪ Auto"
                    required_count -= 1
                else:
                    row[canal] = "✅"
                    canal_count += 1
                    ignored_everywhere = False
            else:
                if is_excluded_in_canal:
                    row[canal] = "⚪ Auto"
                    required_count -= 1
                else:
                    row[canal] = "❌"
                    ignored_everywhere = False

        # Si el spot fue marcado para excluir en ABSOLUTAMENTE TODOS los canales, lo ocultamos
        if ignored_everywhere and required_count == 0:
            continue

        # Determinar estado final: Si tiene todos los que estaba OBLIGADO a tener, pasa limpio
        if required_count == 0:
            row["Estado"] = STATUS_ALL
        elif canal_count == required_count:
            row["Estado"] = STATUS_ALL
        elif canal_count == 0:
            row["Estado"] = STATUS_MISSING
        else:
            row["Estado"] = STATUS_PARTIAL

        rows.append(row)

    return pd.DataFrame(rows)


def compare_acciones_especiales(
    canales_data: Dict[str, pd.DataFrame],
    excluir_autopromos: Dict[str, bool]
) -> pd.DataFrame:
    # Pasamos el diccionario de exclusiones directo a compare_spots
    return compare_spots(canales_data, "accion especial", excluir_autopromos)


def compare_tandas(
    canales_data: Dict[str, pd.DataFrame],
    excluir_autopromos: Dict[str, bool]
) -> pd.DataFrame:
    # Pasamos el diccionario de exclusiones directo a compare_spots
    return compare_spots(canales_data, "tanda publicitaria", excluir_autopromos)


def build_program_summary(
    canales_data: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """
    Construye la tabla resumen del programa por canal:
    Hora Inicio, Hora Fin, Duración Total.
    """
    rows = []

    for canal, df in canales_data.items():
        if "Tipo Bloque Norm" not in df.columns:
            continue

        mask = df["Tipo Bloque Norm"].str.strip().str.lower() == "programa"
        prog_df = df[mask]

        if prog_df.empty:
            rows.append({
                "Canal": canal,
                "Inicio": "—",
                "Fin": "—",
                "Duración Total": "—"
            })
            continue

        inicio = prog_df["Inicio"].dropna().iloc[0] if "Inicio" in prog_df.columns else "—"
        fin = prog_df["Final"].dropna().iloc[-1] if "Final" in prog_df.columns else "—"

        # Calcular duración total sumando las duraciones individuales
        duracion_total = _sum_durations(prog_df.get("Duración", pd.Series()))

        rows.append({
            "Canal": canal,
            "Inicio": str(inicio),
            "Fin": str(fin),
            "Duración Total": duracion_total
        })

    return pd.DataFrame(rows)


def _sum_durations(duration_series: pd.Series) -> str:
    """
    Suma una serie de duraciones en formato HH:MM:SS.
    """
    total_seconds = 0

    for val in duration_series.dropna():
        val = str(val).strip()
        parts = val.split(":")
        try:
            if len(parts) == 3:
                h, m, s = int(parts[0]), int(parts[1]), int(float(parts[2]))
                total_seconds += h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = int(parts[0]), int(float(parts[1]))
                total_seconds += m * 60 + s
        except (ValueError, IndexError):
            continue

    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_metrics(
    canales_data: Dict[str, pd.DataFrame],
    excluir_autopromos: Dict[str, bool]
) -> Dict[str, int]:
    """
    Calcula métricas globales para mostrar en el header de la app.
    """
    total_spots = 0
    total_acciones = 0
    total_tandas = 0
    duraciones = []

    for canal, df in canales_data.items():
        if "Tipo Bloque Norm" not in df.columns:
            continue

        df_work = df.copy()

        # En las métricas sí filtramos para que no inflen los contadores
        if excluir_autopromos.get(canal, False) and "Producto" in df_work.columns:
            mask_auto = df_work["Producto"].fillna("").str.strip().str.lower() == "autopromo"
            df_work = df_work[~mask_auto]

        tipo_norm = df_work["Tipo Bloque Norm"].str.strip().str.lower()

        acciones = (tipo_norm == "accion especial").sum()
        tandas = (tipo_norm == "tanda publicitaria").sum()

        total_acciones += acciones
        total_tandas += tandas
        total_spots += acciones + tandas

        # Duración del programa
        prog_mask = tipo_norm == "programa"
        if prog_mask.any() and "Duración" in df_work.columns:
            dur = _sum_durations(df_work.loc[prog_mask, "Duración"])
            duraciones.append(dur)

    return {
        "total_spots": total_spots,
        "total_acciones": total_acciones,
        "total_tandas": total_tandas,
        "duracion_programa": duraciones[0] if duraciones else "—"
    }


def detect_autopromos(
    canales_data: Dict[str, pd.DataFrame],
    excluir_autopromos: Dict[str, bool]
) -> List[str]:
    """
    Desactivado intencionalmente. Los autopromos ahora se manejan
    visual y lógicamente directo en la tabla con la etiqueta '⚪ Auto'.
    """
    return []
