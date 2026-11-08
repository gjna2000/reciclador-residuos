import torch
from PIL import Image
from time import perf_counter
from .contracts import AnalysisResult, Prediction
from .models.gate import Gate
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

        # 2. Clasificador de residuos
        start = perf_counter()
        predictions = self.classifier.classify(prepared_image)
        timings["classifier_ms"] = (perf_counter() - start) * 1000

        # 3. Validar umbral de confianza y reglas de reciclaje
        if predictions:
            best_pred = predictions[0]
            if best_pred.score < CLASSIFICATION_THRESHOLD:
                timings["total_ms"] = (perf_counter() - total_start) * 1000
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
