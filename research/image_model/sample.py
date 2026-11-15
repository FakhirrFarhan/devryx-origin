"""Sampler for the small research baseline: ancestral DDPM over all
timesteps by default, or DDIM (eta=0) fast sampling with --sample-steps."""
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
    parser.add_argument("--seed", type=int, default=None,
                        help="Fix the sampling seed for reproducible multi-sample evaluation.")
    parser.add_argument("--sample-steps", type=int, default=None,
                        help="Fast sampling: when set below the model's full timestep "
                             "count, use DDIM (eta=0) over that many evenly spaced "
                             "timesteps instead of the full ancestral DDPM loop. "
                             "Default (unset) = full sampling, unchanged.")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()
    if args.seed is not None:
        torch.manual_seed(args.seed)
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

    def predict_eps(x_cur, t_idx):
        """Epsilon prediction with classifier-free guidance (same structure
        as the original sampler: conditional pass, unconditional pass with a
        zero conditioning vector, combined at --guidance)."""
        t = torch.tensor([t_idx], device=device)
        eps_c = model.denoiser(x_cur, t, cond)
        if args.guidance != 1.0:
            eps_u = model.denoiser(x_cur, t, uncond)
            return eps_u + args.guidance * (eps_c - eps_u)
        return eps_c

    if args.sample_steps is None or args.sample_steps >= model.steps:
        # Legacy ancestral DDPM over every timestep (original behavior).
        betas = torch.linspace(1e-4, 0.02, model.steps, device=device)
        alphas = 1 - betas
        for i in reversed(range(model.steps)):
            eps = predict_eps(x, i)
            x = (x - (betas[i] / torch.sqrt(1 - model.alphas_bar[i])) * eps) / torch.sqrt(alphas[i])
            if i > 0:
                x = x + torch.sqrt(betas[i]) * torch.randn_like(x)
    else:
        # DDIM (eta=0, deterministic) over an evenly spaced subsequence of
        # timesteps, using the model's own alphas_bar schedule buffer.
        n = max(1, int(args.sample_steps))
        taus = sorted({int(round(v)) for v in
                       torch.linspace(0, model.steps - 1, n).tolist()})
        print(f"DDIM fast sampling: {len(taus)} steps "
              f"(of {model.steps} full)")
        alphas_bar = model.alphas_bar
        for pos in range(len(taus) - 1, -1, -1):
            t_cur = taus[pos]
            t_prev = taus[pos - 1] if pos > 0 else -1
            eps = predict_eps(x, t_cur)
            a_cur = alphas_bar[t_cur]
            x0 = (x - torch.sqrt(1 - a_cur) * eps) / torch.sqrt(a_cur)
            if t_prev < 0:
                x = x0
            else:
                a_prev = alphas_bar[t_prev]
                x = torch.sqrt(a_prev) * x0 + torch.sqrt(1 - a_prev) * eps
    x = ((x.clamp(-1, 1) + 1) * 127.5).byte()[0].permute(1, 2, 0).cpu().numpy()
    Image.fromarray(x).save(args.out)
    print(f"Saved sample to {args.out}. Quality depends entirely on training and dataset scale.")


if __name__ == "__main__":
    main()
