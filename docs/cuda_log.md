# Registro de trabajo: CUDA

Responsable: Felipe · Rama: `Felipe_branch` · Rol Scrum: desarrollador CUDA

Este archivo es el cuaderno de bitácora de la parte CUDA del proyecto. Cada vez que se hace algo relevante se añade una entrada nueva **arriba** de la sección "Bitácora", con fecha, qué se hizo, qué resultó y qué sigue. Sirve de base para `docs/cuda.md` (la explicación final con nuestras palabras) y para preparar la sustentación del 11 de noviembre.

Los mensajes de commit se escriben en inglés (por ejemplo, `docs(cuda): update work log`).

---

## 1. Entorno de pruebas

| Dato | Valor |
| --- | --- |
| GPU | NVIDIA GeForce GTX 1650 Ti |
| Memoria de la GPU | 4 GB (4096 MiB) |
| Capacidad de cómputo | 7.5 (arquitectura Turing, sin tensor cores) |
| PyTorch | 2.15.0+cu132 |
| CUDA | 13.2 |
| Sistema | WSL con Ubuntu, entorno virtual `cuda_env` |
| Modelo probado | [watersplash/waste-classification](https://huggingface.co/watersplash/waste-classification) (ViT, 85,8 M de parámetros, 12 clases) |
| Imagen de prueba vigente | `tests/images/large_bottle.jpg`, 1200 × 1200 px |

---

## 2. Resultados vigentes

Prueba del 2026-11-02 con `large_bottle.jpg`. Las tres configuraciones predijeron `plastic`.

**CPU contra GPU** (`python -m benchmarks.cpu_vs_gpu tests/images/large_bottle.jpg`, 30 repeticiones por defecto y 5 de calentamiento descartadas):

| Configuración | Copia (ms) | Inferencia (ms) | Desviación (ms) | Clase |
| --- | --- | --- | --- | --- |
| CPU fp32 | 0,00 | 178,60 | 4,27 | plastic |
| GPU fp32 | 0,70 | 28,61 | 1,80 | plastic |
| GPU fp16 | 0,50 | 118,52 | 0,06 | plastic |

**Solo GPU** (`--runs 500 --gpu-only`):

| Configuración | Copia (ms) | Inferencia (ms) | Desviación (ms) | Clase |
| --- | --- | --- | --- | --- |
| GPU fp32 | 0,48 | 28,21 | 0,49 | plastic |
| GPU fp16 | 0,38 | 119,44 | 0,11 | plastic |

Lectura de los números:

- La GPU en fp32 es **6,2 veces más rápida** que la CPU con la misma imagen (178,60 / 28,61).
- fp16 es **4,1 veces más lento** que fp32 en la primera tabla (118,52 / 28,61) y **4,2 veces** en la corrida de 500 repeticiones (119,44 / 28,21). El patrón se repite, y la clase predicha es la misma.
- La copia a la GPU cuesta menos de 1 ms, muy poco frente a los 28 ms de cálculo.
- La copia de la CPU marca 0,00 ms porque el tensor ya está en la memoria de la CPU y no hay traslado.

**Actividad de la GPU** (`nvidia-smi -l 1`):

| Estado | Utilización de la GPU | Memoria utilizada | Temperatura |
| --- | --- | --- | --- |
| Reposo | 0 % | 0 MiB / 4096 MiB | 44 °C |
| Durante la inferencia | 97 % | 463 MiB / 4096 MiB | 56 °C |

El aumento de memoria es coherente con el tamaño del modelo: 85,8 millones de parámetros en fp32 son unos 343 MB, más el contexto de CUDA.

**Conclusión:** en esta imagen y este equipo, GPU fp32 dio el menor tiempo de inferencia y conservó la predicción `plastic`. fp16 dio la misma clase pero fue más lento.

---

## 3. Decisiones tomadas

| Fecha | Decisión | Motivo |
| --- | --- | --- |
| 2026-11-01 | La GPU corre en **fp32**; no se aplica `.half()` | En la GTX 1650 Ti, fp16 tarda unos 118 ms frente a unos 28 ms de fp32, y se confirmó en dos imágenes distintas. La tarjeta no tiene tensor cores |
| 2026-11-01 | El dispositivo se elige solo en `src/device.py`; el resto del código lo recibe como parámetro | Evita escribir `"cuda"` a mano en varios archivos y facilita pasar a CPU en otra máquina |
| 2026-11-01 | Se prueba fp16 y se documenta su descarte | La rúbrica pide declarar los ajustes hechos y explicar los que no se aplicaron |
| 2026-11-02 | Los nombres de carpetas y archivos van en inglés (`docs/evidence/`) | Consistencia con el resto del repositorio |
| 2026-11-06 | No se añade preprocesado de imagen al pipeline | Dos variantes (recorte + JPEG, y ajuste con relleno gris) dieron peores resultados que la imagen original en 25 fotos; el procesador del modelo ya redimensiona y normaliza |

---

## 4. Archivos de evidencia

Todos en `docs/evidence/`.

| Archivo | Qué muestra |
| --- | --- |
| `cpu_vs_gpu.png` | CPU fp32, GPU fp32 y GPU fp16 con la misma imagen. Captura principal del criterio 6 |
| `gpu_fp32_vs_fp16.png` | Corrida solo en GPU con 500 repeticiones, que respalda el descarte de fp16 |
| `nvidia_smi_idle.png` | `nvidia-smi` con la GPU en reposo |
| `nvidia_smi_inference.png` | `nvidia-smi` durante la inferencia: 97 % de utilización y más memoria |

Rótulos para el README y `docs/cuda.md`:

- Figura 1. Misma imagen de 1200 × 1200 px y mismo modelo en tres configuraciones: la GPU en fp32 tarda 28,61 ms y la CPU 178,60 ms.
- Figura 2. Solo GPU, 500 repeticiones: fp32 tarda 28,21 ms y fp16 119,44 ms.
- Figura 3. GPU en reposo: 0 % de utilización y 0 MiB de memoria.
- Figura 4. GPU durante la inferencia: 97 % de utilización y 463 MiB de memoria.

---

## 5. Bitácora

Las entradas nuevas van arriba.

### 2026-11-06 · Pruebas de preprocesado (sugerencia del profesor)

- Qué se hizo: se probaron dos preprocesados antes del pipeline sobre 25 fotos propias. `preprocessing.py` recortaba la imagen a un cuadrado de 224 × 224 con `ImageOps.fit` y la recodificaba como JPEG con calidad 85. `preprocessing_v2.py` ajustaba la imagen completa dentro de un cuadrado de 224 × 224 conservando la proporción, rellenando con gris neutro, sin recortar ni comprimir.
- Resultado: en estas 25 fotos, la imagen original dio mejores resultados que las dos variantes (aciertos: original __ de 25, v1 __ de 25, v2 __ de 25).
- Hallazgo: según la configuración del procesador del modelo, este ya redimensiona a 224 × 224 (bilinear) y normaliza con media 0,5 y desviación 0,5 por canal, sin recorte central ni recodificación. Las variantes añadían transformaciones que no forman parte de la receta del modelo.
- Decisión tomada: no se añade preprocesado al pipeline.
- Pendiente: verificar la configuración imprimiendo el procesador; documentar este resultado en `docs/cuda.md` y en la ficha del modelo.

### 2026-11-05 · Benchmark del pipeline completo (línea base)

- Qué se hizo: se creó `benchmarks/pipeline_cpu_vs_gpu.py` y se midió el pipeline completo (filtro CLIP + clasificador ViT) en CPU y GPU con `large_bottle.jpg` (1200 × 1200 px), 30 repeticiones y 5 de calentamiento, en fp32.
- Resultado: total CPU 328,09 ms y GPU 73,52 ms (4,5 veces más rápida). Filtro: 130,41 ms contra 38,59 ms (3,4 veces). Clasificador: 196,14 ms contra 34,18 ms (5,7 veces). Mismo estado (`reciclable`) y misma clase (`Plastic`) en ambos dispositivos. `wall_ms` (73,60) coincide con `total_ms` (73,52), así que no hay tiempo relevante fuera de las etapas medidas.
- Decisión tomada: se descarta la primera ejecución (CPU 411,50 ms, GPU 83,47 ms) porque los modelos se descargaban en segundo plano durante la medición. Se toma la segunda como referencia.
- Pendiente: capturas de `nvidia-smi` con el pipeline completo; comprobar si el preprocesado en CPU del filtro explica su variabilidad en GPU; repetir la medición después de añadir el preprocesado.

### 2026-11-02 · Segunda ronda de pruebas con una imagen más grande

- Se repitió el benchmark con `large_bottle.jpg` (1200 × 1200 px) y se tomaron las capturas de nuevo.
- Resultado: GPU fp32 es 6,2 veces más rápida que la CPU, y fp16 sigue siendo unas 4 veces más lento que fp32. Los valores coinciden con la primera ronda, así que el resultado es estable.
- La GPU llegó a 97 % de utilización y 463 MiB de memoria, con la temperatura subiendo de 44 a 56 °C.
- Se midió el preprocesado en CPU con la imagen de 1200 × 1200 px.
- Push de `docs/evidence/` y del registro a `Felipe_branch`: hecho.

### 2026-11-01 · Benchmark CPU contra GPU y evidencia

- Se creó `benchmarks/cpu_vs_gpu.py`: carga el modelo de Hugging Face, mide copia a la GPU e inferencia por separado, descarta 5 repeticiones de calentamiento y sincroniza la GPU (`sync()`) antes y después de cada medición.
- Primera ronda con una imagen de 565 × 900 px: CPU fp32 181,43 ms, GPU fp32 28,66 ms y GPU fp16 118,49 ms, todas con la clase `plastic`.
- Se concluyó que fp16 no ayuda en esta tarjeta y se decidió trabajar en fp32.

### 2026-11-01 · `src/device.py`

- Se creó `src/device.py` con `get_device()`, `sync()` y `gpu_info()` según el contrato del equipo.
- `python -m src.device` confirma que PyTorch ve la GTX 1650 Ti.
- Se trabaja en la rama `Felipe_branch` y se abre Pull Request hacia `main`.

### 2026-11-01 · Planeación

- Se definió el plan del proyecto: arquitectura, contrato entre módulos, roles Scrum y backlog.
- Tareas propias: S1-4 (`device.py`), S1-5 (medir tiempos), S2-1 (benchmark y `nvidia-smi`) y S2-4 (`docs/cuda.md`).

### Plantilla para entradas nuevas

```markdown
### AAAA-MM-DD · Título corto

- Qué se hizo:
- Resultado (con números):
- Decisión tomada, si hubo:
- Pendiente:
```

---

## 6. Pendientes

- [x] Hacer push de `docs/evidence/` y de este registro
- [x] Repetir el benchmark con una imagen más grande
- [x] Medir las etapas del pipeline real (filtro, clasificación, total) cuando Javier tenga `pipeline.analyze`
- [x] Escribir `docs/cuda.md` con nuestras palabras: qué corre en el host, qué en el device y cómo viajan los datos (fecha límite: sábado 7 de noviembre)
- [ ] Preparar la explicación para la sustentación: 2 minutos sobre CUDA y la comparación CPU contra GPU
- [x] Tomar las capturas del pipeline completo (tabla de la segunda ejecución y `nvidia-smi` con `--runs 300 --gpu-only`) y guardarlas en `docs/evidence/` con el prefijo `pipeline_`
- [ ] Probar la hipótesis del preprocesado en CPU del filtro con la imagen reducida a 448 × 448 y registrar el resultado
- [ ] Añadir la tabla del pipeline completo a `docs/cuda.md`
- [x] Preprocesado (sugerencia del profesor): crear `src/preprocess.py` y comparar con y sin él sobre las fotos propias de Aura
- [x] Fiabilidad con campana de Gauss (sugerencia del profesor): apoyar a Aura con el puntaje z sobre los logits (descartado por decicion popular)
- [x] Modelo de lenguaje con prompt maestro (sugerencia del profesor): confirmar el modelo con el equipo y medir la memoria de la GPU de cada modelo (ViT, CLIP y LLM) para decidir entre fp16, cuantización o CPU (descartado por decicion popular)
- [ ] Acordar con Javier el cambio del contrato (campos opcionales en `AnalysisResult`) y las claves de `timings_ms`
- [x] Repetir el benchmark del pipeline completo después de añadir el preprocesado y el modelo de lenguaje(descartado por decicion popular, viva la democracia :D)
- [ ] Probar el plan B en Colab o Kaggle antes de la sustentación

---

## 7. Convención de commits

Los mensajes de commit se escriben **en inglés**, con el formato `tipo(ámbito): descripción en imperativo`, en minúsculas y sin punto final.

| Tipo | Cuándo |
| --- | --- |
| `feat` | Funcionalidad nueva |
| `fix` | Corrección de un error |
| `docs` | Documentación o evidencia |
| `perf` | Mejora o medición de rendimiento |
| `refactor` | Cambio interno sin alterar el comportamiento |
| `test` | Pruebas |
| `chore` | Dependencias y mantenimiento |

Ejemplos:

```text
feat(cuda): add device selection helpers
feat(cuda): add CPU vs GPU benchmark with fp32 and fp16
docs(cuda): add GPU evidence screenshots
docs(cuda): add CUDA work log
perf(cuda): keep fp32 on GPU after fp16 measured slower
```

Para ver el historial de commits y completarlo aquí cuando haga falta:

```bash
git log --oneline --author="Tu nombre en GitHub"
```