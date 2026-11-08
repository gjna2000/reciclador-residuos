"""Tipos de la detección en tiempo real.

Viven aparte de contracts.py (que mantiene Aura) para no modificar su contrato.
Solo reutilizan Prediction.
"""

from dataclasses import dataclass, field

from .contracts import Prediction


@dataclass
class DetectedObject:
    """Objeto detectado por YOLO y clasificado individualmente."""

    detection_label: str
    bbox: tuple[int, int, int, int]
    detection_score: float
    classification: Prediction | None = None
    recycling_bin: str | None = None
    recycling_tip: str = ""


@dataclass
class LiveResult:
    """Resultado de analizar un fotograma de la cámara."""

    status: str  # "reciclable" | "no_es_residuo" | "incierto"
    device: str
    total_ms: float
    objects: list[DetectedObject] = field(default_factory=list)
