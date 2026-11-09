"""Benchmark the complete recycling pipeline on original and preprocessed images."""
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


def pretransform(image, size, quality):
    """Optionally resize/crop and JPEG-recode an image before the pipeline."""
    if size:
        image = ImageOps.fit(image, (size, size), method=Image.Resampling.LANCZOS)
    if quality < 100:
        from io import BytesIO
        stream = BytesIO()
        image.save(stream, format="JPEG", quality=quality)
        stream.seek(0)
        with Image.open(stream) as encoded:
            image = encoded.convert("RGB")
    return image


def sync_cuda():
    torch.cuda.synchronize()


def format_result(result):
    if result.status == "no_es_residuo":
        classification = "No detectado como residuo"
    elif result.top:
        classification = f"{result.top[0].label} ({result.top[0].score:.1%})"
    else:
        classification = "Sin clasificación"
    return classification, result.bin or "—", result.tip


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image_dir", type=Path, help="Carpeta con imágenes de prueba")
    parser.add_argument("--runs", type=int, default=3, help="Repeticiones cronometradas por variante")
    parser.add_argument("--warmup", type=int, default=1, help="Ejecuciones de calentamiento por variante")
    parser.add_argument("--resize", type=int, default=0, help="Redimensiona/recorta a NxN antes del pipeline (0=sin cambio)")
    parser.add_argument("--jpeg-quality", type=int, default=100, help="Calidad JPEG (100=no recodificar)")
    parser.add_argument("--csv", type=Path, default=Path("benchmarks/preprocessing_results.csv"))
    args = parser.parse_args()
    if not torch.cuda.is_available():
        parser.error("CUDA no está disponible; este benchmark trabaja exclusivamente con la GPU.")
    if args.runs < 1 or args.warmup < 0:
        parser.error("runs debe ser positivo y warmup no puede ser negativo")
    if not 1 <= args.jpeg_quality <= 100:
        parser.error("jpeg-quality debe estar entre 1 y 100")
    if not args.image_dir.is_dir():
        parser.error(f"No existe la carpeta: {args.image_dir}")
    paths = sorted(p for p in args.image_dir.iterdir() if p.suffix.lower() in EXTENSIONS)
    if not paths:
        parser.error(f"No se encontraron imágenes en {args.image_dir}")

    print(f"Cargando pipeline en GPU: {torch.cuda.get_device_name(0)}")
    pipeline = RecyclingPipeline(device="cuda")
    print(f"Imágenes: {len(paths)} | repeticiones: {args.runs} | preprocesado: resize={args.resize or 'sin cambio'}, JPEG={args.jpeg_quality}")
    rows = []

    for index, path in enumerate(paths, start=1):
        original = load_image(path)
        transform_start = time.perf_counter()
        transformed = pretransform(original, args.resize, args.jpeg_quality)
        transform_ms = (time.perf_counter() - transform_start) * 1000
        outcomes = {}
        print(f"\n[{index}/{len(paths)}] {path.name}")
        for variant, image in (("original", original), ("preprocesada", transformed)):
            for _ in range(args.warmup):
                pipeline.analyze(image)
                sync_cuda()
            elapsed = []
            result = None
            for _ in range(args.runs):
                sync_cuda()
                started = time.perf_counter()
                result = pipeline.analyze(image)
                sync_cuda()
                elapsed.append((time.perf_counter() - started) * 1000)
            mean = statistics.mean(elapsed)
            sd = statistics.stdev(elapsed) if len(elapsed) > 1 else 0.0
            total = mean + (transform_ms if variant == "preprocesada" else 0.0)
            classification, bin_name, tip = format_result(result)
            outcomes[variant] = {"mean": mean, "sd": sd, "total": total,
                                 "classification": classification, "bin": bin_name, "tip": tip,
                                 "status": result.status}
            print(f"  {variant}: {classification} | bote: {bin_name} | {tip}")
            print(f"    Pipeline: {mean:.2f} ms promedio (±{sd:.2f}); preprocesado: {transform_ms:.2f} ms" if variant == "preprocesada" else f"    Pipeline: {mean:.2f} ms promedio (±{sd:.2f})")

        delta = outcomes["preprocesada"]["total"] - outcomes["original"]["mean"]
        rows.append({
            "imagen": path.name,
            "clasificacion_original": outcomes["original"]["classification"],
            "bote_original": outcomes["original"]["bin"],
            "pipeline_original_ms": round(outcomes["original"]["mean"], 3),
            "clasificacion_preprocesada": outcomes["preprocesada"]["classification"],
            "bote_preprocesada": outcomes["preprocesada"]["bin"],
            "pipeline_preprocesada_ms": round(outcomes["preprocesada"]["mean"], 3),
            "preprocesado_ms": round(transform_ms, 3),
            "preprocesada_total_ms": round(outcomes["preprocesada"]["total"], 3),
            "diferencia_ms_preprocesada_menos_original": round(delta, 3),
            "cambio_status": outcomes["original"]["status"] != outcomes["preprocesada"]["status"],
            "cambio_clasificacion": outcomes["original"]["classification"] != outcomes["preprocesada"]["classification"],
            "cambio_bote": outcomes["original"]["bin"] != outcomes["preprocesada"]["bin"],
        })

    print("\nCOMPARACIÓN POR IMAGEN (ms)")
    print(f"{'Imagen':<32} {'Original':>12} {'Preproc. pipeline':>18} {'Preproc. total':>16} {'Diferencia':>13} {'Resultado igual':>16}")
    print("-" * 112)
    for row in rows:
        same = not (row["cambio_status"] or row["cambio_clasificacion"] or row["cambio_bote"])
        print(f"{row['imagen'][:31]:<32} {row['pipeline_original_ms']:>12.2f} {row['pipeline_preprocesada_ms']:>18.2f} {row['preprocesada_total_ms']:>16.2f} {row['diferencia_ms_preprocesada_menos_original']:>+13.2f} {('Sí' if same else 'No'):>16}")
    avg_original = statistics.mean(r["pipeline_original_ms"] for r in rows)
    avg_preproc = statistics.mean(r["pipeline_preprocesada_ms"] for r in rows)
    avg_total = statistics.mean(r["preprocesada_total_ms"] for r in rows)
    avg_delta = avg_total - avg_original
    same_count = sum(not (r["cambio_status"] or r["cambio_clasificacion"] or r["cambio_bote"]) for r in rows)
    print("-" * 112)
    print(f"{'PROMEDIO':<32} {avg_original:>12.2f} {avg_preproc:>18.2f} {avg_total:>16.2f} {avg_delta:>+13.2f} {same_count}/{len(rows):>14}")

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nResultados detallados guardados en: {args.csv}")


if __name__ == "__main__":
    main()
