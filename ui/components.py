import streamlit as st
import plotly.graph_objects as go

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

# Niveles → color CSS + emoji
NIVEL_META = {
    "muy alto": {"emoji": "🟢", "color": "#16a34a", "bg": "#dcfce7", "label": "Muy alto"},
    "alto":     {"emoji": "🔵", "color": "#2563eb", "bg": "#dbeafe", "label": "Alto"},
    "medio":    {"emoji": "🟡", "color": "#d97706", "bg": "#fef9c3", "label": "Medio"},
    "bajo":     {"emoji": "🔴", "color": "#dc2626", "bg": "#fee2e2", "label": "Bajo"},
}

# Paleta corporativa para las 5 ubicaciones (coincide en tabla y gráfico)
LOCATION_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444"]

MEDALLAS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────────────────────────────────────

def _puntaje(ubicacion: dict, clave: str) -> int:
    """Extrae el puntaje de un criterio de forma segura."""
    return ubicacion.get("criterios", {}).get(clave, {}).get("puntaje", 0)


def _nivel_raw(ubicacion: dict, clave: str) -> str:
    return ubicacion.get("criterios", {}).get(clave, {}).get("nivel", "").lower()


def _badge(nivel_raw: str, puntaje: int) -> str:
    """Devuelve un <span> HTML estilizado para el nivel/puntaje de un criterio."""
    meta = NIVEL_META.get(nivel_raw, {"color": "#6b7280", "bg": "#f3f4f6", "label": nivel_raw.title() or "—"})
    return (
        f'<span style="display:inline-flex;align-items:center;gap:4px;'
        f'background:{meta["bg"]};color:{meta["color"]};'
        f'border:1px solid {meta["color"]}33;'
        f'border-radius:6px;padding:2px 8px;font-size:0.78rem;font-weight:600;white-space:nowrap;">'
        f'{puntaje}/10&nbsp;{meta["label"]}'
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

def _render_leyenda() -> None:
    """Leyenda visual que explica los colores de nivel."""
    items_html = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'background:{m["bg"]};color:{m["color"]};border:1px solid {m["color"]}44;'
        f'border-radius:20px;padding:4px 12px;font-size:0.78rem;font-weight:600;">'
        f'{m["emoji"]} {m["label"]}</span>'
        for m in NIVEL_META.values()
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
            f'<div style="font-weight:700;color:{color};font-size:0.9rem;margin-bottom:4px;">{nombre}</div>'
            f'{_score_badge(total, color)}'
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
            cells += f'<td style="text-align:center;padding:8px 12px;background:{bg};">{_badge(n, p)}</td>'
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
            x=criterios,
            y=puntajes,
            marker_color=color,
            marker_line_color=color,
            marker_line_width=0,
            opacity=0.88,
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover_texts,
        ))

    fig.update_layout(
        barmode="group",
        yaxis=dict(
            range=[0, 10],
            title="Puntaje (1–10)",
            gridcolor="rgba(128,128,128,0.2)",
            tickfont=dict(size=11),
        ),
        xaxis=dict(
            tickangle=-25,
            tickfont=dict(size=11),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12),
        ),
        height=430,
        margin=dict(t=50, b=90, l=50, r=20),
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
    fig.add_hline(
        y=7,
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
# 5. render_escenario — tarjetas de métricas del escenario base
# ──────────────────────────────────────────────────────────────────────────────

def render_escenario(escenario: dict) -> None:
    """
    Muestra las métricas clave del escenario financiero en st.metric cards.
    No recalcula — muestra los valores tal como los devolvió parse_scenario().

    Args:
        escenario: dict validado devuelto por core.scenario_parser.parse_scenario().
    """
    ubicacion = escenario.get("ubicacion", "—")
    st.subheader(f"📋 Escenario financiero — {ubicacion}")

    utilidad = escenario.get("utilidad_neta_mes", 0.0)
    mrc = escenario.get("meses_recuperacion_capital")

    # Fila 1: ingresos, costos fijos, costos variables, utilidad neta
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "💰 Ingresos estimados / mes",
            _fmt_moneda(escenario.get("ingresos_estimados_mes", 0.0)),
        )
    with col2:
        st.metric(
            "🏢 Costos fijos / mes",
            _fmt_moneda(escenario.get("costos_fijos_mes", 0.0)),
        )
    with col3:
        st.metric(
            "📦 Costos variables / mes",
            _fmt_moneda(escenario.get("costos_variables_mes", 0.0)),
        )
    with col4:
        color_utilidad = _COLOR_POSITIVO if utilidad >= 0 else _COLOR_NEGATIVO
        st.markdown(
            f'<div style="background:var(--secondary-background-color);border-radius:8px;padding:12px 16px;">'
            f'<div style="font-size:0.85rem;color:var(--text-color);opacity:0.7;margin-bottom:4px;">📈 Utilidad neta / mes</div>'
            f'<div style="font-size:1.6rem;font-weight:700;color:{color_utilidad};">'
            f'{_fmt_moneda(utilidad)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

    # Fila 2: punto de equilibrio, recuperación, precio unitario, margen
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric(
            "⚖️ Punto de equilibrio",
            f"{escenario.get('punto_equilibrio_unidades', 0.0):.0f} unidades/mes",
        )
    with col6:
        st.metric(
            "⏱️ Recuperación del capital",
            _fmt_meses(mrc),
        )
    with col7:
        st.metric(
            "🏷️ Precio unitario promedio",
            _fmt_moneda(escenario.get("precio_unitario_promedio", 0.0)),
        )
    with col8:
        precio = escenario.get("precio_unitario_promedio", 0.0)
        costo_unit = escenario.get("costo_variable_unitario", 0.0)
        margen_pct = ((precio - costo_unit) / precio * 100) if precio > 0 else 0.0
        st.metric(
            "📊 Margen de contribución",
            f"{margen_pct:.1f}%",
        )

    # Alerta visual si utilidad es negativa
    if utilidad < 0:
        st.error(
            "⚠️ El escenario muestra **utilidad neta negativa**. "
            "Considera ajustar precios o reducir costos antes de abrir."
        )
    elif mrc is not None and mrc > 24:
        st.warning(
            f"⚠️ La recuperación del capital tomará **{_fmt_meses(mrc)}** — "
            "más de 2 años. Evalúa si el capital es suficiente."
        )


# ──────────────────────────────────────────────────────────────────────────────
# 6. render_metricas — recálculo en tiempo real con ajustes del usuario
# ──────────────────────────────────────────────────────────────────────────────

def render_metricas(escenario: dict, ajustes: dict) -> None:
    """
    Muestra métricas financieras recalculadas con los overrides del usuario.
    Toda la aritmética ocurre aquí — app.py solo pasa los valores de los controles.

    Args:
        escenario: dict base devuelto por parse_scenario().
        ajustes: dict con claves opcionales que sobreescriben el escenario base:
            - "ingresos_estimados_mes": float
            - "costos_fijos_mes": float
            - "costos_variables_mes": float
            - "precio_unitario_promedio": float
    """
    # Aplicar overrides encima del escenario base
    ingresos = float(ajustes.get("ingresos_estimados_mes",
                                  escenario.get("ingresos_estimados_mes", 0.0)))
    fijos = float(ajustes.get("costos_fijos_mes",
                               escenario.get("costos_fijos_mes", 0.0)))
    variables = float(ajustes.get("costos_variables_mes",
                                   escenario.get("costos_variables_mes", 0.0)))
    precio = float(ajustes.get("precio_unitario_promedio",
                                escenario.get("precio_unitario_promedio", 0.0)))

    costo_unit = escenario.get("costo_variable_unitario", 0.0)
    capital = escenario.get("capital", 0.0)

    # Recálculo
    utilidad = ingresos - fijos - variables
    margen_contrib = precio - costo_unit
    pe_unidades = (fijos / margen_contrib) if margen_contrib > 0 else None
    mrc = (capital / utilidad) if utilidad > 0 else None
    margen_pct = (margen_contrib / precio * 100) if precio > 0 else 0.0

    st.markdown(
        '<div style="background:var(--secondary-background-color);border:1px solid rgba(128,128,128,0.2);border-radius:12px;'
        'padding:20px 24px;margin-top:8px;">'
        '<div style="font-weight:700;color:var(--text-color);font-size:0.95rem;margin-bottom:14px;">'
        '🔄 Métricas recalculadas con tus ajustes</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        base_utilidad = escenario.get("utilidad_neta_mes", 0.0)
        delta_utilidad = utilidad - base_utilidad
        st.metric(
            "Utilidad neta / mes",
            _fmt_moneda(utilidad),
            delta=f"{'+' if delta_utilidad >= 0 else ''}{_fmt_moneda(delta_utilidad)}",
        )
    with c2:
        st.metric(
            "Punto de equilibrio",
            f"{pe_unidades:.0f} u/mes" if pe_unidades is not None else "N/A",
        )
    with c3:
        st.metric(
            "Recuperación del capital",
            _fmt_meses(mrc),
        )
    with c4:
        st.metric(
            "Margen de contribución",
            f"{margen_pct:.1f}%",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    if utilidad < 0:
        st.error("⚠️ Con estos ajustes la utilidad es **negativa**.")
    elif utilidad == 0:
        st.warning("⚖️ Con estos ajustes el negocio **solo cubre costos** — sin utilidad.")


# ──────────────────────────────────────────────────────────────────────────────
# 7. render_foda — cuatro columnas HTML/CSS con las listas del FODA
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
# 8. render_deuda — amortización francesa + métricas actualizadas con deuda
# ──────────────────────────────────────────────────────────────────────────────

def render_deuda(escenario: dict, deuda: dict) -> None:
    """
    Calcula el pago mensual con amortización francesa y muestra métricas
    financieras actualizadas considerando el servicio de deuda.

    Args:
        escenario: dict base de parse_scenario().
        deuda: dict con:
            - "monto": float  — monto del crédito en MXN
            - "tasa_anual": float  — tasa de interés anual en % (ej. 18.0)
            - "plazo_meses": int  — número de mensualidades

    Fórmula de amortización francesa:
        pago = monto * (r * (1 + r)^n) / ((1 + r)^n - 1)
        donde r = tasa_anual / 12 / 100  y  n = plazo_meses
    """
    st.subheader("🏦 Escenario con financiamiento")

    monto = float(deuda.get("monto", 0.0))
    tasa_anual = float(deuda.get("tasa_anual", 0.0))
    plazo = int(deuda.get("plazo_meses", 1))

    # ── Cálculo de amortización francesa ────────────────────────────────────
    if plazo < 1:
        plazo = 1

    r = tasa_anual / 12.0 / 100.0  # tasa mensual como decimal

    if r == 0.0:
        # Sin interés: pago lineal
        pago_mensual = monto / plazo
    else:
        factor = (1 + r) ** plazo
        pago_mensual = monto * (r * factor) / (factor - 1)

    total_pagado = pago_mensual * plazo
    total_intereses = total_pagado - monto

    # ── Métricas con deuda ───────────────────────────────────────────────────
    ingresos = escenario.get("ingresos_estimados_mes", 0.0)
    fijos = escenario.get("costos_fijos_mes", 0.0)
    variables = escenario.get("costos_variables_mes", 0.0)
    capital = escenario.get("capital", 0.0)

    utilidad_sin_deuda = ingresos - fijos - variables
    utilidad_con_deuda = utilidad_sin_deuda - pago_mensual
    mrc_con_deuda = (capital / utilidad_con_deuda) if utilidad_con_deuda > 0 else None

    # ── Resumen del crédito ──────────────────────────────────────────────────
    _label_style = 'font-size:0.75rem;color:var(--text-color);opacity:0.6;'
    _val_style = f'font-weight:700;font-size:1rem;color:var(--text-color);'
    st.markdown(
        f'<div style="background:var(--secondary-background-color);border:1px solid rgba(128,128,128,0.2);border-radius:12px;'
        f'padding:18px 24px;margin-bottom:16px;">'
        f'<div style="font-weight:700;color:var(--text-color);font-size:0.9rem;margin-bottom:10px;">'
        f'📄 Resumen del crédito</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:24px;">'
        f'<div><div style="{_label_style}">Monto solicitado</div>'
        f'<div style="{_val_style}">{_fmt_moneda(monto)}</div></div>'
        f'<div><div style="{_label_style}">Tasa anual</div>'
        f'<div style="{_val_style}">{tasa_anual:.2f}%</div></div>'
        f'<div><div style="{_label_style}">Plazo</div>'
        f'<div style="{_val_style}">{plazo} meses</div></div>'
        f'<div><div style="{_label_style}">Pago mensual</div>'
        f'<div style="font-weight:700;font-size:1rem;color:#2563eb;">{_fmt_moneda(pago_mensual)}</div></div>'
        f'<div><div style="{_label_style}">Total intereses</div>'
        f'<div style="font-weight:700;font-size:1rem;color:#d97706;">{_fmt_moneda(total_intereses)}</div></div>'
        f'<div><div style="{_label_style}">Total a pagar</div>'
        f'<div style="{_val_style}">{_fmt_moneda(total_pagado)}</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # ── Impacto en utilidad ──────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(
            "Utilidad sin deuda / mes",
            _fmt_moneda(utilidad_sin_deuda),
        )
    with c2:
        delta_val = utilidad_con_deuda - utilidad_sin_deuda
        st.metric(
            "Utilidad con deuda / mes",
            _fmt_moneda(utilidad_con_deuda),
            delta=f"{_fmt_moneda(delta_val)}",
        )
    with c3:
        st.metric(
            "Recuperación con deuda",
            _fmt_meses(mrc_con_deuda),
        )

    if utilidad_con_deuda < 0:
        st.error(
            "⚠️ El pago mensual de la deuda hace que la utilidad sea **negativa**. "
            "Considera un monto menor, plazo mayor o reducir costos."
        )
    elif pago_mensual > utilidad_sin_deuda * 0.4:
        st.warning(
            f"⚠️ El pago mensual ({_fmt_moneda(pago_mensual)}) representa más del 40 % "
            "de la utilidad — nivel de deuda alto."
        )
