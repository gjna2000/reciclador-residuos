import logging
import io
import threading
from dataclasses import fields

import streamlit as st
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

from src.contracts import AnalysisResult, Prediction
from ui import components as ui

st.set_page_config(page_title="EcoClasifica • IA & Res. 2184", page_icon="♻️", layout="wide")


@st.cache_resource(show_spinner=False)
def load_gate(device: str):
    from src.models.gate import Gate

    return Gate(device=device)


@st.cache_resource(show_spinner=False)
def load_detector():
    from src.models.gdino_detector import GDinoDetector

    return GDinoDetector()


@st.cache_resource(show_spinner=False)
def load_classifier(device: str):
    from src.models.waste_classifier import WasteClassifier

    return WasteClassifier(device=device)


@st.cache_resource(show_spinner=False)
def load_camera_runtime():
    """Importa una vez PyAV, OpenCV y streamlit-webrtc antes de abrir la cámara."""
    from src.camera import render_live_camera

    return render_live_camera


@st.cache_resource(show_spinner=False)
def load_pipeline_lock():
    """Comparte un lock para que las sesiones no usen la GPU simultáneamente."""
    return threading.Lock()


@st.cache_resource(show_spinner=False)
def load_pipeline(_gate, _detector, _classifier):
    """Conserva una sola instancia del pipeline entre reruns de Streamlit."""
    from src.pipeline import RecyclingPipeline

    return RecyclingPipeline(gate=_gate, detector=_detector, classifier=_classifier)


@st.cache_resource(show_spinner=False)
def warmup_models(_gate, _detector, _classifier):
    """Inicializa una vez los caminos de inferencia antes de la primera prueba real."""
    warmup_image = Image.new("RGB", (1024, 768), color=(127, 127, 127))
    _gate.is_waste(warmup_image)
    _detector.detect(warmup_image)
    _classifier.classify(warmup_image)
    return True


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


def make_analyzer(pipeline, lock, holder=None, analyze_method=None):
    """Crea la función imagen PIL -> AnalysisResult. No usa APIs de Streamlit, así que es
    segura para el hilo de análisis de la cámara."""
    run_analysis = analyze_method or pipeline.analyze

    def analyze(image: Image.Image) -> AnalysisResult:
        with lock:
            result = run_analysis(image)
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


# Límites SOLO de visualización para los recortes de la Fase 2 (no afectan lo que recibe ViT).
_CROP_MAX_WIDTH = 260   # px máximos de ancho mostrado
_CROP_MAX_HEIGHT = 240  # px máximos de alto mostrado (evita recortes verticales muy altos)
_CROP_SLOT_HEIGHT = 300  # alto fijo del espacio de la imagen (recorte + leyenda) para equilibrar tarjetas

# Lienzo de tamaño fijo para la imagen original de la Fase 1 (solo visualización).
# La imagen se escala con proporción original dentro de este lienzo (equivale a `object-fit: contain`)
# y se centra; así imágenes verticales, horizontales y cuadradas ocupan siempre el mismo espacio.
_PHASE1_CANVAS = (560, 320)          # (ancho, alto) en px del lienzo mostrado
_PHASE1_BG = (241, 245, 249)         # fondo neutro del lienzo (franjas del «contain»)


def _phase1_contain_view(image: Image.Image, objects: list) -> Image.Image:
    """Devuelve una COPIA de visualización: la imagen completa, sin recortes ni deformación, centrada
    en un lienzo fijo y con las cajas de Grounding DINO dibujadas sobre ella. No modifica `image`
    ni las coordenadas originales de `objects` (solo se escalan para dibujarlas)."""
    canvas_w, canvas_h = _PHASE1_CANVAS
    source = image.convert("RGB")
    scale = min(canvas_w / source.width, canvas_h / source.height)
    new_w, new_h = max(1, round(source.width * scale)), max(1, round(source.height * scale))
    resized = source.resize((new_w, new_h), Image.LANCZOS)
    offset_x, offset_y = (canvas_w - new_w) // 2, (canvas_h - new_h) // 2

    canvas = Image.new("RGB", (canvas_w, canvas_h), _PHASE1_BG)
    canvas.paste(resized, (offset_x, offset_y))
    draw = ImageDraw.Draw(canvas)

    width, height = source.size
    for item in objects:
        box = item.get("box")
        if not box or len(box) != 4:
            continue
        x1, y1, x2, y2 = (int(value) for value in box)
        x1, x2 = max(0, min(x1, width - 1)), max(0, min(x2, width - 1))
        y1, y2 = max(0, min(y1, height - 1)), max(0, min(y2, height - 1))
        # Mismas cajas, solo convertidas a la escala y posición del lienzo para dibujarlas.
        cx1, cx2 = offset_x + round(x1 * scale), offset_x + round(x2 * scale)
        cy1, cy2 = offset_y + round(y1 * scale), offset_y + round(y2 * scale)
        draw.rectangle((cx1, cy1, cx2, cy2), outline="#16A34A", width=2)
        draw.text((cx1 + 3, max(0, cy1 - 14)), str(item.get("detected_label", "objeto")), fill="#16A34A")
    return canvas


def render_phase1(result: AnalysisResult, image: Image.Image | None = None) -> None:
    """Fase 1 (Grounding DINO). Se dibuja en la columna derecha de la fila superior:
    métricas de detección y, si hay imagen, la vista con las cajas propuestas."""
    timings = result.timings_ms or {}
    objects = result.objects or []

    with st.container(key="phase1_card"):
        st.markdown("#### Fase 1 · Detección de objetos (Grounding DINO)")
        detection_col, classification_col = st.columns(2)
        detection_col.metric("Objetos detectados", len(objects))
        detection_col.metric("Tiempo de detección", f"{timings.get('detection_ms', 0):.0f} ms")
        classification_col.metric("Tiempo de clasificación", f"{timings.get('classifier_ms', 0):.0f} ms")

        if not objects:
            st.info("Grounding DINO no encontró objetos; por eso no hubo recortes para clasificar.")
            return

        if image is not None:
            # Lienzo de tamaño fijo con la imagen completa centrada (contain) y cajas dibujadas.
            st.image(
                _phase1_contain_view(image, objects),
                caption="Cajas propuestas por Grounding DINO",
                use_container_width=True,
            )


def render_phase2(result: AnalysisResult, image: Image.Image | None = None) -> None:
    """Fase 2 (ViT). Se dibuja en la fila inferior, a todo el ancho de la página.
    Sin objetos no hay nada que clasificar (el aviso ya lo muestra la Fase 1)."""
    objects = result.objects or []
    if not objects:
        return

    with st.container(key="phase2_section"):
        st.markdown("#### Fase 2 · Recortes y clasificación (ViT)")
        if image is None:
            st.caption("En cámara en vivo, las cajas se dibujan sobre el video; aquí se detallan sus clasificaciones.")

        # Cuadrícula de dos columnas: dos tarjetas por fila, en el orden original de `objects`.
        # En pantallas angostas Streamlit apila las columnas, quedando una sola columna.
        for row_start in range(0, len(objects), 2):
            grid_columns = st.columns(2, vertical_alignment="top")
            for offset, grid_column in enumerate(grid_columns):
                index = row_start + offset
                if index >= len(objects):
                    break
                item = objects[index]
                with grid_column, st.container(border=True, key=f"phase2_card_{index + 1}"):
                    st.markdown(f"##### Residuo {index + 1}")
                    box = item.get("box")
                    if image is not None and box and len(box) == 4:
                        x1, y1, x2, y2 = (int(value) for value in box)
                        if x2 > x1 and y2 > y1:
                            crop = image.crop((x1, y1, x2, y2))
                            # Escala única para ancho y alto: mantiene la proporción, respeta ambos
                            # límites y nunca amplía un recorte pequeño. El recorte no se modifica.
                            scale = min(1.0, _CROP_MAX_WIDTH / crop.width, _CROP_MAX_HEIGHT / crop.height)
                            display_width = max(1, round(crop.width * scale))
                            with st.container(height=_CROP_SLOT_HEIGHT, border=False):
                                st.image(crop, caption="Recorte enviado a ViT", width=display_width)

                    detected_label = item.get("detected_label") or "Objeto"
                    detected_score = item.get("detection_score")
                    if isinstance(detected_score, (int, float)):
                        st.caption(f"Grounding DINO: {detected_label} · {detected_score:.0%}")
                    else:
                        st.caption(f"Grounding DINO: {detected_label}")

                    classification = item.get("classification")
                    class_score = item.get("classification_score")
                    canonical_label = (
                        _CANONICAL_LABELS.get(str(classification).strip().lower(), classification)
                        if classification is not None
                        else None
                    )
                    prediction = (
                        [Prediction(canonical_label, float(class_score))]
                        if canonical_label is not None and isinstance(class_score, (int, float))
                        else []
                    )
                    has_recommendation = bool(item.get("confident") and item.get("bin"))
                    object_result = AnalysisResult(
                        status="reciclable" if has_recommendation else "incierto",
                        top=prediction,
                        bin=item.get("bin") if has_recommendation else None,
                        tip=item.get("tip") or "No se pudo generar una recomendación para este objeto.",
                        device=result.device,
                        timings_ms={},
                        objects=[item],
                    )
                    ui.result_card(object_result, key_suffix=f"crop_{index + 1}")


def render_pipeline_phases(result: AnalysisResult, image: Image.Image | None = None) -> None:
    """Conservada por compatibilidad (la usa `live_panel`): dibuja las dos fases una tras otra.
    La interfaz principal coloca cada fase por separado con render_phase1 y render_phase2."""
    render_phase1(result, image)
    render_phase2(result, image)


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
    render_pipeline_phases(held)
    ui.tech_info(held)


@st.fragment(run_every=1.0)
def live_phase1_panel(holder: LiveHolder, shown_signature) -> None:
    """Fila superior, columna derecha: Fase 1 en vivo. Si cambia lo detectado, relanza la página
    para que canecas y categorías se actualicen."""
    result = holder.get()
    if result is None:
        ui.empty_state("Analizando la cámara...", "Apunta el residuo a la cámara; el primer resultado tarda unos segundos.",
                       min_height=300, icon="videocam")
        return
    if _signature(result) != shown_signature:
        st.rerun()
    render_phase1(_stable_result(result))


@st.fragment(run_every=1.0)
def live_phase2_panel(holder: LiveHolder, shown_signature) -> None:
    """Fila inferior, ancho completo: Fase 2 en vivo (recortes/clasificación) e información técnica."""
    result = holder.get()
    if result is None:
        return
    if _signature(result) != shown_signature:
        st.rerun()
    held = _stable_result(result)
    render_phase2(held)
    ui.tech_info(held)


st.session_state.setdefault("uploader_key", 0)
st.session_state.setdefault("result", None)
st.session_state.setdefault("file_id", None)
st.session_state.setdefault("loaded_image", None)
st.session_state.setdefault("loaded_preview", None)
st.session_state.setdefault("uploaded_image_bytes", None)
st.session_state.setdefault("live_holder", LiveHolder())
st.session_state.setdefault("live_held", None)


def reset_analysis() -> None:
    st.session_state.uploader_key += 1
    st.session_state.result = None
    st.session_state.file_id = None
    st.session_state.loaded_image = None
    st.session_state.loaded_preview = None
    st.session_state.uploaded_image_bytes = None


def load_image(image_bytes: bytes, *, preview: bool = False) -> Image.Image | None:
    if not image_bytes:
        return None
    try:
        with Image.open(io.BytesIO(image_bytes)) as opened:
            original_size = opened.size
            orientation = opened.getexif().get(274)
            if orientation in (5, 6, 7, 8):
                original_size = (original_size[1], original_size[0])
            # JPEG permite decodificar una versión reducida para la vista previa.
            # El análisis siempre abre el original y conserva toda su resolución.
            if preview:
                opened.draft("RGB", (900, 900))
                # Reducir antes de convertir a RGB evita crear una copia RGB grande.
                opened.thumbnail((900, 900), Image.BILINEAR)
            oriented = ImageOps.exif_transpose(opened)
            image = oriented.convert("RGB")
            if preview:
                image.info["original_size"] = original_size
            return image
    except (UnidentifiedImageError, OSError, ValueError):
        st.error("No se pudo leer el archivo. Verifica que sea una imagen JPG, JPEG o PNG válida.")
        return None


ui.load_theme()

startup = st.empty()
with startup.container():
    ui.render_header()
    st.markdown("## Preparando EcoClasifica")
    st.caption("Cargando los recursos visuales y los tres modelos. La primera carga puede tardar mientras se descargan los pesos.")
    startup_progress = st.progress(0, text="Preparando recursos visuales...")
    startup_detail = st.empty()

    try:
        images_loaded, images_total = ui.preload_category_images()
        startup_progress.progress(8, text="Recursos visuales revisados")
        if images_loaded == images_total:
            startup_detail.success(f"Imágenes del catálogo listas ({images_loaded}/{images_total}).")
        else:
            startup_detail.info(
                f"Imágenes del catálogo disponibles: {images_loaded}/{images_total}. "
                "Las que falten usarán sus iconos alternativos."
            )

        startup_progress.progress(10, text="Preparando los componentes de cámara...")
        startup_detail.write("Cargando PyAV, OpenCV y WebRTC...")
        render_live_camera = load_camera_runtime()

        startup_progress.progress(22, text="Cargando CLIP (filtro auxiliar)...")
        startup_detail.write("Cargando CLIP...")
        gate = load_gate("cuda")

        startup_progress.progress(48, text="Cargando Grounding DINO (detección)...")
        startup_detail.write("Cargando Grounding DINO...")
        detector = load_detector()

        startup_progress.progress(74, text="Cargando ViT (clasificación)...")
        startup_detail.write("Cargando clasificador ViT...")
        classifier = load_classifier("cuda")

        startup_progress.progress(86, text="Preparando inferencia en GPU...")
        startup_detail.write("Inicializando los modelos para la primera imagen y la cámara...")
        warmup_models(gate, detector, classifier)

        startup_progress.progress(94, text="Preparando el pipeline...")
        pipeline = load_pipeline(gate, detector, classifier)
        pipeline_lock = load_pipeline_lock()
        startup_progress.progress(100, text="Todo está listo")
        startup_detail.success("Modelos cargados. Abriendo la aplicación...")
    except Exception as error:
        logging.exception("No se pudo preparar la aplicación")
        startup_detail.error(f"No se pudo preparar la aplicación: {error}")
        st.stop()

startup.empty()
ui.render_header()
ui.render_hero()

live_holder: LiveHolder = st.session_state.live_holder
file_analyzer = make_analyzer(pipeline, pipeline_lock)
live_analyzer = make_analyzer(
    pipeline,
    pipeline_lock,
    holder=live_holder,
    analyze_method=pipeline.analyze_live,
)

ui.section_title("Analiza tu residuo", "Sube una fotografía de tus archivos o analiza en vivo con la cámara de tu dispositivo.", anchor="analizar")

MODE_FILE = "Subir fotografía"
MODE_CAMERA = "Cámara en vivo"

# Fila superior: carga/cámara (izquierda) y solo la Fase 1 (derecha). En pantallas angostas
# Streamlit apila estas dos columnas. La Fase 2 va en una fila inferior a todo el ancho.
col_upload, col_phase1 = st.columns([5, 7], gap="large")
col_phase2 = st.container()

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
            file_id = uploaded.file_id if hasattr(uploaded, "file_id") and uploaded is not None else (uploaded.name if uploaded is not None else None)
            if file_id != st.session_state.file_id or (
                uploaded is not None and st.session_state.loaded_preview is None
            ):
                st.session_state.file_id = file_id
                st.session_state.result = None
                if uploaded is None:
                    st.session_state.loaded_image = None
                    st.session_state.loaded_preview = None
                    st.session_state.uploaded_image_bytes = None
                else:
                    st.session_state.uploaded_image_bytes = uploaded.getvalue()
                    st.session_state.loaded_image = None
                    with st.spinner("Preparando la imagen para mostrarla y analizarla..."):
                        st.session_state.loaded_preview = load_image(
                            st.session_state.uploaded_image_bytes, preview=True
                        )
            preview = st.session_state.loaded_preview

            if preview is not None:
                st.image(preview)
                original_width, original_height = preview.info.get("original_size", preview.size)
                st.caption(f"Imagen lista: {original_width} × {original_height} px")

            c_analyze, c_clear = st.columns([3, 2])
            analyze_clicked = c_analyze.button("Analizar residuo", type="primary", disabled=preview is None)
            c_clear.button("Limpiar", on_click=reset_analysis, disabled=uploaded is None)
        else:

            live_ctx = render_live_camera(analyze_fn=live_analyzer, interval=0.5)
            live_playing = bool(live_ctx is not None and live_ctx.state.playing)
            st.caption("Permite el acceso a la cámara y pulsa START. El análisis se actualiza de forma continua.")

    if analyze_clicked and preview is not None:
        try:
            with st.spinner("Preparando la imagen original..."):
                image = st.session_state.loaded_image
                if image is None:
                    image = load_image(st.session_state.uploaded_image_bytes)
                    st.session_state.loaded_image = image
            with st.spinner("Analizando con modelo de visión IA..."):
                st.session_state.result = file_analyzer(image)
        except Exception as error:
            logging.exception("Falló el análisis de la imagen")
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
    image = st.session_state.loaded_image or st.session_state.loaded_preview

# Fila superior, columna derecha: SOLO Fase 1 (o el estado vacío correspondiente).
with col_phase1:
    if input_mode == MODE_CAMERA:
        if live_playing:
            live_phase1_panel(live_holder, _signature(result) if result is not None else None)
        else:
            ui.empty_state("Cámara detenida", "Pulsa START en el panel de la cámara para comenzar el análisis en vivo.",
                           min_height=300, icon="videocam")
    else:
        if result is not None:
            render_phase1(result, image)
        elif image is not None:
            ui.empty_state("Fotografía lista", "Pulsa «Analizar residuo» para ver la clasificación.",
                           min_height=300, icon="task_alt")
        else:
            ui.empty_state("Aquí aparecerá tu resultado", "Carga una fotografía del residuo para comenzar el análisis.",
                           min_height=300, icon="recycling")

# Fila inferior, ancho completo: Fase 2 (cuadrícula de 2 tarjetas por fila) e información técnica.
with col_phase2:
    if input_mode == MODE_CAMERA:
        if live_playing:
            live_phase2_panel(live_holder, _signature(result) if result is not None else None)
    elif result is not None:
        render_phase2(result, image)
        ui.tech_info(result)

detected = result.top[0].label if result and result.status == "reciclable" and result.top else None
ui.bins_overview(result.bin if result is not None else None)
ui.category_cards_grid(detected)
ui.render_footer()
