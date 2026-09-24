import streamlit as st

from ai.gemini_client import get_locations
from core.parser import parse_response
# ── TEST: quitar estas dos líneas cuando ya no se necesiten ──────────────────
from tests.mock_client import get_mock_locations, get_mock_scenario
# ─────────────────────────────────────────────────────────────────────────────
from ui.components import (
    render_tabla,
    render_grafico,
    render_recomendacion,
    # Fase 2
    render_escenario,
    render_metricas,
    render_foda,
    render_deuda,
)

# Fase 2 — imports de scenario (no afectan Fase 1 si el módulo existe)
from ai.scenario_client import get_scenario
from core.scenario_parser import parse_scenario

# ──────────────────────────────────────────────────────────────────────────────
# Configuración de página
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Analizador de ubicaciones",
    page_icon="📍",
    layout="wide",
)

# ──────────────────────────────────────────────────────────────────────────────
# CSS global — tipografía, bordes, botón corporativo con hover
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Fuente moderna y fondo general ─────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: -apple-system, "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
    }

    /* ── Contenedores redondeados con más padding ────────────────────────── */
    section[data-testid="stVerticalBlock"] > div {
        border-radius: 12px;
    }

    /* ── Formulario: card elevada — usa variables para dark mode ─────────── */
    [data-testid="stForm"] {
        background: var(--secondary-background-color);
        border: 1px solid var(--text-color-05, rgba(128,128,128,0.2));
        border-radius: 16px;
        padding: 28px 32px !important;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
    }

    /* ── Inputs de texto y número ────────────────────────────────────────── */
    input[type="text"], input[type="number"] {
        border-radius: 8px !important;
        border: 1px solid #d1d5db !important;
        padding: 8px 12px !important;
        font-size: 0.9rem !important;
        transition: border-color .2s, box-shadow .2s;
    }
    input[type="text"]:focus, input[type="number"]:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
    }

    /* ── Botón principal: azul corporativo con efecto hover ─────────────── */
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stFormSubmitButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
        padding: 12px 28px !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.30) !important;
        transition: background .2s, box-shadow .2s, transform .1s !important;
        cursor: pointer !important;
    }
    [data-testid="stFormSubmitButton"] button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.40) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="stFormSubmitButton"] button:active {
        transform: translateY(0px) !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25) !important;
    }

    /* ── Subtítulos de sección ───────────────────────────────────────────── */
    h3 {
        font-weight: 700 !important;
        color: var(--text-color) !important;
        margin-top: 32px !important;
    }

    /* ── Alerta de éxito ─────────────────────────────────────────────────── */
    [data-testid="stAlert"][data-baseweb="notification"] {
        border-radius: 10px !important;
    }

    /* ── Spinner ──────────────────────────────────────────────────────────── */
    [data-testid="stSpinner"] {
        font-size: 0.9rem !important;
        color: #3b82f6 !important;
    }

    /* ── Separadores — usa variable para dark mode ────────────────────────── */
    hr {
        border: none !important;
        border-top: 1px solid rgba(128,128,128,0.25) !important;
        margin: 24px 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Encabezado hero
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="padding:32px 0 24px;border-bottom:1px solid rgba(128,128,128,0.25);margin-bottom:28px;">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
        <span style="font-size:2rem;">📍</span>
        <h1 style="margin:0;font-size:1.75rem;font-weight:800;color:var(--text-color);
                   font-family:-apple-system,'Segoe UI',sans-serif;">
          Analizador de ubicaciones <span style="color:#2563eb;">para tu negocio</span>
        </h1>
      </div>
      <p style="margin:0;color:var(--text-color);opacity:0.6;font-size:0.95rem;padding-left:52px;">
        Ingresa los datos de tu negocio y la IA evaluará las mejores zonas de la ciudad.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Formulario de entrada (Fase 1)
# ──────────────────────────────────────────────────────────────────────────────
form_col, img_col = st.columns([1, 1], gap="large")

_GIROS = [
    "Restaurante / Cafetería",
    "Tienda de ropa",
    "Abarrotes / Supermercado",
    "Gimnasio",
    "Estética / Barbería",
    "Papelería",
    "Farmacia",
    "Consultorio médico",
    "Taller mecánico",
    "Ferretería",
    "Zapatería",
    "Panadería / Pastelería",
    "Lavandería",
    "Floristería",
    "Librería",
    "Joyería / Relojería",
    "Óptica",
    "Veterinaria",
    "Artículos deportivos",
    "Electrónica / Celulares",
]

_CIUDADES = [
    "Tijuana",
    "Mexicali",
    "Ensenada",
    "Ciudad de México",
    "Guadalajara",
    "Monterrey",
    "Puebla",
    "Querétaro",
    "Cancún",
    "León",
    "Mérida",
    "San Luis Potosí",
    "Chihuahua",
    "Aguascalientes",
    "Hermosillo",
    "Morelia",
    "Toluca",
    "Saltillo",
    "Culiacán",
    "Veracruz",
]

with form_col:
    with st.form("form_negocio"):
        giro = st.selectbox(
            "Giro del negocio",
            options=_GIROS,
            index=None,
            placeholder="Escribe o selecciona...",
        )
        capital = st.number_input("Capital inicial (MXN)", min_value=1, step=5000, value=100000)
        ciudad = st.selectbox(
            "Ciudad",
            options=_CIUDADES,
            index=None,
            placeholder="Escribe o selecciona...",
        )
        zona_preferida = st.text_input(
            "Zona de interés (opcional)",
            placeholder="Ej. Zona Río, Centro Histórico",
            help="Si ya tienes una zona en mente, la IA la evaluará junto con las demás.",
        )
        submitted = st.form_submit_button("🔍 Analizar ubicaciones", use_container_width=True)

with img_col:
    st.markdown(
        """
        <div style="
            height:220px;
            background:var(--secondary-background-color);
            border:2px dashed rgba(59,130,246,0.5);
            border-radius:16px;
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:center;
            gap:10px;
            color:#3b82f6;
        ">
            <span style="font-size:3rem;">🗺️</span>
            <span style="font-weight:600;font-size:0.95rem;color:var(--text-color);">Imagen orientativa</span>
            <span style="font-size:0.8rem;color:var(--text-color);opacity:0.5;">placeholder</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── TEST — Botón de datos de ejemplo (quitar bloque completo cuando no se use)
st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
if st.button("🧪 Cargar datos de ejemplo (test)", type="secondary"):
    from core.parser import parse_response as _pr
    _raw = get_mock_locations()
    _ubs = _pr(_raw)
    st.session_state["ubicaciones"] = _ubs
    st.session_state["giro"] = "Cafetería"
    st.session_state["capital"] = 150000
    st.session_state["ciudad"] = "Tijuana"
    st.session_state["zona_preferida"] = ""
    for key in ("escenario", "ubicacion_elegida", "mostrar_ajustes",
                "mostrar_foda", "mostrar_deuda"):
        st.session_state.pop(key, None)
    st.rerun()
# ── FIN TEST ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────────────────
# Procesamiento de Fase 1 — guarda resultados en session_state para que
# persistan a través de todos los re-renders posteriores (Fase 2, botones, etc.)
# ──────────────────────────────────────────────────────────────────────────────
if submitted:
    errores = []
    if not giro:
        errores.append("El campo **Giro del negocio** es obligatorio.")
    if not ciudad:
        errores.append("El campo **Ciudad** es obligatorio.")
    if capital <= 0:
        errores.append("El **capital** debe ser mayor a 0.")

    if errores:
        for e in errores:
            st.error(e)
    else:
        with st.spinner("Consultando a la IA… esto puede tardar unos segundos."):
            try:
                raw_json = get_locations(str(giro), capital, str(ciudad), zona_preferida.strip())
                ubicaciones = parse_response(raw_json)
            except EnvironmentError as e:
                st.error(f"⚠️ Configuración faltante: {e}")
                st.stop()
            except RuntimeError as e:
                st.error(f"🌐 Error al contactar la IA: {e}")
                st.stop()
            except Exception as e:
                st.error(f"❌ Error inesperado: {e}")
                st.stop()

        # Persistir resultados y contexto del negocio
        st.session_state["ubicaciones"] = ubicaciones
        st.session_state["giro"] = giro.strip()
        st.session_state["capital"] = capital
        st.session_state["ciudad"] = ciudad.strip()

        # Limpiar estado de Fase 2 si el usuario hace un nuevo análisis
        for key in ("escenario", "ubicacion_elegida", "mostrar_ajustes",
                    "mostrar_foda", "mostrar_deuda"):
            st.session_state.pop(key, None)

# ──────────────────────────────────────────────────────────────────────────────
# Resultados de Fase 1 — se muestran mientras haya ubicaciones en session_state
# Esto garantiza que el contenido no desaparezca cuando el usuario interactúa
# con los widgets de Fase 2 (cada interacción re-ejecuta el script completo).
# ──────────────────────────────────────────────────────────────────────────────
if "ubicaciones" in st.session_state:
    _ubs = st.session_state["ubicaciones"]
    _ciudad = st.session_state.get("ciudad", "")

    st.success(f"Análisis completado para **{_ciudad}** — {len(_ubs)} ubicaciones evaluadas.")

    # ── 1. Recomendaciones de la IA (ancho completo) ───────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    render_recomendacion(_ubs)

    # ── 2. Gráfico (izquierda) + Tabla (derecha) ───────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    graf_col, tabla_col = st.columns([2, 3], gap="large")
    with graf_col:
        render_grafico(_ubs)
    with tabla_col:
        render_tabla(_ubs)

    # ──────────────────────────────────────────────────────────────────────────
    # FASE 2 — Selector de ubicación
    # Está fuera del bloque if submitted para que persista entre re-renders.
    # ──────────────────────────────────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="padding:20px 0 8px;">
          <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:1.4rem;">🎯</span>
            <h2 style="margin:0;font-size:1.3rem;font-weight:800;color:var(--text-color);">
              Fase 2 — Análisis financiero detallado
            </h2>
          </div>
          <p style="margin:6px 0 0;color:var(--text-color);opacity:0.6;font-size:0.9rem;padding-left:38px;">
            Elige la ubicación que más te convence y genera su escenario financiero completo.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Opciones del selector: nombre de cada ubicación
    opciones = [u.get("nombre", f"Ubicación {i+1}") for i, u in enumerate(_ubs)]

    # Mantener la selección previa si ya existía
    idx_previo = 0
    if "ubicacion_elegida" in st.session_state:
        nombre_previo = st.session_state["ubicacion_elegida"]
        if nombre_previo in opciones:
            idx_previo = opciones.index(nombre_previo)

    seleccion = st.selectbox(
        "Selecciona la ubicación para analizar en detalle:",
        options=opciones,
        index=idx_previo,
        key="selectbox_ubicacion",
    )

    # Botón de confirmación — fuera de st.form para no forzar re-run del form
    confirmar = st.button(
        "✅ Confirmar ubicación y generar escenario",
        type="primary",
        use_container_width=False,
    )

    if confirmar:
        st.session_state["ubicacion_elegida"] = seleccion
        # Limpiar estado derivado para forzar nuevo análisis con la nueva ubicación
        for key in ("escenario", "mostrar_ajustes", "mostrar_foda", "mostrar_deuda"):
            st.session_state.pop(key, None)

        _giro = st.session_state.get("giro", "")
        _capital = st.session_state.get("capital", 0)

        with st.spinner(f"Generando escenario financiero para {seleccion}…"):
            try:
                # ── TEST: reemplazar get_mock_scenario por get_scenario cuando corresponda
                raw_escenario = get_mock_scenario(seleccion)
                # raw_escenario = get_scenario(_giro, float(_capital), _ciudad, seleccion)
                # ── FIN TEST
                escenario_parsed = parse_scenario(raw_escenario)
            except EnvironmentError as e:
                st.error(f"⚠️ Configuración faltante: {e}")
                st.stop()
            except RuntimeError as e:
                st.error(f"🌐 Error al contactar la IA (escenario): {e}")
                st.stop()
            except ValueError as e:
                st.error(f"📋 Error al procesar el escenario: {e}")
                st.stop()
            except Exception as e:
                st.error(f"❌ Error inesperado al generar escenario: {e}")
                st.stop()

        st.session_state["escenario"] = escenario_parsed

    # ── Mostrar escenario si ya fue generado ──────────────────────────────────
    if "escenario" in st.session_state:
        _escenario = st.session_state["escenario"]

        st.markdown("<hr>", unsafe_allow_html=True)
        render_escenario(_escenario)

        # ── Botón: Ajustar escenario ─────────────────────────────────────────
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        if st.button("✏️ Ajustar escenario", key="btn_ajustes"):
            st.session_state["mostrar_ajustes"] = not st.session_state.get(
                "mostrar_ajustes", False
            )

        if st.session_state.get("mostrar_ajustes", False):
            st.markdown(
                '<div style="background:var(--secondary-background-color);'
                'border:1px solid rgba(128,128,128,0.25);'
                'border-radius:12px;padding:20px 24px;margin-top:8px;">',
                unsafe_allow_html=True,
            )
            st.markdown("**⚙️ Ajusta las variables del escenario**", unsafe_allow_html=False)

            # Controles fuera de st.form → recálculo inmediato en cada cambio
            aj_col1, aj_col2, aj_col3, aj_col4 = st.columns(4)
            with aj_col1:
                aj_ingresos = st.number_input(
                    "Ingresos / mes (MXN)",
                    min_value=0.0,
                    step=1000.0,
                    value=float(_escenario.get("ingresos_estimados_mes", 0.0)),
                    key="aj_ingresos",
                )
            with aj_col2:
                aj_fijos = st.number_input(
                    "Costos fijos / mes (MXN)",
                    min_value=0.0,
                    step=500.0,
                    value=float(_escenario.get("costos_fijos_mes", 0.0)),
                    key="aj_fijos",
                )
            with aj_col3:
                aj_variables = st.number_input(
                    "Costos variables / mes (MXN)",
                    min_value=0.0,
                    step=500.0,
                    value=float(_escenario.get("costos_variables_mes", 0.0)),
                    key="aj_variables",
                )
            with aj_col4:
                aj_precio = st.number_input(
                    "Precio unitario promedio (MXN)",
                    min_value=0.0,
                    step=10.0,
                    value=float(_escenario.get("precio_unitario_promedio", 0.0)),
                    key="aj_precio",
                )

            st.markdown("</div>", unsafe_allow_html=True)

            # Render de métricas recalculadas — se actualiza en tiempo real
            ajustes = {
                "ingresos_estimados_mes": aj_ingresos,
                "costos_fijos_mes": aj_fijos,
                "costos_variables_mes": aj_variables,
                "precio_unitario_promedio": aj_precio,
            }
            render_metricas(_escenario, ajustes)

        # ── Botón: FODA ───────────────────────────────────────────────────────
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        _foda_abierto = st.session_state.get("mostrar_foda", False)
        _foda_icono = "➖" if _foda_abierto else "➕"
        if st.button(f"{_foda_icono} Agregar análisis FODA", key="btn_foda"):
            st.session_state["mostrar_foda"] = not _foda_abierto

        if st.session_state.get("mostrar_foda", False):
            st.markdown("<hr>", unsafe_allow_html=True)
            foda_base = _escenario.get("foda", {})
            if foda_base:
                render_foda(foda_base)
            else:
                st.info("El escenario no contiene datos de FODA.")

        # ── Botón: Financiamiento con deuda ───────────────────────────────────
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        _deuda_abierta = st.session_state.get("mostrar_deuda", False)
        _deuda_icono = "➖" if _deuda_abierta else "➕"
        if st.button(f"{_deuda_icono} Agregar financiamiento con deuda", key="btn_deuda"):
            st.session_state["mostrar_deuda"] = not _deuda_abierta

        if st.session_state.get("mostrar_deuda", False):
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("**🏦 Configura el crédito**", unsafe_allow_html=False)

            # Controles fuera de st.form → recálculo inmediato
            d_col1, d_col2, d_col3 = st.columns(3)
            with d_col1:
                d_monto = st.number_input(
                    "Monto del crédito (MXN)",
                    min_value=0.0,
                    step=5000.0,
                    value=float(st.session_state.get("capital", 50000)),
                    key="d_monto",
                )
            with d_col2:
                d_tasa = st.number_input(
                    "Tasa de interés anual (%)",
                    min_value=0.0,
                    max_value=200.0,
                    step=0.5,
                    value=18.0,
                    key="d_tasa",
                )
            with d_col3:
                d_plazo = st.number_input(
                    "Plazo (meses)",
                    min_value=1,
                    max_value=120,
                    step=1,
                    value=24,
                    key="d_plazo",
                )

            deuda = {
                "monto": d_monto,
                "tasa_anual": d_tasa,
                "plazo_meses": int(d_plazo),
            }
            render_deuda(_escenario, deuda)
