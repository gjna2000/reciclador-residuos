# Registro de trabajo: CUDA

Responsable: Felipe · Rama: `Felipe_branch` · Rol Scrum: desarrollador CUDA

Este archivo es el cuaderno de bitácora de la parte CUDA del proyecto. Cada vez que se hace algo relevante se añade una entrada nueva **arriba** de la sección "Bitácora", con fecha, qué se hizo, qué resultó y qué sigue. Sirve de base para `docs/cuda.md` (la explicación final con nuestras palabras) y para preparar la sustentación del 11 de noviembre.

---

## 1. Entorno de pruebas

| Dato | Valor |
| --- | --- |
| GPU | NVIDIA GeForce GTX 1650 Ti |
| Memoria de la GPU | 4,0 GB |
| Capacidad de cómputo | 7.5 (arquitectura Turing, sin tensor cores) |
| PyTorch | 2.15.0+cu132 |
| CUDA | 13.2 |
| Sistema | Windows, entorno virtual `cuda_env` |
| Modelo probado | [watersplash/waste-classification](https://huggingface.co/watersplash/waste-classification) (ViT, 85,8 M de parámetros, 12 clases) |
| Imagen de prueba | `tests/images/botella.jpg`, 565 × 900 px |

---

## 2. Resultados vigentes

Benchmark `python -m benchmarks.cpu_vs_gpu tests/images/botella.jpg` (5 repeticiones de calentamiento descartadas antes de medir).

| Configuración | Copia a la GPU (ms) | Inferencia (ms) | Desviación (ms) | Clase |
| --- | --- | --- | --- | --- |
| CPU fp32 | 0,10 | 181,43 | 4,25 | plastic |
| GPU fp32 | 0,55 | 28,66 | 1,88 | plastic |
| GPU fp16 | 0,50 | 118,49 | 0,06 | plastic |

Lectura de los números:

- La GPU en fp32 es **6,3 veces más rápida** que la CPU con la misma imagen (181,43 / 28,66).
- fp16 es **4,1 veces más lento** que fp32 en esta tarjeta (118,49 / 28,66), aunque da la misma clase.
- La copia de la imagen a la GPU cuesta unos 0,5 ms, muy poco frente a los 28,66 ms de cálculo con esta imagen.
- Preprocesado en CPU (redimensionar y normalizar): 77,3 ms. Es una sola medición y puede incluir sobrecarga de la primera llamada; conviene repetirla.

Evidencia de uso de la GPU (`nvidia-smi -l 1`, valores aproximados leídos de las capturas):

| Magnitud | En reposo | En inferencia |
| --- | --- | --- |
| Utilización de la GPU | 0 % | 98 % |
| Memoria utilizada | unos 33 MiB | unos 400 MiB |
| Consumo | unos 2 W | entre 33 y 40 W |

El salto de memoria es coherente con el tamaño del modelo: 85,8 millones de parámetros en fp32 son unos 343 MB, más el contexto de CUDA.

---

## 3. Decisiones tomadas

| Fecha | Decisión | Motivo |
| --- | --- | --- |
| 2026-11-01 | La GPU corre en **fp32**; no se aplica `.half()` | En la GTX 1650 Ti, fp16 tarda 118,49 ms frente a 28,66 ms de fp32. La tarjeta no tiene tensor cores, así que fp16 no acelera |
| 2026-11-01 | El dispositivo se elige solo en `src/device.py`; el resto del código lo recibe como parámetro | Evita escribir `"cuda"` a mano en varios archivos y facilita pasar a CPU en otra máquina |
| 2026-11-01 | Se prueba fp16 y se documenta su descarte | La rúbrica pide declarar los ajustes hechos y explicar los que no se aplicaron |

---

## 4. Archivos de evidencia

Todos en `docs/evidencia/`.

| Archivo | Qué muestra |
| --- | --- |
| `cpu_vs_gpu.png` | Comparación de CPU fp32, GPU fp32 y GPU fp16 con la misma imagen. Es la captura principal del criterio 6 |
| `gpu_fp32_vs_fp16.png` | Corrida solo en GPU (`--gpu-only`) que respalda el descarte de fp16 |
| `nvidia_smi_reposo.png` | `nvidia-smi` con la GPU en reposo |
| `nvidia_smi_inferencia.png` | `nvidia-smi` durante la inferencia: 98 % de utilización y más memoria y consumo |

Rótulos para el README y `docs/cuda.md`:

- Figura 1. Misma imagen y mismo modelo en tres configuraciones: la GPU en fp32 tarda 28,66 ms y la CPU 181,43 ms.
- Figura 2. Solo GPU: fp32 es más rápido que fp16 en la GTX 1650 Ti.
- Figura 3. GPU en reposo.
- Figura 4. GPU durante la inferencia.

---

## 5. Bitácora

Las entradas nuevas van arriba.

### 2026-11-01 · Benchmark CPU contra GPU y evidencia

- Se creó `benchmarks/cpu_vs_gpu.py`: carga el modelo de Hugging Face, mide copia a la GPU e inferencia por separado, descarta 5 repeticiones de calentamiento y sincroniza la GPU (`sync()`) antes y después de cada medición.
- Resultado: GPU fp32 es 6,3 veces más rápida que la CPU. fp16 resultó más lento que fp32, por lo que se descarta.
- Se tomaron cuatro capturas de evidencia (sección 4).
- Pendiente: repetir el benchmark con una imagen más grande y confirmar el número de repeticiones de la corrida `--gpu-only`.

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
- [ ] Repetir el benchmark con una imagen más grande
- [ ] Medir las etapas del pipeline real (filtro, clasificación, total) cuando Javier tenga `pipeline.analyze`
- [ ] Escribir `docs/cuda.md` con nuestras palabras: qué corre en el host, qué en el device y cómo viajan los datos (fecha límite: sábado 7 de noviembre)
- [ ] Preparar la explicación para la sustentación: 2 minutos sobre CUDA y la comparación CPU contra GPU

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
