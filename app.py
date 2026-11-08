import threading
from dataclasses import fields

import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

from src.camera import render_live_camera
from src.contracts import AnalysisResult, Prediction
from src.pipeline import RecyclingPipeline
from ui import components as ui

st.set_page_config(page_title="EcoClasifica • IA & Res. 2184", page_icon="♻️", layout="wide")


@st.cache_resource(show_spinner="Cargando modelos de IA (CLIP, Grounding DINO, ViT)...")
def load_pipeline():
    """Instancia el pipeline con su dispositivo por defecto (CUDA) y un lock para
    que dos hilos (subida de archivo / cámara) no usen los modelos a la vez."""
    return RecyclingPipeline(), threading.Lock()


_CANONICAL_LABELS = {key.lower(): key for key in ui.CATEGORIES}


def _validate(result) -> None:
    """Lanza una excepción si el resultado no cumple el contrato que esperan los componentes."""
    if not isinstance(result, AnalysisResult):
        raise TypeError(f"El pipeline devolvió {type(result).__name__}, se esperaba AnalysisResult.")
    if result.status not in ui.STATUS_STYLE:
        raise ValueError(f"Estado no reconocido por la interfaz: {result.status!r}")
    if result.bin is not None and str(result.bin).strip().lower() not in ui.RESULT_BINS:
        raise ValueError(f"Contenedor no reconocido por la interfaz: {result.bin!r}")
    if not isinstance(result.tip, str):
        raise TypeError("`tip` debe ser texto.")
    if not isinstance(result.top, list) or not all(isinstance(p, Prediction) for p in result.top):
        raise TypeError("`top` debe ser una lista de Prediction.")
    if not isinstance(result.objects, list):
        raise TypeError("`objects` debe ser una lista.")
    if not isinstance(result.timings_ms, dict):
        raise TypeError("`timings_ms` debe ser un diccionario.")
    if result.status == "reciclable" and not result.top:
        raise ValueError("Estado 'reciclable' sin predicciones en `top`.")


def _normalize(result: AnalysisResult) -> None:
    """Deja `top` ordenado por confianza y con las etiquetas tal como las usa la interfaz
    (p. ej. 'Brown-Grass' -> 'Brown-grass'). Los componentes toman top[0] como mejor predicción."""
    for pred in result.top:
        pred.label = _CANONICAL_LABELS.get(str(pred.label).strip().lower(), pred.label)
    result.top.sort(key=lambda pred: pred.score, reverse=True)


def make_analyzer(pipeline, lock, holder=None):
    """Crea la función imagen PIL -> AnalysisResult. No usa APIs de Streamlit, así que es
    segura para el hilo de análisis de la cámara."""
    def analyze(image: Image.Image) -> AnalysisResult:
        with lock:
            result = pipeline.analyze(image)
        _validate(result)
        _normalize(result)
        if holder is not None:
            holder.set(result)
        return result
    return analyze


class LiveHolder:
    """Último resultado de la cámara en vivo (escrito por el hilo de análisis, leído por la UI)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._result = None

    def set(self, result) -> None:
        with self._lock:
            self._result = result

    def get(self):
        with self._lock:
            return self._result


def _signature(result):
    """Lo que, si cambia, justifica redibujar canecas/categorías y reiniciar la animación."""
    top_label = result.top[0].label if result.top else None
    return (result.status, result.bin, top_label)


def _stable_result(result: AnalysisResult) -> AnalysisResult:
    """`result_card` reinicia su animación cada vez que recibe un objeto distinto. En vivo llega un
    objeto nuevo por análisis, así que se conserva el mismo objeto mientras la firma no cambie y
    solo se actualizan sus campos (confianza, tiempos, objetos)."""
    held = st.session_state.get("live_held")
    if held is None or _signature(held) != _signature(result):
        st.session_state["live_held"] = result
        return result
    for field in fields(AnalysisResult):
        setattr(held, field.name, getattr(result, field.name))
    return held


@st.fragment(run_every=1.0)
def live_panel(holder: LiveHolder, shown_signature) -> None:
    """Refresca solo el panel de resultado; si cambia lo detectado, relanza toda la página
    para que canecas y categorías se actualicen."""
    result = holder.get()
    if result is None:
        ui.empty_state("Analizando la cámara...", "Apunta el residuo a la cámara; el primer resultado tarda unos segundos.",
                       min_height=300, icon="videocam")
        return
    if _signature(result) != shown_signature:
        st.rerun()
    held = _stable_result(result)
    ui.result_card(held)
    ui.tech_info(held)


st.session_state.setdefault("uploader_key", 0)
st.session_state.setdefault("result", None)
st.session_state.setdefault("file_id", None)
st.session_state.setdefault("live_holder", LiveHolder())
st.session_state.setdefault("live_held", None)


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

ui.render_header()
ui.render_hero()

try:
    pipeline, pipeline_lock = load_pipeline()
except Exception as error:
    st.error(f"No se pudieron cargar los modelos de IA: {error}")
    st.stop()

live_holder: LiveHolder = st.session_state.live_holder
file_analyzer = make_analyzer(pipeline, pipeline_lock)
live_analyzer = make_analyzer(pipeline, pipeline_lock, holder=live_holder)

ui.section_title("Analiza tu residuo", "Sube una fotografía de tus archivos o analiza en vivo con la cámara de tu dispositivo.", anchor="analizar")

MODE_FILE = "Subir fotografía"
MODE_CAMERA = "Cámara en vivo"

col_upload, col_result = st.columns([7, 5], gap="large")

live_playing = False

with col_upload:
    with st.container(key="upload_card"):
        c_mode, c_fmt = st.columns([3, 2], vertical_alignment="center")
        with c_mode:
            input_mode = st.radio("Modalidad de entrada", [MODE_FILE, MODE_CAMERA], horizontal=True,
                                  key="input_mode", label_visibility="collapsed")
        with c_fmt:
            ui.format_chip()

        uploaded = None
        image = None
        analyze_clicked = False

        if input_mode == MODE_FILE:
            uploaded = st.file_uploader("Fotografía del residuo", type=["jpg", "jpeg", "png"],
                                        key=f"uploader_{st.session_state.uploader_key}",
                                        label_visibility="collapsed")
            image = load_image(uploaded)

            file_id = uploaded.file_id if hasattr(uploaded, "file_id") and uploaded is not None else (uploaded.name if uploaded is not None else None)
            if file_id != st.session_state.file_id:
                st.session_state.file_id = file_id
                st.session_state.result = None

            if image is not None:
                preview = image.copy()
                preview.thumbnail((900, 900))
                st.image(preview)
                st.caption(f"Imagen lista: {image.width} × {image.height} px")

            c_analyze, c_clear = st.columns([3, 2])
            analyze_clicked = c_analyze.button("Analizar residuo", type="primary", disabled=image is None)
            c_clear.button("Limpiar", on_click=reset_analysis, disabled=uploaded is None)
        else:

            live_ctx = render_live_camera(analyze_fn=live_analyzer, interval=0.5)
            live_playing = bool(live_ctx is not None and live_ctx.state.playing)
            st.caption("Permite el acceso a la cámara y pulsa START. El análisis se actualiza de forma continua.")

    if analyze_clicked and image is not None:
        try:
            with st.spinner("Analizando con modelo de visión IA..."):
                st.session_state.result = file_analyzer(image)
        except Exception as error:
            st.session_state.result = None
            st.error(f"No se pudo completar el análisis: {error}")

if input_mode == MODE_CAMERA:
    if live_playing:
        result = live_holder.get()
    else:
        live_holder.set(None)
        st.session_state.live_held = None
        result = None
else:
    live_holder.set(None)
    st.session_state.live_held = None
    result = st.session_state.result

with col_result:
    if input_mode == MODE_CAMERA:
        if live_playing:
            live_panel(live_holder, _signature(result) if result is not None else None)
        else:
            ui.empty_state("Cámara detenida", "Pulsa START en el panel de la cámara para comenzar el análisis en vivo.",
                           min_height=300, icon="videocam")
    else:
        if result is not None:
            ui.result_card(result)
            ui.tech_info(result)
        elif image is not None:
            ui.empty_state("Fotografía lista", "Pulsa «Analizar residuo» para ver la clasificación.",
                           min_height=300, icon="task_alt")
        else:
            ui.empty_state("Aquí aparecerá tu resultado", "Carga una fotografía del residuo para comenzar el análisis.",
                           min_height=300, icon="recycling")

detected = result.top[0].label if result and result.status == "reciclable" and result.top else None
ui.bins_overview(result.bin if result is not None else None)
ui.category_cards_grid(detected)
ui.render_footer()