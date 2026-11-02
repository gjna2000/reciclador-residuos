
from time import perf_counter

from .contracts import AnalysisResult
from .recycling_rules import get_recycling_recommendation


def analyze(image, gate, classifier, device="cuda") -> AnalysisResult:
    """
    Coordina la validación de la imagen,
    clasificación y recomendación de reciclaje.
    """

    total_start = perf_counter()
    timings = {}

    # 1. Verificar si la imagen contiene un residuo
    start = perf_counter()
    is_waste, gate_score = gate.is_waste(image)
    timings["gate_ms"] = (perf_counter() - start) * 1000

    # 2. Si no es un residuo, finalizar el análisis
    if not is_waste:
        timings["total_ms"] = (perf_counter() - total_start) * 1000

        return AnalysisResult(
            status="no_es_residuo",
            top=[],
            bin=None,
            tip="La imagen no parece contener un residuo. Intenta con otra imagen.",
            device=str(device),
            timings_ms=timings
        )

    # 3. Clasificar el residuo
    start = perf_counter()
    predictions = classifier.classify(image)
    timings["classifier_ms"] = (perf_counter() - start) * 1000

    # 4. Obtener recomendación para la mejor predicción
    if predictions:
        recommendation = get_recycling_recommendation(
            predictions[0].label
        )
        waste_bin = recommendation["bin"]
        tip = recommendation["tip"]
    else:
        waste_bin = None
        tip = "No fue posible identificar el residuo."

    # 5. Construir resultado
    timings["total_ms"] = (perf_counter() - total_start) * 1000

    return AnalysisResult(
        status="reciclable" if predictions else "incierto",
        top=predictions,
        bin=waste_bin,
        tip=tip,
        device=str(device),
        timings_ms=timings
    )
