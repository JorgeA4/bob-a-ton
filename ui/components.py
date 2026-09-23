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

# Paleta corporativa para las 4 ubicaciones (coincide en tabla y gráfico)
LOCATION_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"]

MEDALLAS = ["🥇", "🥈", "🥉", "4️⃣"]


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
        'background:#f3f4f6;color:#6b7280;border:1px solid #d1d5db;'
        'border-radius:20px;padding:4px 12px;font-size:0.78rem;font-weight:600;">'
        '⚪ Sin datos</span>'
    )
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;gap:8px;'
        f'background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;'
        f'padding:12px 16px;margin-bottom:16px;">'
        f'<span style="font-size:0.78rem;color:#64748b;font-weight:600;'
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
    header_cells = '<th style="min-width:140px;text-align:left;padding:10px 14px;font-weight:700;color:#1e293b;">Criterio</th>'
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
        bg = "#ffffff" if row_idx % 2 == 0 else "#f8fafc"
        cells = f'<td style="padding:10px 14px;font-weight:600;color:#374151;background:{bg};">{label}</td>'
        for u in ubicaciones:
            p = _puntaje(u, clave)
            n = _nivel_raw(u, clave)
            cells += f'<td style="text-align:center;padding:8px 12px;background:{bg};">{_badge(n, p)}</td>'
        body_rows += f"<tr>{cells}</tr>"

    # ── Fila de totales ──────────────────────────────────────────────────────
    total_cells = '<td style="padding:10px 14px;font-weight:800;color:#0f172a;background:#f1f5f9;">TOTAL</td>'
    for i, total in enumerate(totales):
        color = LOCATION_COLORS[i % len(LOCATION_COLORS)]
        total_cells += (
            f'<td style="text-align:center;padding:10px 12px;background:#f1f5f9;">'
            f'{_score_badge(total, color)}</td>'
        )
    body_rows += f"<tr>{total_cells}</tr>"

    # ── Tabla completa ───────────────────────────────────────────────────────
    table_html = f"""
    <div style="overflow-x:auto;border-radius:12px;border:1px solid #e2e8f0;
                box-shadow:0 1px 4px rgba(0,0,0,0.06);margin-bottom:8px;">
      <table style="width:100%;border-collapse:collapse;font-family:-apple-system,'Segoe UI',sans-serif;font-size:0.87rem;">
        <thead>
          <tr style="background:#f1f5f9;border-bottom:2px solid #e2e8f0;">
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
            gridcolor="#f1f5f9",
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
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
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
                f"background:#ffffff;border-radius:16px;"
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
                f"background:#ffffff;border-radius:14px;"
                f"border:1px solid #e2e8f0;"
                f"box-shadow:0 2px 8px rgba(0,0,0,0.06);"
                f"padding:20px;position:relative;"
            )
            badge_top = ""

        # Barra de progreso del puntaje total
        pct = round((total / 90) * 100)
        progress_bar = (
            f'<div style="background:#f1f5f9;border-radius:99px;height:6px;margin:10px 0 14px;">'
            f'<div style="background:{color};width:{pct}%;height:6px;border-radius:99px;"></div>'
            f'</div>'
        )

        # Descripción breve (si existe)
        desc_html = (
            f'<p style="color:#64748b;font-size:0.82rem;margin:0 0 10px;line-height:1.5;">{descripcion}</p>'
            if descripcion else ""
        )

        # Texto de recomendación
        rec_html = (
            f'<div style="background:#f8fafc;border-left:3px solid {color};'
            f'border-radius:0 8px 8px 0;padding:10px 14px;'
            f'color:#374151;font-size:0.85rem;line-height:1.6;">'
            f'{recomendacion}</div>'
        )

        cards_html += (
            f'<div style="{card_style}">'
            f'{badge_top}'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">'
            f'<span style="font-size:1.6rem;">{medalla}</span>'
            f'<div>'
            f'<div style="font-weight:700;font-size:1rem;color:#0f172a;">{nombre}</div>'
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
