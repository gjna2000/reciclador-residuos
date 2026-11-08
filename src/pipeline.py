"""Pipeline principal de análisis de residuos.

analyze(image)       -> AnalysisResult (contrato de contracts.py, sin cambios)
analyze_live(image)  -> LiveResult (detección YOLO con cajas, para la cámara)

El dispositivo (cuda o cpu) se elige solo en device.py.
"""

from threading import Lock
from time import perf_counter

from PIL import Image

from .config import CLASSIFICATION_THRESHOLD
from .contracts import AnalysisResult
from .detection import DetectedObject, LiveResult
from .device import get_device, sync
from .models.gate import Gate
from .models.waste_classifier import WasteClassifier
from .recycling_rules import get_recycling_recommendation

# Límites para no saturar la GPU cuando YOLO detecta muchos objetos.
MAX_OBJECTS = 5
MIN_BOX_SIDE = 32  # píxeles

TIP_NO_RESIDUO = (
    "La imagen no parece contener un residuo o no es un objeto válido. "
    "Intenta con otra fotografía."
)
TIP_INCIERTO = (
    "El sistema no tiene suficiente confianza en el resultado. "
    "Toma otra fotografía con mejor iluminación."
)
TIP_SIN_RESULTADO = "No fue posible identificar el residuo."


class RecyclingPipeline:
    """Carga los modelos una sola vez y coordina todo el análisis."""

    def __init__(self, device: str | None = None, use_detector: bool = True):
        # La elección del dispositivo vive solo en device.py.
        self.device = device or get_device()

        self.gate = Gate(device=self.device)
        self.classifier = WasteClassifier(device=self.device)

        # Importación diferida: sin ultralytics el resto sigue funcionando.
        self.detector = None
        if use_detector:
            try:
                from .models.yolo_detector import YOLODetector

                self.detector = YOLODetector(device=self.device)
            except ImportError:
                # Sin ultralytics o sin yolo_detector.py solo funciona analyze().
                self.detector = None

        # Los modelos se comparten; evita análisis simultáneos (video en vivo).
        self._lock = Lock()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def analyze(self, image) -> AnalysisResult:
        """Análisis de una imagen completa (contrato original)."""
        with self._lock:
            return self._analyze(image)

    def analyze_live(self, image) -> LiveResult:
        """Detecta objetos con YOLO y clasifica cada uno (para la cámara)."""
        if self.detector is None:
            raise RuntimeError("El detector YOLO está desactivado.")
        with self._lock:
            return self._analyze_live(image)

    # ------------------------------------------------------------------
    # analyze: igual que antes, con device.py y tiempos sincronizados
    # ------------------------------------------------------------------
    def _analyze(self, image) -> AnalysisResult:
        total_start = perf_counter()
        timings: dict[str, float] = {}

        prepared = self._prepare_image(image)

        # 1. Filtro general
        is_waste, _gate_score = self._run(
            timings, "gate_ms", self.gate.is_waste, prepared
        )
        if not is_waste:
            return self._build(
                "no_es_residuo", [], None, TIP_NO_RESIDUO, timings, total_start
            )

        # 2. Clasificador de residuos
        predictions = self._run(
            timings, "classifier_ms", self.classifier.classify, prepared
        )

        # 3. Umbral de confianza y reglas de reciclaje
        if not predictions:
            return self._build(
                "incierto", predictions, None, TIP_SIN_RESULTADO, timings, total_start
            )

        if predictions[0].score < CLASSIFICATION_THRESHOLD:
            return self._build(
                "incierto", predictions, None, TIP_INCIERTO, timings, total_start
            )

        rec = get_recycling_recommendation(predictions[0].label)
        return self._build(
            "reciclable", predictions, rec["bin"], rec["tip"], timings, total_start
        )

    # ------------------------------------------------------------------
    # analyze_live: YOLO + clasificación por objeto
    # ------------------------------------------------------------------
    def _analyze_live(self, image) -> LiveResult:
        total_start = perf_counter()
        timings: dict[str, float] = {}

        prepared = self._prepare_image(image)

        is_waste, _gate_score = self._run(
            timings, "gate_ms", self.gate.is_waste, prepared
        )
        if not is_waste:
            return self._live("no_es_residuo", [], total_start)

        detections = self._run(timings, "detector_ms", self.detector.detect, prepared)
        objects = self._classify_detections(prepared, detections, timings)

        # Respaldo: si YOLO no encontró nada útil, clasifica la imagen completa
        if not any(obj.recycling_bin for obj in objects):
            full = self._classify_full_image(prepared, timings)
            if full is not None:
                objects.append(full)

        status = "reciclable" if any(o.recycling_bin for o in objects) else "incierto"
        return self._live(status, objects, total_start)

    def _classify_detections(self, image: Image.Image, detections, timings):
        valid = [d for d in detections if self._box_is_valid(d["bbox"])]
        valid.sort(key=lambda d: d["confidence"], reverse=True)

        objects = []
        for det in valid[:MAX_OBJECTS]:
            x1, y1, x2, y2 = det["bbox"]
            crop = image.crop((x1, y1, x2, y2))
            predictions = self._run(
                timings, "classifier_ms", self.classifier.classify, crop
            )
            objects.append(
                self._to_object(det["label"], (x1, y1, x2, y2), det["confidence"], predictions)
            )
        return objects

    def _classify_full_image(self, image: Image.Image, timings):
        predictions = self._run(
            timings, "classifier_ms", self.classifier.classify, image
        )
        if not predictions or predictions[0].score < CLASSIFICATION_THRESHOLD:
            return None
        width, height = image.size
        return self._to_object("imagen completa", (0, 0, width, height), 1.0, predictions)

    @staticmethod
    def _to_object(label, bbox, score, predictions) -> DetectedObject:
        obj = DetectedObject(
            detection_label=label, bbox=bbox, detection_score=score
        )
        if predictions:
            obj.classification = predictions[0]
            if predictions[0].score >= CLASSIFICATION_THRESHOLD:
                rec = get_recycling_recommendation(predictions[0].label)
                obj.recycling_bin = rec["bin"]
                obj.recycling_tip = rec["tip"]
        return obj

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    @staticmethod
    def _box_is_valid(bbox) -> bool:
        x1, y1, x2, y2 = bbox
        return (x2 - x1) >= MIN_BOX_SIDE and (y2 - y1) >= MIN_BOX_SIDE

    @staticmethod
    def _run(timings: dict, key: str, fn, *args):
        """Ejecuta fn midiendo el tiempo; sincroniza la GPU antes y después."""
        sync()
        start = perf_counter()
        result = fn(*args)
        sync()
        timings[key] = timings.get(key, 0.0) + (perf_counter() - start) * 1000
        return result

    def _build(self, status, top, waste_bin, tip, timings, total_start):
        timings["total_ms"] = (perf_counter() - total_start) * 1000
        return AnalysisResult(
            status=status,
            top=top,
            bin=waste_bin,
            tip=tip,
            device=self.device,
            timings_ms=timings,
        )

    def _live(self, status, objects, total_start) -> LiveResult:
        return LiveResult(
            status=status,
            device=self.device,
            total_ms=(perf_counter() - total_start) * 1000,
            objects=objects,
        )

    @staticmethod
    def _prepare_image(image) -> Image.Image:
        """Convierte imagen PIL, archivo o ruta a RGB de forma segura."""
        if image is None:
            raise ValueError("No se recibió ninguna imagen.")
        try:
            if isinstance(image, Image.Image):
                return image.convert("RGB")
            if hasattr(image, "seek"):
                image.seek(0)
            with Image.open(image) as opened:
                return opened.convert("RGB")
        except Exception as error:
            raise ValueError("No fue posible abrir la imagen.") from error