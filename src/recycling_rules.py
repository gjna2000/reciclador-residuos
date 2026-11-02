
# Reglas de clasificación de residuos

RECYCLING_RULES = {
    "Plastic": {
        "bin": "Blanco",
        "tip": "Limpia el envase antes de depositarlo."
    },
    "Metal": {
        "bin": "Blanco",
        "tip": "Separa los elementos metálicos y procura limpiarlos."
    },
    "Paper": {
        "bin": "Blanco",
        "tip": "Deposita el papel limpio y seco."
    },
    "Cardboard": {
        "bin": "Blanco",
        "tip": "Pliega el cartón para facilitar su almacenamiento."
    },
    "Green-Glass": {
        "bin": "Blanco",
        "tip": "Deposita el vidrio aprovechable limpio y separado."
    },
    "White-Glass": {
        "bin": "Blanco",
        "tip": "Separa el vidrio aprovechable y evita mezclarlo con otros residuos."
    },
    "Biological": {
        "bin": "Verde",
        "tip": "Los residuos orgánicos aprovechables pueden convertirse en abono."
    },
    "Brown-grass": {
        "bin": "Verde",
        "tip": "Aprovecha los residuos vegetales mediante compostaje."
    },
    "Trash": {
        "bin": "Negro",
        "tip": "Deposita aquí los residuos no aprovechables."
    },
    "Battery": {
        "bin": "Punto-especial",
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

