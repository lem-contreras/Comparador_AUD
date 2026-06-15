"""
app.py
------
TV Monitor — Comparador Multicanal de Emisiones Televisivas
============================================================
Aplicación Streamlit para comparar archivos Excel de monitoreo televisivo
entre múltiples canales. Detecta diferencias en acciones especiales,
tandas publicitarias y horarios de programa.

Autor: TV Monitor Team
Versión: 1.0.0
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional

# ── Configuración de página (DEBE ir primero) ──────────────────────────────
st.set_page_config(
    page_title="TV Monitor — Comparador Multicanal",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "TV Monitor v1.0 — Comparador de emisiones televisivas multicanal",
    }
)

# ── Imports de módulos propios ─────────────────────────────────────────────
from loader import process_uploaded_files
from parser import (
    get_unified_program_list,
    filter_by_program,
    add_clean_program_column,
)
from comparator import (
    compare_acciones_especiales,
    compare_tandas,
    build_program_summary,
    get_metrics,
    detect_autopromos,
)
from validations import (
    validate_program_consistency,
    detect_empty_canales,
)
from ui import (
    inject_css,
    render_app_header,
    render_metrics,
    render_alert,
    render_tab_title,
    render_legend,
    render_autopromo_config,
    render_canales_overview,
    render_comparison_table,
    render_program_summary_table,
)
from exporter import (
    df_to_excel_bytes,
    df_to_csv_bytes,
    build_export_filename,
    prepare_differences_export,
)


# ── CSS global ─────────────────────────────────────────────────────────────
inject_css()


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ══════════════════════════════════════════════════════════════════════════════

def get_filtered_canales(
    canales: Dict[str, pd.DataFrame],
    program_name: str
) -> Dict[str, pd.DataFrame]:
    """
    Filtra todos los canales por el programa seleccionado.
    Agrega la columna 'Programa Limpio' a cada DataFrame.
    """
    result = {}
    for canal, df in canales.items():
        df_with_col = add_clean_program_column(df)
        filtered = filter_by_program(df_with_col, program_name)
        result[canal] = filtered
    return result


def render_export_section(
    comparison_df: pd.DataFrame,
    program_name: str,
    section_key: str,
    canales: List[str],
    label: str
):
    """Renderiza los botones de exportación para una sección."""
    if comparison_df.empty:
        return

    with st.expander("📥 Exportar resultados", expanded=False):
        col_e1, col_e2, col_e3 = st.columns(3)

        # Excel completo
        with col_e1:
            excel_bytes = df_to_excel_bytes({label: comparison_df})
            fname_xlsx = build_export_filename(section_key, program_name, "xlsx")
            st.download_button(
                label="⬇️ Descargar Excel completo",
                data=excel_bytes,
                file_name=fname_xlsx,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=f"dl_xlsx_{section_key}"
            )

        # CSV completo
        with col_e2:
            csv_bytes = df_to_csv_bytes(comparison_df)
            fname_csv = build_export_filename(section_key, program_name, "csv")
            st.download_button(
                label="⬇️ Descargar CSV completo",
                data=csv_bytes,
                file_name=fname_csv,
                mime="text/csv",
                use_container_width=True,
                key=f"dl_csv_{section_key}"
            )

        # Solo diferencias
        with col_e3:
            diff_df = prepare_differences_export(comparison_df, canales)
            if not diff_df.empty:
                diff_bytes = df_to_excel_bytes({f"Diferencias_{label}": diff_df})
                fname_diff = build_export_filename(f"dif_{section_key}", program_name, "xlsx")
                st.download_button(
                    label="⬇️ Solo diferencias detectadas",
                    data=diff_bytes,
                    file_name=fname_diff,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key=f"dl_diff_{section_key}"
                )
            else:
                st.info("✅ Sin diferencias detectadas")


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Carga de archivos y configuración
# ══════════════════════════════════════════════════════════════════════════════

def render_sidebar() -> Optional[Dict[str, pd.DataFrame]]:
    """
    Renderiza el sidebar con la carga de archivos.
    Retorna el diccionario de canales cargados o None si no hay archivos.
    """
    with st.sidebar:
        st.markdown("## 📁 Cargar Archivos")
        st.caption("Sube los archivos Excel de monitoreo. Cada archivo = un canal.")

        uploaded_files = st.file_uploader(
            "Selecciona uno o más archivos Excel",
            type=["xlsx", "xls"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key="file_uploader"
        )

        if not uploaded_files:
            st.markdown("""
            <div style="
                background: #f0f4f8;
                border-radius: 8px;
                padding: 1.25rem;
                text-align: center;
                margin-top: 1rem;
            ">
                <div style="font-size:2rem;margin-bottom:0.5rem">📂</div>
                <div style="font-size:0.8rem;color:#6b7280;font-weight:500">
                    Arrastra archivos .xlsx aquí<br>o haz clic para explorar
                </div>
                <div style="font-size:0.72rem;color:#9ca3af;margin-top:0.5rem">
                    Soporta 2 a 20 archivos simultáneos
                </div>
            </div>
            """, unsafe_allow_html=True)
            return None

        # Procesar archivos
        canales = process_uploaded_files(uploaded_files)

        if canales:
            st.success(f"✅ {len(canales)} canal(es) cargado(s)")
            st.markdown("---")
            st.markdown("**Canales detectados:**")
            for c in canales:
                st.markdown(f"• `{c}`")

        return canales if canales else None


# ══════════════════════════════════════════════════════════════════════════════
# PESTAÑA 1 — ACCIONES ESPECIALES
# ══════════════════════════════════════════════════════════════════════════════

def render_tab_acciones(
    canales_filtrados: Dict[str, pd.DataFrame],
    canales_names: List[str],
    program_name: str,
    excluir_autopromos: Dict[str, bool]
):
    render_tab_title("⚡", "Acciones Especiales")

    # Comparar entre todos los canales
    comparison_df = compare_acciones_especiales(canales_filtrados, excluir_autopromos)

    if comparison_df.empty:
        render_alert(
            "No se encontraron registros de tipo 'Accion especial' para este programa.",
            "info"
        )
        return

    # Estadísticas rápidas
    col_s1, col_s2, col_s3 = st.columns(3)
    total = len(comparison_df)
    from comparator import STATUS_ALL, STATUS_PARTIAL, STATUS_MISSING
    en_todos  = (comparison_df["Estado"] == STATUS_ALL).sum()     if "Estado" in comparison_df.columns else 0
    parciales = (comparison_df["Estado"] == STATUS_PARTIAL).sum() if "Estado" in comparison_df.columns else 0
    faltantes = (comparison_df["Estado"] == STATUS_MISSING).sum() if "Estado" in comparison_df.columns else 0

    with col_s1:
        st.metric("Total IDs únicos", total)
    with col_s2:
        st.metric("✅ En todos los canales", en_todos)
    with col_s3:
        st.metric("⚠️ Con diferencias", parciales + faltantes)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # Leyenda del semáforo
    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l1:
        st.markdown('<span class="badge badge-green">✅ En todos</span> Presente en todos los canales', unsafe_allow_html=True)
    with col_l2:
        st.markdown('<span class="badge badge-yellow">⚠️ Parcial</span> Solo en algunos canales', unsafe_allow_html=True)
    with col_l3:
        st.markdown('<span class="badge badge-red">❌ Faltante</span> Ausente en algún canal', unsafe_allow_html=True)

    st.markdown("")

    # Columnas visibles: Inicio, Duración, ID (Spot Id), Spot
    visible_cols = ["Spot Id", "_Inicio", "_Duración", "_Spot"]
    # Renombrar para mostrar
    display_df = comparison_df.copy()

    # Crear versión para mostrar con columna ID renombrada
    show_df = display_df.rename(columns={"Spot Id": "ID"})
    canal_cols = [c for c in canales_names if c in show_df.columns]
    visible = ["ID"]
    if "_Inicio"    in show_df.columns: visible.append("_Inicio")
    if "_Duración"  in show_df.columns: visible.append("_Duración")
    if "_Spot"      in show_df.columns: visible.append("_Spot")
    visible += canal_cols
    if "Estado" in show_df.columns: visible.append("Estado")

    # Limpiar columnas privadas para mostrar (quitar prefijo _)
    rename_map = {c: c.lstrip("_") for c in show_df.columns if c.startswith("_")}
    show_df = show_df.rename(columns=rename_map)
    visible_clean = [rename_map.get(c, c) for c in visible]

    render_comparison_table(
        comparison_df=show_df,
        canales=canales_names,
        visible_cols=visible_clean,
        tab_key="acciones"
    )

    # Exportación
    render_export_section(comparison_df, program_name, "acciones", canales_names, "Acciones Especiales")


# ══════════════════════════════════════════════════════════════════════════════
# PESTAÑA 2 — TANDA PUBLICITARIA
# ══════════════════════════════════════════════════════════════════════════════

def render_tab_tandas(
    canales_filtrados: Dict[str, pd.DataFrame],
    canales_names: List[str],
    program_name: str,
    excluir_autopromos: Dict[str, bool]
):
    render_tab_title("📢", "Tanda Publicitaria")
    st.caption("Incluye registros de tipo **Carrier** y **Break** (unificados como Tanda Publicitaria)")

    comparison_df = compare_tandas(canales_filtrados, excluir_autopromos)

    if comparison_df.empty:
        render_alert(
            "No se encontraron registros de Tanda Publicitaria (Carrier/Break) para este programa.",
            "info"
        )
        return

    # Estadísticas
    from comparator import STATUS_ALL, STATUS_PARTIAL, STATUS_MISSING
    total     = len(comparison_df)
    en_todos  = (comparison_df["Estado"] == STATUS_ALL).sum()     if "Estado" in comparison_df.columns else 0
    parciales = (comparison_df["Estado"] == STATUS_PARTIAL).sum() if "Estado" in comparison_df.columns else 0
    faltantes = (comparison_df["Estado"] == STATUS_MISSING).sum() if "Estado" in comparison_df.columns else 0

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1: st.metric("Total IDs únicos", total)
    with col_s2: st.metric("✅ Coincidencias", en_todos)
    with col_s3: st.metric("⚠️ Parciales",     parciales)
    with col_s4: st.metric("❌ Faltantes",      faltantes)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # Leyenda
    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l1:
        st.markdown('<span class="badge badge-green">✅ En todos</span> Presente en todos los canales', unsafe_allow_html=True)
    with col_l2:
        st.markdown('<span class="badge badge-yellow">⚠️ Parcial</span> Solo en algunos canales', unsafe_allow_html=True)
    with col_l3:
        st.markdown('<span class="badge badge-red">❌ Faltante</span> Ausente en algún canal', unsafe_allow_html=True)

    st.markdown("")

    # Preparar display
    show_df = comparison_df.copy()
    rename_map = {c: c.lstrip("_") for c in show_df.columns if c.startswith("_")}
    show_df = show_df.rename(columns=rename_map)
    show_df = show_df.rename(columns={"Spot Id": "ID"})

    canal_cols = [c for c in canales_names if c in show_df.columns]
    visible = ["ID"]
    for col in ["Inicio", "Duración", "Posición", "Spot"]:
        if col in show_df.columns:
            visible.append(col)
    visible += canal_cols
    if "Estado" in show_df.columns:
        visible.append("Estado")

    render_comparison_table(
        comparison_df=show_df,
        canales=canales_names,
        visible_cols=visible,
        tab_key="tandas"
    )

    # Exportación
    render_export_section(comparison_df, program_name, "tandas", canales_names, "Tandas Publicitarias")


# ══════════════════════════════════════════════════════════════════════════════
# PESTAÑA 3 — PROGRAMA
# ══════════════════════════════════════════════════════════════════════════════

def render_tab_programa(
    canales_filtrados: Dict[str, pd.DataFrame],
    canales_names: List[str],
    program_name: str
):
    render_tab_title("🎬", "Resumen del Programa")

    summary_df = build_program_summary(canales_filtrados)

    if summary_df.empty:
        render_alert(
            "No se encontraron registros de tipo 'Programa' para los canales cargados.",
            "info"
        )
        return

    st.markdown("**Tabla comparativa de horarios por canal:**")
    render_program_summary_table(summary_df)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # Análisis visual de duración
    st.markdown("**📊 Análisis de duración por canal**")

    dur_data = []
    for _, row in summary_df.iterrows():
        if row["Duración Total"] != "—":
            parts = row["Duración Total"].split(":")
            try:
                total_min = int(parts[0]) * 60 + int(parts[1])
                dur_data.append({"Canal": row["Canal"], "Minutos": total_min})
            except (ValueError, IndexError):
                pass

    if dur_data:
        dur_df = pd.DataFrame(dur_data).set_index("Canal")
        st.bar_chart(dur_df)

    # Exportación
    with st.expander("📥 Exportar resumen del programa", expanded=False):
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            excel_bytes = df_to_excel_bytes({"Programa": summary_df})
            fname = build_export_filename("programa", program_name, "xlsx")
            st.download_button(
                "⬇️ Descargar Excel",
                data=excel_bytes,
                file_name=fname,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="dl_programa_xlsx"
            )
        with col_e2:
            csv_bytes = df_to_csv_bytes(summary_df)
            fname_csv = build_export_filename("programa", program_name, "csv")
            st.download_button(
                "⬇️ Descargar CSV",
                data=csv_bytes,
                file_name=fname_csv,
                mime="text/csv",
                use_container_width=True,
                key="dl_programa_csv"
            )


# ══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # ── Header ──────────────────────────────────────────────────────────────
    render_app_header()

    # ── Sidebar: carga de archivos ──────────────────────────────────────────
    canales = render_sidebar()

    if not canales:
        # Estado inicial — sin archivos cargados
        st.markdown("""
        <div style="
            text-align: center;
            padding: 4rem 2rem;
            color: #9ca3af;
            font-family: 'Inter', sans-serif;
        ">
            <div style="font-size:4rem;margin-bottom:1rem">📺</div>
            <div style="font-size:1.2rem;font-weight:600;color:#6b7280;margin-bottom:0.5rem">
                Ningún archivo cargado
            </div>
            <div style="font-size:0.875rem">
                Usa el panel lateral para cargar los archivos Excel de monitoreo televisivo.<br>
                Puedes cargar entre 2 y 20 archivos simultáneamente.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    canales_names = list(canales.keys())

    # ── Resumen de canales cargados ─────────────────────────────────────────
    render_canales_overview(canales_names)

    # ── Selector de programa ────────────────────────────────────────────────
    programas = get_unified_program_list(canales)

    if not programas:
        render_alert("No se detectaron programas en los archivos cargados.", "danger")
        return

    col_prog, col_cfg = st.columns([3, 1])

    with col_prog:
        program_name = st.selectbox(
            "🔍 Seleccionar programa",
            options=programas,
            index=0,
            key="selected_program",
            help="El sistema busca por nombre limpio, ignorando horarios y EMS"
        )

    # ── Panel de Autopromos (en expander) ───────────────────────────────────
    with st.expander("⚙️ Configuración de Autopromos", expanded=False):
        excluir_autopromos = render_autopromo_config(canales_names)

    # ── Filtrar datos por programa ──────────────────────────────────────────
    canales_filtrados = get_filtered_canales(canales, program_name)

    # ── Validaciones ────────────────────────────────────────────────────────
    # 1. Canales sin datos para el programa
    vacios = detect_empty_canales(canales, program_name)
    if vacios:
        render_alert(
            f"🔔 Los siguientes canales no tienen datos del programa seleccionado: "
            f"<strong>{', '.join(vacios)}</strong>",
            "warning"
        )
                   
    # 3. Alertas de autopromos activos
    alertas_auto = detect_autopromos(canales_filtrados, excluir_autopromos)
    for canal_con_auto in alertas_auto:
        render_alert(
            f"🔔 Autopromo detectado en <strong>{canal_con_auto}</strong> "
            f"(la exclusión está activa pero persisten registros de autopromo)",
            "warning"
        )

    # ── Leyenda del programa ────────────────────────────────────────────────
    render_legend(program_name)

    # ── Métricas superiores ─────────────────────────────────────────────────
    metrics = get_metrics(canales_filtrados, excluir_autopromos)
    render_metrics(metrics)

    st.markdown("")

    # ══════════════════════════════════════════════════════════════════════
    # PESTAÑAS PRINCIPALES
    # ══════════════════════════════════════════════════════════════════════

    tab1, tab2, tab3 = st.tabs([
        "⚡ Acciones Especiales",
        "📢 Tanda Publicitaria",
        "🎬 Programa",
    ])

    with tab1:
        render_tab_acciones(
            canales_filtrados=canales_filtrados,
            canales_names=canales_names,
            program_name=program_name,
            excluir_autopromos=excluir_autopromos
        )

    with tab2:
        render_tab_tandas(
            canales_filtrados=canales_filtrados,
            canales_names=canales_names,
            program_name=program_name,
            excluir_autopromos=excluir_autopromos
        )

    with tab3:
        render_tab_programa(
            canales_filtrados=canales_filtrados,
            canales_names=canales_names,
            program_name=program_name
        )


# ── Inicializar session_state ───────────────────────────────────────────────
if "selected_spot" not in st.session_state:
    st.session_state.selected_spot = None

if __name__ == "__main__":
    main()
