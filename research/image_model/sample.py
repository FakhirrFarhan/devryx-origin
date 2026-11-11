"""Basic ancestral DDPM sampler for the small research baseline."""
import argparse
from pathlib import Path
import torch
from PIL import Image
from .model import ScratchImageDiffusion


@torch.no_grad()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--out", default="sample.png")
    parser.add_argument("--size", type=int, default=64)
    parser.add_argument("--guidance", type=float, default=3.0,
                        help="Classifier-free guidance scale (v3, run 4). 1.0 = no guidance.")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()
    device = torch.device(args.device)
    saved = torch.load(args.checkpoint, map_location=device, weights_only=False)
    # v4: rebuild the model with the checkpoint's own word vocabulary.
    model = ScratchImageDiffusion(vocab=saved.get("vocab")).to(device)
    # Prefer EMA weights when the checkpoint carries them (cleaner samples).
    model.load_state_dict(saved.get("model_ema") or saved["model"])
    model.eval()
    x = torch.randn(1, 3, args.size, args.size, device=device)
    cond = model.text.encode([args.prompt], device)
    uncond = torch.zeros_like(cond)
    betas = torch.linspace(1e-4, 0.02, model.steps, device=device)
    alphas = 1 - betas
    for i in reversed(range(model.steps)):
        t = torch.tensor([i], device=device)
        eps_c = model.denoiser(x, t, cond)
        if args.guidance != 1.0:
            eps_u = model.denoiser(x, t, uncond)
            eps = eps_u + args.guidance * (eps_c - eps_u)
        else:
            eps = eps_c
        x = (x - (betas[i] / torch.sqrt(1 - model.alphas_bar[i])) * eps) / torch.sqrt(alphas[i])
        if i > 0:
            x = x + torch.sqrt(betas[i]) * torch.randn_like(x)
    x = ((x.clamp(-1, 1) + 1) * 127.5).byte()[0].permute(1, 2, 0).cpu().numpy()
    Image.fromarray(x).save(args.out)
    print(f"Saved sample to {args.out}. Quality depends entirely on training and dataset scale.")


if __name__ == "__main__":
    main()
