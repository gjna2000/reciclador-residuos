
from ultralytics import YOLO
import torch


class YOLODetector:
    """
    Detector de objetos mediante YOLO.

    Detecta objetos, obtiene sus coordenadas,
    clases y niveles de confianza.
    """

    def __init__(
        self,
        model_name: str = "yolo26n.pt",
        device: str = "cuda"
    ):
        self.device = device

        if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA no está disponible.")

        # Cargar modelo YOLO.
        self.model = YOLO(model_name)

    def detect(self, image, confidence: float = 0.25):
        """
        Detecta objetos presentes en una imagen.

        Retorna una lista de detecciones.
        """

        results = self.model.predict(
            source=image,
            conf=confidence,
            device=self.device,
            verbose=False
        )

        detections = []

        for result in results:
            boxes = result.boxes

            if boxes is None:
                continue

            for box in boxes:
                class_id = int(box.cls[0])
                score = float(box.conf[0])

                x1, y1, x2, y2 = (
                    box.xyxy[0].tolist()
                )

                detections.append({
                    "class_id": class_id,
                    "label": self.model.names[class_id],
                    "confidence": score,
                    "bbox": [
                        int(x1),
                        int(y1),
                        int(x2),
                        int(y2)
                    ]
                })

        return detections

    def count_objects(self, detections):
        """
        Cuenta los objetos detectados por categoría.
        """

        counts = {}

        for detection in detections:
            label = detection["label"]

            counts[label] = counts.get(label, 0) + 1

        return counts
