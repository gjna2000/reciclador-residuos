"""Compare the full GPU pipeline on original images and aspect-preserving letterboxed images."""
import argparse
import csv
import statistics
import time
from pathlib import Path

import torch
from PIL import Image, ImageOps

from src.pipeline import RecyclingPipeline

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def load_image(path):
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).convert("RGB")


def letterbox(image, size, background=(127, 127, 127)):
    """Fit the whole image in a square without cropping or lossy re-encoding."""
    fitted = ImageOps.contain(image, (size, size), method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), background)
    canvas.paste(fitted, ((size - fitted.width) // 2, (size - fitted.height) // 2))
    return canvas


def sync_cuda():
    torch.cuda.synchronize()


def result_fields(result):
    if result.status == "no_es_residuo":
        label, confidence = "no_es_residuo", ""
        display = "No detectado como residuo"
    elif result.top:
        label = result.top[0].label.strip().lower()
        confidence = result.top[0].score
        display = f"{result.top[0].label} ({confidence:.1%})"
    else:
        label, confidence, display = "incierto", "", "Sin clasificación"
    return {"status": result.status, "label": label, "confidence": confidence,
            "display": display, "bin": result.bin or "—", "tip": result.tip}


def read_labels(path):
    if path is None:
        return {}
    with path.open(newline="", encoding="utf-8-sig") as source:
        return {row["imagen"]: row["etiqueta"].strip().lower()
                for row in csv.DictReader(source)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image_dir", type=Path, help="Carpeta de imágenes")
    parser.add_argument("--runs", type=int, default=5, help="Repeticiones medidas por variante")
    parser.add_argument("--warmup", type=int, default=2, help="Calentamientos descartados por variante")
    parser.add_argument("--size", type=int, default=224, help="Lado del cuadrado con relleno (por defecto 224)")
    parser.add_argument("--labels", type=Path, help="CSV opcional con columnas imagen,etiqueta para medir aciertos")
    parser.add_argument("--csv", type=Path, default=Path("benchmarks/preprocessing_v2_results.csv"))
    args = parser.parse_args()
    if not torch.cuda.is_available():
        parser.error("CUDA no está disponible; esta prueba utiliza exclusivamente la GPU.")
    if args.runs < 1 or args.warmup < 0 or args.size < 1:
        parser.error("runs y size deben ser positivos; warmup no puede ser negativo")
    if not args.image_dir.is_dir():
        parser.error(f"No existe la carpeta: {args.image_dir}")
    paths = sorted(p for p in args.image_dir.iterdir() if p.suffix.lower() in EXTENSIONS)
    if not paths:
        parser.error(f"No se encontraron imágenes en {args.image_dir}")
    truth = read_labels(args.labels)

    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print("Preprocesado v2: ajustar sin recortar + márgenes gris neutro; sin recodificación JPEG")
    print(f"Imágenes: {len(paths)} | calentamiento: {args.warmup} | repeticiones: {args.runs}")
    pipeline = RecyclingPipeline(device="cuda")
    rows = []

    for index, path in enumerate(paths, start=1):
        original = load_image(path)
        started = time.perf_counter()
        prepared = letterbox(original, args.size)
        transform_ms = (time.perf_counter() - started) * 1000
        variants = [("original", original), ("letterbox", prepared)]
        # Alternate which variant runs first to reduce systematic GPU warm-state bias.
        if index % 2 == 0:
            variants.reverse()
        outcomes = {}
        print(f"\n[{index}/{len(paths)}] {path.name}")
        for name, image in variants:
            for _ in range(args.warmup):
                pipeline.analyze(image)
                sync_cuda()
            samples, result = [], None
            for _ in range(args.runs):
                sync_cuda()
                tick = time.perf_counter()
                result = pipeline.analyze(image)
                sync_cuda()
                samples.append((time.perf_counter() - tick) * 1000)
            fields = result_fields(result)
            fields.update(mean_ms=statistics.mean(samples),
                          sd_ms=statistics.stdev(samples) if len(samples) > 1 else 0.0)
            outcomes[name] = fields
            print(f"  {name}: {fields['display']} | bote: {fields['bin']} | {fields['tip']}")
            print(f"    Pipeline: {fields['mean_ms']:.2f} ms ± {fields['sd_ms']:.2f} ms")

        base, alt = outcomes["original"], outcomes["letterbox"]
        total_alt = alt["mean_ms"] + transform_ms
        truth_label = truth.get(path.name, "")
        rows.append({
            "imagen": path.name, "etiqueta_real": truth_label,
            "clase_original": base["label"], "confianza_original": base["confidence"],
            "bote_original": base["bin"], "tiempo_original_ms": round(base["mean_ms"], 3),
            "clase_letterbox": alt["label"], "confianza_letterbox": alt["confidence"],
            "bote_letterbox": alt["bin"], "tiempo_pipeline_letterbox_ms": round(alt["mean_ms"], 3),
            "tiempo_transformacion_ms": round(transform_ms, 3),
            "tiempo_total_letterbox_ms": round(total_alt, 3),
            "diferencia_total_menos_original_ms": round(total_alt - base["mean_ms"], 3),
            "acierto_original": base["label"] == truth_label if truth_label else "",
            "acierto_letterbox": alt["label"] == truth_label if truth_label else "",
        })

    print("\nRESUMEN POR IMAGEN (ms; diferencia = letterbox total − original)")
    print(f"{'Imagen':<32} {'Original':>12} {'Letterbox':>12} {'Transform.':>12} {'Total alt.':>12} {'Diferencia':>12} {'Aciertos O/L':>14}")
    print("-" * 116)
    for row in rows:
        hits = f"{row['acierto_original']}/{row['acierto_letterbox']}" if row["etiqueta_real"] else "sin etiqueta"
        print(f"{row['imagen'][:31]:<32} {row['tiempo_original_ms']:>12.2f} {row['tiempo_pipeline_letterbox_ms']:>12.2f} {row['tiempo_transformacion_ms']:>12.2f} {row['tiempo_total_letterbox_ms']:>12.2f} {row['diferencia_total_menos_original_ms']:>+12.2f} {hits:>14}")
    print("-" * 116)
    avg_original = statistics.mean(row["tiempo_original_ms"] for row in rows)
    avg_pipeline_alt = statistics.mean(row["tiempo_pipeline_letterbox_ms"] for row in rows)
    avg_transform = statistics.mean(row["tiempo_transformacion_ms"] for row in rows)
    avg_total_alt = statistics.mean(row["tiempo_total_letterbox_ms"] for row in rows)
    print(f"{'PROMEDIO':<32} {avg_original:>12.2f} {avg_pipeline_alt:>12.2f} {avg_transform:>12.2f} {avg_total_alt:>12.2f} {avg_total_alt - avg_original:>+12.2f}")
    if truth:
        labeled = [row for row in rows if row["etiqueta_real"]]
        if labeled:
            hits_original = sum(row["acierto_original"] is True for row in labeled)
            hits_alt = sum(row["acierto_letterbox"] is True for row in labeled)
            print(f"Aciertos con etiquetas proporcionadas: original {hits_original}/{len(labeled)}; letterbox {hits_alt}/{len(labeled)}")
    else:
        equal = sum(row["clase_original"] == row["clase_letterbox"] for row in rows)
        print(f"Predicción igual en ambas variantes: {equal}/{len(rows)}. Sin etiquetas reales no se puede calcular exactitud automáticamente.")

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Resultados guardados en: {args.csv}")


if __name__ == "__main__":
    main()
