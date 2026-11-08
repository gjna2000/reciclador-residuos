import torch
from PIL import Image
from time import perf_counter
from .contracts import AnalysisResult, Prediction
from .models.gate import Gate
from .models.gdino_detector import GDinoDetector
from .models.waste_classifier import WasteClassifier
from .recycling_rules import get_recycling_recommendation
from .config import CLASSIFICATION_THRESHOLD


class RecyclingPipeline:
    """
    Pipeline principal para analizar imágenes de residuos.
    Carga los modelos una sola vez y coordina la validación,
    clasificación y recomendación.
    """
    def __init__(self, device: str = "cuda"):
        self.device = torch.device(device)
        if self.device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA no está disponible. Verifica la instalación de PyTorch y los controladores NVIDIA."
            )
        
        # Cargar los modelos una sola vez
        self.gate = Gate(device=str(self.device))
        self.classifier = WasteClassifier(device=str(self.device))
        self.detector = GDinoDetector()

    def _prepare_image(self, image) -> Image.Image:
        """Convierte la imagen a formato RGB de forma segura."""
        if image is None:
            raise ValueError("No se recibió ninguna imagen.")
        try:
            if isinstance(image, Image.Image):
                return image.convert("RGB")
            if hasattr(image, "seek"):
                image.seek(0)
            with Image.open(image) as opened_image:
                return opened_image.convert("RGB")
        except Exception as error:
            raise ValueError("No fue posible abrir la imagen.") from error

    def analyze(self, image) -> AnalysisResult:
        """Ejecuta el pipeline completo de análisis de residuos."""
        total_start = perf_counter()
        timings = {}
        
        prepared_image = self._prepare_image(image)

        # 1. Filtro general (Gate CLIP)
        start = perf_counter()
        is_waste, gate_score = self.gate.is_waste(prepared_image)
        timings["gate_ms"] = (perf_counter() - start) * 1000

        if not is_waste:
            timings["total_ms"] = (perf_counter() - total_start) * 1000
            return AnalysisResult(
                status="no_es_residuo",
                top=[],
                bin=None,
                tip="La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.",
                device=str(self.device),
                timings_ms=timings
            )

        
# 2. Detectar objetos con Grounding DINO
start = perf_counter()
detections = self.detector.detect(prepared_image)
timings["detection_ms"] = (perf_counter() - start) * 1000

if not detections:
    timings["total_ms"] = (perf_counter() - total_start) * 1000

    return AnalysisResult(
        status="no_es_residuo",
        top=[],
        bin=None,
        tip="No se detectaron residuos en la imagen.",
        device=str(self.device),
        timings_ms=timings
    )

# 3. Clasificar individualmente cada objeto
start = perf_counter()

predictions = []
object_results = []

for detection in detections:

    xmin, ymin, xmax, ymax = detection["box"]

    # Recortar objeto detectado
    crop = prepared_image.crop(
        (xmin, ymin, xmax, ymax)
    )

    # Clasificar el recorte
    crop_predictions = self.classifier.classify(crop)

    if not crop_predictions:
        continue

    best_pred = crop_predictions[0]

    # Obtener recomendación de reciclaje
    recommendation = get_recycling_recommendation(
        best_pred.label
    )

    # Guardar resultado individual
    object_results.append({
        "detected_label": detection["label"],
        "detection_score": detection["score"],
        "box": detection["box"],
        "classification": best_pred.label,
        "classification_score": best_pred.score,
        "bin": recommendation["bin"],
        "tip": recommendation["tip"]
    })

    predictions.append(best_pred)

timings["classifier_ms"] = (perf_counter() - start) * 1000

# 4. Construir resultado general
if object_results:
    first_object = object_results[0]

    waste_bin = first_object["bin"]
    tip = first_object["tip"]
    status = "reciclable"
else:
    waste_bin = None
    tip = "No fue posible clasificar los objetos detectados."
    status = "incierto"

                return AnalysisResult(
                    status="incierto",
                    top=predictions,
                    bin=None,
                    tip="El sistema no tiene suficiente confianza en el resultado. Toma otra fotografía con mejor iluminación.",
                    device=str(self.device),
                    timings_ms=timings
                )

            recommendation = get_recycling_recommendation(best_pred.label)
            waste_bin = recommendation["bin"]
            tip = recommendation["tip"]
            status = "reciclable"
        else:
            waste_bin = None
            tip = "No fue posible identificar el residuo."
            status = "incierto"

        timings["total_ms"] = (perf_counter() - total_start) * 1000
        return AnalysisResult(
            status=status,
            top=predictions,
            bin=waste_bin,
            tip=tip,
            device=str(self.device),
            timings_ms=timings
        )
