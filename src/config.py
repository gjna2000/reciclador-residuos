
# ==========================================
# MODELOS DE HUGGING FACE
# ==========================================

GATE_MODEL_ID = "openai/clip-vit-base-patch32"

CLASSIFIER_MODEL_ID = "watersplash/waste-classification"


# ==========================================
# CONFIGURACIÓN DE CLASIFICACIÓN
# ==========================================

TOP_K = 3

GATE_THRESHOLD = 0.60

CLASSIFICATION_THRESHOLD = 0.60

USE_FP16 = False


# ==========================================
# CLASES DEL CLASIFICADOR
# ==========================================

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


# ==========================================
# GROUNDING DINO
# ==========================================

GDINO_MODEL_ID = "IDEA-Research/grounding-dino-tiny"

GDINO_THRESHOLD = 0.20

GDINO_MAX_AREA = 0.70

GDINO_NMS_IOU = 0.50

GDINO_TOP_N = 4


# Etiquetas en inglés

GDINO_LABELS = [
    "trash",
    "waste",
    "packaging",
    "wrapper",
    "peel",
    "bottle",
    "can",
]


# Etiquetas en español

GDINO_LABELS_ES = [
    "basura",
    "residuo",
    "empaque",
    "envoltura",
    "cáscara",
    "botella",
    "lata",
    "plástico",
    "papel",
    "cartón",
    "vidrio",
    "metal",
    "residuo orgánico",
    "bolsa plástica",
]


