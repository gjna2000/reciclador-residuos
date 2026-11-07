"""Pipeline principal de análisis de residuos.

Flujo de una imagen:
    1. Filtro general (Gate): ¿la imagen contiene un residuo?
    2. Detector YOLO (opcional): encuentra objetos y sus cajas.
    3. Clasificador de residuos: clasifica cada recorte (o la imagen completa
       si YOLO no encuentra nada útil).
    4. Reglas de reciclaje: contenedor y consejo.

El dispositivo (cuda o cpu) se elige solo en device.py.
"""

from threading import Lock
from time import perf_counter

from PIL import Image

from .config import CLASSIFICATION_THRESHOLD
from .contracts import AnalysisResult, DetectedObject
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

        # Importación diferida: si ultralytics no está instalado,
        # el resto del pipeline sigue funcionando con use_detector=False.
        self.detector = None
        if use_detector:
            from .models.yolo_detector import YOLODetector

            self.detector = YOLODetector(device=self.device)

        # Los modelos se comparten; evita dos análisis simultáneos
        # (por ejemplo, con video en tiempo real).
        self._lock = Lock()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def analyze(self, image, detect: bool = True) -> AnalysisResult:
        """Ejecuta el análisis completo sobre una imagen."""
        with self._lock:
            return self._analyze(image, detect)

    # ------------------------------------------------------------------
    # Lógica interna
    # ------------------------------------------------------------------
    def _analyze(self, image, detect: bool) -> AnalysisResult:
        total_start = perf_counter()
        timings: dict[str, float] = {}

        prepared = self._prepare_image(image)

        # 1. Filtro general
        is_waste, _gate_score = self._run(
            timings, "gate_ms", self.gate.is_waste, prepared
        )
        if not is_waste:
            return self._build(
                "no_es_residuo", [], None, TIP_NO_RESIDUO, [], timings, total_start
            )

        # 2 y 3. Detección y clasificación por objeto
        object_results = []
        if detect and self.detector is not None:
            detections = self._run(
                timings, "detector_ms", self.detector.detect, prepared
            )
            object_results = self._classify_detections(
                prepared, detections, timings
            )

        objects = [obj for obj, _ in object_results]

        # Resultado principal: el objeto clasificado con mayor confianza
        confident = [
            (obj, preds)
            for obj, preds in object_results
            if obj.recycling_bin is not None
        ]
        if confident:
            obj, preds = max(confident, key=lambda t: t[0].classification.score)
            return self._build(
                "reciclable",
                preds,
                obj.recycling_bin,
                obj.recycling_tip,
                objects,
                timings,
                total_start,
            )

        # Respaldo: clasificar la imagen completa (YOLO no detectó nada útil)
        predictions = self._run(
            timings, "classifier_ms", self.classifier.classify, prepared
        )
        if predictions and predictions[0].score >= CLASSIFICATION_THRESHOLD:
            rec = get_recycling_recommendation(predictions[0].label)
            return self._build(
                "reciclable",
                predictions,
                rec["bin"],
                rec["tip"],
                objects,
                timings,
                total_start,
            )

        tip = TIP_INCIERTO if predictions else TIP_SIN_RESULTADO
        return self._build(
            "incierto", predictions, None, tip, objects, timings, total_start
        )

    def _classify_detections(self, image: Image.Image, detections, timings):
        """Clasifica el recorte de cada objeto detectado por YOLO."""
        valid = [d for d in detections if self._box_is_valid(d["bbox"])]
        valid.sort(key=lambda d: d["confidence"], reverse=True)

        results = []
        for det in valid[:MAX_OBJECTS]:
            x1, y1, x2, y2 = det["bbox"]
            crop = image.crop((x1, y1, x2, y2))

            predictions = self._run(
                timings, "classifier_ms", self.classifier.classify, crop
            )

            obj = DetectedObject(
                detection_label=det["label"],
                bbox=(x1, y1, x2, y2),
                detection_score=det["confidence"],
            )
            if predictions:
                obj.classification = predictions[0]
                if predictions[0].score >= CLASSIFICATION_THRESHOLD:
                    rec = get_recycling_recommendation(predictions[0].label)
                    obj.recycling_bin = rec["bin"]
                    obj.recycling_tip = rec["tip"]

            results.append((obj, predictions))
        return results

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

    def _build(self, status, top, waste_bin, tip, objects, timings, total_start):
        timings["total_ms"] = (perf_counter() - total_start) * 1000
        return AnalysisResult(
            status=status,
            top=top,
            bin=waste_bin,
            tip=tip,
            device=self.device,
            timings_ms=timings,
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