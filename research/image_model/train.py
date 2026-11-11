import argparse
from pathlib import Path
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from .data import CaptionedImageDataset
from .model import ScratchImageDiffusion


def main():
    parser = argparse.ArgumentParser(description="Train our own randomly initialized image diffusion baseline.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--image-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--out", default="research/checkpoints")
    args = parser.parse_args()

    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable in this PyTorch installation.")
    dataset = CaptionedImageDataset(args.data, args.image_size)
    if len(dataset) == 0:
        raise RuntimeError("Dataset is empty.")
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)
    # v4 (run 5): word vocabulary built from this dataset's own captions.
    from .model import build_vocab
    vocab = build_vocab([caption for _, caption in dataset])
    model = ScratchImageDiffusion(vocab=vocab).to(device)  # random initialization; no checkpoint is loaded
    # v3 (Origin run 4): EMA shadow weights — a slowly averaged copy of the
    # model that typically samples far more cleanly than the raw weights.
    import copy
    ema = copy.deepcopy(model).eval()
    for p in ema.parameters():
        p.requires_grad_(False)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    model.train()
    step = 0
    bar = tqdm(total=args.steps, desc="Training from random initialization")
    while step < args.steps:
        for images, captions in loader:
            images = images.to(device)
            loss = model(images, list(captions))
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            with torch.no_grad():
                for p_ema, p in zip(ema.parameters(), model.parameters()):
                    p_ema.mul_(0.999).add_(p.detach(), alpha=0.001)
                for b_ema, b in zip(ema.buffers(), model.buffers()):
                    b_ema.copy_(b)
            step += 1
            bar.update(1)
            bar.set_postfix(loss=f"{loss.item():.4f}")
            if step >= args.steps:
                break
    bar.close()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    target = out / "devryx_image_scratch.pt"
    torch.save({"model": model.state_dict(), "model_ema": ema.state_dict(), "steps": step, "image_size": args.image_size, "vocab": vocab}, target)
    print(f"Saved our trained checkpoint to {target}")


if __name__ == "__main__":
    main()
