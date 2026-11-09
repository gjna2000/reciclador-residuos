# Selección de configuración para Grounding DINO

## Decisión

Para las siguientes pruebas se elige la **configuración 3 de `gdino_calibration_v2.py`**:

- Modelo: `IDEA-Research/grounding-dino-tiny` (Grounding DINO).
- Umbral de confianza: **0.20**.
- NMS global, sin separar por etiqueta, con IoU de **0.5**.
- Se descartan cajas vacías y cajas que cubren más del **70 %** de la imagen.
- Máximo de **4 detecciones** por imagen.
- Ejecución en GPU CUDA.

Esta es una selección operativa basada en la inspección visual de las pruebas realizadas. No representa una calibración probabilística de los puntajes ni un reentrenamiento del modelo.

## Fragmento exacto de la configuración elegida

El archivo de prueba conserva las tres opciones para que los resultados sean reproducibles. La opción seleccionada es `configuration_03`:

```python
CONFIGURATIONS = [
    {"name": "configuration_01", "threshold": 0.05},
    {"name": "configuration_02", "threshold": 0.10},
    {"name": "configuration_03", "threshold": 0.20},
]
MAX_AREA = 0.7
NMS_IOU = 0.5
TOP_N = 4
```

La supresión de duplicados aplicada en la versión 2 es independiente de las etiquetas: entre cajas muy solapadas conserva la de mayor puntaje, aunque el modelo les haya asignado etiquetas distintas.

```python
keep = nms(boxes, scores, NMS_IOU)[:TOP_N]
```

En la ejecución, Grounding DINO recibe el umbral de la configuración seleccionada:

```python
raw = detector(
    image,
    candidate_labels=LABELS,
    threshold=config["threshold"],
)
detections = select_detections(raw, width, height)
```

El código completo permanece en [`benchmarks/gdino_calibration_v2.py`](../benchmarks/gdino_calibration_v2.py). La versión 1 no se modifica.

## Cómo se llegó a esta decisión

1. Se preparó una primera prueba con tres umbrales: `0.05`, `0.10` y `0.20`. La versión 1 aplicaba NMS por etiqueta, por lo que una misma región podía aparecer varias veces con etiquetas como `wrapper` y `peel`.
2. Se creó la versión 2 para aplicar NMS sin separar por etiqueta. Así se redujeron duplicados que correspondían a la misma región, conservando la detección con mayor puntaje.
3. En `babana_coffee_sachet_1.jpg`, la configuración 3 produjo el resultado visual que se consideró correcto: dos objetos detectados y clasificados correctamente.
4. En `babana_coffee_sachet_2.jpg`, la configuración 3 mantuvo las detecciones principales de la cáscara y el sachet. La configuración 2 añadía detecciones de menor puntaje, incluido un detalle impreso en el empaque, y detectaba un empaque adicional que debía evaluarse según si se consideraba residuo.
5. En `plastic_bag.jpg`, la configuración 3 detectó la bolsa y evitó las cajas dudosas sobre el escritorio y la hoja. La configuración 2 recuperaba una posible detección sobre la hoja, pero también producía detecciones no deseadas.
6. Después se probó la configuración con `exit_mf.jpeg`, `kitchen.jpg`, `disassembled_motorcycle.jpg`, `chair_pants.jpg` y una imagen borrosa. Tras revisar esas salidas, se decidió conservar la configuración 3 como la opción que mejor funcionó en el tiempo disponible.

La decisión prioriza resultados visuales más limpios y menos falsos positivos. Un umbral de `0.20` también puede descartar objetos reales con puntajes menores; por eso, si se incorporan imágenes nuevas donde la configuración 3 omite residuos importantes, conviene registrar ese caso y reevaluar el umbral.

## Ejecución reproducible

La versión 2 genera las tres configuraciones para cada imagen y guarda las imágenes anotadas y el CSV en `benchmarks/gdino_calibration_v2_results/`:

```bash
python benchmarks/gdino_calibration_v2.py "tests/images/test2/exit_mf.jpeg"
```

Para revisar la configuración seleccionada, abrir la imagen cuyo nombre termina en `_configuration_03.jpg` y consultar las filas `configuration_03` del CSV correspondiente.
