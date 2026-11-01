
# Modelos de Hugging Face

GATE_MODEL_ID = "openai/clip-vit-base-patch32"

CLASSIFIER_MODEL_ID = "watersplash/waste-classification"

# Configuración de clasificación

TOP_K = 3

CLASSIFICATION_THRESHOLD = 0.60

# Configuración de inferencia

USE_FP16 = True

# Clases reconocidas por el clasificador

WASTE_CLASSES = [
    "Plastic",
    "Metal",
    "Paper",
    "Cardboard",
    "Green-Glass",
    "White-Glass",
    "Biological",
    "Brown-grass",
    "Trash",
    "Battery",
    "Clothes",
    "Shoes",
]
