
from dataclasses import dataclass


@dataclass
class Prediction:
    label: str
    score: float
    
@dataclass
class DetectedObject:
    """
    Representa un objeto detectado por YOLO
    y posteriormente clasificado.
    """

    detection_label: str
    bbox: tuple[int, int, int, int]
    detection_score: float

    classification: Prediction | None = None

    recycling_bin: str | None = None
    recycling_tip: str = ""

@dataclass
class AnalysisResult:
    status: str
    top: list[Prediction]
    bin: str | None
    tip: str
    device: str
    timings_ms: dict[str, float]

    # Objetos detectados y clasificados individualmente.
    objects: list[DetectedObject] = field(default_factory=list)
