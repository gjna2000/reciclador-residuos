import base64
import io
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps

THEME_PATH = Path(__file__).parent / "theme.css"

CATEGORIES = {
    "Plastic": "Plástico",
    "Metal": "Metal",
    "Paper": "Papel",
    "Cardboard": "Cartón",
    "Green-Glass": "Vidrio verde",
    "White-Glass": "Vidrio transparente",
    "Biological": "Orgánico",
    "Brown-grass": "Residuo vegetal",
    "Trash": "Basura general",
    "Battery": "Pila o batería",
    "Clothes": "Ropa",
    "Shoes": "Calzado",
}

CATEGORY_DETAILS = {
    "Plastic": {
        "title": "Plástico (PET / Polímeros)",
        "code": "Código SPI: #1 PETE / #2 HDPE / #5 PP",
        "bin_name": "Contenedor Blanco",
        "bin_color": "#F8FAFC",
        "bin_heading": "Caneca Blanca: Residuos Aprovechables",
        "bin_tag": "Caneca Blanca: Aprovechable",
        "icon": "water_bottle",
        "filename": "plastico.jpg",
        "desc": "Botellas de bebidas, envases de lácteos enjuagados, frascos de champú, recipientes de detergente y tapas plásticas limpias y compactadas.",
        "admissible": ["Botellas plásticas vacías y escurridas", "Tapas plásticas colocadas en la botella", "Envases limpios de champú y detergentes"],
        "inadmissible": ["Envases con restos de aceite comestible o grasa", "Plásticos sucios con comida pegada", "Cepillos de dientes o juguetes multimaterial"],
        "tip": "Deposita el envase completamente seco y limpio. Enjuágalo, retira restos de líquido y aplástalo para maximizar el espacio.",
        "rec": "Asegúrate de enjuagar rápidamente el envase para evitar hongos y malos olores. Aplástalo y coloca la tapa en el mismo contenedor.",
        "recyclable": True
    },
    "Metal": {
        "title": "Metal y Aluminio",
        "code": "Clasificación: Metales ferrosos y aluminio (Alu-41)",
        "bin_name": "Contenedor Blanco",
        "bin_color": "#F8FAFC",
        "bin_heading": "Caneca Blanca: Residuos Aprovechables",
        "bin_tag": "Caneca Blanca: Aprovechable",
        "icon": "local_drink",
        "filename": "metal.jpg",
        "desc": "Latas de aluminio de bebidas, conservas de hojalata desocupadas, desodorantes en aerosol vacíos y tapas metálicas de frascos.",
        "admissible": ["Latas de gaseosa y cerveza aplastadas", "Latas de atún o verduras lavadas sin grasa", "Tapas corona y tapas metálicas de mermelada"],
        "inadmissible": ["Envases con pintura, solventes o agroquímicos", "Latas oxidadas o con restos orgánicos podridos", "Cables eléctricos o alambres sueltos"],
        "tip": "Lava las latas de conserva para evitar malos olores y aplástalas presionando el centro.",
        "rec": "Asegúrate de aplastarlas un poco para ahorrar espacio. Retira etiquetas gruesas si es posible.",
        "recyclable": True
    },
    "Paper": {
        "title": "Papel",
        "code": "Estándar: Fibra celulósica limpia PAP-22",
        "bin_name": "Contenedor Blanco",
        "bin_color": "#F8FAFC",
        "bin_heading": "Caneca Blanca: Residuos Aprovechables",
        "bin_tag": "Caneca Blanca: Aprovechable",
        "icon": "description",
        "filename": "papel.jpg",
        "desc": "Hojas de oficina, cuadernos sin espiral metálico, periódicos, revistas, folletos y sobres sin restos de comida ni grasa.",
        "admissible": ["Hojas impresas o fotocopias secas", "Revistas, periódicos y cuadernos sin alambres", "Sobres de correspondencia sin burbuja plástica"],
        "inadmissible": ["Servilletas usadas y papel higiénico (van a negra)", "Papel carbón, papel encerado o papel fotográfico", "Papel con grasa de comida"],
        "tip": "Mantén el papel completamente seco y estirado. Los papeles plastificados o con cera deben ir a basura general.",
        "rec": "No debe estar arrugado en bolas apretadas ni mojado. El papel con grasa NO es reciclable.",
        "recyclable": True
    },
    "Cardboard": {
        "title": "Cartón",
        "code": "Estándar: Cartón corrugado PAP-20 / PAP-21",
        "bin_name": "Contenedor Blanco",
        "bin_color": "#F8FAFC",
        "bin_heading": "Caneca Blanca: Residuos Aprovechables",
        "bin_tag": "Caneca Blanca: Aprovechable",
        "icon": "package_2",
        "filename": "carton.jpg",
        "desc": "Cajas de envíos, embalajes de electrodomésticos, rollos de papel higiénico y cartulinas limpias.",
        "admissible": ["Cajas de cartón aplanadas y desarmadas", "Rollos de cartón de papel higiénico y toallas", "Empaques de cereal limpios y plegados"],
        "inadmissible": ["Cajas de pizza empapadas de queso o grasa", "Vasos de café desechables con polietileno interior", "Cartón húmedo o descompuesto"],
        "tip": "Desarma las solapas inferiores y aplana la caja para ahorrar hasta un 80% de volumen.",
        "rec": "Desarma las cajas para aplanarlas completamente. Retira cintas adhesivas gruesas.",
        "recyclable": True
    },
    "Green-Glass": {
        "title": "Vidrio Verde",
        "code": "Vidrio calcosódico coloreado GL-71",
        "bin_name": "Contenedor Blanco",
        "bin_color": "#F8FAFC",
        "bin_heading": "Caneca Blanca: Residuos Aprovechables",
        "bin_tag": "Caneca Blanca: Aprovechable",
        "icon": "wine_bar",
        "filename": "vidrio_verde.jpg",
        "desc": "Botellas de vino, cerveza y frascos de vidrio verde esmeralda u oliva limpios sin tapas.",
        "admissible": ["Botellas de vino vacías y enjuagadas", "Envases de cerveza sin tapa metálica", "Frascos de aceites gourmet previamente lavados"],
        "inadmissible": ["Bombillas o tubos fluorescentes (son RESPEL)", "Vidrio de ventanas, parabrisas o espejos", "Cerámica, loza o cristal fino de copas"],
        "tip": "Enjuaga brevemente el interior. El vidrio es 100% infinitamente reciclable.",
        "rec": "Retira el corcho o tapa metálica. No deposites cristalería rota de ventanas.",
        "recyclable": True
    },
    "White-Glass": {
        "title": "Vidrio Transparente",
        "code": "Vidrio sílice puro GL-70",
        "bin_name": "Contenedor Blanco",
        "bin_color": "#F8FAFC",
        "bin_heading": "Caneca Blanca: Residuos Aprovechables",
        "bin_tag": "Caneca Blanca: Aprovechable",
        "icon": "liquor",
        "filename": "vidrio_claro.jpg",
        "desc": "Frascos de conservas, botellas de agua o licores transparentes y potes de perfumes limpios.",
        "admissible": ["Frascos de mermelada y mayonesa escurridos", "Botellas de jugo y agua de cristal puro", "Frascos de perfumes desocupados"],
        "inadmissible": ["Espejos y marcos de vidrio laminado", "Pyrex o refractarias para horno de cocina", "Bombillas halógenas o incandescentes"],
        "tip": "Excelente candidato para reutilización doméstica directa previa esterilización térmica.",
        "rec": "Enjuagar y depositar sin tapas. Si está quebrado, envuélvelo en papel periódico.",
        "recyclable": True
    },
    "Biological": {
        "title": "Orgánico",
        "code": "Materia biodegradable / Compostaje",
        "bin_name": "Contenedor Verde",
        "bin_color": "#15803D",
        "bin_heading": "Caneca Verde: Residuos Orgánicos Aprovechables",
        "bin_tag": "Caneca Verde: Orgánico Compostable",
        "icon": "nutrition",
        "filename": "organico.jpg",
        "desc": "Cáscaras de frutas, restos de verduras crudas, posos de café y cáscaras de huevo aptos para biocompost.",
        "admissible": ["Cáscaras de banano, naranja, manzana y frutas", "Restos de vegetales crudos de preparación", "Posos de café y bolsas de té sin grapas"],
        "inadmissible": ["Huesos grandes de res o cerdo en exceso", "Excrementos de mascotas o arena de gato (van a negra)", "Empaques biodegradables con polímeros mixtos"],
        "tip": "Sepáralos en una caneca con tapa hermética para evitar insectos y aprovecha para hacer abono.",
        "rec": "Ideal para compostaje doméstico o vermicultura.",
        "recyclable": True
    },
    "Brown-grass": {
        "title": "Residuo vegetal",
        "code": "Poda y biomasa seca",
        "bin_name": "Contenedor Verde",
        "bin_color": "#15803D",
        "bin_heading": "Caneca Verde: Biomasa y Residuos Verdes",
        "bin_tag": "Caneca Verde: Poda y Biomasa",
        "icon": "yard",
        "filename": "vegetal.jpg",
        "desc": "Ramas de poda, césped cortado, hojas secas de jardín y flores marchitas libres de basura.",
        "admissible": ["Hojas secas caídas de árboles y jardines", "Pasto cortado y ramas delgadas podadas", "Ramas trituradas para cobertura vegetal"],
        "inadmissible": ["Madera tratada químicamente con barniz", "Tierra con escombros o trozos de ladrillos", "Bolsas plásticas dentro del atado de poda"],
        "tip": "Trata de no mezclarlos con piedras ni plásticos para que la trituradora comunal trabaje limpiamente.",
        "rec": "Amárralo en atados pequeños o úsalo como acolchado orgánico (mulch).",
        "recyclable": True
    },
    "Trash": {
        "title": "Basura general",
        "code": "Residuo No Aprovechable",
        "bin_name": "Contenedor Negro",
        "bin_color": "#334155",
        "bin_heading": "Caneca Negra: No Aprovechables",
        "bin_tag": "Caneca Negra: No Aprovechable",
        "icon": "delete_sweep",
        "filename": "general.jpg",
        "desc": "Papel higiénico usado, servilletas sucias, colillas de cigarrillo, pañales y envases de comida grasientos.",
        "admissible": ["Papel higiénico y toallas de mano usadas", "Servilletas con restos de salsa o grasa", "Pañales desechables y toallas sanitarias"],
        "inadmissible": ["Plásticos limpios o latas (van a blanca)", "Pilas y baterías (van a punto especial rojo)", "Restos orgánicos crudos"],
        "tip": "Este material no tiene proceso de reciclaje actual. Reduce su generación comprando a granel.",
        "rec": "Bolsa negra cerrada herméticamente con destino a relleno sanitario municipal.",
        "recyclable": False
    },
    "Battery": {
        "title": "Pila o batería",
        "code": "Residuo Peligroso (RESPEL)",
        "bin_name": "Punto Rojo Especial",
        "bin_color": "#DC2626",
        "bin_heading": "Punto Especial: Residuo Peligroso (RESPEL)",
        "bin_tag": "Punto Rojo Especial: Peligroso RESPEL",
        "icon": "battery_alert",
        "filename": "bateria.jpg",
        "desc": "Pilas alcalinas AA/AAA, pilas de botón, baterías de litio de smartphones y acumuladores portátiles.",
        "admissible": ["Pilas alcalinas cilíndricas descargadas", "Baterías de litio de teléfonos antiguos", "Pilas botón de relojes y calculadoras"],
        "inadmissible": ["Arrojar a la basura común o caneca negra", "Baterías infladas o perforadas sin aislar", "Mezclar con residuos húmedos"],
        "tip": "Cubre los polos de las baterías con cinta adhesiva antes de depositarlas en el tótem de acopio.",
        "rec": "NUNCA arrojes al contenedor común. Los metales pesados contaminan mantos acuíferos.",
        "recyclable": False
    },
    "Clothes": {
        "title": "Ropa y textiles",
        "code": "Fibras naturales y sintéticas",
        "bin_name": "Punto Textil / Donación",
        "bin_color": "#0E3B2E",
        "bin_heading": "Punto Textil: Reutilización y Donación",
        "bin_tag": "Punto Textil: Donación / Reúso",
        "icon": "apparel",
        "filename": "ropa.jpg",
        "desc": "Camisetas, pantalones, toallas y retazos textiles limpios aptos para segundo ciclo de vida.",
        "admissible": ["Prendas de vestir limpias y secas", "Sábanas, toallas y cortinas en desuso", "Retazos de tela para hilatura industrial"],
        "inadmissible": ["Prendas húmedas o con moho contaminante", "Textiles impregnados de aceite o pintura", "Ropa interior muy deteriorada"],
        "tip": "Prolonga la vida útil de tus prendas lavándolas con agua fría y reparando costuras.",
        "rec": "Si están en buen estado, prioriza donación. Si están rotas, córtalas para trapos de limpieza.",
        "recyclable": True
    },
    "Shoes": {
        "title": "Calzado",
        "code": "Material compuesto (Caucho/Cuero)",
        "bin_name": "Punto Calzado / Donación",
        "bin_color": "#0E3B2E",
        "bin_heading": "Punto Calzado: Reacondicionamiento",
        "bin_tag": "Punto Calzado: Donación / Reúso",
        "icon": "roller_skating",
        "filename": "calzado.jpg",
        "desc": "Zapatillas deportivas, zapatos de cuero, botas y sandalias con pares completos.",
        "admissible": ["Zapatos y zapatillas en pares completos", "Calzado limpio con suelas íntegras", "Botas de caucho sin grietas"],
        "inadmissible": ["Zapatos con restos químicos peligrosos", "Zapatos huérfanos sin su pareja", "Calzado mojado o con hongos"],
        "tip": "Límpialos antes de donarlos para asegurar su segundo uso inmediato.",
        "rec": "Átalos por los cordones para que la pareja no se separe.",
        "recyclable": True
    }
}

STATUS_STYLE = {
    "reciclable": ("Reciclable", "ok"),
    "no_es_residuo": ("No parece un residuo", "neutral"),
    "incierto": ("Resultado incierto", "warn"),
}

LOGO_SVG = (
    '<svg width="36" height="36" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<path d="M24 4c8 6 9 16 0 23-9-7-8-17 0-23z" fill="#0E3B2E"/>'
    '<path d="M24 4c8 6 9 16 0 23-9-7-8-17 0-23z" fill="#16A34A" transform="rotate(120 24 24)"/>'
    '<path d="M24 4c8 6 9 16 0 23-9-7-8-17 0-23z" fill="#84CC16" transform="rotate(240 24 24)"/>'
    '</svg>'
)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "categorias"
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")

SHORT_CODES = {
    "Plastic": "#1 PET", "Metal": "Alu-41", "Paper": "PAP-22", "Cardboard": "PAP-20",
    "Green-Glass": "GL-71", "White-Glass": "GL-70", "Biological": "Bio", "Brown-grass": "Mulch",
    "Trash": "Relleno", "Battery": "Tótem", "Clothes": "Fibra", "Shoes": "Suela",
}

BIN_INFO = {
    "Contenedor Blanco": {"short": "Blanca", "sub": "Aprovechables limpios y secos", "group": "blanca",
                          "kind": ("Aprovechable", "ok"), "badge": "Caneca Blanca", "special": False},
    "Contenedor Verde": {"short": "Verde", "sub": "Orgánicos aprovechables", "group": "verde",
                         "kind": ("Compostable", "bio"), "badge": "Caneca Verde", "special": False},
    "Contenedor Negro": {"short": "Negra", "sub": "No aprovechables", "group": "negra",
                         "kind": ("No aprovechable", "neutral"), "badge": "Caneca Negra", "special": False},
    "Punto Rojo Especial": {"short": "Punto rojo", "sub": "Recolección autorizada (RESPEL)", "group": "especial",
                            "kind": ("Peligroso RESPEL", "danger"), "badge": "Punto Especial", "special": True},
    "Punto Textil / Donación": {"short": "Punto textil", "sub": "Donación o reúso", "group": "especial",
                                "kind": ("Donación / Reúso", "ok"), "badge": "Punto Textil", "special": True},
    "Punto Calzado / Donación": {"short": "Punto calzado", "sub": "Donación o reacondicionamiento", "group": "especial",
                                 "kind": ("Reacondicionable", "ok"), "badge": "Punto Calzado", "special": True},
}
DEFAULT_BIN_INFO = BIN_INFO["Contenedor Blanco"]

# Valores reales de `result.bin` (los que entrega recycling_rules.py) -> presentación.
# No se deduce nada a partir de la categoría: solo se traduce el valor del contrato.
RESULT_BINS = {
    "blanco": {"group": "blanca", "color": "#F8FAFC", "short": "Blanca", "badge": "Caneca Blanca",
               "sub": "Aprovechables limpios y secos", "heading": "Caneca Blanca: Residuos Aprovechables",
               "special": False},
    "verde": {"group": "verde", "color": "#15803D", "short": "Verde", "badge": "Caneca Verde",
              "sub": "Orgánicos aprovechables", "heading": "Caneca Verde: Residuos Orgánicos Aprovechables",
              "special": False},
    "negro": {"group": "negra", "color": "#334155", "short": "Negra", "badge": "Caneca Negra",
              "sub": "No aprovechables", "heading": "Caneca Negra: No Aprovechables",
              "special": False},
    "punto-especial": {"group": "especial", "color": "#0E3B2E", "short": "Punto especial", "badge": "Punto Especial",
                       "sub": "Recolección posconsumo o reúso", "heading": "Punto Especial: Recolección Posconsumo",
                       "special": True},
}


def _result_bin(bin_value: str | None) -> dict | None:
    """Devuelve la presentación de `result.bin`, o None si no existe o no se reconoce."""
    if not bin_value:
        return None
    return RESULT_BINS.get(str(bin_value).strip().lower())

FILTERS = {
    "Todos": None,
    "Aprovechables (Caneca Blanca)": "blanca",
    "Orgánicos (Caneca Verde)": "verde",
    "No aprovechables (Caneca Negra)": "negra",
    "Puntos especiales / posconsumo": "especial",
}

_LEAF_PATHS = (
    '<path d="M24 4c8 6 9 16 0 23-9-7-8-17 0-23z" fill="#0E3B2E"/>'
    '<path d="M24 4c8 6 9 16 0 23-9-7-8-17 0-23z" fill="#16A34A" transform="rotate(120 24 24)"/>'
    '<path d="M24 4c8 6 9 16 0 23-9-7-8-17 0-23z" fill="#84CC16" transform="rotate(240 24 24)"/>'
)


def _bin_info(det: dict) -> dict:
    return BIN_INFO.get(det.get("bin_name", ""), DEFAULT_BIN_INFO)


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _shade(hex_color: str, factor: float) -> str:
    r, g, b = _rgb(hex_color)
    return "#%02X%02X%02X" % (int(r * factor), int(g * factor), int(b * factor))


def _tint(hex_color: str, amount: float) -> str:
    r, g, b = _rgb(hex_color)
    return "#%02X%02X%02X" % tuple(int(c + (255 - c) * amount) for c in (r, g, b))


def _is_light(hex_color: str) -> bool:
    r, g, b = _rgb(hex_color)
    return (0.299 * r + 0.587 * g + 0.114 * b) > 200


def _icon(name: str, size: int | None = None) -> str:
    style = f' style="font-size:{size}px"' if size else ""
    return f'<span class="material-symbols-outlined"{style}>{name}</span>'


def _html(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def _md(text: str) -> None:
    st.markdown(_html(text), unsafe_allow_html=True)


def load_theme(path: Path = THEME_PATH) -> None:
    try:
        css = path.read_text(encoding="utf-8")
    except OSError:
        st.warning("No se encontró ui/theme.css; la interfaz se mostrará sin estilos personalizados.")
        return
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _image_data_uri(path_str: str, mtime: float, max_px: int) -> str | None:
    """Redimensiona y codifica la imagen (cacheado por ruta + fecha de modificación)."""
    try:
        with Image.open(path_str) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            img.thumbnail((max_px, max_px))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=84, optimize=True)
        return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception:
        return None


def get_local_image_base64(filepath: Path, max_px: int = 720) -> str | None:
    """Devuelve la imagen como data URI. Si el archivo no existe o no se puede leer, None.

    Acepta .jpg, .jpeg, .png y .webp con el mismo nombre base, de modo que el usuario
    puede guardar su fotografía en cualquiera de esos formatos sin tocar el código.
    """
    filepath = Path(filepath)
    candidates = [filepath]
    candidates += [filepath.with_suffix(ext) for ext in IMAGE_EXTS]
    candidates += [filepath.with_suffix(ext.upper()) for ext in IMAGE_EXTS]
    for candidate in candidates:
        if candidate.is_file():
            return _image_data_uri(str(candidate), candidate.stat().st_mtime, max_px)
    return None


def preload_category_images(max_px: int = 560) -> tuple[int, int]:
    """Prepara en caché las imágenes locales que aparecen en las tarjetas."""
    filenames = [item.get("filename", "") for item in CATEGORY_DETAILS.values()]
    total = len(filenames)
    loaded = sum(
        get_local_image_base64(ASSETS_DIR / filename, max_px=max_px) is not None
        for filename in filenames
        if filename
    )
    return loaded, total


def render_header() -> None:
    _md(f"""
        <header class="eco-header">
          <div class="eco-header-inner">
            <div class="eco-brand">
              <div class="eco-logo"><div>{LOGO_SVG}</div></div>
              <div>
                <div class="eco-brand-name">Eco<span class="accent">Clasifica</span></div>
                <div class="eco-brand-sub">Clasificación inteligente de residuos &amp; economía circular</div>
              </div>
            </div>
            <nav class="eco-nav">
              <a class="active" href="#analizar">Analizar</a>
              <a href="#categorias">Categorías (12)</a>
            </nav>
          </div>
        </header>
    """)


def render_hero() -> None:
    _md(f"""
        <div class="eco-hero">
          <h1>Cada residuo tiene un destino exacto.<br>
            <span class="eco-grad">Descubre cómo clasificarlo con IA y Norma 2184.</span>
          </h1>
          <p class="lead">Identifica tus residuos a partir de una fotografía en milisegundos y descubre con precisión técnica cómo depositarlos para maximizar el reciclaje circular en Colombia.</p>
          <div class="eco-steps">
            <div class="eco-step">
              <div class="eco-step-n">1</div>
              <div><b>Carga una fotografía</b><span class="s">Cámara o archivo local</span></div>
              {_icon("arrow_forward")}
            </div>
            <div class="eco-step active">
              <div class="eco-step-n">2</div>
              <div><b>Analiza el residuo</b><span class="s">Clasificación con visión IA</span></div>
              {_icon("arrow_forward")}
            </div>
            <div class="eco-step last">
              <div class="eco-step-n">3</div>
              <div><b>Consulta disposición</b><span class="s">Contenedor &amp; recomendaciones</span></div>
              {_icon("check_circle")}
            </div>
          </div>
        </div>
    """)


def section_title(title: str, subtitle: str, anchor: str = "", badge: str = "", aside: str = "") -> None:
    anchor_attr = f' id="{anchor}"' if anchor else ""
    badge_html = f'<span class="eco-count">{badge}</span>' if badge else ""
    _md(f"""
        <div class="eco-section"{anchor_attr}>
          <div>
            <h2>{title}{badge_html}</h2>
            <p>{subtitle}</p>
          </div>
          {aside}
        </div>
    """)


def format_chip() -> None:
    """Chip informativo de formatos admitidos (panel de carga)."""
    _md('<div style="text-align:right"><span class="eco-chip-fmt">JPG · JPEG · PNG</span></div>')


def empty_state(title: str, body: str, min_height: int | None = None, icon: str = "image") -> None:
    height = f"min-height:{min_height}px;" if min_height else ""
    _md(f"""
        <div class="eco-empty" style="{height}">
          {_icon(icon)}
          <b>{title}</b>
          <p>{body}</p>
        </div>
    """)


def render_footer() -> None:
    _md(f"""
        <footer class="eco-footer">
          <div class="l"><b>EcoClasifica</b><span>Clasificación de residuos según la Resolución 2184 de 2019 (Colombia)</span></div>
          <span>Blanca: aprovechables · Negra: no aprovechables · Verde: orgánicos</span>
        </footer>
    """)


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

# Refinamiento visual SOLO de `result_card` (Fases 1 y 2). Todas las reglas están acotadas al
# contenedor `st-key-result_card*`, por lo que no afectan a bins_overview, category_cards_grid
# ni a ningún otro componente. Se evita tocar `opacity` / `transform` de los elementos animados.
_RESULT_CARD_CSS = """<style>
div[class*="st-key-result_card"]{background:#FBFDFC;border:1px solid rgba(14,59,46,.09);border-radius:1.15rem;box-shadow:0 1px 3px rgba(14,59,46,.04),0 8px 20px -10px rgba(14,59,46,.10);padding:1.25rem 1.25rem 1.25rem 1.5rem;}
div[class*="st-key-result_card"][class*="_crop_"]{background:#F7FBF8;border-color:rgba(22,163,74,.12);box-shadow:none;}
div[class*="st-key-result_card"][class*="_crop_"] .eco-metric{background:rgba(255,255,255,.8);}
[data-testid="stVerticalBlockBorderWrapper"]:has(div[class*="st-key-result_card"]){border-color:rgba(14,59,46,.10);border-radius:1.25rem;}
div[class*="st-key-result_card"] .eco-binbar{width:5px;border-right:0;}
div[class*="st-key-result_card"] .eco-res-head{align-items:center;flex-wrap:wrap;gap:.6rem .75rem;margin-bottom:1rem;padding-bottom:.85rem;border-bottom:1px solid rgba(14,59,46,.07);}
div[class*="st-key-result_card"] .eco-eyebrow{font-size:10.5px;font-weight:600;letter-spacing:.07em;color:#6F8178;}
div[class*="st-key-result_card"] .eco-res-title{font-size:1.5rem;line-height:1.18;margin-top:.2rem;}
div[class*="st-key-result_card"] .eco-pill{font-weight:600;padding:.3rem .8rem;}
div[class*="st-key-result_card"] .eco-pill-ok{background:#E4F5EA;color:#1B6B3A;border-color:rgba(22,163,74,.18);}
div[class*="st-key-result_card"] .eco-pill-warn{background:#FEF5DC;color:#A5620F;border-color:rgba(217,119,6,.20);}
div[class*="st-key-result_card"] .eco-pill-neutral{background:#EEF2EF;color:#4B5A52;border-color:rgba(14,59,46,.12);}
div[class*="st-key-result_card"] .eco-stage{background:linear-gradient(180deg,#F8FBF9,#EEF6F1);border:1px solid rgba(14,59,46,.07);border-radius:1rem;margin-bottom:1rem;}
div[class*="st-key-result_card"] .eco-stage-head{border-bottom-color:rgba(14,59,46,.06);color:var(--forest-mid);font-weight:600;}
div[class*="st-key-result_card"] .eco-stage svg{filter:drop-shadow(0 5px 7px rgba(14,59,46,.10));}
div[class*="st-key-result_card"] .eco-bin-dot,div[class*="st-key-result_card"] .eco-bin-row .sw{border:1px solid rgba(14,59,46,.18);box-shadow:inset 0 1px 2px rgba(0,0,0,.05);}
div[class*="st-key-result_card"] .eco-toast{background:#E6F5EC;color:#166534;font-weight:600;border:1px solid rgba(22,163,74,.20);box-shadow:0 4px 12px -6px rgba(14,59,46,.18);}
div[class*="st-key-result_card"] .eco-metrics{gap:.75rem;margin-bottom:1rem;}
div[class*="st-key-result_card"] .eco-metric{background:#F6FAF8;border:1px solid rgba(14,59,46,.07);border-radius:.85rem;}
div[class*="st-key-result_card"] .eco-metric .lbl{color:#6B7B73;}
div[class*="st-key-result_card"] .eco-meter{background:#E6EFEA;}
div[class*="st-key-result_card"] .eco-tip{background:linear-gradient(135deg,#F5FBF7,#EBF5EF);border:1px solid rgba(22,163,74,.16);border-radius:.9rem;padding:.9rem 1rem;margin-bottom:.25rem;}
div[class*="st-key-result_card"] .eco-tip .ic{border-radius:.6rem;box-shadow:0 2px 6px -2px rgba(22,163,74,.35);}
div[class*="st-key-result_card"] .eco-preds-title{border-top-color:rgba(14,59,46,.06);}
div[class*="st-key-result_card"] .eco-pred .bar{background:#E8F0EB;}
div[class*="st-key-result_card"] .eco-pred .bar>div{background:#C4D4CA;}
div[class*="st-key-result_card"] .eco-pred.top .bar>div{background:var(--eco-green);}
</style>"""


def _soft_bar_style(color: str) -> str:
    """Estilo del acento lateral de la tarjeta: mismo color del contenedor, más suave.
    Los colores claros (caneca blanca) conservan su tono y reciben solo un borde interior tenue."""
    if _is_light(color):
        return f"background:{color};box-shadow:inset -1px 0 0 rgba(14,59,46,.10)"
    return f"background:{_tint(color, 0.18)}"

def _bin_svg(color: str) -> str:
    light = _is_light(color)
    stroke = "#CBD5E1" if light else _shade(color, 0.88)
    rim = "#E8EEF3" if light else _shade(color, 0.92)
    stripe = "#E8EEF3" if light else _tint(color, 0.22)
    handle = "#94A3B8" if light else _shade(color, 0.78)
    return (
        '<svg viewBox="0 0 200 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Caneca de separación">'
        '<ellipse cx="100" cy="202" rx="55" ry="8" fill="#111e19" opacity="0.12"/>'
        '<g class="eco-item">'
        '<circle cx="100" cy="44" r="18" fill="#E6F7F0" stroke="#5E9C85" stroke-width="1.25"/>'
        '<rect x="96" y="30" width="8" height="5" rx="1.5" fill="#2F6F5B"/>'
        '<rect x="92" y="35" width="16" height="18" rx="4" fill="#2F6F5B" opacity="0.8"/>'
        '</g>'
        f'<path d="M 65 92 L 72 195 C 73 199 78 202 84 202 L 116 202 C 122 202 127 199 128 195 L 135 92 Z" fill="{color}" stroke="{stroke}" stroke-width="1.5"/>'
        f'<path d="M 74 100 L 78 192 M 126 100 L 122 192" stroke="{stripe}" stroke-linecap="round" stroke-width="1.5" fill="none"/>'
        '<rect x="82" y="128" width="36" height="36" rx="6" fill="#FFFFFF" opacity="0.93" stroke="#DDE6E0"/>'
        f'<g transform="translate(82 128) scale(0.75)">{_LEAF_PATHS}</g>'
        f'<rect x="60" y="84" width="80" height="9" rx="4.5" fill="{rim}" stroke="{stroke}" stroke-width="1"/>'
        '<g class="eco-lid">'
        f'<path d="M 62 82 C 65 72 135 72 138 82 Z" fill="{color}" stroke="{stroke}" stroke-width="1.25"/>'
        f'<rect x="92" y="66" width="16" height="6" rx="3" fill="{handle}"/>'
        f'<path d="M 60 81 L 140 81" stroke="{stroke}" stroke-linecap="round" stroke-width="2"/>'
        '</g>'
        '</svg>'
    )


def top_predictions(predictions, heading: str) -> None:
    rows = []
    for i, pred in enumerate(predictions[:3]):
        label = CATEGORIES.get(pred.label, pred.label)
        score = min(max(pred.score, 0.0), 1.0)
        rows.append(
            f'<div class="eco-pred{" top" if i == 0 else ""}">'
            f'<div class="row"><span>{i + 1}. {label}</span><span class="pct">{score * 100:.0f} %</span></div>'
            f'<div class="bar"><div style="width:{score * 100:.1f}%"></div></div></div>'
        )
    _md(f'<div class="eco-preds-title"><span>{heading}</span></div>' + "".join(rows))


def _replay_animation(key_suffix: str) -> None:
    tick_key = f"eco_anim_tick_{key_suffix}"
    st.session_state[tick_key] = st.session_state.get(tick_key, 0) + 1
    st.session_state[f"eco_anim_replay_{key_suffix}"] = True


def result_card(result, key_suffix: str = "main") -> None:
    pill, css = STATUS_STYLE.get(result.status, STATUS_STYLE["incierto"])
    ss = st.session_state
    tick_key = f"eco_anim_tick_{key_suffix}"
    replay_key = f"eco_anim_replay_{key_suffix}"
    signature_key = f"_eco_anim_signature_{key_suffix}"
    signature = (
        result.status,
        result.bin,
        result.top[0].label if result.top else None,
    )

    if ss.get(signature_key) != signature:
        ss[signature_key] = signature
        ss[tick_key] = ss.get(tick_key, 0) + 1
        ss[replay_key] = False
    tick = ss.get(tick_key, 0)

    with st.container(key=f"result_card_{css}_{key_suffix}"):
        if result.status == "reciclable" and result.top:
            best = result.top[0]
            # Solo el nombre para mostrar sale de CATEGORY_DETAILS; contenedor y consejo salen del resultado.
            det = CATEGORY_DETAILS.get(best.label, {})
            title = det.get("title", CATEGORIES.get(best.label, best.label))
            rbin = _result_bin(result.bin)
            score = min(max(best.score, 0.0), 1.0)
            level = "Alta" if score >= 0.8 else "Media" if score >= 0.5 else "Baja"

            if rbin:
                color = rbin["color"]
                destino = "punto de recolección autorizado" if rbin["special"] else rbin["badge"].lower()
                stage_html = f"""
                    <div class="eco-stage">
                      <div class="eco-stage-head">
                        <span class="eco-bin-dot" style="background:{color}"></span>
                        <span>{rbin["heading"]}</span>
                      </div>
                      <div class="eco-stage-body eco-anim-{tick % 2}{' eco-replay' if ss.get(replay_key) else ''}">
                        {_bin_svg(color)}
                        <div class="eco-toast">{_icon("verified")}<span>Entrega en {destino}</span></div>
                      </div>
                    </div>
                """
                bin_metric = f"""
                    <div class="lbl"><span>{"Destino" if rbin["special"] else "Color caneca"}</span>{_icon("recycling")}</div>
                    <div class="eco-bin-row"><span class="sw" style="background:{color}"></span><span>{rbin["short"]}</span></div>
                    <div class="sub">{rbin["sub"]}</div>
                """
            else:
                # Sin `result.bin` no se asigna ningún contenedor.
                color = "#CBD5E1"
                stage_html = ""
                bin_metric = f"""
                    <div class="lbl"><span>Destino</span>{_icon("recycling")}</div>
                    <div class="eco-bin-row"><span class="sw" style="background:{color}"></span><span>Sin asignar</span></div>
                    <div class="sub">No hay contenedor indicado para este residuo</div>
                """

            _md(f"""
                {_RESULT_CARD_CSS}
                <div class="eco-binbar" style="{_soft_bar_style(color)}"></div>
                <div class="eco-res-head">
                  <div>
                    <div class="eco-eyebrow">Norma técnica Colombia (Res. 2184)</div>
                    <div class="eco-res-title">{title}</div>
                  </div>
                  <span class="eco-pill eco-pill-{css}">{_icon("check_circle", 16)}{pill}</span>
                </div>
                {stage_html}
            """)

            if rbin:
                st.button(
                    "Animar depósito",
                    key=f"replay_anim_{key_suffix}",
                    on_click=_replay_animation,
                    args=(key_suffix,),
                    type="secondary",
                )

            _md(f"""
                <div class="eco-metrics">
                  <div class="eco-metric">
                    <div class="lbl"><span>Confianza IA</span>{_icon("verified")}</div>
                    <div class="val eco-num">{score * 100:.0f}%<small>{level}</small></div>
                    <div class="eco-meter"><div style="width:{score * 100:.1f}%"></div></div>
                  </div>
                  <div class="eco-metric">
                    {bin_metric}
                  </div>
                </div>
                <div class="eco-tip">
                  <div class="ic">{_icon("tips_and_updates", 20)}</div>
                  <div><b>Recomendación de disposición</b><p>{result.tip}</p></div>
                </div>
            """)
            n_top = min(len(result.top), 3)
            top_predictions(result.top, f"Top {n_top} predicciones del modelo" if n_top > 1 else "Predicción del modelo")
        else:
            title = "La imagen no parece un residuo" if result.status == "no_es_residuo" else "Resultado incierto"
            icon = "image_search" if result.status == "no_es_residuo" else "help"
            _md(f"""
                {_RESULT_CARD_CSS}
                <div class="eco-res-head">
                  <div>
                    <div class="eco-eyebrow">Norma técnica Colombia (Res. 2184)</div>
                    <div class="eco-res-title">{title}</div>
                  </div>
                  <span class="eco-pill eco-pill-{css}">{pill}</span>
                </div>
                <div class="eco-tip" style="background:linear-gradient(135deg,#FFFBEF,#FEF4DA);border-color:rgba(217,119,6,.20)">
                  <div class="ic" style="background:#D9902F;box-shadow:0 2px 6px -2px rgba(217,119,6,.35)">{_icon(icon, 20)}</div>
                  <div><b>Sugerencia</b><p>{result.tip}</p></div>
                </div>
            """)
            if result.top:
                top_predictions(result.top, "Predicciones del modelo")


def tech_info(result) -> None:
    with st.expander("Información técnica del análisis", expanded=False):
        c1, c2 = st.columns(2)
        c1.metric("Dispositivo de inferencia", result.device)
        timings = result.timings_ms or {}
        # `total_ms` ya es la suma de las etapas: no se vuelve a sumar junto con los parciales.
        if "total_ms" in timings:
            total_time = timings["total_ms"]
        else:
            total_time = sum(timings.values())
        c2.metric("Tiempo de análisis", f"{total_time:.0f} ms")


def bins_overview(selected_bin: str | None = None) -> None:
    """Resumen compacto de las 3 canecas y los puntos especiales.

    `selected_bin` debe ser `result.bin` (blanco, verde, negro, punto-especial). Solo se
    resalta ese contenedor; nunca se deduce a partir de la categoría detectada.
    """
    rbin = _result_bin(selected_bin)
    active_group = rbin["group"] if rbin else None
    highlight = "outline:3px solid #16A34A;outline-offset:2px;box-shadow:0 0 0 6px rgba(22,163,74,.15);"
    groups: dict[str, list[tuple[str, dict]]] = {}
    for key, det in CATEGORY_DETAILS.items():
        groups.setdefault(_bin_info(det)["group"], []).append((key, det))

    def chips(items, with_dest: bool = False) -> str:
        out = []
        for key, det in items:
            dest = f'<small>{_bin_info(det)["short"]}</small>' if with_dest else ""
            out.append(f'<span class="eco-bchip">{CATEGORIES.get(key, key)}{dest}</span>')
        return "".join(out)

    cards = ""
    for group in ("blanca", "verde", "negra"):
        items = groups.get(group, [])
        if not items:
            continue
        first = items[0][1]
        info = _bin_info(first)
        is_active = group == active_group
        cards += f"""
            <div class="eco-bin-card{" active" if is_active else ""}"{f' style="{highlight}"' if is_active else ""}>
              <div class="eco-bin-card-head">
                <span class="eco-bin-dot" style="background:{first.get('bin_color', '#F8FAFC')}"></span>
                <div><b>{info['badge']}</b><span class="s">{info['sub']}</span></div>
              </div>
              <div class="eco-bchips">{chips(items)}</div>
            </div>"""

    special = groups.get("especial", [])
    strip_style = f' style="{highlight}"' if active_group == "especial" else ""
    strip = (f'<div class="eco-bin-special{" active" if strip_style else ""}"{strip_style}><span class="lbl">{_icon("recycling", 16)}Puntos especiales</span>'
             f'{chips(special, True)}</div>') if special else ""

    section_title("¿Qué va en cada caneca?", "Separación en la fuente según la Resolución 2184.", anchor="canecas")
    _md(f'<div class="eco-bins">{cards}</div>{strip}')


def _select_category(key: str) -> None:
    st.session_state["manual_category"] = key


def _category_card_html(key: str, selected: bool) -> str:
    info = CATEGORY_DETAILS.get(key, {})
    binfo = _bin_info(info)
    name = CATEGORIES[key]
    kind_text, kind_css = binfo["kind"]
    img = get_local_image_base64(ASSETS_DIR / info.get("filename", ""), max_px=560)
    if img:
        media = f'<img src="{img}" alt="{name}" loading="lazy"/><div class="scrim"></div>'
    else:
        media = f'<div class="cat-placeholder">{_icon(info.get("icon", "recycling"))}</div>'
    check = f'<div class="cat-check">{_icon("check")}</div>' if selected else ""
    return f"""
        <div class="cat-card{" selected" if selected else ""}">
          <div class="cat-photo">
            {media}
            <div class="cat-badge">{binfo["badge"]}</div>
            {check}
          </div>
          <div class="cat-body">
            <div class="cat-name">{name}</div>
            <p class="cat-desc">{info.get("desc", "")}</p>
            <div class="cat-foot">
              <span class="st-pill {kind_css}">{kind_text}</span>
              <span class="cat-code">{SHORT_CODES.get(key, "")}</span>
            </div>
          </div>
        </div>
    """


def _category_detail_html(key: str) -> str:
    info = CATEGORY_DETAILS[key]
    binfo = _bin_info(info)
    name = CATEGORIES.get(key, info["title"])
    adm = "".join(f"<li>{item}</li>" for item in info.get("admissible", []))
    inadm = "".join(f"<li>{item}</li>" for item in info.get("inadmissible", []))
    img = get_local_image_base64(ASSETS_DIR / info.get("filename", ""), max_px=1000)
    media = (f'<img src="{img}" alt="{name}"/>' if img
             else f'<div class="ph">{_icon(info.get("icon", "recycling"))}</div>')
    color = info.get("bin_color", "#F8FAFC")
    dot = f'<span class="eco-bin-dot" style="background:{color};width:11px;height:11px"></span>'
    return f"""
        <div class="eco-detail">
          <div class="eco-detail-media">
            {media}
            <div class="scrim"></div>
            <div class="cap">
              <span class="tag">{dot}{info["bin_tag"]}</span>
              <h4>{info["title"]}</h4>
            </div>
          </div>
          <div class="eco-detail-main">
            <div class="eco-detail-head">
              <div class="l">
                <div class="eco-detail-icon">{_icon(info.get("icon", "recycling"))}</div>
                <div><h3>Información sobre {name}</h3><span class="code">{info["code"]}</span></div>
              </div>
              <span class="eco-bin-pill">{dot}{info["bin_name"]}</span>
            </div>
            <div>
              <div class="desc-l">Descripción técnica</div>
              <p class="desc">{info["desc"]}</p>
            </div>
            <div class="eco-two">
              <div class="eco-box yes"><div class="t">{_icon("check_circle")}Residuos admisibles (sí depositar)</div><ul>{adm}</ul></div>
              <div class="eco-box no"><div class="t">{_icon("warning")}No admisibles (evitar contaminar)</div><ul>{inadm}</ul></div>
            </div>
            <div class="eco-guide">
              <div class="ic">{_icon("checklist")}</div>
              <div><b>Guía paso a paso de disposición</b><p>{info["rec"]}</p></div>
            </div>
          </div>
        </div>
    """


def category_cards_grid(detected: str | None = None) -> None:
    section_title(
        "Explora las categorías",
        "Catálogo visual interactivo. Selecciona un residuo para conocer su destino normativo, código y recomendaciones paso a paso.",
        anchor="categorias",
        badge=f"{len(CATEGORIES)} tipos de residuos",
        aside='<span class="eco-note"><i></i>Fotografías provistas por el proyecto</span>',
    )

    ss = st.session_state
    ss.setdefault("manual_category", list(CATEGORIES.keys())[0])
    ss.setdefault("_last_detected", None)

    # Un residuo recién detectado selecciona su categoría, pero el usuario puede seguir explorando.
    if detected and detected != ss["_last_detected"]:
        ss["manual_category"] = detected
    ss["_last_detected"] = detected
    active_category = ss["manual_category"]

    filter_labels = [f"Todos ({len(CATEGORIES)})"] + list(FILTERS)[1:]
    chosen = st.radio("Filtrar categorías", filter_labels, horizontal=True,
                      key="cat_filter", label_visibility="collapsed")
    group = FILTERS.get(list(FILTERS)[filter_labels.index(chosen)])

    keys = [k for k in CATEGORIES
            if group is None or _bin_info(CATEGORY_DETAILS.get(k, {}))["group"] == group]

    with st.container(key="cat_grid"):
        per_row = 6
        for i in range(0, len(keys), per_row):
            cols = st.columns(per_row)
            for col, key in zip(cols, keys[i:i + per_row]):
                with col:
                    with st.container(key=f"catcard_{key}"):
                        _md(_category_card_html(key, key == active_category))
                        st.button(f"Ver {CATEGORIES[key]}", key=f"cat_sel_{key}",
                                  on_click=_select_category, args=(key,))

    if active_category in CATEGORY_DETAILS:
        _md(_category_detail_html(active_category))