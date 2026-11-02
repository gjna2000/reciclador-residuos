
from pathlib import Path

import torch
from PIL import Image

from .analyze import analyze as run_analysis
from .contracts import AnalysisResult
from .models.gate import Gate
from .models.waste_classifier import WasteClassifier


class RecyclingPipeline:
    """
    Pipeline principal para analizar imágenes de residuos.

    Carga los modelos una sola vez y coordina
    la validación, clasificación y recomendación.
    """

    def __init__(self, device: str = "cuda"):
        self.device = torch.device(device)

        # Este proyecto está configurado para trabajar con CUDA.
        if self.device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA no está disponible. "
                "Verifica la instalación de PyTorch y los controladores NVIDIA."
            )

        # Cargar los modelos una sola vez.
        self.gate = Gate(device=str(self.device))
        self.classifier = WasteClassifier(device=str(self.device))

    def _prepare_image(self, image) -> Image.Image:
        """
        Recibe una imagen PIL, un archivo o una ruta
        y la convierte al formato RGB.
        """

        if image is None:
            raise ValueError("No se recibió ninguna imagen.")

        try:
            # Si ya es una imagen PIL.
            if isinstance(image, Image.Image):
                return image.convert("RGB")

            # Si es un archivo o una ruta.
            if hasattr(image, "seek"):
                image.seek(0)

            with Image.open(image) as opened_image:
                return opened_image.convert("RGB")

        except Exception as error:
            raise ValueError(
                "No fue posible abrir la imagen. "
                "Verifica que el archivo sea una imagen válida."
            ) from error

    def analyze(self, image) -> AnalysisResult:
        """
        Ejecuta el pipeline completo sobre una imagen.
        """

        prepared_image = self._prepare_image(image)

        return run_analysis(
            image=prepared_image,
            gate=self.gate,
            classifier=self.classifier,
            device=str(self.device)
        )
