"""Small educational text-conditioned diffusion baseline; all weights start randomly."""
import torch
from torch import nn


class TextConditioner(nn.Module):
    """Byte-level text embedding trained from scratch; no external tokenizer/model."""
    def __init__(self, width: int = 128, max_bytes: int = 160):
        super().__init__()
        self.max_bytes = max_bytes
        self.embedding = nn.Embedding(257, width, padding_idx=0)
        self.proj = nn.Sequential(nn.Linear(width, width), nn.SiLU(), nn.Linear(width, width))

    def encode(self, captions, device):
        ids = torch.zeros(len(captions), self.max_bytes, dtype=torch.long, device=device)
        for row, caption in enumerate(captions):
            raw = list(caption.encode("utf-8")[: self.max_bytes])
            if raw:
                ids[row, :len(raw)] = torch.tensor([b + 1 for b in raw], device=device)
        mask = (ids != 0).float().unsqueeze(-1)
        pooled = (self.embedding(ids) * mask).sum(1) / mask.sum(1).clamp_min(1)
        return self.proj(pooled)


class ResBlock(nn.Module):
    def __init__(self, channels, cond_dim):
        super().__init__()
        self.norm1 = nn.GroupNorm(8, channels)
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1)
        self.norm2 = nn.GroupNorm(8, channels)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1)
        self.condition = nn.Linear(cond_dim, channels * 2)

    def forward(self, x, cond):
        scale, shift = self.condition(cond).chunk(2, dim=1)
        h = self.norm1(x) * (1 + scale[:, :, None, None]) + shift[:, :, None, None]
        h = self.conv1(torch.nn.functional.silu(h))
        h = self.conv2(torch.nn.functional.silu(self.norm2(h)))
        return x + h * 0.5


class FromScratchDenoiser(nn.Module):
    def __init__(self, width=64, cond_dim=128):
        super().__init__()
        self.time_mlp = nn.Sequential(nn.Linear(1, cond_dim), nn.SiLU(), nn.Linear(cond_dim, cond_dim))
        self.input = nn.Conv2d(3, width, 3, padding=1)
        self.down = nn.Conv2d(width, width * 2, 4, stride=2, padding=1)
        self.mid1 = ResBlock(width * 2, cond_dim)
        self.mid2 = ResBlock(width * 2, cond_dim)
        self.up = nn.ConvTranspose2d(width * 2, width, 4, stride=2, padding=1)
        self.output = nn.Sequential(nn.GroupNorm(8, width), nn.SiLU(), nn.Conv2d(width, 3, 3, padding=1))

    def forward(self, noisy, timestep, text_cond):
        t = timestep.float().view(-1, 1) / 1000.0
        cond = text_cond + self.time_mlp(t)
        x = self.input(noisy)
        h = self.down(torch.nn.functional.silu(x))
        h = self.mid1(h, cond)
        h = self.mid2(h, cond)
        h = self.up(torch.nn.functional.silu(h))
        return self.output(torch.nn.functional.silu(h + x))


class ScratchImageDiffusion(nn.Module):
    def __init__(self, width=64, cond_dim=128, steps=1000):
        super().__init__()
        self.text = TextConditioner(cond_dim)
        self.denoiser = FromScratchDenoiser(width, cond_dim)
        self.steps = steps
        betas = torch.linspace(1e-4, 0.02, steps)
        alphas = 1.0 - betas
        self.register_buffer("alphas_bar", torch.cumprod(alphas, dim=0))

    def forward(self, images, captions):
        device = images.device
        batch = images.shape[0]
        cond = self.text.encode(captions, device)
        t = torch.randint(0, self.steps, (batch,), device=device)
        noise = torch.randn_like(images)
        a_bar = self.alphas_bar[t].view(batch, 1, 1, 1)
        noisy = a_bar.sqrt() * images + (1 - a_bar).sqrt() * noise
        predicted = self.denoiser(noisy, t, cond)
        return torch.nn.functional.mse_loss(predicted, noise)
