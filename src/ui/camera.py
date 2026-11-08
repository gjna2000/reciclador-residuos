"""Cámara en tiempo real: detecta objetos con YOLO y los clasifica.

Uso desde app.py:
    from src.ui.camera import render_camera_tab
    render_camera_tab(pipeline)

La interfaz solo habla con RecyclingPipeline (analyze y analyze_live);
no importa modelos. El análisis corre en un hilo aparte para que el video
no se congele.
"""

import threading
import time

import av
import cv2
import streamlit as st
from PIL import Image
from streamlit_webrtc import (
    RTCConfiguration,
    VideoProcessorBase,
    WebRtcMode,
    webrtc_streamer,
)

RTC_CONFIG = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# Colores BGR (OpenCV) según el contenedor recomendado
BIN_COLORS = {
    "blanco": (240, 240, 240),
    "negro": (90, 90, 90),
    "verde": (60, 180, 60),
    "punto": (0, 165, 255),  # punto especial (acepta punto_especial o punto-especial)
}
UNCERTAIN_COLOR = (150, 150, 150)
FONT = cv2.FONT_HERSHEY_SIMPLEX


def _color_for(bin_name):
    if not bin_name:
        return UNCERTAIN_COLOR
    key = "punto" if bin_name.startswith("punto") else bin_name
    return BIN_COLORS.get(key, UNCERTAIN_COLOR)


def _text(img, text, origin, color):
    """Texto con contorno oscuro para que se lea sobre cualquier fondo."""
    cv2.putText(img, text, origin, FONT, 0.6, (0, 0, 0), 4)
    cv2.putText(img, text, origin, FONT, 0.6, color, 2)


class DetectorProcessor(VideoProcessorBase):
    """Recibe los fotogramas, los manda a analizar y dibuja el último resultado."""

    def __init__(self, pipeline, interval: float = 0.5):
        self.pipeline = pipeline
        self.interval = interval  # segundos mínimos entre análisis
        self._lock = threading.Lock()
        self._latest = None  # último fotograma RGB pendiente de analizar
        self._result = None  # último LiveResult
        self._last_submit = 0.0
        self._stop = threading.Event()
        self._worker = threading.Thread(target=self._loop, daemon=True)
        self._worker.start()

    # ---- hilo de análisis -------------------------------------------------
    def _loop(self):
        while not self._stop.is_set():
            with self._lock:
                frame, self._latest = self._latest, None
            if frame is None:
                time.sleep(0.02)
                continue
            try:
                result = self.pipeline.analyze_live(Image.fromarray(frame))
            except Exception:
                time.sleep(0.5)
                continue
            with self._lock:
                self._result = result

    def on_ended(self):
        self._stop.set()

    # ---- hilo de video ----------------------------------------------------
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")

        now = time.time()
        if now - self._last_submit >= self.interval:
            with self._lock:
                if self._latest is None:
                    self._latest = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    self._last_submit = now

        with self._lock:
            result = self._result
        if result is not None:
            self._draw(img, result)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    @staticmethod
    def _draw(img, result):
        for obj in result.objects:
            x1, y1, x2, y2 = obj.bbox
            color = _color_for(obj.recycling_bin)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            if obj.classification:
                label = f"{obj.classification.label} {obj.classification.score:.0%}"
            else:
                label = obj.detection_label
            _text(img, label, (x1, max(y1 - 8, 18)), color)

        if result.status == "no_es_residuo":
            banner = "No parece un residuo"
        else:
            banner = f"{result.status} | {result.device} | {result.total_ms:.0f} ms"
        _text(img, banner, (10, 24), (255, 255, 255))


def render_camera_tab(pipeline):
    """Pestaña de cámara en vivo, con respaldo de foto instantánea."""
    st.subheader("Cámara en tiempo real")
    st.caption(
        "Pulsa START, permite el acceso a la cámara y apunta a un residuo. "
        "Blanco, negro, verde y naranja indican la caneca recomendada."
    )

    webrtc_streamer(
        key="camara-residuos",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTC_CONFIG,
        media_stream_constraints={
            "video": {"width": {"ideal": 640}, "height": {"ideal": 480}},
            "audio": False,
        },
        video_processor_factory=lambda: DetectorProcessor(pipeline),
        async_processing=True,
    )

    with st.expander("¿No funciona el video? Usa una foto"):
        photo = st.camera_input("Toma una foto del residuo")
        if photo:
            result = pipeline.analyze(photo)
            if result.status == "reciclable":
                st.success(f"Caneca: {result.bin}. {result.tip}")
            elif result.status == "no_es_residuo":
                st.warning(result.tip)
            else:
                st.info(result.tip)
            for prediction in result.top:
                st.write(f"{prediction.label}: {prediction.score:.1%}")
