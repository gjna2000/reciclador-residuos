
import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification

from ..config import CLASSIFIER_MODEL_ID, TOP_K, USE_FP16
from ..contracts import Prediction


class WasteClassifier:

    def __init__(self, device="cuda"):
        self.device = torch.device(device)
        self.use_fp16 = USE_FP16

        self.processor = AutoImageProcessor.from_pretrained(
            CLASSIFIER_MODEL_ID
        )

        self.model = AutoModelForImageClassification.from_pretrained(
            CLASSIFIER_MODEL_ID
        ).to(self.device)

        self.model.eval()

    def classify(self, image) -> list[Prediction]:

        # Preparar imagen
        inputs = self.processor(
            images=image,
            return_tensors="pt"
        )

        pixel_values = inputs["pixel_values"].to(self.device)

        # Ejecutar inferencia
        with torch.inference_mode():

            if self.use_fp16 and self.device.type == "cuda":
                with torch.autocast(
                    device_type="cuda",
                    dtype=torch.float16
                ):
                    outputs = self.model(pixel_values=pixel_values)
            else:
                outputs = self.model(pixel_values=pixel_values)

            probabilities = torch.softmax(
                outputs.logits,
                dim=-1
            )[0]

        # Obtener las mejores predicciones
        k = min(TOP_K, len(probabilities))

        scores, indices = torch.topk(probabilities, k)

        predictions = []

        for score, index in zip(scores, indices):

            label = self.model.config.id2label[index.item()]

            predictions.append(
                Prediction(
                    label=label.title(),
                    score=score.item()
                )
            )

        return predictions
