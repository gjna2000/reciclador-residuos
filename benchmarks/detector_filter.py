import sys
import time

import torch
from PIL import Image, ImageDraw
from torchvision.ops import box_convert, nms
from transformers import Owlv2ForObjectDetection, Owlv2Processor, pipeline
from huggingface_hub import hf_hub_download
from ultralytics import YOLOWorld

MODELS = {
    "gdino": "IDEA-Research/grounding-dino-tiny",
    "owlv2": "google/owlv2-base-patch16-ensemble",
    "owlv2-obj": "google/owlv2-base-patch16-ensemble",
    "yolo-world-lvis": "mbar0075/YOLO-World-LVIS",
}
WEIGHT_FILES = {"yolo-world-lvis": "yolov8s-worldv2-lvis.pt"}
LABELS = ["trash", "waste", "packaging", "wrapper", "peel", "bottle", "can"]
MIN_SCORE = {"gdino": 0.10, "owlv2": 0.10, "owlv2-obj": 0.20, "yolo-world-lvis": 0.10}  # puntaje mínimo por modo
MAX_AREA = 0.7   # descarta cajas que cubren casi toda la foto
IOU = 0.5        # cajas que se solapan más que esto se fusionan
TOP_N = 4        # máximo de recortes


def pick(boxes, scores, W, H, min_score):
    """Filtra sin mirar etiquetas: puntaje, tamaño y cajas solapadas."""
    boxes = boxes.clone()
    boxes[:, 0::2] = boxes[:, 0::2].clamp(0, W)
    boxes[:, 1::2] = boxes[:, 1::2].clamp(0, H)
    area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1]) / (W * H)
    ok = (scores >= min_score) & (area <= MAX_AREA)
    boxes, scores = boxes[ok], scores[ok]
    keep = nms(boxes, scores, IOU)[:TOP_N]
    return boxes[keep], scores[keep]


def make_runner(mode, image):
    name = MODELS[mode]
    W, H = image.size
    if mode == "yolo-world-lvis":
        weights = hf_hub_download(
            repo_id=name,
            filename=WEIGHT_FILES[mode],
        )
        model = YOLOWorld(weights)
        model.set_classes(LABELS)

        def go():
            results = model.predict(
                source=image,
                # Keep nearly all YOLO-World proposals; this mode is inspected
                # without the benchmark's score/area/NMS/top-N post-filter.
                conf=0.05,
                device="cuda",
                verbose=False,
            )
            torch.cuda.synchronize()
            result = results[0]
            if result.boxes is None or len(result.boxes) == 0:
                return torch.zeros((0, 4)), torch.zeros(0)
            boxes = result.boxes.xyxy.detach().cpu().to(torch.float32)
            scores = result.boxes.conf.detach().cpu().to(torch.float32)
            return boxes, scores

        return go

    if mode == "owlv2-obj":
        processor = Owlv2Processor.from_pretrained(name)
        model = Owlv2ForObjectDetection.from_pretrained(name).to("cuda").eval()
        inputs = processor(text=[["an object"]], images=image, return_tensors="pt").to("cuda")

        def go():
            with torch.inference_mode():
                out = model(**inputs)
            torch.cuda.synchronize()
            if not hasattr(out, "objectness_logits"):
                raise RuntimeError(f"sin objectness_logits; campos: {list(out.keys())}")
            scores = out.objectness_logits[0].sigmoid().cpu()
            boxes = box_convert(out.pred_boxes[0].cpu(), "cxcywh", "xyxy") * max(W, H)
            return boxes, scores

        return go

    det = pipeline("zero-shot-object-detection", model=name, device=0)

    def go():
        out = det(image, candidate_labels=LABELS, threshold=0.05)
        torch.cuda.synchronize()
        if not out:
            return torch.zeros((0, 4)), torch.zeros(0)
        boxes = torch.tensor(
            [[d["box"]["xmin"], d["box"]["ymin"], d["box"]["xmax"], d["box"]["ymax"]] for d in out],
            dtype=torch.float32,
        )
        scores = torch.tensor([d["score"] for d in out])
        return boxes, scores

    return go


mode, path = sys.argv[1], sys.argv[2]
image = Image.open(path).convert("RGB")
image.thumbnail((1024, 1024))
W, H = image.size

go = make_runner(mode, image)
go()  # calentamiento
torch.cuda.reset_peak_memory_stats()
times = []
for _ in range(3):
    t0 = time.perf_counter()
    boxes, scores = go()
    times.append((time.perf_counter() - t0) * 1000)
peak = torch.cuda.max_memory_allocated() / 2**20
print(f"{mode}: {sum(times) / len(times):.0f} ms promedio, pico {peak:.0f} MiB, "
      f"{len(scores)} candidatos antes de filtrar")

if mode == "yolo-world-lvis":
    # Inspect raw model detections: do not discard boxes by score, area,
    # overlap, or TOP_N in this mode.
    boxes = boxes.clone()
    boxes[:, 0::2] = boxes[:, 0::2].clamp(0, W)
    boxes[:, 1::2] = boxes[:, 1::2].clamp(0, H)
else:
    boxes, scores = pick(boxes, scores, W, H, MIN_SCORE[mode])
draw = ImageDraw.Draw(image)
for box, score in zip(boxes.tolist(), scores.tolist()):
    x0, y0, x1, y1 = box
    draw.rectangle([x0, y0, x1, y1], outline="red", width=4)
    draw.text((x0 + 6, y0 + 6), f"objeto {score:.2f}", fill="red")
    print(f"  objeto {score:.2f}  ({x0:.0f},{y0:.0f})-({x1:.0f},{y1:.0f})")
image.save(f"detector_{mode}.jpg")
print(f"{len(scores)} objetos en detector_{mode}.jpg")
