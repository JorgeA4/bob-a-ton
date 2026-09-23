import streamlit as st

from ai.gemini_client import get_locations

# core.parser no existe aún (Dev C pendiente) — mock hasta que entregue
try:
    from core.parser import parse_response
except ImportError:
    def parse_response(json_str: str) -> list:
        """Mock temporal hasta que Dev C entregue core/parser.py."""
        import json
        data = json.loads(json_str)
        return data.get("ubicaciones", [])


from ui.components import render_tabla, render_grafico, render_recomendacion

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

    /* ── Formulario: card elevada ────────────────────────────────────────── */
    [data-testid="stForm"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
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
        color: #0f172a !important;
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

    /* ── Separadores ──────────────────────────────────────────────────────── */
    hr {
        border: none !important;
        border-top: 1px solid #e2e8f0 !important;
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
    <div style="padding:32px 0 24px;border-bottom:1px solid #e2e8f0;margin-bottom:28px;">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
        <span style="font-size:2rem;">📍</span>
        <h1 style="margin:0;font-size:1.75rem;font-weight:800;color:#0f172a;
                   font-family:-apple-system,'Segoe UI',sans-serif;">
          Analizador de ubicaciones <span style="color:#2563eb;">para tu negocio</span>
        </h1>
      </div>
      <p style="margin:0;color:#64748b;font-size:0.95rem;padding-left:52px;">
        Ingresa los datos de tu negocio y la IA evaluará las mejores zonas de la ciudad.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Formulario de entrada
# ──────────────────────────────────────────────────────────────────────────────
with st.form("form_negocio"):
    col1, col2, col3 = st.columns(3)
    with col1:
        giro = st.text_input("Giro del negocio", placeholder="Ej. Cafetería, Taller mecánico")
    with col2:
        capital = st.number_input("Capital inicial (MXN)", min_value=1, step=5000, value=100000)
    with col3:
        ciudad = st.text_input("Ciudad", placeholder="Ej. Guadalajara, CDMX")
    submitted = st.form_submit_button("🔍 Analizar ubicaciones", use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Lógica de análisis — sin cambios funcionales
# ──────────────────────────────────────────────────────────────────────────────
if submitted:
    errores = []
    if not giro.strip():
        errores.append("El campo **Giro del negocio** es obligatorio.")
    if not ciudad.strip():
        errores.append("El campo **Ciudad** es obligatorio.")
    if capital <= 0:
        errores.append("El **capital** debe ser mayor a 0.")

    if errores:
        for e in errores:
            st.error(e)
    else:
        with st.spinner("Consultando a la IA… esto puede tardar unos segundos."):
            try:
                raw_json = get_locations(giro.strip(), capital, ciudad.strip())
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

        st.success(f"Análisis completado para **{ciudad.strip()}** — {len(ubicaciones)} ubicaciones evaluadas.")

        st.markdown("<hr>", unsafe_allow_html=True)
        render_tabla(ubicaciones)
        st.markdown("<hr>", unsafe_allow_html=True)
        render_grafico(ubicaciones)
        st.markdown("<hr>", unsafe_allow_html=True)
        render_recomendacion(ubicaciones)
