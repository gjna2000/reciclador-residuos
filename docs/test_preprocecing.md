En este documento se registran las pruebas de preprocesamiento debido a que se considero que las capturas de pantalla no son adecuadas por la longitud de la salida por consola.

# Salida prueba 1
(cuda_env) Repo$ python -m benchmarks.preprocessing "tests/images/test2/" --runs 3 --resize 224 --jpeg-quality 85
Cargando pipeline en GPU: NVIDIA GeForce GTX 1650 Ti
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|█████████████████████████████████████████████████████████████████████████████████████████████████| 398/398 [00:00<00:00, 8177.35it/s]
[transformers] `torch_dtype` is deprecated! Use `dtype` instead!
Loading weights: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████| 200/200 [00:00<00:00, 280.23it/s]
Imágenes: 25 | repeticiones: 3 | preprocesado: resize=224, JPEG=85

[1/25] babana_coffee_sachet_1.jpg
  original: Biological (98.8%) | bote: verde | Los residuos orgánicos aprovechables pueden convertirse en abono.
    Pipeline: 391.38 ms promedio (±112.24)
  preprocesada: Biological (99.7%) | bote: verde | Los residuos orgánicos aprovechables pueden convertirse en abono.
    Pipeline: 59.96 ms promedio (±1.10); preprocesado: 756.80 ms

[2/25] babana_coffee_sachet_2.jpg
  original: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 173.68 ms promedio (±43.66)
  preprocesada: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 25.67 ms promedio (±1.75); preprocesado: 77.37 ms

[3/25] bag.jpg
  original: Clothes (96.9%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 74.32 ms promedio (±5.33)
  preprocesada: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 26.05 ms promedio (±3.78); preprocesado: 14.72 ms

[4/25] banana_cloth.jpg
  original: Clothes (97.8%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 266.07 ms promedio (±43.42)
  preprocesada: Clothes (42.8%) | bote: — | El sistema no tiene suficiente confianza en el resultado. Toma otra fotografía con mejor iluminación.
    Pipeline: 54.68 ms promedio (±2.08); preprocesado: 81.65 ms

[5/25] bed_with_items.jpg
  original: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 77.64 ms promedio (±8.27)
  preprocesada: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 25.97 ms promedio (±1.47); preprocesado: 41.50 ms

[6/25] bed_with_items_yoshi.jpg
  original: Paper (81.2%) | bote: blanco | Deposita el papel limpio y seco.
    Pipeline: 198.19 ms promedio (±3.42)
  preprocesada: Battery (62.1%) | bote: punto-especial | Lleva las baterías a un punto de recolección posconsumo.
    Pipeline: 68.42 ms promedio (±20.66); preprocesado: 43.94 ms

[7/25] bed_with_items_yoshi_hand.jpg
  original: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 79.20 ms promedio (±6.29)
  preprocesada: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 26.48 ms promedio (±1.78); preprocesado: 42.66 ms

[8/25] blurry.jpg
  original: Paper (99.7%) | bote: blanco | Deposita el papel limpio y seco.
    Pipeline: 68.84 ms promedio (±1.91)
  preprocesada: Paper (99.7%) | bote: blanco | Deposita el papel limpio y seco.
    Pipeline: 56.27 ms promedio (±1.34); preprocesado: 11.55 ms

[9/25] brocke_pastic_mechanism.jpg
  original: Cardboard (32.5%) | bote: — | El sistema no tiene suficiente confianza en el resultado. Toma otra fotografía con mejor iluminación.
    Pipeline: 68.31 ms promedio (±1.83)
  preprocesada: Cardboard (98.6%) | bote: blanco | Pliega el cartón para facilitar su almacenamiento.
    Pipeline: 58.67 ms promedio (±4.29); preprocesado: 6.42 ms

[10/25] cardboard_scrap.jpg
  original: Clothes (99.8%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 260.24 ms promedio (±22.26)
  preprocesada: Clothes (99.2%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 64.12 ms promedio (±18.74); preprocesado: 83.38 ms

[11/25] chair_pants.jpg
  original: Clothes (99.7%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 152.94 ms promedio (±27.18)
  preprocesada: Clothes (40.8%) | bote: — | El sistema no tiene suficiente confianza en el resultado. Toma otra fotografía con mejor iluminación.
    Pipeline: 53.68 ms promedio (±1.78); preprocesado: 45.91 ms

[12/25] desserts.jpg
  original: Plastic (82.6%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 273.67 ms promedio (±68.20)
  preprocesada: Plastic (52.1%) | bote: — | El sistema no tiene suficiente confianza en el resultado. Toma otra fotografía con mejor iluminación.
    Pipeline: 67.89 ms promedio (±9.09); preprocesado: 71.99 ms

[13/25] disassembled_motorcycle.jpg
  original: Clothes (85.6%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 180.26 ms promedio (±21.87)
  preprocesada: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 27.94 ms promedio (±1.77); preprocesado: 43.12 ms

[14/25] door.jpg
  original: Cardboard (98.4%) | bote: blanco | Pliega el cartón para facilitar su almacenamiento.
    Pipeline: 82.73 ms promedio (±21.46)
  preprocesada: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 28.78 ms promedio (±1.14); preprocesado: 11.09 ms

[15/25] exit_mf.jpeg
  original: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 85.27 ms promedio (±6.99)
  preprocesada: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 31.18 ms promedio (±2.78); preprocesado: 46.62 ms

[16/25] kitchen.jpg
  original: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 124.86 ms promedio (±20.30)
  preprocesada: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 38.44 ms promedio (±6.26); preprocesado: 73.58 ms

[17/25] laptop_bed.jpg
  original: Cardboard (96.9%) | bote: blanco | Pliega el cartón para facilitar su almacenamiento.
    Pipeline: 163.12 ms promedio (±25.32)
  preprocesada: Cardboard (97.3%) | bote: blanco | Pliega el cartón para facilitar su almacenamiento.
    Pipeline: 80.58 ms promedio (±20.06); preprocesado: 48.78 ms

[18/25] mirror.jpg
  original: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 45.98 ms promedio (±23.80)
  preprocesada: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 36.37 ms promedio (±19.09); preprocesado: 11.12 ms

[19/25] plastic_bag.jpg
  original: Clothes (99.8%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 246.19 ms promedio (±14.09)
  preprocesada: Clothes (99.1%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 71.79 ms promedio (±31.25); preprocesado: 72.70 ms

[20/25] plastic_bottle_1.jpg
  original: Plastic (99.7%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 192.77 ms promedio (±22.62)
  preprocesada: Plastic (99.7%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 55.40 ms promedio (±0.89); preprocesado: 70.57 ms

[21/25] plastic_bottle_2.jpg
  original: Plastic (99.7%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 220.11 ms promedio (±27.01)
  preprocesada: Plastic (99.7%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 66.30 ms promedio (±12.23); preprocesado: 75.57 ms

[22/25] plastic_bottle_3.jpg
  original: White-Glass (99.6%) | bote: blanco | Separa el vidrio aprovechable y evita mezclarlo con otros residuos.
    Pipeline: 180.89 ms promedio (±5.43)
  preprocesada: White-Glass (99.6%) | bote: blanco | Separa el vidrio aprovechable y evita mezclarlo con otros residuos.
    Pipeline: 55.47 ms promedio (±1.82); preprocesado: 72.46 ms

[23/25] plastic_cap_1.jpg
  original: Plastic (96.8%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 209.16 ms promedio (±9.93)
  preprocesada: Plastic (47.2%) | bote: — | El sistema no tiene suficiente confianza en el resultado. Toma otra fotografía con mejor iluminación.
    Pipeline: 63.74 ms promedio (±19.40); preprocesado: 71.47 ms

[24/25] plastic_cap_2.jpg
  original: Plastic (96.0%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 171.28 ms promedio (±1.64)
  preprocesada: Plastic (92.4%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 52.63 ms promedio (±0.46); preprocesado: 75.67 ms

[25/25] post-it_notes.jpg
  original: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 155.28 ms promedio (±38.72)
  preprocesada: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 50.66 ms promedio (±16.77); preprocesado: 43.66 ms

# Tabla comparativa

| Imagen | Original (ms) | Preproc. pipeline (ms) | Preproc. total (ms) | Diferencia (ms) | Resultado igual |
|---|---:|---:|---:|---:|:---:|
| babana_coffee_sachet_1.jpg | 391.38 | 59.96 | 816.75 | +425.37 | No |
| babana_coffee_sachet_2.jpg | 173.68 | 25.67 | 103.05 | -70.64 | Sí |
| bag.jpg | 74.32 | 26.05 | 40.77 | -33.55 | No |
| banana_cloth.jpg | 266.07 | 54.68 | 136.33 | -129.74 | No |
| bed_with_items.jpg | 77.64 | 25.97 | 67.47 | -10.17 | Sí |
| bed_with_items_yoshi.jpg | 198.19 | 68.42 | 112.36 | -85.82 | No |
| bed_with_items_yoshi_hand.jpg | 79.20 | 26.48 | 69.14 | -10.06 | Sí |
| blurry.jpg | 68.84 | 56.27 | 67.82 | -1.02 | Sí |
| brocke_pastic_mechanism.jpg | 68.31 | 58.67 | 65.10 | -3.21 | No |
| cardboard_scrap.jpg | 260.24 | 64.12 | 147.51 | -112.73 | No |
| chair_pants.jpg | 152.94 | 53.68 | 99.59 | -53.35 | No |
| desserts.jpg | 273.67 | 67.89 | 139.88 | -133.79 | No |
| disassembled_motorcycle.jpg | 180.26 | 27.94 | 71.06 | -109.20 | No |
| door.jpg | 82.73 | 28.78 | 39.87 | -42.86 | No |
| exit_mf.jpeg | 85.27 | 31.18 | 77.80 | -7.47 | Sí |
| kitchen.jpg | 124.86 | 38.44 | 112.01 | -12.84 | Sí |
| laptop_bed.jpg | 163.12 | 80.58 | 129.36 | -33.76 | No |
| mirror.jpg | 45.98 | 36.37 | 47.49 | +1.51 | Sí |
| plastic_bag.jpg | 246.19 | 71.79 | 144.50 | -101.69 | No |
| plastic_bottle_1.jpg | 192.77 | 55.40 | 125.97 | -66.80 | Sí |
| plastic_bottle_2.jpg | 220.11 | 66.30 | 141.87 | -78.24 | Sí |
| plastic_bottle_3.jpg | 180.88 | 55.47 | 127.93 | -52.95 | Sí |
| plastic_cap_1.jpg | 209.16 | 63.74 | 135.21 | -73.95 | No |
| plastic_cap_2.jpg | 171.28 | 52.63 | 128.30 | -42.98 | No |
| post-it_notes.jpg | 155.28 | 50.66 | 94.31 | -60.97 | Sí |
| **PROMEDIO** | **165.69** | **49.89** | **129.66** | **-36.04** | **11/25** |

# Conclusiones
El preprocesamiento con recorte a 224 × 224 y compresión JPEG redujo el tiempo de inferencia, pero al incluir el costo de transformar la imagen fue más lento en promedio. Además, cambió varias predicciones y coincidió con el resultado original en solo 11 de 25 imágenes, las predicciones tambien empeoraron en su mayoria en comparacion con la version sin preprocesar.

# Prueba salida 2

(cuda_env) Repo$ python -m benchmarks.preprocessing_v2 "tests/images/test2/" --runs 5 --warmup 2
GPU: NVIDIA GeForce GTX 1650 Ti
Preprocesado v2: ajustar sin recortar + márgenes gris neutro; sin recodificación JPEG
Imágenes: 25 | calentamiento: 2 | repeticiones: 5
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|█████████████████████████████████████████████████████████████████████████████████████████████████| 398/398 [00:00<00:00, 7490.33it/s]
[transformers] `torch_dtype` is deprecated! Use `dtype` instead!
Loading weights: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████| 200/200 [00:00<00:00, 293.59it/s]

[1/25] babana_coffee_sachet_1.jpg
  original: Biological (98.8%) | bote: verde | Los residuos orgánicos aprovechables pueden convertirse en abono.
    Pipeline: 446.48 ms ± 51.07 ms
  letterbox: Shoes (99.4%) | bote: punto-especial | Si están en buen estado, considera reutilizarlos o donarlos.
    Pipeline: 74.79 ms ± 19.72 ms

[2/25] babana_coffee_sachet_2.jpg
  letterbox: Biological (99.5%) | bote: verde | Los residuos orgánicos aprovechables pueden convertirse en abono.
    Pipeline: 64.97 ms ± 9.79 ms
  original: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 185.49 ms ± 31.09 ms

[3/25] bag.jpg
  original: Clothes (96.9%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 99.02 ms ± 12.68 ms
  letterbox: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 35.01 ms ± 4.24 ms

[4/25] banana_cloth.jpg
  letterbox: Shoes (50.2%) | bote: — | El sistema no tiene suficiente confianza en el resultado. Toma otra fotografía con mejor iluminación.
    Pipeline: 63.77 ms ± 3.79 ms
  original: Clothes (97.8%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 280.34 ms ± 55.93 ms

[5/25] bed_with_items.jpg
  original: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 86.02 ms ± 11.12 ms
  letterbox: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 28.23 ms ± 1.72 ms

[6/25] bed_with_items_yoshi.jpg
  letterbox: Paper (84.6%) | bote: blanco | Deposita el papel limpio y seco.
    Pipeline: 60.21 ms ± 14.35 ms
  original: Paper (81.2%) | bote: blanco | Deposita el papel limpio y seco.
    Pipeline: 164.19 ms ± 1.70 ms

[7/25] bed_with_items_yoshi_hand.jpg
  original: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 74.91 ms ± 3.52 ms
  letterbox: Battery (77.3%) | bote: punto-especial | Lleva las baterías a un punto de recolección posconsumo.
    Pipeline: 65.59 ms ± 19.84 ms

[8/25] blurry.jpg
  letterbox: Paper (99.5%) | bote: blanco | Deposita el papel limpio y seco.
    Pipeline: 54.70 ms ± 2.60 ms
  original: Paper (99.7%) | bote: blanco | Deposita el papel limpio y seco.
    Pipeline: 64.80 ms ± 0.81 ms

[9/25] brocke_pastic_mechanism.jpg
  original: Cardboard (32.5%) | bote: — | El sistema no tiene suficiente confianza en el resultado. Toma otra fotografía con mejor iluminación.
    Pipeline: 64.41 ms ± 1.33 ms
  letterbox: Biological (43.5%) | bote: — | El sistema no tiene suficiente confianza en el resultado. Toma otra fotografía con mejor iluminación.
    Pipeline: 52.92 ms ± 1.14 ms

[10/25] cardboard_scrap.jpg
  letterbox: Clothes (98.7%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 53.12 ms ± 0.96 ms
  original: Clothes (99.8%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 227.84 ms ± 9.34 ms

[11/25] chair_pants.jpg
  original: Clothes (99.7%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 156.80 ms ± 9.61 ms
  letterbox: Clothes (81.4%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 58.73 ms ± 3.22 ms

[12/25] desserts.jpg
  letterbox: Metal (52.5%) | bote: — | El sistema no tiene suficiente confianza en el resultado. Toma otra fotografía con mejor iluminación.
    Pipeline: 58.10 ms ± 3.35 ms
  original: Plastic (82.6%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 205.06 ms ± 19.70 ms

[13/25] disassembled_motorcycle.jpg
  original: Clothes (85.6%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 191.99 ms ± 10.88 ms
  letterbox: Shoes (83.6%) | bote: punto-especial | Si están en buen estado, considera reutilizarlos o donarlos.
    Pipeline: 56.07 ms ± 1.96 ms

[14/25] door.jpg
  letterbox: Cardboard (98.3%) | bote: blanco | Pliega el cartón para facilitar su almacenamiento.
    Pipeline: 56.56 ms ± 4.18 ms
  original: Cardboard (98.4%) | bote: blanco | Pliega el cartón para facilitar su almacenamiento.
    Pipeline: 65.58 ms ± 1.96 ms

[15/25] exit_mf.jpeg
  original: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 91.58 ms ± 25.25 ms
  letterbox: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 25.28 ms ± 0.97 ms

[16/25] kitchen.jpg
  letterbox: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 31.01 ms ± 10.52 ms
  original: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 124.12 ms ± 12.81 ms

[17/25] laptop_bed.jpg
  original: Cardboard (96.9%) | bote: blanco | Pliega el cartón para facilitar su almacenamiento.
    Pipeline: 247.73 ms ± 16.95 ms
  letterbox: Cardboard (90.9%) | bote: blanco | Pliega el cartón para facilitar su almacenamiento.
    Pipeline: 56.35 ms ± 5.12 ms

[18/25] mirror.jpg
  letterbox: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 24.85 ms ± 1.17 ms
  original: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 33.36 ms ± 0.49 ms

[19/25] plastic_bag.jpg
  original: Clothes (99.8%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 252.20 ms ± 20.24 ms
  letterbox: Clothes (99.8%) | bote: punto-especial | Si está en buen estado, considera reutilizarlo o donarlo.
    Pipeline: 56.58 ms ± 7.16 ms

[20/25] plastic_bottle_1.jpg
  letterbox: Plastic (99.7%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 53.01 ms ± 1.61 ms
  original: Plastic (99.7%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 165.95 ms ± 6.50 ms

[21/25] plastic_bottle_2.jpg
  original: Plastic (99.7%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 222.08 ms ± 20.13 ms
  letterbox: Plastic (99.7%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 78.59 ms ± 21.52 ms

[22/25] plastic_bottle_3.jpg
  letterbox: White-Glass (99.5%) | bote: blanco | Separa el vidrio aprovechable y evita mezclarlo con otros residuos.
    Pipeline: 55.20 ms ± 0.96 ms
  original: White-Glass (99.6%) | bote: blanco | Separa el vidrio aprovechable y evita mezclarlo con otros residuos.
    Pipeline: 189.20 ms ± 8.19 ms

[23/25] plastic_cap_1.jpg
  original: Plastic (96.8%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 232.18 ms ± 16.94 ms
  letterbox: Plastic (79.3%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 55.42 ms ± 1.99 ms

[24/25] plastic_cap_2.jpg
  letterbox: Cardboard (69.1%) | bote: blanco | Pliega el cartón para facilitar su almacenamiento.
    Pipeline: 52.93 ms ± 0.54 ms
  original: Plastic (96.0%) | bote: blanco | Limpia el envase antes de depositarlo.
    Pipeline: 169.32 ms ± 18.92 ms

[25/25] post-it_notes.jpg
  original: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 129.32 ms ± 11.35 ms
  letterbox: No detectado como residuo | bote: — | La imagen no parece contener un residuo o no es un objeto válido. Intenta con otra fotografía.
    Pipeline: 36.20 ms ± 17.47 ms

# Tabla comparativa

| Imagen | Original (ms) | Letterbox (ms) | Transform. (ms) | Total alt. (ms) | Diferencia (ms) | Aciertos O/L |
|---|---:|---:|---:|---:|---:|---|
| babana_coffee_sachet_1.jpg | 446.48 | 74.79 | 93.11 | 167.89 | -278.59 | sin etiqueta |
| babana_coffee_sachet_2.jpg | 185.49 | 64.97 | 90.05 | 155.02 | -30.47 | sin etiqueta |
| bag.jpg | 99.02 | 35.01 | 18.44 | 53.45 | -45.56 | sin etiqueta |
| banana_cloth.jpg | 280.34 | 63.77 | 95.52 | 159.28 | -121.06 | sin etiqueta |
| bed_with_items.jpg | 86.02 | 28.23 | 68.22 | 96.45 | +10.43 | sin etiqueta |
| bed_with_items_yoshi.jpg | 164.19 | 60.21 | 67.44 | 127.66 | -36.53 | sin etiqueta |
| bed_with_items_yoshi_hand.jpg | 74.91 | 65.59 | 67.82 | 133.41 | +58.51 | sin etiqueta |
| blurry.jpg | 64.80 | 54.70 | 10.74 | 65.44 | +0.64 | sin etiqueta |
| brocke_pastic_mechanism.jpg | 64.41 | 52.92 | 8.58 | 61.51 | -2.91 | sin etiqueta |
| cardboard_scrap.jpg | 227.84 | 53.12 | 90.55 | 143.67 | -84.17 | sin etiqueta |
| chair_pants.jpg | 156.79 | 58.73 | 69.84 | 128.57 | -28.22 | sin etiqueta |
| desserts.jpg | 205.06 | 58.10 | 87.76 | 145.86 | -59.20 | sin etiqueta |
| disassembled_motorcycle.jpg | 191.99 | 56.07 | 62.14 | 118.21 | -73.78 | sin etiqueta |
| door.jpg | 65.58 | 56.56 | 11.41 | 67.97 | +2.39 | sin etiqueta |
| exit_mf.jpeg | 91.58 | 25.28 | 60.72 | 86.00 | -5.59 | sin etiqueta |
| kitchen.jpg | 124.12 | 31.01 | 89.66 | 120.67 | -3.45 | sin etiqueta |
| laptop_bed.jpg | 247.73 | 56.35 | 70.51 | 126.86 | -120.87 | sin etiqueta |
| mirror.jpg | 33.36 | 24.85 | 10.37 | 35.22 | +1.86 | sin etiqueta |
| plastic_bag.jpg | 252.19 | 56.58 | 91.62 | 148.20 | -104.00 | sin etiqueta |
| plastic_bottle_1.jpg | 165.95 | 53.02 | 90.97 | 143.98 | -21.97 | sin etiqueta |
| plastic_bottle_2.jpg | 222.08 | 78.59 | 95.72 | 174.31 | -47.77 | sin etiqueta |
| plastic_bottle_3.jpg | 189.20 | 55.20 | 90.12 | 145.31 | -43.88 | sin etiqueta |
| plastic_cap_1.jpg | 232.18 | 55.42 | 92.28 | 147.69 | -84.48 | sin etiqueta |
| plastic_cap_2.jpg | 169.32 | 52.93 | 96.74 | 149.67 | -19.65 | sin etiqueta |
| post-it_notes.jpg | 129.32 | 36.20 | 68.83 | 105.03 | -24.29 | sin etiqueta |
| **PROMEDIO** | **166.80** | **52.33** | **67.97** | **120.29** | **-46.50** | — |

# Concluciones

El método letterbox, que conserva la imagen completa y añade márgenes, también fue más rápido en el promedio registrado, pero cambió algunas clasificaciones sin mejorar consistentemente los aciertos. Según la revisión visual, el resultado original siguió siendo más confiable.