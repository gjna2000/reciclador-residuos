
"""
Grounding DINO detector for the waste recycling project.
"""

from dataclasses import dataclass
from typing import Any

import torch
from transformers import pipeline
from PIL import Image


@dataclass
class Detection:
    label: str
    score: float
    box: tuple[int, int, int, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "score": self.score,
            "box": list(self.box),
        }


class GDinoDetector:

    MODEL_ID = "IDEA-Research/grounding-dino-tiny"

    LABELS = [
        "trash",
        "waste",
        "packaging",
        "wrapper",
        "peel",
        "bottle",
        "can",
    ]

    def __init__(
        self,
        threshold: float = 0.20,
        max_area: float = 0.70,
        top_n: int = 4,
    ):
        self.threshold = threshold
        self.max_area = max_area
        self.top_n = top_n

        self.device = 0 if torch.cuda.is_available() else -1

        print(
            f"Loading Grounding DINO on "
            f"{'CUDA' if self.device == 0 else 'CPU'}..."
        )

        self.detector = pipeline(
            task="zero-shot-object-detection",
            model=self.MODEL_ID,
            device=self.device,
        )

        print("Grounding DINO loaded successfully.")

    @staticmethod
    def _area(box: dict, image_area: int) -> float:
        width = max(0, box["xmax"] - box["xmin"])
        height = max(0, box["ymax"] - box["ymin"])
        return (width * height) / image_area

    @staticmethod
    def _iou(box_a: tuple, box_b: tuple) -> float:
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b

        x1 = max(ax1, bx1)
        y1 = max(ay1, by1)
        x2 = min(ax2, bx2)
        y2 = min(ay2, by2)

        intersection = max(0, x2 - x1) * max(0, y2 - y1)

        area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
        area_b = max(0, bx2 - bx1) * max(0, by2 - by1)

        union = area_a + area_b - intersection

        return intersection / union if union > 0 else 0.0

    def _nms(
        self,
        detections: list[Detection],
        iou_threshold: float = 0.50,
    ) -> list[Detection]:

        detections = sorted(
            detections,
            key=lambda item: item.score,
            reverse=True,
        )

        selected = []

        for detection in detections:
            overlapping = any(
                self._iou(detection.box, existing.box) > iou_threshold
                for existing in selected
            )

            if not overlapping:
                selected.append(detection)

        return selected

    def detect(self, image: Image.Image) -> list[dict]:

        if not isinstance(image, Image.Image):
            raise TypeError("image must be a PIL.Image.Image")

        image = image.convert("RGB")

        width, height = image.size
        image_area = width * height

        results = self.detector(
            image,
            candidate_labels=self.LABELS,
            threshold=self.threshold,
        )

        detections = []

        for result in results:

            box = result["box"]

            xmin = max(0, min(width, int(box["xmin"])))
            ymin = max(0, min(height, int(box["ymin"])))
            xmax = max(0, min(width, int(box["xmax"])))
            ymax = max(0, min(height, int(box["ymax"])))

            normalized_box = {
                "xmin": xmin,
                "ymin": ymin,
                "xmax": xmax,
                "ymax": ymax,
            }

            area_ratio = self._area(normalized_box, image_area)

            if area_ratio <= 0 or area_ratio > self.max_area:
                continue

            detections.append(
                Detection(
                    label=result["label"],
                    score=float(result["score"]),
                    box=(xmin, ymin, xmax, ymax),
                )
            )

        detections = self._nms(detections)

        detections = sorted(
            detections,
            key=lambda item: item.score,
            reverse=True,
        )[:self.top_n]

        return [detection.to_dict() for detection in detections]
