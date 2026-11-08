
from dataclasses import dataclass
from typing import Any

import torch
from PIL import Image
from transformers import pipeline

from ..config import (
    GDINO_MODEL_ID,
    GDINO_THRESHOLD,
    GDINO_MAX_AREA,
    GDINO_NMS_IOU,
    GDINO_TOP_N,
    GDINO_LABELS,
)


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

    def __init__(self, device: str = "cuda"):
        self.model_id = GDINO_MODEL_ID
        self.threshold = GDINO_THRESHOLD
        self.max_area = GDINO_MAX_AREA
        self.nms_iou = GDINO_NMS_IOU
        self.top_n = GDINO_TOP_N
        self.labels = GDINO_LABELS

        self.device = torch.device(device)

        if self.device.type == "cuda":
            if not torch.cuda.is_available():
                raise RuntimeError(
                    "CUDA fue solicitado, pero no está disponible."
                )
            self.pipeline_device = self.device.index
            if self.pipeline_device is None:
                self.pipeline_device = 0

        elif self.device.type == "cpu":
            self.pipeline_device = -1

        else:
            raise ValueError(
                f"Dispositivo no compatible: {self.device}"
            )

        print(
            f"Cargando Grounding DINO en {self.device}..."
        )

        self.detector = pipeline(
            task="zero-shot-object-detection",
            model=self.model_id,
            device=self.pipeline_device,
        )

        print("Grounding DINO cargado correctamente.")

    @staticmethod
    def _area(box: dict, image_area: int) -> float:
        width = max(0, box["xmax"] - box["xmin"])
        height = max(0, box["ymax"] - box["ymin"])

        if image_area <= 0:
            return 0.0

        return (width * height) / image_area

    @staticmethod
    def _iou(
        box_a: tuple[int, int, int, int],
        box_b: tuple[int, int, int, int],
    ) -> float:

        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b

        x1 = max(ax1, bx1)
        y1 = max(ay1, by1)
        x2 = min(ax2, bx2)
        y2 = min(ay2, by2)

        intersection = (
            max(0, x2 - x1) * max(0, y2 - y1)
        )

        area_a = (
            max(0, ax2 - ax1) * max(0, ay2 - ay1)
        )
        area_b = (
            max(0, bx2 - bx1) * max(0, by2 - by1)
        )

        union = area_a + area_b - intersection

        return intersection / union if union > 0 else 0.0

    def _nms(
        self,
        detections: list[Detection],
    ) -> list[Detection]:

        ordered = sorted(
            detections,
            key=lambda item: item.score,
            reverse=True,
        )

        selected = []

        for detection in ordered:
            overlaps = any(
                self._iou(detection.box, existing.box)
                > self.nms_iou
                for existing in selected
            )

            if not overlaps:
                selected.append(detection)

        return selected

    def detect(self, image: Image.Image) -> list[dict]:

        if not isinstance(image, Image.Image):
            raise TypeError(
                "image debe ser una instancia de PIL.Image.Image"
            )

        image = image.convert("RGB")

        width, height = image.size
        image_area = width * height

        if image_area <= 0:
            return []

        results = self.detector(
            image,
            candidate_labels=self.labels,
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

            area_ratio = self._area(
                normalized_box,
                image_area,
            )

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

        return [
            detection.to_dict()
            for detection in detections
        ]
