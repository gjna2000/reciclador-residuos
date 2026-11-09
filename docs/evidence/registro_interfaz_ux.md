# Registro de trabajo: Interfaz y UX (UI/UX)

**Proyecto:** EcoClasifica
**Responsable:** Viviana Marcela Jimenez Rojas
**Rama:** `feat/ui`
**Rol Scrum:** Desarrolladora UI/UX y Documentación

Bitácora de las decisiones de diseño visual, la estructura de componentes, el tema corporativo y el flujo de integración del frontend de EcoClasifica.

---

## 1. Resumen del entorno y tecnologías UI

| Componente | Tecnología / Valor |
|---|---|
| Framework web | Streamlit 1.40+ (se usan contenedores con `key` y `st.columns(vertical_alignment=...)`) |
| Tipografía | Manrope (títulos, 500 a 800) e Inter (texto), vía Google Fonts |
| Iconografía | Material Symbols Outlined |
| Paleta | Forest `#0E3B2E` / `#164E3F`, Eco green `#16A34A`, Lime `#84CC16` / `#A3E635`, ámbar `#F59E0B` para advertencias |
| Fondo | Degradado verde muy suave (`#E7F1EA` → `#EDF5EF` → `#E4EEE7`) con paneles blancos |
| Estilos | Archivo global `ui/theme.css`, inyectado con `load_theme()` |
| Componentes | Módulo `ui/components.py` (encabezado, hero, tarjetas, chips, resultado, catálogo) |
| Referencia de diseño | Prototipo de Google Stitch (`DESIGN.md` y `code.html`), adaptado a Streamlit |

> Nota: en el registro inicial la paleta se describía como Forest `#285C45` / Sage / Mint / Cream. A partir del 2026-11-05 el tema se rehízo con la paleta de Stitch indicada arriba.

## 2. Estructura de archivos

```
proyecto/
├─ .streamlit/config.toml     Configuración del servidor (maxUploadSize = 200)
├─ assets/categorias/         Fotografías de las 12 categorías
├─ docs/                      Documentación
├─ src/                       Módulos del equipo (pipeline, YOLO, etc.)
├─ ui/
│  ├─ components.py           Componentes visuales y datos de las 12 categorías
│  └─ theme.css               Estilos globales, variables, animaciones y responsive
├─ app.py                     Punto de entrada: sesión, carga de imagen y flujo de análisis
└─ requirements.txt
```

| Archivo | Responsabilidad |
|---|---|
| `app.py` | Coordina la sesión, la carga de imágenes y la llamada al análisis. No contiene HTML/CSS crudo. |
| `ui/theme.css` | Variables de color, fondo, paneles, vista previa de imagen, animación de la caneca, rejilla de categorías y reglas responsive. |
| `ui/components.py` | `render_header`, `render_hero`, `section_title`, `empty_state`, `result_card`, `tech_info`, `category_cards_grid`, `render_footer` y el diccionario de las 12 categorías. |

## 3. Decisiones técnicas y de diseño

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-11-01 | Encapsular la UI en `ui/` | Separar responsabilidades y no ensuciar `app.py` con HTML/CSS. |
| 2026-11-02 | Centrado de imagen con flexbox | Alineación correcta con `margin: 0 auto` en `.stImage`. |
| 2026-11-03 | Compactar la cabecera | Reducir el padding de `.block-container` para eliminar espacios muertos. |
| 2026-11-04 | Conexión con backend | Invocación de `pipeline.analyze` con `@st.cache_resource`. |
| 2026-11-05 | Rediseño con la referencia de Stitch | Mantener la identidad visual del prototipo: distribución 7/12 (carga) y 5/12 (resultado), tarjetas, sombras tintadas y hover. |
| 2026-11-05 | Fondo verde suave en lugar de blanco | Dar identidad ambiental sin saturar; los paneles quedan blancos para contraste. |
| 2026-11-05 | Contenedor de vista previa de tamaño fijo con `object-fit: contain` | Evitar que una imagen vertical, horizontal o cuadrada deforme o desplace el panel. |
| 2026-11-05 | Selector de modalidad (subir archivo / cámara) con el mismo flujo de análisis | No duplicar la lógica de clasificación. |
| 2026-11-05 | Fotografías de categorías cargadas desde `assets/categorias/` | Que aparezcan al guardar el archivo, sin tocar el código; con espacio provisional si faltan. |
| 2026-11-05 | Animación de caneca (tapa que se abre y objeto que cae) con SVG y CSS | Mostrar la caneca según el color de la categoría detectada; respeta la preferencia `prefers-reduced-motion`. |
| 2026-11-06 | Barra de color de la caneca anclada a la tarjeta | La barra (`.eco-binbar`) se posicionaba respecto al bloque de texto y tapaba el inicio del título. Se corrige con `position: static` en los contenedores intermedios. |
| 2026-11-06 | Prototipo de cámara en vivo descartado | El equipo decidió que YOLO lo implementan los compañeros; el frontend se devolvió a la versión anterior a YOLO. |
| 2026-11-07 | Encabezado sin elementos decorativos | Se retiraron "IA YOLOv8 Edge Activa", "CO Res. 2184", el ícono oscuro y la insignia "Simulación de Integración Activa", porque no reflejaban estados reales. |
| 2026-11-07 | Sección compacta "¿Qué va en cada caneca?" | Mostrar las canecas y sus categorías sin ocupar buena parte de la página. |
| 2026-11-07 | Zona de carga y espacios revisados | Vista previa centrada, zona de arrastrar y soltar real (el propio cargador) y distribución equilibrada entre paneles. |

## 4. Bitácora de avances

- **2026-11-07:** Interfaz finalizada. Fotografías de las 12 categorías cargadas. Encabezado limpio, sección de canecas y categorías, vista previa centrada, zona de arrastrar y soltar y ajuste de espacios. Se prepara la integración de `app.py` con el pipeline y con YOLO.
- **2026-11-06:** Corrección del título recortado en el panel de resultados. Análisis del espacio vacío bajo el panel de carga. Prototipo de cámara en vivo con YOLOv8-World y `streamlit-webrtc`, que se descartó cuando el equipo asumió YOLO. Revisión del detector del equipo (`YOLODetector`): devuelve `class_id`, `label`, `confidence` y `bbox`; no dibuja, no recorta y no maneja vídeo.
- **2026-11-05:** Rediseño del frontend con la referencia de Stitch (encabezado, hero con pasos, panel de carga, tarjeta de resultado, catálogo de categorías con filtros y tarjeta de detalle, pie de página). Fondo verde suave. Panel de imagen controlado. Selector de modalidad de entrada. Animación de caneca.
- **2026-11-04:** Conexión limpia con el pipeline real de IA, optimización del CSS y compactación de diccionarios en `ui/components.py`.
- **2026-11-03:** Ajustes de alineación en las tarjetas de previsualización y refinamiento de estados vacíos ("Fotografía lista", "Aquí aparecerá tu resultado").
- **2026-11-02:** Catálogo interactivo de 12 categorías con tarjetas informativas.
- **2026-11-01:** Definición del tema ecológico verde, barra de navegación superior y sección hero.

## 5. Clasificación de las 12 categorías por caneca

Según la separación en la fuente en Colombia (Resolución 2184), tal como la muestra la interfaz (`CATEGORY_DETAILS` y `BIN_INFO` en `ui/components.py`):

| Destino | Categorías (clave del modelo) |
|---|---|
| Caneca blanca (aprovechables limpios y secos) | Plástico `Plastic`, Metal `Metal`, Papel `Paper`, Cartón `Cardboard`, Vidrio verde `Green-Glass`, Vidrio claro `White-Glass` |
| Caneca verde (orgánicos aprovechables) | Orgánico `Biological`, Residuo vegetal `Brown-grass` |
| Caneca negra (no aprovechables) | Basura general `Trash` |
| Puntos de recolección autorizados | Pila o batería `Battery`, Ropa textil `Clothes`, Calzado `Shoes` |

## 6. Contrato entre la interfaz y el análisis

La interfaz espera este formato de resultado (no se modifica `ui/components.py` al integrar):

- `status`: `"reciclable"`, `"no_es_residuo"` o `"incierto"`.
- `top`: lista ordenada de predicciones con `label` y `score` (0 a 1). Los `label` deben ser exactamente las claves de la tabla anterior.
- `tip` (texto), `device` (texto), `timings_ms` (diccionario) y `bin` (puede ser `None`).
- La caneca que se muestra se calcula en `components.py` a partir del `label`. Si el pipeline calcula su propia caneca, ambas deben coincidir.

## 7. Pendientes y próximos entregables

- [x] Diseñar la interfaz modular y el esquema CSS corporativo.
- [x] Rediseñar el frontend con la referencia de Stitch y cargar las fotografías de las categorías.
- [x] Dejar la interfaz final (encabezado limpio, canecas y categorías, vista previa centrada).
- [ ] Conectar `app.py` con el pipeline real (sin simulación) de forma que la interfaz siga funcionando igual.
- [ ] Integrar el detector YOLO del equipo para la cámara en vivo: detectar, recortar cada objeto y clasificarlo con el pipeline.
- [ ] Verificar que la caneca del pipeline y la de la interfaz coincidan para las 12 categorías.
- [ ] Participar en las sesiones cruzadas de equipo.
- [ ] Redactar la sección de interfaz y capturas de pantalla para el `README.md`.
- [ ] Grabar la intervención correspondiente en el video final de demostración (5 minutos).
