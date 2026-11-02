
# Reglas de clasificación de residuos

RECYCLING_RULES = {
    "Plastic": {
        "bin": "blanco",
        "tip": "Limpia el envase antes de depositarlo."
    },
    "Metal": {
        "bin": "blanco",
        "tip": "Separa los elementos metálicos y procura limpiarlos."
    },
    "Paper": {
        "bin": "blanco",
        "tip": "Deposita el papel limpio y seco."
    },
    "Cardboard": {
        "bin": "blanco",
        "tip": "Pliega el cartón para facilitar su almacenamiento."
    },
    "Green-Glass": {
        "bin": "blanco",
        "tip": "Deposita el vidrio aprovechable limpio y separado."
    },
    "White-Glass": {
        "bin": "blanco",
        "tip": "Separa el vidrio aprovechable y evita mezclarlo con otros residuos."
    },
    "Biological": {
        "bin": "verde",
        "tip": "Los residuos orgánicos aprovechables pueden convertirse en abono."
    },
    "Brown-grass": {
        "bin": "verde",
        "tip": "Aprovecha los residuos vegetales mediante compostaje."
    },
    "Trash": {
        "bin": "negro",
        "tip": "Deposita aquí los residuos no aprovechables."
    },
    "Battery": {
        "bin": "punto-especial",
        "tip": "Lleva las baterías a un punto de recolección posconsumo."
    },
    "Clothes": {
        "bin": "Donation or textile collection",
        "tip": "Si está en buen estado, considera reutilizarlo o donarlo."
    },
    "Shoes": {
        "bin": "Donation or specialized collection",
        "tip": "Si están en buen estado, considera reutilizarlos o donarlos."
    },
}


def get_recycling_recommendation(label: str) -> dict:
    """Obtiene el contenedor y consejo asociado a un residuo."""

    normalized_label = label.strip().lower()

    for waste_class, recommendation in RECYCLING_RULES.items():
        if waste_class.lower() == normalized_label:
            return recommendation

    return {
        "bin": None,
        "tip": "No hay una recomendación disponible para este residuo."
    }

