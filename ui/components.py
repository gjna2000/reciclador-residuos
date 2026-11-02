from pathlib import Path
import streamlit as st

THEME_PATH = Path(__file__).parent / "theme.css"

CATEGORIES = {
    "Plastic": "Plástico", "Metal": "Metal", "Paper": "Papel", "Cardboard": "Cartón",
    "Green-Glass": "Vidrio verde", "White-Glass": "Vidrio transparente",
    "Biological": "Orgánico", "Brown-grass": "Residuo vegetal", "Trash": "Basura general",
    "Battery": "Pila o batería", "Clothes": "Ropa", "Shoes": "Calzado",
}

STATUS_STYLE = {
    "reciclable": ("Reciclable", "ok"),
    "no_es_residuo": ("No parece un residuo", "neutral"),
    "incierto": ("Resultado incierto", "warn"),
}


BIN_SWATCH = {"blanco": "#FFFFFF"}
BIN_SWATCH_DEFAULT = "#C9CFC6"

LOGO_SVG = (
    '<svg width="42" height="42" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<path d="M24 4c8 6 9 16 0 23-9-7-8-17 0-23z" fill="#2F5D46"/>'
    '<path d="M24 4c8 6 9 16 0 23-9-7-8-17 0-23z" fill="#8FAA93" transform="rotate(120 24 24)"/>'
    '<path d="M24 4c8 6 9 16 0 23-9-7-8-17 0-23z" fill="#A8E6CF" transform="rotate(240 24 24)"/>'
    "</svg>"
)


def _html(text: str) -> str:
    """Quita sangrías y líneas vacías para que Markdown no lo trate como bloque de código."""
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def _md(text: str) -> None:
    st.markdown(_html(text), unsafe_allow_html=True)


def load_theme(path: Path = THEME_PATH) -> None:
    """Inyecta ui/theme.css en la página."""
    try:
        css = path.read_text(encoding="utf-8")
    except OSError:
        st.warning("No se encontró ui/theme.css; la interfaz se mostrará sin estilos personalizados.")
        return
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_header() -> None:
    _md(f"""
        <div class="eco-nav" id="inicio">
          <div class="eco-brand">{LOGO_SVG}
            <div><div class="eco-wordmark eco-display">EcoClasifica</div>
            <div class="eco-tag">Clasificación de residuos con IA, a partir de una fotografía.</div></div>
          </div>
          <div class="eco-links"><a href="#inicio">Inicio</a><a href="#analizar">Analizar</a><a href="#categorias">Categorías</a></div>
        </div>""")


def render_hero() -> None:
    _md("""
        <div class="eco-hero"><h1>Cada residuo tiene un destino. Descubre cuál es el suyo.</h1>
        <p>Basta con cargar una fotografía para recibir una orientación sobre cómo disponer del residuo:
        qué es, en qué contenedor va y cómo prepararlo.</p>
        <div class="eco-steps"><span class="eco-step"><b>1</b>Carga una fotografía</span>
        <span class="eco-step"><b>2</b>Pulsa analizar</span>
        <span class="eco-step"><b>3</b>Deposítalo donde corresponde</span></div></div>""")


def section_title(title: str, subtitle: str, anchor: str = "") -> None:
    anchor_attr = f' id="{anchor}"' if anchor else ""
    _md(f"""
        <div class="eco-section-title eco-display"{anchor_attr}>{title}</div>
        <div class="eco-section-sub">{subtitle}</div>""")


def empty_state(title: str, body: str) -> None:
    _md(f'<div class="eco-empty"><b>{title}</b>{body}</div>')


def top_predictions(predictions, heading: str) -> None:
    _md(f'<div class="eco-subhead">{heading}</div>')
    for pred in predictions[:3]:
        c_label, c_bar, c_pct = st.columns([3, 5, 1.4], vertical_alignment="center")
        c_label.write(CATEGORIES.get(pred.label, pred.label))
        c_bar.progress(min(max(pred.score, 0.0), 1.0))
        c_pct.write(f"{pred.score * 100:.0f} %")


def result_card(result, simulated: bool = True) -> None:
    pill, css = STATUS_STYLE.get(result.status, STATUS_STYLE["incierto"])
    with st.container(border=True, key=f"result_card_{css}"):
        badge = '<span class="eco-demo-badge">DEMOSTRACIÓN CON DATOS SIMULADOS</span>' if simulated else ""
        _md(f'{badge}<span class="eco-pill eco-pill-{css}">{pill}</span>')

        if result.status == "reciclable" and result.top:
            best = result.top[0]
            bin_key = (result.bin or "").lower()
            swatch = BIN_SWATCH.get(bin_key, BIN_SWATCH_DEFAULT)
            _md(f"""
                <div class="eco-result-label eco-display">{CATEGORIES.get(best.label, best.label)}</div>
                <div class="eco-result-sub">Categoría del modelo: {best.label}</div>
                <div class="eco-kpis">
                <div><div class="eco-kpi-label">Confianza</div><div class="eco-kpi-value">{best.score * 100:.0f} %</div></div>
                <div><div class="eco-kpi-label">Contenedor recomendado</div>
                <div class="eco-kpi-value"><span class="eco-swatch" style="background:{swatch}"></span>{bin_key.capitalize()}</div></div>
                </div>
                <div class="eco-tip"><b>Cómo desecharlo</b>{result.tip}</div>""")
            top_predictions(result.top, "Las tres predicciones principales")

        elif result.status == "no_es_residuo":
            _md(f"""
                <div class="eco-message"><h3 class="eco-display">Esto no parece un residuo</h3>
                <p>La imagen no corresponde a un objeto que podamos clasificar. Puedes intentarlo con otra fotografía.</p></div>
                <div class="eco-tip"><b>Sugerencia</b>{result.tip}</div>""")

        else: 
            _md(f"""
                <div class="eco-message"><h3 class="eco-display">No tenemos suficiente confianza</h3>
                <p>El sistema no puede clasificar esta imagen con seguridad, así que prefiere no darte una recomendación equivocada.</p></div>
                <div class="eco-tip"><b>Qué hacer</b>{result.tip}</div>""")
            if result.top:
                top_predictions(result.top, "Lo más cercano que detectó (poco fiable)")


def tech_info(result, simulated: bool = True) -> None:
    with st.expander("Información técnica"):
        c1, c2 = st.columns(2)
        c1.metric("Dispositivo de inferencia", result.device)
        c2.metric("Tiempo de análisis", f"{sum(result.timings_ms.values()):.0f} ms")
        if simulated:
            st.caption("Valores simulados: no se ejecutó ninguna inferencia real.")


def category_chips(detected: str | None = None) -> None:
    chips = "".join(
        f'<span class="eco-cat{" eco-cat-on" if key == detected else ""}">{name}<small>{key}</small></span>'
        for key, name in CATEGORIES.items()
    )
    section_title("Lo que EcoClasifica reconoce", "Doce categorías de residuos.", anchor="categorias")
    _md(f'<div class="eco-cats">{chips}</div>')