
from dataclasses import dataclass, field


@dataclass
class Prediction:
    label: str
    score: float
    
@dataclass
class AnalysisResult:
    status: str
    top: list[Prediction]
    bin: str | None
    tip: str
    device: str
    timings_ms: dict[str, float]
    objects: list[dict] = field(default_factory=list)
