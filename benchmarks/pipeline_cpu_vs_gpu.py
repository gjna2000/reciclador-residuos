"""Compare end-to-end recycling-pipeline latency on CPU and CUDA."""

import argparse
import gc
import statistics
import time
from collections import defaultdict

import torch
from PIL import Image

from src.device import get_device, gpu_info, sync


def _result_label(result):
    """Return the leading predicted label, when the pipeline has one."""
    predictions = getattr(result, "top", None) or []
    if not predictions:
        return None
    return getattr(predictions[0], "label", str(predictions[0]))


def _measure_pipeline(pipeline, image, runs, warmup):
    samples = defaultdict(list)
    outcomes = []

    for iteration in range(warmup + runs):
        # CUDA launches are asynchronous. Synchronize around the wall timer so
        # it includes work queued by analyze(), as well as host-side work.
        sync()
        started = time.perf_counter()
        result = pipeline.analyze(image)
        sync()
        wall_ms = (time.perf_counter() - started) * 1000

        if iteration >= warmup:
            samples["wall_ms"].append(wall_ms)
            timings = getattr(result, "timings_ms", {}) or {}
            for key, value in timings.items():
                samples[key].append(float(value))
            outcomes.append((result.status, _result_label(result)))

    return samples, outcomes


def _mean_and_deviation(values):
    mean = statistics.mean(values)
    deviation = statistics.stdev(values) if len(values) > 1 else 0.0
    return mean, deviation


def main():
    parser = argparse.ArgumentParser(
        description="Measure the complete recycling pipeline on CPU and CUDA."
    )
    parser.add_argument("image", help="Path to the image to analyze")
    parser.add_argument("--runs", type=int, default=30,
                        help="Measured repetitions per device (default: 30)")
    parser.add_argument("--warmup", type=int, default=5,
                        help="Warm-up repetitions excluded from results (default: 5)")
    parser.add_argument("--gpu-only", action="store_true",
                        help="Run only on CUDA; fail if CUDA is unavailable")
    args = parser.parse_args()

    if args.runs < 1:
        parser.error("--runs must be at least 1")
    if args.warmup < 0:
        parser.error("--warmup cannot be negative")

    available_device = get_device()
    if args.gpu_only and available_device != "cuda":
        parser.error("--gpu-only was requested, but CUDA is unavailable")

    # Import after argument validation so --help and input errors stay useful
    # even when the project's model modules are not installed yet.
    try:
        from src.pipeline import RecyclingPipeline
    except ModuleNotFoundError as error:
        missing = error.name or "an unknown module"
        parser.error(
            f"cannot import the integrated pipeline ({missing} is missing). "
            "Run this benchmark after all pipeline modules are present."
        )

    print(f"Dispositivo detectado: {available_device}")
    print(f"GPU/PyTorch: {gpu_info()}")

    with Image.open(args.image) as opened_image:
        image = opened_image.convert("RGB")
    print(f"Imagen: {args.image} ({image.width} x {image.height})")
    print(f"Repeticiones: {args.runs}; calentamiento: {args.warmup}")

    devices = ["cuda"] if args.gpu_only else ["cpu"]
    if not args.gpu_only and available_device == "cuda":
        devices.append("cuda")

    results = {}
    outcomes_by_device = {}

    for device in devices:
        print(f"\nCargando pipeline en {device}...")
        pipeline = RecyclingPipeline(device=device)
        samples, outcomes = _measure_pipeline(
            pipeline, image, runs=args.runs, warmup=args.warmup
        )
        results[device] = samples
        outcomes_by_device[device] = outcomes

        statuses = sorted({status for status, _ in outcomes})
        labels = sorted({label for _, label in outcomes if label is not None})
        print(f"[{device}] estado(s)={', '.join(statuses) or 'sin datos'}; "
              f"clase(s)={', '.join(labels) or 'sin predicción'}")
        for key, values in samples.items():
            mean, deviation = _mean_and_deviation(values)
            print(f"  {key:<18} {mean:>9.2f} ms  desv {deviation:>6.2f}")

        del pipeline
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()

    if "cpu" in results and "cuda" in results:
        cpu_outcomes = set(outcomes_by_device["cpu"])
        gpu_outcomes = set(outcomes_by_device["cuda"])
        if cpu_outcomes != gpu_outcomes:
            print("\nAviso: el estado o la clase difieren entre CPU y GPU.")

        common_keys = results["cpu"].keys() & results["cuda"].keys()
        print("\nAceleración GPU frente a CPU (promedios):")
        for key in sorted(common_keys):
            cpu_mean = statistics.mean(results["cpu"][key])
            gpu_mean = statistics.mean(results["cuda"][key])
            if gpu_mean > 0:
                print(f"  {key:<18} {cpu_mean / gpu_mean:>7.2f}x")


if __name__ == "__main__":
    main()
