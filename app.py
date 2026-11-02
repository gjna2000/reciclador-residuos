import time
from dataclasses import dataclass
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError
from ui import components as ui

# 1. Importamos tu pipeline real y la función de dispositivo de Felipe
from src.pipeline import RecyclingPipeline
from src.device import get_device

st.set_page_config(page_title="EcoClasifica", page_icon="♻️", layout="wide")

# 2. Cargamos el pipeline una sola vez usando la caché de Streamlit (Regla de oro)
@st.cache_resource
def load_recycling_pipeline():
    device = get_device()
    return RecyclingPipeline(device=device)

# Inicializamos el pipeline
try:
    pipeline = load_recycling_pipeline()
except Exception as e:
    st.error(f"Error al cargar los modelos en el dispositivo: {e}")
    pipeline = None

st.session_state.setdefault("uploader_key", 0)
st.session_state.setdefault("result", None)
st.session_state.setdefault("file_id", None)

def reset_analysis() -> None:
    st.session_state.uploader_key += 1
    st.session_state.result = None
    st.session_state.file_id = None

def clear_result() -> None:
    st.session_state.result = None

def load_image(uploaded) -> Image.Image | None:
    if uploaded is None:
        return None
    try:
        return ImageOps.exif_transpose(Image.open(uploaded)).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        st.error("No se pudo leer el archivo. Verifica que sea una imagen JPG, JPEG o PNG válida.")
        return None

ui.load_theme()

# Eliminamos la barra lateral de simulación (o la dejamos solo informativa si lo prefieres)
with st.sidebar:
    st.subheader("Estado del Sistema")
    st.caption("Conectado al pipeline real de Hugging Face mediante CUDA.")
    st.info(f"Dispositivo activo: {get_device().upper()}")

ui.render_header()
ui.render_hero()
ui.section_title("Analiza tu residuo", "Sube una fotografía para clasificar el residuo con IA.", anchor="analizar")

col_upload, col_result = st.columns(2, gap="large")

with col_upload:
    with st.container(border=True, key="upload_card"):
        uploaded = st.file_uploader("Fotografía del residuo", type=["jpg", "jpeg", "png"],
                                    key=f"uploader_{st.session_state.uploader_key}",
                                    label_visibility="collapsed")
        image = load_image(uploaded)

        file_id = uploaded.file_id if uploaded is not None else None
        if file_id != st.session_state.file_id:
            st.session_state.file_id = file_id
            st.session_state.result = None

        if image is not None:
            preview = image.copy()
            preview.thumbnail((900, 900))
            st.image(preview)
            st.caption(f"Imagen original: {image.width} × {image.height} px")
        else:
            st.caption("Selecciona una fotografía del residuo para comenzar.")

        c_analyze, c_clear = st.columns([3, 2])
        analyze_clicked = c_analyze.button("Analizar residuo", type="primary", disabled=image is None or pipeline is None)
        c_clear.button("Limpiar", on_click=reset_analysis, disabled=uploaded is None)

    # 3. AQUÍ ESTÁ EL CAMBIO CLAVE: Ejecutamos tu pipeline real en lugar del mock
    if analyze_clicked and image is not None and pipeline is not None:
        try:
            with st.spinner("Analizando fotografía con los modelos de IA..."):
                # Llamada directa a tu contrato de pipeline
                st.session_state.result = pipeline.analyze(image)
        except Exception as error:
            st.session_state.result = None
            st.error(f"No se pudo completar el análisis: {error}")

result = st.session_state.result

with col_result:
    if result is not None:
        # Pasamos false en simulated para que la interfaz sepa que es real
        ui.result_card(result, simulated=False)
    elif image is not None:
        ui.empty_state("Fotografía lista", "Pulsa «Analizar residuo» para ver la clasificación real.")
    else:
        ui.empty_state("Aquí aparecerá tu resultado", "Carga una fotografía del residuo para comenzar.")

if result is not None:
    ui.tech_info(result, simulated=False)

detected = result.top[0].label if result and result.status == "reciclable" and result.top else None
ui.category_chips(detected)