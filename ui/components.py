from pathlib import Path
import streamlit as st

THEME_PATH = Path(__file__).parent / "theme.css"

CATEGORIES = {
    "Plastic": "Plástico", "Metal": "Metal", "Paper": "Papel", "Cardboard": "Cartón",
    "Green-Glass": "Vidrio verde", "White-Glass": "Vidrio transparente",
    "Biological": "Orgánico", "Brown-grass": "Residuo vegetal", "Trash": "Basura general",
    "Battery": "Pila o batería", "Clothes": "Ropa", "Shoes": "Calzado",
}

CATEGORY_DETAILS = {
    "Plastic": {"desc": "Botellas, envases y bolsas plásticas.", "tip": "Enjuaga el envase y retira las tapas antes de reciclar."},
    "Metal": {"desc": "Latas de aluminio, conservas y tapas metálicas.", "tip": "Asegúrate de aplastarlas un poco para ahorrar espacio."},
    "Paper": {"desc": "Hojas de cuaderno, periódicos, revistas y sobres.", "tip": "Evita reciclar papel sucio con grasa o restos de comida."},
    "Cardboard": {"desc": "Cajas de cartón corrugado y empaques.", "tip": "Desarma las cajas completamente antes de depositarlas."},
    "Green-Glass": {"desc": "Botellas y frascos de vidrio de color verde.", "tip": "No incluyas cerámica, espejos ni focos."},
    "White-Glass": {"desc": "Botellas y envases de vidrio transparente.", "tip": "Lava bien el recipiente y retira etiquetas si es posible."},
    "Biological": {"desc": "Restos de comida, frutas y verduras.", "tip": "Ideal para la creación de abono o compostaje casero."},
    "Brown-grass": {"desc": "Hojas secas, ramas y residuos de jardinería.", "tip": "Mantén los residuos secos y libres de plásticos."},
    "Trash": {"desc": "Residuos no reciclables ni aprovechables.", "tip": "Deposítalos en el contenedor de uso general."},
    "Battery": {"desc": "Pilas alcalinas, de botón y acumuladores.", "tip": "Llévalos siempre a puntos de recolección especializados, nunca a la basura común."},
    "Clothes": {"desc": "Prendas de vestir en desuso o textiles.", "tip": "Si están en buen estado, considera donarlas antes de desechar."},
    "Shoes": {"desc": "Calzado viejo o dañado.", "tip": "Agrupa los pares juntos si vas a entregarlos en puntos de acopio."},
}

STATUS_STYLE = {
    "reciclable": ("Reciclable", "ok"),
    "no_es_residuo": ("No parece un residuo", "neutral"),
    "incierto": ("Resultado incierto", "warn"),
}

BIN_SWATCH = {"blanco": "#FFFFFF"}
BIN_SWATCH_DEFAULT = "#C9CFC6"

LOGO_SVG = (
    '<svg width="36" height="36" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<path d="M24 4c8 6 9 16 0 23-9-7-8-17 0-23z" fill="#285C45"/>'
    '<path d="M24 4c8 6 9 16 0 23-9-7-8-17 0-23z" fill="#4F8A68" transform="rotate(120 24 24)"/>'
    '<path d="M24 4c8 6 9 16 0 23-9-7-8-17 0-23z" fill="#DDF2E6" transform="rotate(240 24 24)"/>'
    '</svg>'
)

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

def render_header() -> None:
    _md(f"""
        <div class="eco-nav" id="inicio">
            <div class="eco-brand">
                {LOGO_SVG}
                <div>
                    <div class="eco-wordmark">EcoClasifica</div>
                    <div class="eco-tag">Clasificación inteligente de residuos</div>
                </div>
            </div>
            <div class="eco-links">
                <a href="#inicio">Inicio</a>
                <a href="#analizar">Analizar</a>
                <a href="#categorias">Categorías</a>
            </div>
        </div>
    """)

def render_hero() -> None:
    _md("""
        <div class="eco-hero">
            <h1>Cada residuo tiene un destino.<br>Descubre cómo clasificarlo.</h1>
            <p>Identifica tus residuos a partir de una fotografía y descubre cómo disponer de ellos correctamente.</p>
            <div class="eco-steps">
                <span class="eco-step"><b>1</b>Carga una fotografía</span>
                <span class="eco-step"><b>2</b>Analiza el residuo</span>
                <span class="eco-step"><b>3</b>Consulta su disposición</span>
            </div>
        </div>
    """)

def section_title(title: str, subtitle: str, anchor: str = "") -> None:
    anchor_attr = f' id="{anchor}"' if anchor else ""
    _md(f"""
        <div class="eco-section-title"{anchor_attr}>{title}</div>
        <div class="eco-section-sub">{subtitle}</div>
    """)

def empty_state(title: str, body: str) -> None:
    _md(f"""
        <div class="eco-empty">
            <b>{title}</b>
            <p style="margin: 0.3rem 0 0; color: var(--muted); font-size: 0.9rem;">{body}</p>
        </div>
    """)

def top_predictions(predictions, heading: str) -> None:
    _md(f'<div class="eco-subhead">{heading}</div>')
    for pred in predictions[:3]:
        c_label, c_bar, c_pct = st.columns([3, 5, 1.4], vertical_alignment="center")
        label = CATEGORIES.get(pred.label, pred.label)
        score = min(max(pred.score, 0.0), 1.0)
        c_label.write(label)
        c_bar.progress(score)
        c_pct.write(f"{score * 100:.0f} %")

def result_card(result, simulated: bool = True) -> None:
    pill, css = STATUS_STYLE.get(result.status, STATUS_STYLE["incierto"])
    with st.container(border=True, key=f"result_card_{css}"):
        badge = '<span class="eco-demo-badge">DEMOSTRACIÓN CON DATOS SIMULADOS</span>' if simulated else ""
        _md(f'{badge}<span class="eco-pill eco-pill-{css}">{pill}</span>')

        if result.status == "reciclable" and result.top:
            best = result.top[0]
            bin_key = (result.bin or "").lower()
            swatch = BIN_SWATCH.get(bin_key, BIN_SWATCH_DEFAULT)
            category_name = CATEGORIES.get(best.label, best.label)
            confidence = best.score * 100
            _md(f"""
                <div class="eco-result-label">{category_name}</div>
                <div class="eco-result-sub">Categoría del modelo: {best.label}</div>
                <div class="eco-kpis">
                    <div>
                        <div class="eco-kpi-label">Confianza del modelo</div>
                        <div class="eco-kpi-value">{confidence:.0f} %</div>
                    </div>
                    <div>
                        <div class="eco-kpi-label">Contenedor recomendado</div>
                        <div class="eco-kpi-value">
                            <span class="eco-swatch" style="background:{swatch}"></span>
                            {bin_key.capitalize()}
                        </div>
                    </div>
                </div>
                <div class="eco-tip">
                    <b>¿Cómo desecharlo?</b>
                    {result.tip}
                </div>
            """)
            top_predictions(result.top, "Otras predicciones del modelo")

        elif result.status == "no_es_residuo":
            _md(f"""
                <div class="eco-message">
                    <h3>Esto no parece un residuo</h3>
                    <p>La imagen no corresponde a un objeto que podamos clasificar.</p>
                </div>
                <div class="eco-tip">
                    <b>Sugerencia</b>
                    {result.tip}
                </div>
            """)

        else:
            _md(f"""
                <div class="eco-message">
                    <h3>No tenemos suficiente confianza</h3>
                    <p>El sistema no puede clasificar esta imagen con seguridad.</p>
                </div>
                <div class="eco-tip">
                    <b>Qué hacer</b>
                    {result.tip}
                </div>
            """)
            if result.top:
                top_predictions(result.top, "Posibles categorías detectadas")

def tech_info(result, simulated: bool = True) -> None:
    with st.expander("Información técnica del análisis", expanded=False):
        c1, c2 = st.columns(2)
        c1.metric("Dispositivo de inferencia", result.device)
        total_time = sum(result.timings_ms.values())
        c2.metric("Tiempo de análisis", f"{total_time:.0f} ms")
        if simulated:
            st.caption("Valores simulados: no se ejecutó ninguna inferencia real.")

def category_chips(detected: str | None = None) -> None:
    section_title(
        "Explora las categorías",
        "Selecciona un tipo de residuo para conocer sus características y recomendaciones.",
        anchor="categorias"
    )

    st.session_state.setdefault("manual_category", list(CATEGORIES.keys())[0])
    active_category = detected if detected else st.session_state.get("manual_category")
    keys = list(CATEGORIES.keys())
    cols_per_row = 4

    for i in range(0, len(keys), cols_per_row):
        row_keys = keys[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col_idx, key in enumerate(row_keys):
            name = CATEGORIES[key]
            is_selected = (key == active_category)
            btn_type = "primary" if is_selected else "secondary"
            with cols[col_idx]:
                if st.button(name, key=f"cat_btn_{key}", type=btn_type, use_container_width=True):
                    st.session_state.manual_category = key
                    st.rerun()

    if active_category and active_category in CATEGORY_DETAILS:
        info = CATEGORY_DETAILS[active_category]
        name = CATEGORIES.get(active_category, active_category)
        _md(f"""
            <div class="eco-category-info-card">
                <div style="font-size: 1.1rem; font-weight: 700; color: var(--forest); margin-bottom: 0.7rem;">
                    Información sobre {name}
                </div>
                <p style="color: var(--ink); font-size: 0.9rem; margin-bottom: 0.7rem;">
                    <b>Descripción:</b> {info['desc']}
                </p>
                <div class="eco-tip">
                    <b>Recomendación de manejo</b>
                    {info['tip']}
                </div>
            </div>
        """)