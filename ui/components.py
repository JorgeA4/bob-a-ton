import streamlit as st
import plotly.graph_objects as go

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

NIVEL_COLOR = {
    "muy alto": "🟢",
    "alto": "🔵",
    "medio": "🟡",
    "bajo": "🔴",
}


def _puntaje(ubicacion: dict, clave: str) -> int:
    """Extrae el puntaje de un criterio de forma segura."""
    return ubicacion.get("criterios", {}).get(clave, {}).get("puntaje", 0)


def _nivel(ubicacion: dict, clave: str) -> str:
    nivel = ubicacion.get("criterios", {}).get(clave, {}).get("nivel", "")
    emoji = NIVEL_COLOR.get(nivel.lower(), "⚪")
    return f"{emoji} {nivel}"


def render_tabla(ubicaciones: list) -> None:
    """Tabla comparativa: filas = criterios, columnas = ubicaciones."""
    st.subheader("📊 Tabla comparativa")

    nombres = [u.get("nombre", f"Ubicación {i+1}") for i, u in enumerate(ubicaciones)]
    totales = [u.get("puntaje_total", 0) for u in ubicaciones]

    # Cabecera con nombre + puntaje total
    headers = ["Criterio"] + [f"{n}\n**{t}/90**" for n, t in zip(nombres, totales)]

    rows = []
    for clave, label in CRITERIOS_LABELS.items():
        fila = [label]
        for u in ubicaciones:
            puntaje = _puntaje(u, clave)
            nivel = _nivel(u, clave)
            fila.append(f"{puntaje}/10  {nivel}")
        rows.append(fila)

    # Fila de totales al final
    rows.append(["**TOTAL**"] + [f"**{t}/90**" for t in totales])

    import pandas as pd
    df = pd.DataFrame(rows, columns=headers)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_grafico(ubicaciones: list) -> None:
    """Gráfico de barras agrupadas: puntaje por criterio por ubicación."""
    st.subheader("📈 Comparativa por criterio")

    criterios = list(CRITERIOS_LABELS.values())
    claves = list(CRITERIOS_LABELS.keys())

    fig = go.Figure()
    for u in ubicaciones:
        nombre = u.get("nombre", "—")
        puntajes = [_puntaje(u, c) for c in claves]
        fig.add_trace(go.Bar(name=nombre, x=criterios, y=puntajes))

    fig.update_layout(
        barmode="group",
        yaxis=dict(range=[0, 10], title="Puntaje"),
        xaxis=dict(tickangle=-25),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420,
        margin=dict(t=40, b=80),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_recomendacion(ubicaciones: list) -> None:
    """Tarjetas con la recomendación de la IA por ubicación, ordenadas por puntaje."""
    st.subheader("💡 Recomendaciones de la IA")

    ordenadas = sorted(ubicaciones, key=lambda u: u.get("puntaje_total", 0), reverse=True)

    for i, u in enumerate(ordenadas):
        nombre = u.get("nombre", "—")
        total = u.get("puntaje_total", 0)
        descripcion = u.get("descripcion_breve", "")
        recomendacion = u.get("recomendacion_ia", "Sin recomendación.")

        medalla = ["🥇", "🥈", "🥉", "4️⃣"][i] if i < 4 else f"{i+1}."
        with st.expander(f"{medalla} {nombre} — {total}/90 puntos", expanded=(i == 0)):
            if descripcion:
                st.caption(descripcion)
            st.info(recomendacion)
