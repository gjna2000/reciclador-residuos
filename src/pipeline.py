
from time import perf_counter

import torch
from PIL import Image

from .contracts import AnalysisResult
from .config import CLASSIFICATION_THRESHOLD
from .models.gate import Gate
from .models.gdino_detector import GDinoDetector
from .models.waste_classifier import WasteClassifier
from .recycling_rules import get_recycling_recommendation


class RecyclingPipeline:
    """
    Pipeline híbrido de detección y clasificación de residuos.

    Grounding DINO:
        Detecta residuos y genera cajas delimitadoras.

    WasteClassifier:
        Clasifica individualmente cada objeto detectado.

    RecyclingRules:
        Genera recomendaciones de reciclaje.
    """

    def __init__(self, device: str = "cuda"):
        self.device = torch.device(device)

        if self.device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA no está disponible. Verifica PyTorch y los "
                "controladores NVIDIA."
            )

        print(f"Cargando pipeline en {self.device}...")

        self.gate = Gate(device=str(self.device))
        self.detector = GDinoDetector(device=str(self.device))
        self.classifier = WasteClassifier(device=str(self.device))

        print("Pipeline cargado correctamente.")

    @staticmethod
    def _prepare_image(image) -> Image.Image:
        """Convierte cualquier imagen válida a RGB."""

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
                "No fue posible abrir la imagen."
            ) from error

    def analyze(self, image) -> AnalysisResult:
        """Detecta, clasifica y recomienda sobre cada objeto."""

        total_start = perf_counter()
        timings = {}

        prepared_image = self._prepare_image(image)

        # 1. Gate CLIP: información auxiliar, no bloquea DINO.
        start = perf_counter()

        try:
            is_waste, gate_score = self.gate.is_waste(
                prepared_image
            )
        except Exception:
            is_waste = None
            gate_score = None

        timings["gate_ms"] = (
            perf_counter() - start
        ) * 1000

        # 2. Detectar objetos con Grounding DINO.
        start = perf_counter()

        detections = self.detector.detect(
            prepared_image
        )

        timings["detection_ms"] = (
            perf_counter() - start
        ) * 1000

        # 3. Si no hay detecciones, devolver resultado.
        if not detections:
            timings["total_ms"] = (
                perf_counter() - total_start
            ) * 1000

            return AnalysisResult(
                status="no_es_residuo",
                top=[],
                bin=None,
                tip="No se detectaron residuos. "
                    "Intenta con otra fotografía.",
                device=str(self.device),
                timings_ms=timings,
                objects=[]
            )

        # 4. Clasificar individualmente cada objeto.
        object_results = []
        predictions = []

        classifier_start = perf_counter()

        image_width, image_height = prepared_image.size

        for detection in detections:

            xmin, ymin, xmax, ymax = detection["box"]

            # Validar y limitar las coordenadas.
            xmin = max(0, min(image_width, int(xmin)))
            ymin = max(0, min(image_height, int(ymin)))
            xmax = max(0, min(image_width, int(xmax)))
            ymax = max(0, min(image_height, int(ymax)))

            if xmax <= xmin or ymax <= ymin:
                continue

            # Recortar el objeto.
            crop = prepared_image.crop(
                (xmin, ymin, xmax, ymax)
            )

            # Clasificar el recorte.
            crop_predictions = self.classifier.classify(
                crop
            )

            if not crop_predictions:
                continue

            best_pred = crop_predictions[0]

            # Evaluar confianza.
            confident = (
                best_pred.score >= CLASSIFICATION_THRESHOLD
            )

            # Aplicar reglas únicamente a predicciones confiables.
            if confident:
                recommendation = get_recycling_recommendation(
                    best_pred.label
                )

                waste_bin = recommendation["bin"]
                tip = recommendation["tip"]

                predictions.append(best_pred)

            else:
                waste_bin = None
                tip = (
                    "Clasificación incierta. "
                    "Intenta tomar otra fotografía."
                )

            # Registrar información individual.
            object_results.append({
                "detected_label": detection["label"],
                "detection_score": float(detection["score"]),
                "box": [xmin, ymin, xmax, ymax],
                "classification": best_pred.label,
                "classification_score": float(best_pred.score),
                "bin": waste_bin,
                "tip": tip,
                "confident": confident
            })

        timings["classifier_ms"] = (
            perf_counter() - classifier_start
        ) * 1000

        # 5. Construir resultado general.
        if predictions:

            best_pred = max(
                predictions,
                key=lambda prediction: prediction.score
            )

            recommendation = get_recycling_recommendation(
                best_pred.label
            )

            status = "reciclable"
            waste_bin = recommendation["bin"]
            tip = recommendation["tip"]

        else:
            status = "incierto"
            waste_bin = None
            tip = (
                "Se detectaron objetos, pero no fue posible "
                "clasificarlos con suficiente confianza."
            )

        # 6. Finalizar análisis.
        timings["total_ms"] = (
            perf_counter() - total_start
        ) * 1000

        return AnalysisResult(
            status=status,
            top=predictions,
            bin=waste_bin,
            tip=tip,
            device=str(self.device),
            timings_ms=timings,
            objects=object_results
        )
