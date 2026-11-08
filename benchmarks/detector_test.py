import gc
import sys
import time

import torch
from PIL import Image
from transformers import pipeline

MODELS = ["IDEA-Research/grounding-dino-tiny", "google/owlv2-base-patch16-ensemble"]
LABELS = ["trash", "waste", "packaging", "wrapper", "peel", "bottle", "can"]

image = Image.open(sys.argv[1]).convert("RGB")
for name in MODELS:
    det = None
    try:
        torch.cuda.reset_peak_memory_stats()
        det = pipeline("zero-shot-object-detection", model=name, device=0)
        det(image, candidate_labels=LABELS)  # calentamiento
        t0 = time.perf_counter()
        out = det(image, candidate_labels=LABELS, threshold=0.1)
        torch.cuda.synchronize()
        ms = (time.perf_counter() - t0) * 1000
        peak = torch.cuda.max_memory_allocated() / 2**20
        print(f"\n{name}: {ms:.0f} ms, pico {peak:.0f} MiB, {len(out)} detecciones")
        for d in out:
            b = d["box"]
            print(f"  {d['label']:<10} {d['score']:.2f}  "
                  f"({b['xmin']},{b['ymin']})-({b['xmax']},{b['ymax']})")
    except Exception as error:
        print(f"\n{name}: falló -> {error}")
    finally:
        del det
        gc.collect()
        torch.cuda.empty_cache()