"""
ui.py
-----
Componentes de interfaz reutilizables para la aplicación de monitoreo televisivo.
Estilos, semaforización visual y renderizado de tablas comparativas.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
from comparator import STATUS_ALL, STATUS_PARTIAL, STATUS_MISSING, BG_COLOR_MAP, COLOR_MAP


# ─── CSS Global ──────────────────────────────────────────────────────────────

GLOBAL_CSS = """
<style>
/* ── Fuentes y variables ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --primary:       #0d1b2a;
    --accent:        #1565c0;
    --accent-light:  #1976d2;
    --surface:       #f8fafc;
    --surface-2:     #eef2f7;
    --border:        #dde3ec;
    --text:          #1a202c;
    --text-muted:    #6b7280;
    --green:         #1a7a4a;
    --green-bg:      #d4edda;
    --yellow:        #b8860b;
    --yellow-bg:     #fff3cd;
    --red:           #c0392b;
    --red-bg:        #f8d7da;
    --radius:        8px;
    --shadow:        0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
    --shadow-md:     0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.05);
}

/* ── Layout principal ── */
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* ── Header de la app ── */
.app-header {
    background: linear-gradient(135deg, var(--primary) 0%, #1a2d4a 100%);
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    box-shadow: var(--shadow-md);
}
.app-header-icon {
    font-size: 2.2rem;
    line-height: 1;
}
.app-header-title {
    color: #fff;
    font-family: 'Inter', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.3px;
}
.app-header-subtitle {
    color: rgba(255,255,255,0.65);
    font-size: 0.82rem;
    margin: 0;
    font-weight: 400;
}

/* ── Métricas ── */
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.25rem;
    text-align: center;
    box-shadow: var(--shadow);
    transition: box-shadow 0.2s;
}
.metric-card:hover {
    box-shadow: var(--shadow-md);
}
.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--accent);
    line-height: 1;
    margin-bottom: 0.25rem;
}
.metric-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Alertas personalizadas ── */
.alert-warning {
    background: var(--yellow-bg);
    border-left: 4px solid var(--yellow);
    border-radius: var(--radius);
    padding: 0.875rem 1.25rem;
    margin: 0.75rem 0;
    color: #856404;
    font-size: 0.875rem;
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
}
.alert-danger {
    background: var(--red-bg);
    border-left: 4px solid var(--red);
    border-radius: var(--radius);
    padding: 0.875rem 1.25rem;
    margin: 0.75rem 0;
    color: #721c24;
    font-size: 0.875rem;
}
.alert-info {
    background: #e8f4f8;
    border-left: 4px solid var(--accent);
    border-radius: var(--radius);
    padding: 0.875rem 1.25rem;
    margin: 0.75rem 0;
    color: #0c5460;
    font-size: 0.875rem;
}
.alert-success {
    background: var(--green-bg);
    border-left: 4px solid var(--green);
    border-radius: var(--radius);
    padding: 0.875rem 1.25rem;
    margin: 0.75rem 0;
    color: #155724;
    font-size: 0.875rem;
}

/* ── Semáforo badges ── */
.badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.badge-green  { background: var(--green-bg);  color: var(--green);  }
.badge-yellow { background: var(--yellow-bg); color: var(--yellow); }
.badge-red    { background: var(--red-bg);    color: var(--red);    }

/* ── Panel lateral (sidebar) de detalle ── */
.spot-detail-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow);
}
.spot-detail-title {
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-weight: 600;
    margin-bottom: 0.2rem;
}
.spot-detail-value {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text);
    font-family: 'Inter', sans-serif;
}
.spot-id-badge {
    background: var(--accent);
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    font-weight: 500;
    display: inline-block;
    margin-bottom: 1rem;
}

/* ── Tabla comparativa ── */
.compare-table th {
    background: var(--primary);
    color: white;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 0.6rem 0.8rem;
}
.compare-table td {
    font-size: 0.82rem;
    padding: 0.5rem 0.8rem;
    vertical-align: middle;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--surface-2);
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px;
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-muted);
    padding: 0.4rem 1rem;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: var(--accent) !important;
    box-shadow: var(--shadow);
}

/* ── Sección título de pestaña ── */
.tab-section-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--primary);
    margin: 0.5rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--accent);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Canal tag ── */
.canal-tag {
    background: var(--accent);
    color: white;
    border-radius: 20px;
    padding: 0.15rem 0.7rem;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}

/* ── Separador visual ── */
.section-divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.25rem 0;
}

/* ── Instrucción de selección ── */
.selection-hint {
    background: #e8f4f8;
    border-radius: var(--radius);
    padding: 0.5rem 1rem;
    font-size: 0.8rem;
    color: #0c5460;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

/* ── DataEditor override ── */
[data-testid="stDataFrame"] {
    border-radius: var(--radius);
    border: 1px solid var(--border);
    overflow: hidden;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface-2); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #b0b7c3; }
</style>
"""


def inject_css():
    """Inyecta el CSS global en la aplicación."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def render_app_header():
    """Renderiza el header principal de la aplicación."""
    st.markdown("""
    <div class="app-header">
        <div class="app-header-icon">📺</div>
        <div>
            <p class="app-header-title">Monitor TV — Comparador Multicanal</p>
            <p class="app-header-subtitle">Análisis y detección de diferencias en emisiones televisivas</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_metrics(metrics: dict):
    """Renderiza las métricas superiores en 4 columnas."""
    col1, col2, col3, col4 = st.columns(4)

    items = [
        (col1, metrics.get("total_spots", 0), "Total Spots", "📊"),
        (col2, metrics.get("total_acciones", 0), "Acciones Especiales", "⚡"),
        (col3, metrics.get("total_tandas", 0), "Tandas Publicitarias", "📢"),
        (col4, metrics.get("duracion_programa", "—"), "Duración Programa", "⏱️"),
    ]

    for col, value, label, icon in items:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size:1.3rem;margin-bottom:0.2rem">{icon}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)


def render_alert(message: str, kind: str = "warning"):
    """
    Renderiza una alerta visual personalizada.

    Args:
        kind: "warning", "danger", "info", "success"
    """
    icons = {
        "warning": "⚠️",
        "danger":  "🔴",
        "info":    "ℹ️",
        "success": "✅",
    }
    icon = icons.get(kind, "ℹ️")
    st.markdown(f"""
    <div class="alert-{kind}">
        {icon} {message}
    </div>
    """, unsafe_allow_html=True)


def render_status_badge(status: str) -> str:
    """Retorna HTML del badge de estado semafórico."""
    if STATUS_ALL in status:
        return f'<span class="badge badge-green">{status}</span>'
    elif STATUS_PARTIAL in status:
        return f'<span class="badge badge-yellow">{status}</span>'
    else:
        return f'<span class="badge badge-red">{status}</span>'


def render_tab_title(icon: str, title: str):
    """Renderiza el título de sección dentro de una pestaña."""
    st.markdown(f"""
    <div class="tab-section-title">
        {icon} {title}
    </div>
    """, unsafe_allow_html=True)


def render_spot_detail_sidebar(row_data: dict):
    """
    Renderiza el panel lateral con el detalle de un spot seleccionado.

    Args:
        row_data: Diccionario con los datos del spot (claves con prefijo _).
    """
    spot_id = row_data.get("Spot Id", row_data.get("_Spot Id", "—"))

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Detalle del Spot")
    st.sidebar.markdown(f'<div class="spot-id-badge">ID: {spot_id}</div>', unsafe_allow_html=True)

    fields = [
        ("_Compañía",  "🏢 Compañía"),
        ("_Marca",     "🏷️ Marca"),
        ("_SubMarca",  "📎 SubMarca"),
        ("_Producto",  "📦 Producto"),
        ("_Campaña",   "📣 Campaña"),
    ]

    # Fallback sin prefijo
    fields_fallback = [
        ("Compañía",  "🏢 Compañía"),
        ("Marca",     "🏷️ Marca"),
        ("SubMarca",  "📎 SubMarca"),
        ("Producto",  "📦 Producto"),
        ("Campaña",   "📣 Campaña"),
    ]

    for (key, label), (key_fb, _) in zip(fields, fields_fallback):
        value = row_data.get(key) or row_data.get(key_fb) or "—"
        st.sidebar.markdown(f"""
        <div class="spot-detail-card">
            <div class="spot-detail-title">{label}</div>
            <div class="spot-detail-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

    if st.sidebar.button("✕ Cerrar detalle", use_container_width=True):
        st.session_state.selected_spot = None
        st.rerun()


def render_comparison_table(
    comparison_df: pd.DataFrame,
    canales: List[str],
    visible_cols: List[str],
    tab_key: str
):
    """
    Renderiza la tabla comparativa multicanal con semaforización.
    Al seleccionar una fila, muestra el detalle en el sidebar.

    Args:
        comparison_df: DataFrame de comparación con columna 'Estado'.
        canales: Lista de nombres de canales.
        visible_cols: Columnas a mostrar en la tabla principal.
        tab_key: Clave única para este widget (evita conflictos de estado).
    """
    if comparison_df.empty:
        render_alert("No se encontraron datos para comparar.", "info")
        return

    # Preparar tabla de visualización (solo columnas visibles)
    display_cols = [c for c in visible_cols if c in comparison_df.columns]
    # Agregar columnas de canales y estado
    canal_cols = [c for c in canales if c in comparison_df.columns]
    all_display = display_cols + canal_cols + (["Estado"] if "Estado" in comparison_df.columns else [])

    # Eliminar duplicados manteniendo orden
    seen = set()
    final_cols = []
    for c in all_display:
        if c not in seen:
            seen.add(c)
            final_cols.append(c)

    display_df = comparison_df[final_cols].copy() if final_cols else comparison_df.copy()

    # Instrucción de selección
    st.markdown("""
    <div class="selection-hint">
        👆 Haz clic en una fila para ver el detalle completo del spot en el panel lateral
    </div>
    """, unsafe_allow_html=True)

    # Renderizar con st.dataframe con selección de filas
    event = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"df_{tab_key}",
        column_config={
            "Estado": st.column_config.TextColumn(
                "Estado",
                width="medium",
            ),
            **{c: st.column_config.TextColumn(c, width="small") for c in canal_cols}
        }
    )

    # Procesar selección de fila
    if event and hasattr(event, "selection") and event.selection:
        selected_rows = event.selection.get("rows", [])
        if selected_rows:
            row_idx = selected_rows[0]
            if row_idx < len(comparison_df):
                row_data = comparison_df.iloc[row_idx].to_dict()
                render_spot_detail_sidebar(row_data)


def render_program_summary_table(summary_df: pd.DataFrame):
    """
    Renderiza la tabla resumen del programa con estilo corporativo.
    """
    if summary_df.empty:
        render_alert("No se encontraron datos del programa.", "info")
        return

    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Canal":           st.column_config.TextColumn("📺 Canal",            width="medium"),
            "Inicio":          st.column_config.TextColumn("🕐 Inicio",           width="small"),
            "Fin":             st.column_config.TextColumn("🕑 Fin",              width="small"),
            "Duración Total":  st.column_config.TextColumn("⏱️ Duración Total",  width="small"),
        }
    )


def render_legend(program_name: str):
    """Renderiza la leyenda superior con el nombre del programa."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, #0d1b2a 0%, #1a2d4a 100%);
        color: white;
        border-radius: 8px;
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-family: 'Inter', sans-serif;
    ">
        <span style="font-size:1.2rem">🎬</span>
        <div>
            <div style="font-size:0.7rem;color:rgba(255,255,255,0.6);letter-spacing:1px;text-transform:uppercase;font-weight:500">
                Programa analizado
            </div>
            <div style="font-size:1rem;font-weight:700;letter-spacing:-0.2px">
                {program_name}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_autopromo_config(canales: List[str]) -> Dict[str, bool]:
    """
    Renderiza el panel de configuración de exclusión de autopromos.

    Returns:
        Diccionario {canal: excluir_bool}
    """
    st.markdown("#### ⚙️ Configuración de Autopromos")
    st.caption("Activa la exclusión para ignorar registros donde Producto = 'Autopromo' en cada canal.")

    config = {}
    cols = st.columns(min(len(canales), 4))

    for i, canal in enumerate(canales):
        with cols[i % len(cols)]:
            config[canal] = st.checkbox(
                f"Excluir autopromos\n**{canal}**",
                key=f"excluir_auto_{canal}",
                value=False
            )

    return config


def render_canales_overview(canales: List[str]):
    """Renderiza un resumen visual de los canales cargados."""
    st.markdown(f"**{len(canales)} canal(es) cargado(s):**")
    tags = " ".join([f'<span class="canal-tag">{c}</span>' for c in canales])
    st.markdown(tags, unsafe_allow_html=True)
    st.markdown("")
