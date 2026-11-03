

import torch
from PIL import Image

from .analyze import analyze as run_analysis
from .contracts import AnalysisResult
from .models.gate import Gate
from .models.waste_classifier import WasteClassifier


class RecyclingPipeline:
    """
    Pipeline principal para analizar imágenes de residuos.
    Carga los modelos una sola vez y coordina el análisis.
    """

    def __init__(self, device: str | None = None):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = torch.device(device)

        if self.device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA no está disponible.")

        self.gate = Gate(device=str(self.device))
        self.classifier = WasteClassifier(device=str(self.device))

    def _prepare_image(self, image) -> Image.Image:
        """Convierte una imagen, archivo o ruta a RGB."""

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
            raise ValueError(
                "No fue posible abrir la imagen. "
                "Verifica que sea válida."
            ) from error

    def analyze(self, image) -> AnalysisResult:
        """Ejecuta el análisis completo."""

        prepared_image = self._prepare_image(image)

        return run_analysis(
            image=prepared_image,
            gate=self.gate,
            classifier=self.classifier,
            device=str(self.device)
        )


# Instancias reutilizables
_pipelines = {}


def analyze(
    image: Image.Image,
    device: str | None = None
) -> AnalysisResult:
    """Interfaz pública para analizar imágenes."""

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    if device not in _pipelines:
        _pipelines[device] = RecyclingPipeline(device=device)

    return _pipelines[device].analyze(image)

