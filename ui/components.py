import streamlit as st
import plotly.graph_objects as go

from core.parser import CRITERIOS_INVERTIDOS

# ──────────────────────────────────────────────────────────────────────────────
# Constantes de dominio
# ──────────────────────────────────────────────────────────────────────────────

CRITERIOS_LABELS = {
    "costo_renta": "Costo renta",
    "flujo_peatonal": "Flujo peatonal",
    "accesibilidad_transporte": "Transporte",
    "nivel_competencia": "Competencia",
    "afinidad_con_giro": "Afinidad giro",
    "seguridad_zona": "Seguridad",
    "potencial_crecimiento": "Crecimiento",
    "visibilidad_local": "Visibilidad",
    "compatibilidad_capital": "Capital",
}

# Niveles → color CSS + emoji  (criterios normales: alto = bueno = verde)
NIVEL_META = {
    "muy alto": {"emoji": "🟢", "color": "#16a34a", "bg": "#dcfce7", "label": "Muy alto"},
    "alto":     {"emoji": "🔵", "color": "#2563eb", "bg": "#dbeafe", "label": "Alto"},
    "medio":    {"emoji": "🟡", "color": "#d97706", "bg": "#fef9c3", "label": "Medio"},
    "bajo":     {"emoji": "🔴", "color": "#dc2626", "bg": "#fee2e2", "label": "Bajo"},
}

# Para criterios invertidos el color refleja bondad (puntaje alto = bueno = verde)
# aunque el label diga "Bajo" (renta baja = bueno).
NIVEL_META_INVERTIDO = {
    "bajo":     {"emoji": "🟢", "color": "#16a34a", "bg": "#dcfce7", "label": "Bajo"},
    "medio":    {"emoji": "🔵", "color": "#2563eb", "bg": "#dbeafe", "label": "Medio"},
    "alto":     {"emoji": "🟡", "color": "#d97706", "bg": "#fef9c3", "label": "Alto"},
    "muy alto": {"emoji": "🔴", "color": "#dc2626", "bg": "#fee2e2", "label": "Muy alto"},
}

# Paleta corporativa para las 5 ubicaciones (coincide en tabla y gráfico)
LOCATION_COLORS = ["#0ea5e9", "#ec4899", "#f97316", "#8b5cf6", "#14b8a6"]

MEDALLAS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────────────────────────────────────

def _puntaje(ubicacion: dict, clave: str) -> int:
    """Extrae el puntaje de un criterio de forma segura."""
    return ubicacion.get("criterios", {}).get(clave, {}).get("puntaje", 0)


def _nivel_raw(ubicacion: dict, clave: str) -> str:
    return ubicacion.get("criterios", {}).get(clave, {}).get("nivel", "").lower()


def _badge(nivel_raw: str, puntaje: int, invertido: bool = False) -> str:
    """Devuelve un <span> HTML estilizado para el nivel/puntaje de un criterio.
    Si invertido=True usa la paleta de colores invertida (bajo=verde, muy alto=rojo).
    """
    tabla = NIVEL_META_INVERTIDO if invertido else NIVEL_META
    meta = tabla.get(nivel_raw, {"color": "#6b7280", "bg": "#f3f4f6", "label": nivel_raw.title() or "—"})
    return (
        f'<span style="display:inline-flex;align-items:center;gap:4px;'
        f'background:{meta["bg"]};color:{meta["color"]};'
        f'border:1px solid {meta["color"]}33;'
        f'border-radius:6px;padding:2px 8px;font-size:0.78rem;font-weight:600;white-space:nowrap;">'
        f'{puntaje:.0f}/10&nbsp;{meta["label"]}'
        f'</span>'
    )


def _score_badge(total: int, color: str) -> str:
    """Badge grande con el puntaje total de una ubicación."""
    return (
        f'<span style="display:inline-block;background:{color};color:#fff;'
        f'border-radius:8px;padding:3px 10px;font-size:0.85rem;font-weight:700;">'
        f'{total}/90</span>'
    )


# ──────────────────────────────────────────────────────────────────────────────
# 1. Leyenda de simbología
# ──────────────────────────────────────────────────────────────────────────────

# Leyenda semántica: describe qué significa cada color para el negocio,
# independientemente de si el criterio es normal o invertido.
_LEYENDA_ITEMS = [
    {"emoji": "🟢", "color": "#16a34a", "bg": "#dcfce7", "label": "Óptimo"},
    {"emoji": "🔵", "color": "#2563eb", "bg": "#dbeafe", "label": "Aceptable"},
    {"emoji": "🟡", "color": "#d97706", "bg": "#fef9c3", "label": "Regular"},
    {"emoji": "🔴", "color": "#dc2626", "bg": "#fee2e2", "label": "Deficiente"},
]


def _render_leyenda() -> None:
    """Leyenda visual que explica los colores por bondad para el negocio."""
    items_html = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'background:{m["bg"]};color:{m["color"]};border:1px solid {m["color"]}44;'
        f'border-radius:20px;padding:4px 12px;font-size:0.78rem;font-weight:600;">'
        f'{m["emoji"]} {m["label"]}</span>'
        for m in _LEYENDA_ITEMS
    )
    # Nivel "sin datos"
    items_html += (
        '<span style="display:inline-flex;align-items:center;gap:5px;'
        'background:rgba(128,128,128,0.1);color:var(--text-color);border:1px solid rgba(128,128,128,0.3);'
        'border-radius:20px;padding:4px 12px;font-size:0.78rem;font-weight:600;">'
        '⚪ Sin datos</span>'
    )
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;gap:8px;'
        f'background:var(--secondary-background-color);border:1px solid rgba(128,128,128,0.2);border-radius:10px;'
        f'padding:12px 16px;margin-bottom:16px;">'
        f'<span style="font-size:0.78rem;color:var(--text-color);opacity:0.6;font-weight:600;'
        f'align-self:center;margin-right:4px;">Simbología:</span>'
        f'{items_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# 2. Tabla comparativa interactiva (HTML puro, inyectada con st.markdown)
# ──────────────────────────────────────────────────────────────────────────────

def render_tabla(ubicaciones: list) -> None:
    """Tabla comparativa: filas = criterios, columnas = ubicaciones."""
    st.subheader("📊 Tabla comparativa")
    _render_leyenda()

    nombres = [u.get("nombre", f"Ubicación {i+1}") for i, u in enumerate(ubicaciones)]
    totales = [u.get("puntaje_total", 0) for u in ubicaciones]

    # ── Encabezados de columnas ──────────────────────────────────────────────
    header_cells = '<th style="min-width:140px;text-align:left;padding:10px 14px;font-weight:700;color:var(--text-color);">Criterio</th>'
    for i, (nombre, total) in enumerate(zip(nombres, totales)):
        color = LOCATION_COLORS[i % len(LOCATION_COLORS)]
        header_cells += (
            f'<th style="text-align:center;padding:10px 14px;min-width:150px;">'
            f'<div style="font-weight:700;color:{color};font-size:0.9rem;">{nombre}</div>'
            f'</th>'
        )

    # ── Filas de criterios ───────────────────────────────────────────────────
    body_rows = ""
    for row_idx, (clave, label) in enumerate(CRITERIOS_LABELS.items()):
        bg = "var(--background-color)" if row_idx % 2 == 0 else "var(--secondary-background-color)"
        cells = f'<td style="padding:10px 14px;font-weight:600;color:var(--text-color);background:{bg};">{label}</td>'
        for u in ubicaciones:
            p = _puntaje(u, clave)
            n = _nivel_raw(u, clave)
            inv = clave in CRITERIOS_INVERTIDOS
            cells += f'<td style="text-align:center;padding:8px 12px;background:{bg};">{_badge(n, p, inv)}</td>'
        body_rows += f"<tr>{cells}</tr>"

    # ── Fila de totales ──────────────────────────────────────────────────────
    total_cells = '<td style="padding:10px 14px;font-weight:800;color:var(--text-color);background:var(--secondary-background-color);">TOTAL</td>'
    for i, total in enumerate(totales):
        color = LOCATION_COLORS[i % len(LOCATION_COLORS)]
        total_cells += (
            f'<td style="text-align:center;padding:10px 12px;background:var(--secondary-background-color);">'
            f'{_score_badge(total, color)}</td>'
        )
    body_rows += f"<tr>{total_cells}</tr>"

    # ── Tabla completa ───────────────────────────────────────────────────────
    table_html = f"""
    <div style="overflow-x:auto;border-radius:12px;border:1px solid rgba(128,128,128,0.2);
                box-shadow:0 1px 4px rgba(0,0,0,0.06);margin-bottom:8px;">
      <table style="width:100%;border-collapse:collapse;font-family:-apple-system,'Segoe UI',sans-serif;font-size:0.87rem;">
        <thead>
          <tr style="background:var(--secondary-background-color);border-bottom:2px solid rgba(128,128,128,0.2);">
            {header_cells}
          </tr>
        </thead>
        <tbody>
          {body_rows}
        </tbody>
      </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# 3. Gráfico de barras agrupadas — Plotly interactivo con colores coordinados
# ──────────────────────────────────────────────────────────────────────────────

def render_grafico(ubicaciones: list) -> None:
    """Gráfico de barras agrupadas: puntaje por criterio por ubicación."""
    st.subheader("📈 Comparativa por criterio")

    criterios = list(CRITERIOS_LABELS.values())
    claves = list(CRITERIOS_LABELS.keys())

    fig = go.Figure()
    for i, u in enumerate(ubicaciones):
        nombre = u.get("nombre", "—")
        puntajes = [_puntaje(u, c) for c in claves]
        color = LOCATION_COLORS[i % len(LOCATION_COLORS)]

        # Tooltip personalizado mostrando nivel + puntaje
        hover_texts = []
        for c in claves:
            p = _puntaje(u, c)
            n = _nivel_raw(u, c)
            meta = NIVEL_META.get(n, {"label": "—"})
            hover_texts.append(f"<b>{CRITERIOS_LABELS[c]}</b><br>Puntaje: {p}/10<br>Nivel: {meta['label']}")

        fig.add_trace(go.Bar(
            name=nombre,
            x=puntajes,
            y=criterios,
            orientation="h",
            marker_color=color,
            marker_line_color=color,
            marker_line_width=0,
            opacity=0.88,
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover_texts,
        ))

    fig.update_layout(
        barmode="group",
        xaxis=dict(
            range=[0, 10],
            title="Puntaje (1–10)",
            gridcolor="rgba(128,128,128,0.2)",
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            tickfont=dict(size=11),
            autorange="reversed",
        ),
        showlegend=False,
        height=650,
        margin=dict(t=50, b=50, l=130, r=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="-apple-system, 'Segoe UI', sans-serif"),
        hoverlabel=dict(
            bgcolor="#1e293b",
            font_color="#f8fafc",
            font_size=13,
            bordercolor="#1e293b",
        ),
    )

    # Línea de referencia en 7 (puntaje "bueno")
    fig.add_vline(
        x=7,
        line_dash="dot",
        line_color="#94a3b8",
        annotation_text="Umbral recomendado (7)",
        annotation_position="top right",
        annotation_font_size=11,
        annotation_font_color="#94a3b8",
    )

    st.plotly_chart(fig, use_container_width=True)


# ──────────────────────────────────────────────────────────────────────────────
# 4. Tarjetas de Recomendación (HTML/CSS Cards)
# ──────────────────────────────────────────────────────────────────────────────

def render_recomendacion(ubicaciones: list) -> None:
    """Tarjetas HTML con la recomendación de la IA, ordenadas por puntaje."""
    st.subheader("💡 Recomendaciones de la IA")

    ordenadas = sorted(ubicaciones, key=lambda u: u.get("puntaje_total", 0), reverse=True)

    cards_html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;margin-top:8px;">'

    for i, u in enumerate(ordenadas):
        nombre = u.get("nombre", "—")
        total = u.get("puntaje_total", 0)
        descripcion = u.get("descripcion_breve", "")
        recomendacion = u.get("recomendacion_ia", "Sin recomendación.")
        medalla = MEDALLAS[i] if i < len(MEDALLAS) else f"{i+1}."
        color = LOCATION_COLORS[i % len(LOCATION_COLORS)]

        # La tarjeta del primer lugar tiene borde brillante y tamaño mayor
        if i == 0:
            card_style = (
                f"background:var(--secondary-background-color);border-radius:16px;"
                f"border:2px solid {color};"
                f"box-shadow:0 0 0 4px {color}22, 0 4px 20px rgba(0,0,0,0.10);"
                f"padding:24px;position:relative;grid-row:span 1;"
                f"transition:box-shadow .2s;"
            )
            badge_top = (
                f'<div style="position:absolute;top:-12px;left:20px;'
                f'background:{color};color:#fff;border-radius:20px;'
                f'padding:3px 14px;font-size:0.75rem;font-weight:700;'
                f'letter-spacing:.05em;box-shadow:0 2px 8px {color}55;">'
                f'✦ MEJOR OPCIÓN</div>'
            )
        else:
            card_style = (
                f"background:var(--secondary-background-color);border-radius:14px;"
                f"border:1px solid rgba(128,128,128,0.2);"
                f"box-shadow:0 2px 8px rgba(0,0,0,0.06);"
                f"padding:20px;position:relative;"
            )
            badge_top = ""

        # Barra de progreso del puntaje total
        pct = round((total / 90) * 100)
        progress_bar = (
            f'<div style="background:rgba(128,128,128,0.15);border-radius:99px;height:6px;margin:10px 0 14px;">'
            f'<div style="background:{color};width:{pct}%;height:6px;border-radius:99px;"></div>'
            f'</div>'
        )

        # Descripción breve (si existe)
        desc_html = (
            f'<p style="color:var(--text-color);opacity:0.6;font-size:0.82rem;margin:0 0 10px;line-height:1.5;">{descripcion}</p>'
            if descripcion else ""
        )

        # Texto de recomendación
        rec_html = (
            f'<div style="background:var(--background-color);border-left:3px solid {color};'
            f'border-radius:0 8px 8px 0;padding:10px 14px;'
            f'color:var(--text-color);font-size:0.85rem;line-height:1.6;">'
            f'{recomendacion}</div>'
        )

        cards_html += (
            f'<div style="{card_style}">'
            f'{badge_top}'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">'
            f'<span style="font-size:1.6rem;">{medalla}</span>'
            f'<div>'
            f'<div style="font-weight:700;font-size:1rem;color:var(--text-color);">{nombre}</div>'
            f'<div style="font-size:0.8rem;color:{color};font-weight:600;">{total}/90 puntos</div>'
            f'</div>'
            f'</div>'
            f'{progress_bar}'
            f'{desc_html}'
            f'{rec_html}'
            f'</div>'
        )

    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════════════════════════
# FASE 2 — Escenario financiero, métricas, FODA y deuda
# ══════════════════════════════════════════════════════════════════════════════

# Colores semánticos para métricas de fase 2 (verde = positivo, rojo = negativo)
_COLOR_POSITIVO = "#16a34a"
_COLOR_NEGATIVO = "#dc2626"
_COLOR_NEUTRO = "#2563eb"
_COLOR_ADVERTENCIA = "#d97706"

# Categorías del FODA con su color e ícono
_FODA_META = {
    "fortalezas":    {"label": "Fortalezas",    "emoji": "💪", "color": "#16a34a", "bg": "#dcfce7"},
    "oportunidades": {"label": "Oportunidades", "emoji": "🚀", "color": "#2563eb", "bg": "#dbeafe"},
    "debilidades":   {"label": "Debilidades",   "emoji": "⚠️", "color": "#d97706", "bg": "#fef9c3"},
    "amenazas":      {"label": "Amenazas",       "emoji": "🛡️", "color": "#dc2626", "bg": "#fee2e2"},
}


def _fmt_moneda(valor: float) -> str:
    """Formatea un float como moneda MXN sin decimales innecesarios."""
    return f"${valor:,.0f} MXN"


def _fmt_meses(valor: float | None) -> str:
    """Formatea meses de recuperación, o 'N/A' si es None."""
    if valor is None:
        return "N/A"
    return f"{valor:.1f} meses"


# ──────────────────────────────────────────────────────────────────────────────
# 5. render_escenario — informe financiero vertical (P&L → viabilidad → supuestos)
# ──────────────────────────────────────────────────────────────────────────────

def _pl_row(label: str, valor: str, color: str, indent: int = 0,
            is_total: bool = False, help_text: str = "") -> str:
    """Genera una fila HTML del estado de resultados."""
    indent_px = f"{indent * 16}px"
    font_size = "1rem" if is_total else "0.875rem"
    font_weight = "700" if is_total else "400"
    border_top = (
        "border-top:2px solid rgba(128,128,128,0.2);margin-top:6px;padding-top:10px;"
        if is_total else ""
    )
    label_opacity = "" if is_total else "opacity:0.8;"

    help_icon = ""
    if help_text:
        help_icon = (
            f' <span title="{help_text}" style="cursor:help;font-size:0.8rem;'
            f'opacity:0.45;user-select:none;" aria-label="{help_text}">ⓘ</span>'
        )

    return (
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
        f'padding:6px 0;padding-left:{indent_px};{border_top}">'
        f'<span style="font-size:{font_size};font-weight:{font_weight};'
        f'color:var(--text-color);{label_opacity}">'
        f'{label}{help_icon}'
        f'</span>'
        f'<span style="font-size:{font_size};font-weight:{font_weight};'
        f'color:{color};white-space:nowrap;">'
        f'{valor}'
        f'</span>'
        f'</div>'
    )


def _pl_desglose(items: list) -> str:
    """Genera filas de desglose indentadas a partir de lista [{concepto, monto}]."""
    html = ""
    for item in items:
        html += _pl_row(item["concepto"], _fmt_moneda(item["monto"]), "var(--text-color)", indent=2)
    return html


def _kpi_card(emoji: str, titulo: str, valor: str, color: str, subtitulo: str = "") -> str:
    """Tarjeta de KPI con título grande y valor destacado."""
    sub_html = (
        f'<div style="font-size:0.72rem;color:var(--text-color);opacity:0.5;margin-top:5px;">'
        f'{subtitulo}</div>'
        if subtitulo else ""
    )
    return (
        f'<div style="background:var(--secondary-background-color);'
        f'border:1px solid rgba(128,128,128,0.2);border-radius:12px;'
        f'padding:16px 20px;margin-bottom:10px;">'
        f'<div style="font-size:0.82rem;font-weight:600;color:var(--text-color);'
        f'margin-bottom:6px;">{emoji} {titulo}</div>'
        f'<div style="font-size:1.55rem;font-weight:800;color:{color};line-height:1.1;">'
        f'{valor}</div>'
        f'{sub_html}'
        f'</div>'
    )


def render_escenario(escenario: dict, modo_edicion: bool = False) -> dict:
    """
    Muestra el escenario financiero como informe vertical en tres bloques:
      1. Estado de resultados mensual (P&L) — editable inline cuando modo_edicion=True
      2. Métricas de viabilidad con semáforo (recalculadas en tiempo real)
      3. Supuestos unitarios del modelo

    Args:
        escenario: dict validado devuelto por core.scenario_parser.parse_scenario().
        modo_edicion: si True, las filas del P&L se convierten en number_inputs inline.

    Returns:
        dict con los valores activos (base o ajustados por el usuario), con las mismas
        claves que el escenario original. Útil para pasar a render_madurez().
    """
    ubicacion  = escenario.get("ubicacion", "—")
    capital    = escenario.get("capital", 0.0)
    costo_unit = escenario.get("costo_variable_unitario", 0.0)
    df         = escenario.get("desglose_fijos")
    dv         = escenario.get("desglose_variables")

    # Valores base de la IA (nunca se modifican — son la referencia)
    _base_ingresos  = float(escenario.get("ingresos_estimados_mes", 0.0))
    _base_fijos     = float(escenario.get("costos_fijos_mes", 0.0))
    _base_variables = float(escenario.get("costos_variables_mes", 0.0))
    _base_precio    = float(escenario.get("precio_unitario_promedio", 0.0))

    # ── Cabecera: título + botón ✏️ ───────────────────────────────────────────
    hdr_left, hdr_right = st.columns([8, 2])
    with hdr_left:
        st.subheader(f"📋 Escenario financiero — {ubicacion}")
    with hdr_right:
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        _btn_label = "✅ Ver informe" if modo_edicion else "✏️ Ajustar valores"
        if st.button(_btn_label, key="btn_modo_edicion", use_container_width=True):
            st.session_state["modo_edicion_escenario"] = not modo_edicion
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # BLOQUE 1 — Estado de resultados + BLOQUE 2 — Viabilidad (lado a lado)
    # ══════════════════════════════════════════════════════════════════════════
    pl_col, gap_col, kpi_col = st.columns([5, 1, 4])

    with pl_col:
        titulo_pl = (
            '<div style="font-size:0.7rem;font-weight:700;letter-spacing:.09em;'
            'color:var(--text-color);opacity:0.45;margin-bottom:8px;text-transform:uppercase;">'
        )
        if modo_edicion:
            st.markdown(
                titulo_pl + 'Estado de resultados · ajuste manual</div>',
                unsafe_allow_html=True,
            )

            # ── Modo edición: inputs dentro de la tarjeta ─────────────────────
            st.markdown(
                '<div style="background:var(--secondary-background-color);'
                'border:2px solid #2563eb44;border-radius:14px;padding:20px 24px;">',
                unsafe_allow_html=True,
            )

            inp_col1, inp_col2 = st.columns(2)
            with inp_col1:
                ingresos = st.number_input(
                    "Ingresos estimados",
                    min_value=0.0, step=1000.0,
                    value=_base_ingresos,
                    key="escenario_ingresos",
                    help="Proyección mensual de ventas.",
                )
                fijos = st.number_input(
                    "Costos fijos",
                    min_value=0.0, step=500.0,
                    value=_base_fijos,
                    key="escenario_fijos",
                    help="Renta, nómina base, servicios — independientes del volumen de ventas.",
                )
            with inp_col2:
                variables = st.number_input(
                    "Costos variables",
                    min_value=0.0, step=500.0,
                    value=_base_variables,
                    key="escenario_variables",
                    help="Insumos, comisiones, empaque — proporcionales a las ventas.",
                )
                precio = st.number_input(
                    "Precio unitario promedio",
                    min_value=0.0, step=10.0,
                    value=_base_precio,
                    key="escenario_precio",
                    help="Precio de venta promedio por producto o servicio.",
                )

            # Recalcular con los valores editados
            utilidad = ingresos - fijos - variables
            margen_contrib = precio - costo_unit
            pe = (fijos / margen_contrib) if margen_contrib > 0 else 0.0
            mrc = (capital / utilidad) if utilidad > 0 else None

            # Fila de resultado inline
            color_utilidad = _COLOR_POSITIVO if utilidad >= 0 else _COLOR_NEGATIVO
            delta_utilidad = utilidad - (_base_ingresos - _base_fijos - _base_variables)
            delta_sign = "+" if delta_utilidad >= 0 else ""
            delta_color = _COLOR_POSITIVO if delta_utilidad >= 0 else _COLOR_NEGATIVO
            st.markdown(
                f'<div style="border-top:2px solid rgba(128,128,128,0.2);'
                f'margin-top:8px;padding-top:12px;'
                f'display:flex;justify-content:space-between;align-items:baseline;">'
                f'<span style="font-size:1rem;font-weight:700;color:var(--text-color);">'
                f'Utilidad neta</span>'
                f'<span>'
                f'<span style="font-size:1rem;font-weight:700;color:{color_utilidad};">'
                f'{_fmt_moneda(utilidad)}</span>'
                f'<span style="font-size:0.75rem;color:{delta_color};margin-left:8px;">'
                f'({delta_sign}{_fmt_moneda(delta_utilidad)} vs. IA)</span>'
                f'</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.markdown("</div>", unsafe_allow_html=True)

        else:
            # ── Modo lectura: HTML estático ───────────────────────────────────
            st.markdown(
                titulo_pl + 'Estado de resultados · mensual</div>',
                unsafe_allow_html=True,
            )

            ingresos  = _base_ingresos
            fijos     = _base_fijos
            variables = _base_variables
            precio    = _base_precio

            utilidad = ingresos - fijos - variables
            margen_contrib = precio - costo_unit
            pe  = (fijos / margen_contrib) if margen_contrib > 0 else 0.0
            mrc = (capital / utilidad) if utilidad > 0 else None

            rows_html = _pl_row(
                "Ingresos estimados", _fmt_moneda(ingresos), _COLOR_NEUTRO,
                help_text="Proyección mensual de ventas estimada por la IA para este giro y ubicación.",
            )
            rows_html += _pl_row(
                "Costos fijos", _fmt_moneda(fijos), "var(--text-color)", indent=1,
                help_text="Gastos fijos mensuales que se pagan independientemente de cuánto vendas: renta, nómina base, servicios.",
            )
            if df:
                rows_html += _pl_desglose(df)
            rows_html += _pl_row(
                "Costos variables", _fmt_moneda(variables), "var(--text-color)", indent=1,
                help_text="Gastos que crecen con el volumen de ventas: materia prima, insumos, comisiones.",
            )
            if dv:
                rows_html += _pl_desglose(dv)

            color_utilidad = _COLOR_POSITIVO if utilidad >= 0 else _COLOR_NEGATIVO
            rows_html += _pl_row(
                "Utilidad neta", _fmt_moneda(utilidad), color_utilidad,
                is_total=True,
                help_text="Lo que queda después de restar todos los costos a los ingresos. Si es negativa, el negocio pierde dinero ese mes.",
            )

            st.markdown(
                f'<div style="background:var(--secondary-background-color);'
                f'border:1px solid rgba(128,128,128,0.2);border-radius:14px;'
                f'padding:20px 24px;">'
                f'{rows_html}'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ══════════════════════════════════════════════════════════════════════════
    # BLOQUE 2 — Métricas de viabilidad (siempre recalculadas con valores activos)
    # ══════════════════════════════════════════════════════════════════════════
    with kpi_col:
        st.markdown(
            '<div style="font-size:0.7rem;font-weight:700;letter-spacing:.09em;'
            'color:var(--text-color);opacity:0.45;margin-bottom:8px;text-transform:uppercase;">'
            'Viabilidad</div>',
            unsafe_allow_html=True,
        )

        margen_pct = ((precio - costo_unit) / precio * 100) if precio > 0 else 0.0
        mc_color = _COLOR_POSITIVO if margen_pct >= 40 else (_COLOR_ADVERTENCIA if margen_pct >= 20 else _COLOR_NEGATIVO)

        pe_subtitulo = (
            f"{_fmt_moneda(precio)} precio · {_fmt_moneda(costo_unit)} costo variable"
            if precio > 0 else "Ventas mínimas al mes para cubrir todos los costos"
        )

        st.markdown(
            _kpi_card(
                "📊", "Margen de contribución",
                f"{margen_pct:.1f}%", mc_color,
                subtitulo=f"De cada venta, {margen_pct:.0f}% cubre costos fijos y genera utilidad",
            )
            + _kpi_card(
                "⚖️", "Punto de equilibrio",
                f"{pe:.0f} unidades", "var(--text-color)",
                subtitulo=pe_subtitulo,
            ),
            unsafe_allow_html=True,
        )

    # ── Alerta de utilidad negativa (estructural — la curva también lo reflejará)
    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    if utilidad < 0:
        st.error(
            "⚠️ El escenario muestra **utilidad neta negativa** en régimen estable. "
            "Considera ajustar precios o reducir costos antes de abrir."
        )

    # ── Devolver valores activos para que app.py los pase a render_madurez ───
    return {
        **escenario,
        "ingresos_estimados_mes":  ingresos,
        "costos_fijos_mes":        fijos,
        "costos_variables_mes":    variables,
        "precio_unitario_promedio": precio,
        "utilidad_neta_mes":       utilidad,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 6. render_foda — cuatro columnas HTML/CSS con las listas del FODA
# ──────────────────────────────────────────────────────────────────────────────

def render_foda(foda: dict) -> None:
    """
    Renderiza el análisis FODA en cuatro columnas con el mismo estilo de cards
    que render_recomendacion(). Los items son editables por el usuario.

    Args:
        foda: dict con claves 'fortalezas', 'oportunidades', 'debilidades', 'amenazas'.
             Cada valor es una lista de strings.
    """
    st.subheader("🔍 Análisis FODA")
    st.caption("Puedes editar cada sección del FODA directamente.")

    cols = st.columns(4)
    for col, (clave, meta) in zip(cols, _FODA_META.items()):
        items = foda.get(clave, [])
        color = meta["color"]
        emoji = meta["emoji"]
        label = meta["label"]

        with col:
            # Encabezado de la tarjeta
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
                f'<span style="font-size:1.2rem;">{emoji}</span>'
                f'<span style="font-weight:700;font-size:0.9rem;color:{color};">{label}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            # Área de texto editable — una línea por item
            default_text = "\n".join(items) if items else ""
            edited = st.text_area(
                label=label,
                value=default_text,
                height=160,
                key=f"foda_{clave}",
                label_visibility="collapsed",
                help=f"Un punto por línea",
            )
            # Guardar en session_state para que persista y pueda usarse después
            st.session_state.setdefault("foda_editable", {})[clave] = [
                line.strip() for line in edited.splitlines() if line.strip()
            ]


# ──────────────────────────────────────────────────────────────────────────────
# 8. _calcular_pago_mensual — amortización francesa (helper puro, sin UI)
# ──────────────────────────────────────────────────────────────────────────────

def _calcular_pago_mensual(monto: float, tasa_anual: float, plazo_meses: int) -> tuple[float, float, float]:
    """
    Calcula el pago mensual con amortización francesa.

    Fórmula: pago = monto * (r * (1+r)^n) / ((1+r)^n - 1)
    donde r = tasa_anual / 12 / 100  y  n = plazo_meses

    Returns:
        (pago_mensual, total_pagado, total_intereses)
    """
    plazo = max(1, plazo_meses)
    r = tasa_anual / 12.0 / 100.0
    if r == 0.0:
        pago_mensual = monto / plazo
    else:
        factor = (1 + r) ** plazo
        pago_mensual = monto * (r * factor) / (factor - 1)
    total_pagado = pago_mensual * plazo
    return pago_mensual, total_pagado, total_pagado - monto


# ──────────────────────────────────────────────────────────────────────────────
# 9. render_madurez — curva de maduración del negocio con 3 escenarios
# ──────────────────────────────────────────────────────────────────────────────

import math as _math


def _curva_params(meses_madurez: int, pct_mes1: float) -> float:
    """
    Deriva la tasa k de la curva logística exponencial:
        ventas(t) = ventas_maduras × (1 - e^(-k·t))

    Se calibra para que ventas(meses_madurez) == 95 % de ventas_maduras
    y se verifica que ventas(1) ≈ pct_mes1 / 100 × ventas_maduras.

    En la práctica usamos k resuelto de la condición del 95 %:
        k = -ln(0.05) / meses_madurez
    """
    return _math.log(20.0) / meses_madurez  # ln(1/0.05) = ln(20)


def _flujo_mensual(
    t: int,
    ventas_maduras: float,
    costos_totales: float,
    k: float,
    pct_mes1: float,
) -> tuple[float, float]:
    """
    Devuelve (ingresos_t, utilidad_t) para el mes t (1-based).

    El factor de escala del mes 1 se fuerza a pct_mes1/100 ajustando
    la amplitud de la curva de modo que ventas(1) coincida con el estimado
    de la IA, en lugar de depender puramente de k.

    Estrategia: usar la curva normal pero forzar que el valor en t=1
    sea exactamente pct_mes1/100 × ventas_maduras, interpolando linealmente
    entre pct_mes1 en t=1 y 95% en t=meses_madurez.  Para los meses
    intermedios usamos la curva exponencial re-escalada.
    """
    raw = 1.0 - _math.exp(-k * t)          # curva pura [0, ~0.95]
    raw_mes1 = 1.0 - _math.exp(-k)         # valor puro en t=1
    raw_tmax = 1.0 - _math.exp(-k * (3.0 / k))  # ≈ 0.95

    # Re-escalar para que raw_mes1 → pct_mes1/100 y raw_tmax → 0.95
    p1 = pct_mes1 / 100.0
    p_max = 0.95
    if raw_tmax > raw_mes1:
        factor = (raw - raw_mes1) / (raw_tmax - raw_mes1)
        escala = p1 + (p_max - p1) * factor
    else:
        escala = p1

    escala = max(0.0, min(1.0, escala))
    ingresos_t = ventas_maduras * escala
    utilidad_t = ingresos_t - costos_totales
    return ingresos_t, utilidad_t


# Factores de ajuste para cada escenario
_ESCENARIO_FACTORES = {
    "pesimista":  {"meses_factor": 1.5,  "pct_factor": 0.7},
    "moderado":   {"meses_factor": 1.0,  "pct_factor": 1.0},
    "optimista":  {"meses_factor": 0.65, "pct_factor": 1.4},
}

_ESCENARIO_META = {
    "pesimista": {"label": "🔴 Pesimista",  "color": _COLOR_NEGATIVO,    "bg": "#fee2e2"},
    "moderado":  {"label": "⚪ Moderado",   "color": "#64748b",           "bg": "var(--secondary-background-color)"},
    "optimista": {"label": "🟢 Optimista",  "color": _COLOR_POSITIVO,    "bg": "#dcfce7"},
}


def render_madurez(escenario: dict, deuda: dict | None = None) -> None:
    """
    Muestra la curva de maduración del negocio con tres escenarios seleccionables.

    Si se proporciona `deuda`, el pago mensual calculado con amortización francesa
    se suma a los costos totales en la curva, y se muestra una pill informativa
    con los datos del crédito encima de la gráfica.

    Calcula para cada escenario (pesimista / moderado / optimista):
      - Una curva de ingresos vs costos (+ deuda) mes a mes hasta la madurez + 6 meses buffer
      - El mes de break-even real (primer mes con utilidad > 0)
      - El capital consumido (quemado) antes del break-even
      - La recuperación de inversión real sobre flujo acumulado

    El escenario activo se guarda en st.session_state["escenario_madurez"].

    Args:
        escenario: dict validado por core.scenario_parser.parse_scenario().
                   Requiere las claves: ingresos_estimados_mes, costos_fijos_mes,
                   costos_variables_mes, capital, madurez.
        deuda: dict opcional con monto, tasa_anual, plazo_meses.
               Si es None o monto == 0, la curva se muestra sin deuda.
    """
    st.subheader("📈 Curva de maduración del negocio")
    st.caption(
        "Estimación de cómo evolucionarán los ingresos desde la apertura hasta que el negocio "
        "alcance ventas estabilizadas. Los tres escenarios reflejan distintas velocidades de adopción."
    )

    # ── Datos base ────────────────────────────────────────────────────────────
    ventas_maduras = float(escenario.get("ingresos_estimados_mes", 0.0))
    costos_operativos = (
        float(escenario.get("costos_fijos_mes", 0.0))
        + float(escenario.get("costos_variables_mes", 0.0))
    )
    capital = float(escenario.get("capital", 0.0))
    madurez_data = escenario.get("madurez", {})
    base_meses = int(madurez_data.get("meses_hasta_madurez", 18))
    base_pct   = float(madurez_data.get("porcentaje_ventas_mes1", 25.0))

    # ── Cálculo del pago de deuda (si aplica) ────────────────────────────────
    pago_mensual_deuda = 0.0
    total_intereses_deuda = 0.0
    monto_deuda = 0.0
    plazo_deuda = 0
    tasa_deuda = 0.0
    con_deuda = False

    if deuda:
        monto_deuda = float(deuda.get("monto", 0.0))
        tasa_deuda = float(deuda.get("tasa_anual", 0.0))
        plazo_deuda = int(deuda.get("plazo_meses", 1))
        if monto_deuda > 0:
            pago_mensual_deuda, _, total_intereses_deuda = _calcular_pago_mensual(
                monto_deuda, tasa_deuda, plazo_deuda
            )
            con_deuda = True

    costos_totales = costos_operativos + pago_mensual_deuda

    # ── Pill informativa de deuda (solo si hay crédito activo) ───────────────
    if con_deuda:
        utilidad_madura = ventas_maduras - costos_operativos
        pct_deuda = (pago_mensual_deuda / utilidad_madura * 100) if utilidad_madura > 0 else None
        pct_texto = f" · {pct_deuda:.0f}% de la utilidad madura" if pct_deuda is not None else ""
        deuda_color = _COLOR_NEGATIVO if (pct_deuda or 0) > 40 else _COLOR_ADVERTENCIA
        st.markdown(
            f'<div style="display:inline-flex;align-items:center;gap:8px;'
            f'background:var(--secondary-background-color);'
            f'border:1px solid {deuda_color}55;border-radius:8px;'
            f'padding:6px 14px;margin-bottom:10px;font-size:0.82rem;">'
            f'<span style="color:{deuda_color};font-weight:700;">🏦 Crédito incluido</span>'
            f'<span style="color:var(--text-color);opacity:0.7;">'
            f'{_fmt_moneda(monto_deuda)} · {tasa_deuda:.1f}% anual · {plazo_deuda} meses · '
            f'pago {_fmt_moneda(pago_mensual_deuda)}/mes{pct_texto} · '
            f'intereses totales {_fmt_moneda(total_intereses_deuda)}'
            f'</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Selector de escenario ─────────────────────────────────────────────────
    escenario_activo = st.session_state.get("escenario_madurez", "moderado")

    btn_cols = st.columns(3)
    for col, (key, meta) in zip(btn_cols, _ESCENARIO_META.items()):
        with col:
            btn_type = "primary" if escenario_activo == key else "secondary"
            if st.button(meta["label"], key=f"btn_madurez_{key}", use_container_width=True, type=btn_type):
                st.session_state["escenario_madurez"] = key
                st.rerun()

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

    # ── Calcular curva del escenario activo ───────────────────────────────────
    factores = _ESCENARIO_FACTORES[escenario_activo]
    meses_madurez = max(3, round(base_meses * factores["meses_factor"]))
    pct_mes1      = min(90.0, max(5.0, base_pct * factores["pct_factor"]))

    k = _curva_params(meses_madurez, pct_mes1)
    _HORIZONTE_MAX = 60  # tope absoluto en meses

    # ── Paso 1: calcular KPIs sin límite de horizonte (hasta 60 m) ───────────
    _n_calculo = min(_HORIZONTE_MAX, meses_madurez + 6)
    # Extendemos temporalmente hasta el tope para encontrar mes_recuperacion
    _meses_calc   = list(range(1, _HORIZONTE_MAX + 1))
    _utilidad_calc = [
        _flujo_mensual(t, ventas_maduras, costos_totales, k, pct_mes1)[1]
        for t in _meses_calc
    ]

    mes_breakeven = next((t for t, u in zip(_meses_calc, _utilidad_calc) if u >= 0), None)

    if mes_breakeven is not None:
        capital_quemado = abs(sum(u for u in _utilidad_calc[:mes_breakeven - 1] if u < 0))
    else:
        capital_quemado = abs(sum(u for u in _utilidad_calc if u < 0))

    flujo_acumulado = 0.0
    mes_recuperacion = None
    for t, u in zip(_meses_calc, _utilidad_calc):
        flujo_acumulado += u
        if flujo_acumulado >= capital and mes_recuperacion is None:
            mes_recuperacion = t

    # ── Paso 2: fijar horizonte de la gráfica ────────────────────────────────
    # Si la recuperación ocurre antes del tope, extender hasta ahí + 2 meses
    # de margen visual. Si no ocurre, usar el horizonte base topado en 60.
    _horizonte_base = meses_madurez + 6
    if mes_recuperacion is not None:
        n_meses = min(_HORIZONTE_MAX, max(_horizonte_base, mes_recuperacion + 2))
    else:
        n_meses = min(_HORIZONTE_MAX, _horizonte_base)

    meses      = list(range(1, n_meses + 1))
    ingresos_v = []
    utilidad_v = []
    for t in meses:
        ing, util = _flujo_mensual(t, ventas_maduras, costos_totales, k, pct_mes1)
        ingresos_v.append(ing)
        utilidad_v.append(util)

    costos_v = [costos_totales] * n_meses

    # ── Gráfica Plotly ────────────────────────────────────────────────────────
    fig = go.Figure()

    # Línea de costos totales (operativos + deuda si aplica)
    costos_label = "Costos + deuda" if con_deuda else "Costos totales"
    fig.add_trace(go.Scatter(
        x=meses, y=costos_v,
        mode="lines",
        name=costos_label,
        line=dict(color=_COLOR_NEGATIVO, width=2, dash="dot"),
        fill=None,
    ))

    # Si hay deuda, añadir línea de costos solo operativos como referencia
    if con_deuda:
        costos_op_v = [costos_operativos] * n_meses
        fig.add_trace(go.Scatter(
            x=meses, y=costos_op_v,
            mode="lines",
            name="Costos operativos",
            line=dict(color=_COLOR_ADVERTENCIA, width=1, dash="dot"),
            fill=None,
        ))

    # Curva de ingresos
    fig.add_trace(go.Scatter(
        x=meses, y=ingresos_v,
        mode="lines",
        name="Ingresos proyectados",
        line=dict(color=_COLOR_NEUTRO, width=3),
        fill="tonexty",
        fillcolor="rgba(220,38,38,0.08)",
    ))

    # Línea de ingresos maduros (referencia)
    fig.add_hline(
        y=ventas_maduras,
        line_dash="dot",
        line_color="#94a3b8",
        annotation_text=f"Ventas maduras: {_fmt_moneda(ventas_maduras)}/mes",
        annotation_position="top left",
        annotation_font_size=11,
        annotation_font_color="#94a3b8",
    )

    # Línea vertical de break-even
    if mes_breakeven is not None:
        fig.add_vline(
            x=mes_breakeven,
            line_dash="dash",
            line_color=_COLOR_POSITIVO,
            annotation_text=f"Break-even: mes {mes_breakeven}",
            annotation_position="top right",
            annotation_font_size=11,
            annotation_font_color=_COLOR_POSITIVO,
        )

    # Línea vertical de recuperación de inversión (si cae dentro del horizonte)
    if mes_recuperacion is not None and mes_recuperacion <= n_meses:
        fig.add_vline(
            x=mes_recuperacion,
            line_dash="dash",
            line_color=_COLOR_NEUTRO,
            annotation_text=f"Recuperación: mes {mes_recuperacion}",
            annotation_position="bottom right",
            annotation_font_size=11,
            annotation_font_color=_COLOR_NEUTRO,
        )

    meta_activa = _ESCENARIO_META[escenario_activo]
    fig.update_layout(
        xaxis=dict(
            title="Mes de operación",
            tickmode="linear",
            dtick=max(1, n_meses // 12),
            gridcolor="rgba(128,128,128,0.15)",
        ),
        yaxis=dict(
            title="MXN / mes",
            tickformat="$,.0f",
            gridcolor="rgba(128,128,128,0.15)",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=360,
        margin=dict(t=50, b=50, l=80, r=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="-apple-system, 'Segoe UI', sans-serif"),
        hoverlabel=dict(
            bgcolor="#1e293b",
            font_color="#f8fafc",
            font_size=12,
            bordercolor="#1e293b",
        ),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── KPI cards ─────────────────────────────────────────────────────────────
    k1, k2, k3 = st.columns(3)

    with k1:
        if mes_breakeven is not None:
            be_color = _COLOR_POSITIVO if mes_breakeven <= 12 else (_COLOR_ADVERTENCIA if mes_breakeven <= 24 else _COLOR_NEGATIVO)
            be_texto = f"Mes {mes_breakeven}"
        else:
            be_color = _COLOR_NEGATIVO
            be_texto = "No alcanzado"
        st.markdown(
            _kpi_card(
                "🎯", "Break-even real",
                be_texto, be_color,
                subtitulo="Primer mes con ingresos > costos" + (" + deuda" if con_deuda else ""),
            ),
            unsafe_allow_html=True,
        )

    with k2:
        cq_color = _COLOR_NEGATIVO if capital_quemado > capital * 0.5 else _COLOR_ADVERTENCIA
        alcanza = "⚠️ Capital insuficiente" if capital_quemado > capital else f"Cubre {capital_quemado/capital*100:.0f}% del capital"
        st.markdown(
            _kpi_card(
                "🔥", "Capital en riesgo (rampa)",
                _fmt_moneda(capital_quemado), cq_color,
                subtitulo=alcanza,
            ),
            unsafe_allow_html=True,
        )

    with k3:
        if mes_recuperacion is not None:
            rec_color = _COLOR_POSITIVO if mes_recuperacion <= 24 else _COLOR_ADVERTENCIA
            rec_texto = f"Mes {mes_recuperacion}"
            rec_sub = "Flujo acumulado real" + (" · deuda incluida" if con_deuda else "")
        else:
            rec_color = _COLOR_NEGATIVO
            rec_texto = "> 60 meses"
            rec_sub = "No se recupera dentro del horizonte máximo proyectado"
        st.markdown(
            _kpi_card(
                "💰", "Recuperación real de inversión",
                rec_texto, rec_color,
                subtitulo=rec_sub,
            ),
            unsafe_allow_html=True,
        )

    # ── Alerta narrativa ──────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
    if capital_quemado > capital:
        st.error(
            f"⚠️ En el escenario **{meta_activa['label']}**, el negocio necesita absorber "
            f"**{_fmt_moneda(capital_quemado)}** antes de ser rentable, "
            f"pero el capital disponible es solo **{_fmt_moneda(capital)}**. "
            "Considera reducir costos, conseguir financiamiento adicional o revisar el precio."
        )
    elif mes_breakeven is None:
        st.error(
            "⚠️ En este escenario el negocio no alcanza el break-even dentro del horizonte proyectado."
        )
    elif mes_breakeven > 18:
        st.warning(
            f"⚠️ En el escenario **{meta_activa['label']}**, el negocio tardará **{mes_breakeven} meses** "
            "en ser rentable. Asegúrate de tener reservas suficientes para ese período."
        )
    elif mes_recuperacion is None:
        st.warning(
            f"⚠️ En el escenario **{meta_activa['label']}**, el negocio alcanza el break-even en el "
            f"**mes {mes_breakeven}** pero no recupera la inversión completa en los primeros 60 meses proyectados."
        )
    else:
        st.success(
            f"✅ En el escenario **{meta_activa['label']}**, el negocio alcanza el break-even en el "
            f"**mes {mes_breakeven}** y recupera la inversión completa en el **mes {mes_recuperacion}**."
        )

    # ── Nota de supuestos ─────────────────────────────────────────────────────
    st.markdown(
        f'<div style="font-size:0.75rem;color:var(--text-color);opacity:0.45;margin-top:8px;">'
        f'ⓘ Supuestos de maduración (escenario {escenario_activo}): '
        f'{meses_madurez} meses hasta ventas estables · '
        f'arranque en {pct_mes1:.0f}% de las ventas maduras · '
        f'costos fijos desde el mes 1'
        + (f' · pago de deuda {_fmt_moneda(pago_mensual_deuda)}/mes incluido' if con_deuda else '')
        + f'.</div>',
        unsafe_allow_html=True,
    )
