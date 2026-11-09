"""Compare Grounding DINO thresholds using class-agnostic NMS."""

import argparse
import csv
import time
from pathlib import Path

import torch
from PIL import Image, ImageDraw
from torchvision.ops import nms
from transformers import pipeline


MODEL = "IDEA-Research/grounding-dino-tiny"
LABELS = ["trash", "waste", "packaging", "wrapper", "peel", "bottle", "can"]
CONFIGURATIONS = [
    {"name": "configuration_01", "threshold": 0.05},
    {"name": "configuration_02", "threshold": 0.10},
    {"name": "configuration_03", "threshold": 0.20},
]
MAX_AREA = 0.7
NMS_IOU = 0.5
TOP_N = 4


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run IDEA-Research Grounding DINO on one image with three confidence "
            "thresholds and class-agnostic duplicate suppression."
        )
    )
    parser.add_argument("image", type=Path, help="Path to the image to analyze")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmarks/gdino_calibration_v2_results"),
        help="Directory for annotated images and the CSV summary",
    )
    return parser.parse_args()


def select_detections(detections, width, height):
    """Suppress duplicate boxes even when Grounding DINO assigns other labels."""
    if not detections:
        return []

    boxes = torch.tensor(
        [
            [d["box"]["xmin"], d["box"]["ymin"], d["box"]["xmax"], d["box"]["ymax"]]
            for d in detections
        ],
        dtype=torch.float32,
    )
    scores = torch.tensor([d["score"] for d in detections], dtype=torch.float32)
    labels = [str(d.get("label", "object")) for d in detections]

    boxes[:, 0::2].clamp_(0, width)
    boxes[:, 1::2].clamp_(0, height)
    areas = ((boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])) / (width * height)
    valid = (areas > 0) & (areas <= MAX_AREA)
    valid_indices = torch.where(valid)[0]
    if valid_indices.numel() == 0:
        return []

    boxes = boxes[valid_indices]
    scores = scores[valid_indices]
    labels = [labels[index] for index in valid_indices.tolist()]
    # Unlike v1, suppression is not separated by label. This lets a high-score
    # "wrapper" box suppress an almost identical "peel" box for the same item.
    keep = nms(boxes, scores, NMS_IOU)[:TOP_N]
    return [
        {
            "label": labels[index],
            "score": float(scores[index]),
            "box": boxes[index].tolist(),
        }
        for index in keep.tolist()
    ]


def save_annotated_image(image, detections, path):
    result = image.copy()
    draw = ImageDraw.Draw(result)
    for detection in detections:
        x0, y0, x1, y1 = detection["box"]
        caption = f'{detection["label"]} {detection["score"]:.2f}'
        draw.rectangle((x0, y0, x1, y1), outline="red", width=4)
        draw.text((x0 + 5, y0 + 5), caption, fill="red", stroke_width=1, stroke_fill="white")
    result.save(path)


def main():
    args = parse_args()
    if not args.image.is_file():
        raise SystemExit(f"No se encontró la imagen: {args.image}")
    if not torch.cuda.is_available():
        raise SystemExit("CUDA no está disponible; este benchmark está configurado para GPU.")

    image = Image.open(args.image).convert("RGB")
    image.thumbnail((1024, 1024))
    width, height = image.size
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Imagen: {args.image.name} ({width} × {height})")
    print(f"Cargando {MODEL} en CUDA...")
    detector = pipeline("zero-shot-object-detection", model=MODEL, device=0)

    # Warm up the model once; the warm-up is not included in the measurements.
    detector(image, candidate_labels=LABELS, threshold=CONFIGURATIONS[0]["threshold"])
    torch.cuda.synchronize()

    csv_path = args.output_dir / f"{args.image.stem}_results.csv"
    rows = []
    print("\nResultados por configuración:")
    for config in CONFIGURATIONS:
        torch.cuda.synchronize()
        start = time.perf_counter()
        raw = detector(
            image,
            candidate_labels=LABELS,
            threshold=config["threshold"],
        )
        torch.cuda.synchronize()
        elapsed_ms = (time.perf_counter() - start) * 1000
        detections = select_detections(raw, width, height)

        output_image = args.output_dir / f"{args.image.stem}_{config['name']}.jpg"
        save_annotated_image(image, detections, output_image)
        print(
            f"\n{config['name']}: umbral={config['threshold']:.2f} | "
            f"{elapsed_ms:.2f} ms | {len(raw)} candidatas | "
            f"{len(detections)} seleccionadas"
        )
        for detection in detections:
            x0, y0, x1, y1 = detection["box"]
            print(
                f"  {detection['label']} ({detection['score']:.3f}) "
                f"({x0:.0f},{y0:.0f})-({x1:.0f},{y1:.0f})"
            )
            rows.append(
                {
                    "image": args.image.name,
                    "configuration": config["name"],
                    "threshold": config["threshold"],
                    "inference_ms": f"{elapsed_ms:.2f}",
                    "candidate_count": len(raw),
                    "selected_count": len(detections),
                    "label": detection["label"],
                    "score": f"{detection['score']:.4f}",
                    "box_xyxy": f"{x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f}",
                    "annotated_image": str(output_image),
                }
            )
        if not detections:
            rows.append(
                {
                    "image": args.image.name,
                    "configuration": config["name"],
                    "threshold": config["threshold"],
                    "inference_ms": f"{elapsed_ms:.2f}",
                    "candidate_count": len(raw),
                    "selected_count": 0,
                    "label": "",
                    "score": "",
                    "box_xyxy": "",
                    "annotated_image": str(output_image),
                }
            )
        print(f"  Imagen anotada: {output_image}")

    fieldnames = [
        "image",
        "configuration",
        "threshold",
        "inference_ms",
        "candidate_count",
        "selected_count",
        "label",
        "score",
        "box_xyxy",
        "annotated_image",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nCSV: {csv_path}")


if __name__ == "__main__":
    main()
