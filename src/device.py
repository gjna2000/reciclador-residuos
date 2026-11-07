import torch


def get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def sync() -> None:
    # Espera a que la GPU termine antes de medir tiempos
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def gpu_info() -> dict:
    if not torch.cuda.is_available():
        return {"device": "cpu", "torch": torch.__version__}
    p = torch.cuda.get_device_properties(0)
    return {
        "device": "cuda",
        "name": p.name,
        "vram_gb": round(p.total_memory / 1024**3, 2),
        "capability": f"{p.major}.{p.minor}",
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
    }


if __name__ == "__main__":
    print(f"Dispositivo: {get_device()}")
    print(gpu_info())
