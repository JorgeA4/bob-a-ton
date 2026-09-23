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

st.set_page_config(page_title="Analizador de ubicaciones", page_icon="📍", layout="wide")
st.title("📍 Analizador de ubicaciones para tu negocio")
st.caption("Ingresa los datos de tu negocio y la IA evaluará las mejores zonas de la ciudad.")

with st.form("form_negocio"):
    col1, col2, col3 = st.columns(3)
    with col1:
        giro = st.text_input("Giro del negocio", placeholder="Ej. Cafetería, Taller mecánico")
    with col2:
        capital = st.number_input("Capital inicial (MXN)", min_value=1, step=5000, value=100000)
    with col3:
        ciudad = st.text_input("Ciudad", placeholder="Ej. Guadalajara, CDMX")
    submitted = st.form_submit_button("Analizar ubicaciones", type="primary", use_container_width=True)

if submitted:
    # Validaciones
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
        with st.spinner("Consultando a la IA... esto puede tardar unos segundos."):
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
        render_tabla(ubicaciones)
        render_grafico(ubicaciones)
        render_recomendacion(ubicaciones)
