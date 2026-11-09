import argparse
import statistics
import time

import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

from src.device import get_device, gpu_info, sync

MODEL_ID = "watersplash/waste-classification"


def measure(model, x, runs, warmup=5):
    times = []
    with torch.inference_mode():
        for i in range(warmup + runs):
            sync()
            t0 = time.perf_counter()
            logits = model(pixel_values=x).logits
            sync()
            if i >= warmup:
                times.append((time.perf_counter() - t0) * 1000)
    return statistics.mean(times), statistics.stdev(times), logits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--gpu-only", action="store_true")
    args = ap.parse_args()

    print(gpu_info())
    img = Image.open(args.image).convert("RGB")
    print(f"Tamaño de la imagen: {img.size}")

    processor = AutoImageProcessor.from_pretrained(MODEL_ID)
    t0 = time.perf_counter()
    pixels = processor(images=img, return_tensors="pt")["pixel_values"]
    prep_ms = (time.perf_counter() - t0) * 1000
    print(f"Preprocesado en CPU: {prep_ms:.1f} ms")

    configs = [] if args.gpu_only else [("CPU fp32", "cpu", torch.float32)]
    if get_device() == "cuda":
        configs += [("GPU fp32", "cuda", torch.float32),
                    ("GPU fp16", "cuda", torch.float16)]

    print(f"\n{'Config':<10} {'copia ms':>9} {'infer ms':>9} {'desv':>6}  clase")
    for name, dev, dtype in configs:
        model = AutoModelForImageClassification.from_pretrained(
            MODEL_ID, torch_dtype=dtype).to(dev).eval()
        sync()
        t0 = time.perf_counter()
        x = pixels.to(dev, dtype=dtype)
        sync()
        copy_ms = (time.perf_counter() - t0) * 1000
        mean, sd, logits = measure(model, x, args.runs)
        label = model.config.id2label[logits.argmax(-1).item()]
        print(f"{name:<10} {copy_ms:>9.2f} {mean:>9.2f} {sd:>6.2f}  {label}")
        del model
        if dev == "cuda":
            torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
