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

STATUS_ALL     = "✅ En todos"      
STATUS_PARTIAL = "⚠️ Parcial"       
STATUS_MISSING = "❌ Faltante"      

# ─── Colores de semaforización ───────────────────────────────────────────────

COLOR_MAP = {
    STATUS_ALL:     "#1a7a4a",   
    STATUS_PARTIAL: "#b8860b",   
    STATUS_MISSING: "#c0392b",   
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
    Compara spots entre canales aplicando sincronización inteligente.
    Calcula el desfase de inicio del programa por canal y lo descuenta
    para comparar en tiempos relativos con +/- 10s de tolerancia.
    """
    if excluir_autopromos is None:
        excluir_autopromos = {}

    canal_names = list(canales_data.keys())
    
    # 1. Calcular desfases globales (offsets) de los canales basados en el inicio del programa
    channel_offsets = {}
    program_starts = {}
    
    for canal, df in canales_data.items():
        if "Tipo Bloque Norm" in df.columns and "Inicio" in df.columns:
            mask_prog = df["Tipo Bloque Norm"].str.strip().str.lower() == "programa"
            df_prog = df[mask_prog]
            if not df_prog.empty:
                inicio_str = df_prog["Inicio"].dropna().iloc[0]
                try:
                    program_starts[canal] = pd.to_datetime(str(inicio_str).strip())
                except Exception:
                    pass
                    
    if program_starts:
        global_min_start = min(program_starts.values())
        for canal, start_time in program_starts.items():
            # Cuántos segundos empezó tarde este canal respecto al primero
            channel_offsets[canal] = (start_time - global_min_start).total_seconds()

    # 2. Filtrar solo los registros del tipo de bloque que estamos comparando
    spots_por_canal: Dict[str, pd.DataFrame] = {}
    for canal, df in canales_data.items():
        if "Tipo Bloque Norm" not in df.columns:
            spots_por_canal[canal] = pd.DataFrame()
            continue

        mask = df["Tipo Bloque Norm"].str.strip().str.lower() == tipo_bloque_norm.lower()
        spots_por_canal[canal] = df[mask].copy()

    # 3. Obtener universo total de IDs y detectar Autopromos
    all_ids = set()
    autopromo_ids = set()

    for canal, df in spots_por_canal.items():
        if not df.empty and key_column in df.columns:
            all_ids.update(df[key_column].dropna().astype(str).unique())
            
            if "Producto" in df.columns:
                mask_auto = df["Producto"].fillna("").str.strip().str.lower() == "autopromo"
                autos = df[mask_auto][key_column].dropna().astype(str).unique()
                autopromo_ids.update(autos)

    if not all_ids:
        return pd.DataFrame()

    # 4. Construir las filas de comparación
    rows = []
    for spot_id in sorted(all_ids):
        row = {"Spot Id": spot_id}
        is_autopromo = spot_id in autopromo_ids

        canal_count = 0
        required_count = len(canal_names)
        ignored_everywhere = True

        # Recopilar tiempos AJUSTADOS de "Inicio" (Tiempo Real - Desfase del Canal)
        adjusted_times_for_spot = {}
        for canal in canal_names:
            df_canal = spots_por_canal.get(canal, pd.DataFrame())
            if not df_canal.empty and key_column in df_canal.columns:
                matches = df_canal[df_canal[key_column].astype(str) == spot_id]
                if not matches.empty:
                    first = matches.iloc[0]
                    if "Inicio" in first.index and pd.notna(first["Inicio"]):
                        try:
                            actual_time = pd.to_datetime(str(first["Inicio"]).strip())
                            offset = channel_offsets.get(canal, 0.0)
                            # Restamos el retraso original del canal para nivelarlos
                            adjusted_times_for_spot[canal] = actual_time - pd.Timedelta(seconds=offset)
                        except Exception:
                            pass
                            
        min_adj_time = min(adjusted_times_for_spot.values()) if adjusted_times_for_spot else None
        has_delay = False

        for canal in canal_names:
            df_canal = spots_por_canal.get(canal, pd.DataFrame())
            has_spot = False
            
            if not df_canal.empty and key_column in df_canal.columns:
                matches = df_canal[df_canal[key_column].astype(str) == spot_id]
                if not matches.empty:
                    has_spot = True
                    if "_Spot" not in row:
                        first = matches.iloc[0]
                        for col in ["Inicio", "Duración", "Spot", "Posición", "Compañía", "Marca", "SubMarca", "Producto", "Campaña", "Tipo"]:
                            if col in first.index and f"_{col}" not in row:
                                row[f"_{col}"] = first[col]

            is_excluded_in_canal = is_autopromo and excluir_autopromos.get(canal, False)

            if has_spot:
                if is_excluded_in_canal:
                    row[canal] = "⚪ Auto"
                    required_count -= 1
                else:
                    is_delayed = False
                    if min_adj_time and canal in adjusted_times_for_spot:
                        # Diferencia relativa (ya nivelada)
                        diff_sec = abs((adjusted_times_for_spot[canal] - min_adj_time).total_seconds())
                        if diff_sec > 10:
                            is_delayed = True
                            has_delay = True
                            
                    if is_delayed:
                        if diff_sec > 60:
                            m = int(diff_sec // 60)
                            s = int(diff_sec % 60)
                            row[canal] = f"⏱️ +{m}m {s}s"
                        else:
                            row[canal] = f"⏱️ +{int(diff_sec)}s"
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

        if ignored_everywhere and required_count == 0:
            continue

        if required_count == 0:
            row["Estado"] = STATUS_ALL
        elif canal_count == required_count:
            row["Estado"] = STATUS_PARTIAL if has_delay else STATUS_ALL
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
    return compare_spots(canales_data, "accion especial", excluir_autopromos)


def compare_tandas(
    canales_data: Dict[str, pd.DataFrame],
    excluir_autopromos: Dict[str, bool]
) -> pd.DataFrame:
    return compare_spots(canales_data, "tanda publicitaria", {})


def build_program_summary(
    canales_data: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
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

        duracion_total = _sum_durations(prog_df.get("Duración", pd.Series()))

        rows.append({
            "Canal": canal,
            "Inicio": str(inicio),
            "Fin": str(fin),
            "Duración Total": duracion_total
        })

    return pd.DataFrame(rows)


def _sum_durations(duration_series: pd.Series) -> str:
    total_seconds = 0

    for val in duration_series.dropna():
        val = str(val).strip()
        if not val:
            continue
            
        if ":" in val:
            parts = val.split(":")
            try:
                if len(parts) == 3:
                    total_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(float(parts[2]))
                elif len(parts) == 2:
                    total_seconds += int(parts[0]) * 60 + int(float(parts[1]))
            except (ValueError, IndexError):
                continue
        else:
            try:
                total_seconds += int(float(val))
            except ValueError:
                continue

    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"


def get_metrics(
    canales_data: Dict[str, pd.DataFrame],
    excluir_autopromos: Dict[str, bool]
) -> Dict[str, int]:
    total_spots = 0
    total_acciones = 0
    total_tandas = 0
    duraciones_totales = []

    for canal, df in canales_data.items():
        if "Tipo Bloque Norm" not in df.columns:
            continue

        tipo_norm = df["Tipo Bloque Norm"].str.strip().str.lower()
        
        mask_acciones = tipo_norm == "accion especial"
        mask_tandas = tipo_norm == "tanda publicitaria"

        if excluir_autopromos.get(canal, False) and "Producto" in df.columns:
            mask_auto = df["Producto"].fillna("").str.strip().str.lower() == "autopromo"
            mask_acciones = mask_acciones & (~mask_auto)

        acciones = mask_acciones.sum()
        tandas = mask_tandas.sum()

        total_acciones += acciones
        total_tandas += tandas
        total_spots += acciones + tandas

        prog_mask = tipo_norm == "programa"
        df_prog = df[prog_mask]
        
        if not df_prog.empty:
            try:
                inicio_val = df_prog["Inicio"].dropna().iloc[0] if "Inicio" in df_prog.columns else None
                fin_val = df_prog["Final"].dropna().iloc[-1] if "Final" in df_prog.columns else None
                
                if inicio_val and fin_val:
                    ini_dt = pd.to_datetime(str(inicio_val).strip())
                    fin_dt = pd.to_datetime(str(fin_val).strip())
                    diff = (fin_dt - ini_dt).total_seconds()
                    if diff > 0:
                        duraciones_totales.append(diff)
            except Exception:
                pass

    if duraciones_totales:
        avg_sec = sum(duraciones_totales) / len(duraciones_totales)
        h = int(avg_sec // 3600)
        m = int((avg_sec % 3600) // 60)
        s = int(avg_sec % 60)
        dur_str = f"{h:02d}:{m:02d}:{s:02d}"
    else:
        dur_str = "—"

    return {
        "total_spots": total_spots,
        "total_acciones": total_acciones,
        "total_tandas": total_tandas,
        "duracion_programa": dur_str
    }


def detect_autopromos(
    canales_data: Dict[str, pd.DataFrame],
    excluir_autopromos: Dict[str, bool]
) -> List[str]:
    return []
