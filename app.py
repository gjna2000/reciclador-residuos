import time
from dataclasses import dataclass
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError
from ui import components as ui

st.set_page_config(page_title="EcoClasifica • IA & Res. 2184", page_icon="♻️", layout="wide")

@dataclass
class Prediction:
    label: str
    score: float

@dataclass
class AnalysisResult:
    status: str
    top: list[Prediction]
    bin: str | None
    tip: str
    device: str
    timings_ms: dict[str, float]

SCENARIOS = {
    "reciclable": "Reciclable (Plastic, 95 %)",
    "no_es_residuo": "La imagen no es un residuo",
    "incierto": "Resultado incierto (baja confianza)",
}

def mock_analyze(image: Image.Image, scenario: str = "reciclable") -> AnalysisResult:
    """SIMULADO. Se reemplazará por el pipeline real si está disponible."""
    time.sleep(0.5)
    if scenario == "no_es_residuo":
        return AnalysisResult("no_es_residuo", [], None,
                              "Prueba con otra fotografía donde el objeto se vea completo y de cerca.",
                              "CPU", {"total": 110.0})
    if scenario == "incierto":
        return AnalysisResult("incierto",
                              [Prediction("Paper", 0.38), Prediction("Cardboard", 0.31), Prediction("Plastic", 0.18)],
                              None, "Toma otra fotografía con mejor iluminación y enfoque.",
                              "CPU", {"total": 115.0})
    return AnalysisResult("reciclable",
                          [Prediction("Plastic", 0.95), Prediction("Cardboard", 0.03), Prediction("Metal", 0.02)],
                          "blanco", "Deposita el material limpio y seco en la caneca blanca.", "CPU", {"total": 112.0})

st.session_state.setdefault("uploader_key", 0)
st.session_state.setdefault("result", None)
st.session_state.setdefault("file_id", None)

def reset_analysis() -> None:
    st.session_state.uploader_key += 1
    st.session_state.result = None
    st.session_state.file_id = None

def load_image(uploaded) -> Image.Image | None:
    if uploaded is None:
        return None
    try:
        return ImageOps.exif_transpose(Image.open(uploaded)).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        st.error("No se pudo leer el archivo. Verifica que sea una imagen JPG, JPEG o PNG válida.")
        return None

ui.load_theme()

with st.sidebar:
    st.subheader("Herramienta de pruebas")
    st.caption("Solo para demostración de estados. Al cambiar el escenario, pulsa nuevamente «Analizar residuo».")
    scenario = st.selectbox("Estado simulado", list(SCENARIOS), format_func=SCENARIOS.get)

ui.render_header()
ui.render_hero()

ui.section_title("Analiza tu residuo", "Sube una fotografía de tus archivos o captura una imagen con la cámara de tu dispositivo.", anchor="analizar")

MODE_FILE = "Subir fotografía"
MODE_CAMERA = "Tomar fotografía"

col_upload, col_result = st.columns([7, 5], gap="large")

with col_upload:
    with st.container(key="upload_card"):
        # Selector de modalidad de entrada
        c_mode, c_fmt = st.columns([3, 2], vertical_alignment="center")
        with c_mode:
            input_mode = st.radio("Modalidad de entrada", [MODE_FILE, MODE_CAMERA], horizontal=True,
                                  key="input_mode", label_visibility="collapsed")
        with c_fmt:
            ui.format_chip()

        uploaded = None
        if input_mode == MODE_FILE:
            uploaded = st.file_uploader("Fotografía del residuo", type=["jpg", "jpeg", "png"],
                                        key=f"uploader_{st.session_state.uploader_key}",
                                        label_visibility="collapsed")
        else:
            uploaded = st.camera_input("Capturar fotografía con cámara",
                                       key=f"camera_{st.session_state.uploader_key}",
                                       label_visibility="collapsed")

        image = load_image(uploaded)

        file_id = uploaded.file_id if hasattr(uploaded, "file_id") and uploaded is not None else (uploaded.name if uploaded is not None else None)
        if file_id != st.session_state.file_id:
            st.session_state.file_id = file_id
            st.session_state.result = None

        if input_mode == MODE_FILE and image is not None:
            # Vista previa en un contenedor de tamaño fijo (ver theme.css): la imagen se ajusta sin deformarse.
            preview = image.copy()
            preview.thumbnail((900, 900))
            st.image(preview)
        if image is not None:
            st.caption(f"Imagen lista: {image.width} × {image.height} px")
        elif input_mode == MODE_CAMERA:
            st.caption("Permite el acceso a la cámara y pulsa el botón de captura para tomar la fotografía.")

        c_analyze, c_clear = st.columns([3, 2])
        analyze_clicked = c_analyze.button("Analizar residuo", type="primary", disabled=image is None)
        c_clear.button("Limpiar", on_click=reset_analysis, disabled=uploaded is None)

    if analyze_clicked and image is not None:
        try:
            with st.spinner("Analizando con modelo de visión IA..."):
                st.session_state.result = mock_analyze(image, scenario)
        except Exception:
            st.session_state.result = None
            st.error("No se pudo completar el análisis. Inténtalo de nuevo.")

result = st.session_state.result
with col_result:
    if result is not None:
        ui.result_card(result)
    elif image is not None:
        ui.empty_state("Fotografía lista", "Pulsa «Analizar residuo» para ver la clasificación.",
                       min_height=300, icon="task_alt")
    else:
        ui.empty_state("Aquí aparecerá tu resultado", "Carga o captura una fotografía del residuo para comenzar el análisis.",
                       min_height=300, icon="recycling")
    if result is not None:
        ui.tech_info(result)

detected = result.top[0].label if result and result.status == "reciclable" and result.top else None
ui.bins_overview()
ui.category_cards_grid(detected)
ui.render_footer()