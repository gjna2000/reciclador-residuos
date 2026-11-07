"""Run the YOLO-assisted recycling pipeline on one image and report each crop."""
import argparse
import csv
import re
import statistics
import sys
import time
from pathlib import Path

import torch
from PIL import Image, ImageOps

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import RecyclingPipeline


def safe_name(text):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("._") or "objeto"


def sync(device):
    if str(device).startswith("cuda"):
        torch.cuda.synchronize(torch.device(device))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Ruta a una sola imagen")
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--runs", type=int, default=3, help="Repeticiones medidas")
    parser.add_argument("--warmup", type=int, default=1, help="Ejecuciones iniciales descartadas")
    parser.add_argument("--crops-dir", type=Path, default=Path("benchmarks/yolo_single_crops"),
                        help="Carpeta para guardar recortes detectados")
    parser.add_argument("--csv", type=Path, default=Path("benchmarks/yolo_single_result.csv"),
                        help="Archivo CSV de resultados")
    args = parser.parse_args()

    if args.runs < 1 or args.warmup < 0:
        parser.error("--runs debe ser positivo y --warmup no puede ser negativo")
    if not args.image.is_file():
        parser.error(f"No existe la imagen: {args.image}")
    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("Se pidió CUDA, pero PyTorch no detecta una GPU disponible")

    with Image.open(args.image) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
    print(f"Imagen: {args.image.name} ({image.width} × {image.height})")
    print(f"Cargando pipeline completo en {args.device.upper()} (Gate + YOLO + clasificador)...")
    pipeline = RecyclingPipeline(device=args.device, use_detector=True)

    wall_samples = []
    component_samples = {}
    final = None
    for iteration in range(args.warmup + args.runs):
        sync(args.device)
        started = time.perf_counter()
        result = pipeline.analyze(image, detect=True)
        sync(args.device)
        wall_ms = (time.perf_counter() - started) * 1000
        final = result
        if iteration >= args.warmup:
            wall_samples.append(wall_ms)
            for name, value in result.timings_ms.items():
                component_samples.setdefault(name, []).append(float(value))

    wall_mean = statistics.mean(wall_samples)
    wall_sd = statistics.stdev(wall_samples) if len(wall_samples) > 1 else 0.0
    print(f"\nEstado del pipeline: {final.status}")
    print(f"Resultado global/fallback: ", end="")
    if final.top:
        top = final.top[0]
        print(f"{top.label} ({top.score:.1%})")
    elif final.status == "no_es_residuo":
        print("No detectado como residuo")
    else:
        print("sin clasificación")
    if final.bin:
        print(f"Bote: {final.bin} | {final.tip}")

    rows = []
    objects = final.objects or []
    if objects:
        print(f"\nObjetos YOLO clasificados: {len(objects)}")
        for number, obj in enumerate(objects, start=1):
            label = safe_name(obj.detection_label)
            x1, y1, x2, y2 = obj.bbox
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(image.width, x2), min(image.height, y2)
            crop_path = ""
            if x2 > x1 and y2 > y1:
                args.crops_dir.mkdir(parents=True, exist_ok=True)
                crop_file = args.crops_dir / f"{safe_name(args.image.stem)}_objeto_{number:02d}_{label}.jpg"
                image.crop((x1, y1, x2, y2)).save(crop_file, quality=95)
                crop_path = str(crop_file)

            pred = obj.classification
            class_name = pred.label if pred else "Sin clasificación"
            class_score = float(pred.score) if pred else ""
            print(f"\n  Objeto {number}")
            print(f"    YOLO: {obj.detection_label} ({obj.detection_score:.1%})")
            print(f"    Caja: ({x1}, {y1}, {x2}, {y2})")
            print(f"    Clasificación: {class_name}"
                  + (f" ({class_score:.1%})" if pred else ""))
            print(f"    Bote: {obj.recycling_bin or '—'}")
            print(f"    Consejo: {obj.recycling_tip or 'Sin recomendación (confianza insuficiente).'}")
            print(f"    Recorte guardado: {crop_path or 'no se pudo guardar'}")
            rows.append({
                "imagen": str(args.image), "tipo": "objeto_yolo", "objeto_numero": number,
                "yolo_label": obj.detection_label, "yolo_confianza": obj.detection_score,
                "bbox_xyxy": f"{x1},{y1},{x2},{y2}", "clasificacion": class_name,
                "clasificacion_confianza": class_score, "bote": obj.recycling_bin or "",
                "consejo": obj.recycling_tip, "recorte": crop_path,
                "estado_pipeline": final.status,
            })
    else:
        print("\nYOLO no produjo recortes válidos; el pipeline muestra su fallback sobre la imagen completa.")
        rows.append({
            "imagen": str(args.image), "tipo": "fallback_imagen_completa", "objeto_numero": "",
            "yolo_label": "", "yolo_confianza": "", "bbox_xyxy": "",
            "clasificacion": final.top[0].label if final.top else "",
            "clasificacion_confianza": final.top[0].score if final.top else "",
            "bote": final.bin or "", "consejo": final.tip, "recorte": "",
            "estado_pipeline": final.status,
        })

    print(f"\nTiempo total promedio: {wall_mean:.2f} ms ± {wall_sd:.2f} ms")
    for name, values in component_samples.items():
        print(f"  {name}: {statistics.mean(values):.2f} ms promedio")

    # Include the same full-pipeline timings in every CSV row for easy review.
    for row in rows:
        row["tiempo_total_promedio_ms"] = round(wall_mean, 3)
        row["tiempo_total_desviacion_ms"] = round(wall_sd, 3)
        for name, values in component_samples.items():
            row[f"{name}_promedio_ms"] = round(statistics.mean(values), 3)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    columns = list(dict.fromkeys(key for row in rows for key in row))
    with args.csv.open("w", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nResultados CSV: {args.csv}")
    if objects:
        print(f"Recortes: {args.crops_dir}")


if __name__ == "__main__":
    main()
