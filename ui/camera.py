

import logging
import threading
import time

import av
import cv2
from PIL import Image
import streamlit as st
from streamlit_webrtc import (
    RTCConfiguration,
    VideoProcessorBase,
    WebRtcMode,
    webrtc_streamer,
)

logger = logging.getLogger(__name__)

# Se conserva el video WebRTC original para mostrarlo; solo se limita el tamaño
# de los fotogramas que consumen los modelos durante el análisis en vivo.
LIVE_ANALYSIS_MAX_WIDTH = 1280
LIVE_ANALYSIS_MAX_HEIGHT = 720

DEFAULT_KEY = "camara-residuos"

DEFAULT_RTC_CONFIG = RTCConfiguration(
    {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun.cloudflare.com:3478"]},
        ]
    }
)


def _configured_rtc_config():
    """Permite añadir un TURN relay en secrets sin exponer credenciales en el código."""
    try:
        ice_servers = st.secrets.get("webrtc", {}).get("ice_servers")
    except Exception:
        ice_servers = None
    if ice_servers:
        return RTCConfiguration({"iceServers": list(ice_servers)})
    return DEFAULT_RTC_CONFIG

# Colores BGR (OpenCV) según el contenedor recomendado
BIN_COLORS = {
    "blanco": (240, 240, 240),
    "negro": (90, 90, 90),
    "verde": (60, 180, 60),
    "punto": (0, 165, 255),  # punto especial (acepta punto_especial o punto-especial)
}
UNCERTAIN_COLOR = (150, 150, 150)
FONT = cv2.FONT_HERSHEY_SIMPLEX


def is_live_available(pipeline) -> bool:
    """True si el pipeline tiene analyze_live y (si lo expone) un detector cargado."""
    if not callable(getattr(pipeline, "analyze_live", None)):
        return False
    return getattr(pipeline, "detector", True) is not None


# ----------------------------------------------------------------------
# Lectura tolerante del resultado (objeto o diccionario)
# ----------------------------------------------------------------------
def _get(item, *names, default=None):
    """Primer campo que exista y no sea None, en un diccionario o un objeto."""
    for name in names:
        if isinstance(item, dict):
            value = item.get(name)
        else:
            value = getattr(item, name, None)
        if value is not None:
            return value
    return default


def _objects(result):
    return _get(result, "objects", "detections", default=[]) or []


def _total_ms(result):
    value = _get(result, "total_ms")
    if value is None:
        timings = _get(result, "timings_ms", default={})
        if isinstance(timings, dict):
            value = timings.get("total_ms")
    return value


def _bbox(item):
    box = _get(item, "bbox", "box")
    if box is None:
        return None
    if isinstance(box, dict):
        values = [box.get(k) for k in ("xmin", "ymin", "xmax", "ymax")]
    else:
        values = list(box)
    if len(values) != 4 or any(v is None for v in values):
        return None
    return tuple(int(v) for v in values)


def _label_text(item) -> str:
    detected_label = _get(item, "detected_label", "detection_label")
    classification = _get(item, "classification")
    if classification is None:
        return str(
            detected_label or _get(item, "label", default="objeto")
        )
    if isinstance(classification, str):
        label = classification
        score = _get(item, "classification_score", "score", "confidence")
    else:
        label = _get(classification, "label", default="?")
        score = _get(classification, "score")
    if detected_label:
        prefix = f"{detected_label} → "
        suffix = f" {score:.0%}" if isinstance(score, (int, float)) else ""
        return f"{prefix}{label}{suffix}"[:48]
    if isinstance(score, (int, float)):
        return f"{label} {score:.0%}"
    return str(label)


def _color_for(bin_name):
    if not bin_name:
        return UNCERTAIN_COLOR
    key = "punto" if str(bin_name).startswith("punto") else str(bin_name)
    return BIN_COLORS.get(key, UNCERTAIN_COLOR)


def _text(img, text, origin, color):
    """Texto con contorno oscuro para que se lea sobre cualquier fondo."""
    cv2.putText(img, text, origin, FONT, 0.6, (0, 0, 0), 4)
    cv2.putText(img, text, origin, FONT, 0.6, color, 2)


def draw_result(img, result):
    """Dibuja cajas, etiquetas y la línea de estado sobre el fotograma (BGR)."""
    height, width = img.shape[:2]

    for item in _objects(result):
        box = _bbox(item)
        if box is None:
            continue
        x1, y1, x2, y2 = box
        x1, x2 = max(0, min(x1, width - 1)), max(0, min(x2, width - 1))
        y1, y2 = max(0, min(y1, height - 1)), max(0, min(y2, height - 1))

        color = _color_for(_get(item, "recycling_bin", "bin"))
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        _text(img, _label_text(item), (x1, max(y1 - 8, 18)), color)

    status = _get(result, "status", default="")
    if status == "no_es_residuo":
        banner = "No parece un residuo"
    else:
        ms = _total_ms(result)
        parts = [
            str(status),
            str(_get(result, "device", default="")),
            f"{ms:.0f} ms" if isinstance(ms, (int, float)) else "",
        ]
        banner = " | ".join(p for p in parts if p)
    if banner:
        _text(img, banner, (10, 24), (255, 255, 255))


# ----------------------------------------------------------------------
# Procesador de video
# ----------------------------------------------------------------------
class DetectorProcessor(VideoProcessorBase):
    """Recibe los fotogramas, los manda a analizar y dibuja el último resultado."""

    def __init__(self, analyze_fn, interval: float = 0.5):
        self._analyze = analyze_fn  # imagen PIL -> resultado
        self.interval = interval  # segundos mínimos entre análisis
        self._lock = threading.Lock()
        self._latest = None  # último fotograma RGB pendiente de analizar
        self._result = None  # último resultado
        self._error = None  # último error del análisis (texto) o None
        self._last_submit = 0.0
        self._logged_first_frame = False
        self._logged_first_result = False
        self._stop = threading.Event()
        self._worker = threading.Thread(target=self._loop, daemon=True)
        self._worker.start()

    # ---- hilo de análisis -------------------------------------------------
    def _loop(self):
        while not self._stop.is_set():
            with self._lock:
                pending, self._latest = self._latest, None
            if pending is None:
                time.sleep(0.02)
                continue
            frame, scale_x, scale_y = pending
            try:
                result = self._analyze(Image.fromarray(frame))
                if scale_x != 1.0 or scale_y != 1.0:
                    for item in _objects(result):
                        box = _bbox(item)
                        if box is not None and isinstance(item, dict):
                            item["box"] = [
                                round(box[0] * scale_x), round(box[1] * scale_y),
                                round(box[2] * scale_x), round(box[3] * scale_y),
                            ]
            except Exception as error:
                # Nunca se silencia: queda en el log y se dibuja en el video.
                logger.exception("Falló el análisis del fotograma")
                with self._lock:
                    self._error = f"{type(error).__name__}: {error}"
                time.sleep(0.5)
                continue
            with self._lock:
                self._result = result
                self._error = None
                should_log_result = not self._logged_first_result
                self._logged_first_result = True
            if should_log_result:
                logger.info("Cámara WebRTC: terminó correctamente el primer análisis de fotograma.")

    def on_ended(self):
        self._stop.set()

    @property
    def last_result(self):
        """Último resultado (o None). Útil si app.py quiere mostrarlo aparte."""
        with self._lock:
            return self._result

    @property
    def last_error(self):
        """Último error del análisis (texto) o None si todo va bien."""
        with self._lock:
            return self._error

    # ---- hilo de video ----------------------------------------------------
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")

        if not self._logged_first_frame:
            self._logged_first_frame = True
            logger.info(
                "Cámara WebRTC: llegó el primer fotograma al servidor (%s × %s).",
                img.shape[1],
                img.shape[0],
            )

        now = time.time()
        if now - self._last_submit >= self.interval:
            frame_width, frame_height = img.shape[1], img.shape[0]
            scale = min(
                1.0,
                LIVE_ANALYSIS_MAX_WIDTH / frame_width,
                LIVE_ANALYSIS_MAX_HEIGHT / frame_height,
            )
            if scale < 1.0:
                analysis_frame = cv2.resize(
                    img,
                    (max(1, round(frame_width * scale)), max(1, round(frame_height * scale))),
                    interpolation=cv2.INTER_AREA,
                )
            else:
                analysis_frame = img
            analysis_height, analysis_width = analysis_frame.shape[:2]
            with self._lock:
                # Keep the newest pending frame; after slow inference, don't
                # analyze an old frame that was queued at the start of it.
                self._latest = (
                    cv2.cvtColor(analysis_frame, cv2.COLOR_BGR2RGB),
                    frame_width / analysis_width,
                    frame_height / analysis_height,
                )
                self._last_submit = now

        with self._lock:
            result = self._result
            error = self._error
        if result is not None:
            draw_result(img, result)
        if error:
            _text(img, f"Error: {error[:70]}", (10, 48), (0, 0, 255))

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ----------------------------------------------------------------------
# Función pública para app.py
# ----------------------------------------------------------------------
def render_live_camera(
    pipeline=None,
    key: str = DEFAULT_KEY,
    interval: float = 0.5,
    rtc_configuration=None,
    analyze_fn=None,
):
    """Muestra la cámara en vivo con las detecciones dibujadas.

    No agrega títulos ni textos: eso lo decide app.py.
    Devuelve el contexto de streamlit-webrtc (ctx.state.playing indica si el
    video está activo; ctx.video_processor.last_error muestra el último error).
    """
    analyze = analyze_fn or getattr(pipeline, "analyze_live", None)
    if not callable(analyze):
        raise ValueError("Se necesita un pipeline con analyze_live o un analyze_fn.")

    return webrtc_streamer(
        key=key,
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=rtc_configuration or _configured_rtc_config(),
        media_stream_constraints={
            "video": {"width": {"ideal": 1280}, "height": {"ideal": 720}},
            "audio": False,
        },
        video_processor_factory=lambda: DetectorProcessor(analyze, interval),
        async_processing=True,
    )
