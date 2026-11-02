
import torch
from transformers import CLIPModel, CLIPProcessor

from ..config import GATE_MODEL_ID, CLASSIFICATION_THRESHOLD


class Gate:

    def __init__(self, device="cuda"):
        self.device = device

        self.processor = CLIPProcessor.from_pretrained(
            GATE_MODEL_ID
        )

        self.model = CLIPModel.from_pretrained(
            GATE_MODEL_ID
        ).to(self.device)

        self.model.eval()

        self.labels = [
            "a photograph of a waste item, such as plastic, paper, metal or glass",
            "a photograph of something that is not waste, such as a person, animal or landscape"
        ]

    def is_waste(self, image) -> tuple[bool, float]:

        inputs = self.processor(
            text=self.labels,
            images=image,
            return_tensors="pt",
            padding=True
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        with torch.inference_mode():
            outputs = self.model(**inputs)

            probabilities = outputs.logits_per_image.softmax(dim=1)

        score = probabilities[0][0].item()

        return (
            score >= CLASSIFICATION_THRESHOLD,
            score
        )
