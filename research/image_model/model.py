"""Small educational text-conditioned diffusion baseline; all weights start randomly."""
import re

import torch
from torch import nn


def tokenize(text: str):
    return re.findall(r"[a-z0-9]+", text.lower())


def build_vocab(captions):
    words = set()
    for caption in captions:
        words.update(tokenize(caption))
    return sorted(words)


DEFAULT_VOCAB = ["a", "amber", "background", "blue", "circle", "dark",
                 "green", "on", "red", "square", "triangle"]


class TextConditioner(nn.Module):
    """Text embedding trained from scratch; no external tokenizer/model.

    v4 (Origin run 5): word-level embeddings. The v1-v3 byte-level encoder
    blurred whole words together (runs 3-4 showed color words binding
    unreliably). Words from the dataset's own captions form the vocabulary;
    every embedding is learned from random initialization like the rest.
    """
    def __init__(self, width: int = 128, vocab=None, max_words: int = 24):
        super().__init__()
        self.max_words = max_words
        self.vocab = list(vocab) if vocab else list(DEFAULT_VOCAB)
        self.word_to_id = {w: i + 2 for i, w in enumerate(self.vocab)}  # 0=pad, 1=unk
        self.embedding = nn.Embedding(len(self.vocab) + 2, width, padding_idx=0)
        # mean+max pooling (kept from v2): max keeps the strongest word
        # features alive in the conditioning vector.
        self.proj = nn.Sequential(nn.Linear(width * 2, width), nn.SiLU(), nn.Linear(width, width))

    def encode(self, captions, device):
        ids = torch.zeros(len(captions), self.max_words, dtype=torch.long, device=device)
        for row, caption in enumerate(captions):
            tokens = tokenize(caption)[: self.max_words]
            for col, tok in enumerate(tokens):
                ids[row, col] = self.word_to_id.get(tok, 1)
        emb = self.embedding(ids)
        mask = (ids != 0).float().unsqueeze(-1)
        mean_pooled = (emb * mask).sum(1) / mask.sum(1).clamp_min(1)
        max_pooled = (emb + (mask - 1.0) * 1e9).max(1).values
        return self.proj(torch.cat([mean_pooled, max_pooled], dim=1))


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
        # v2 (Origin run 3): a conditioned block at full resolution, so the
        # text/time signal shapes features at 64x64 too, not only at the
        # bottleneck as in v1.
        self.block_in = ResBlock(width, cond_dim)
        self.down = nn.Conv2d(width, width * 2, 4, stride=2, padding=1)
        self.mid1 = ResBlock(width * 2, cond_dim)
        self.mid2 = ResBlock(width * 2, cond_dim)
        self.up = nn.ConvTranspose2d(width * 2, width, 4, stride=2, padding=1)
        self.output = nn.Sequential(nn.GroupNorm(8, width), nn.SiLU(), nn.Conv2d(width, 3, 3, padding=1))

    def forward(self, noisy, timestep, text_cond):
        t = timestep.float().view(-1, 1) / 1000.0
        cond = text_cond + self.time_mlp(t)
        x = self.block_in(self.input(noisy), cond)
        h = self.down(torch.nn.functional.silu(x))
        h = self.mid1(h, cond)
        h = self.mid2(h, cond)
        h = self.up(torch.nn.functional.silu(h))
        return self.output(torch.nn.functional.silu(h + x))


class ScratchImageDiffusion(nn.Module):
    def __init__(self, width=64, cond_dim=128, steps=1000, vocab=None):
        super().__init__()
        self.text = TextConditioner(cond_dim, vocab=vocab)
        self.denoiser = FromScratchDenoiser(width, cond_dim)
        self.steps = steps
        betas = torch.linspace(1e-4, 0.02, steps)
        alphas = 1.0 - betas
        self.register_buffer("alphas_bar", torch.cumprod(alphas, dim=0))

    def forward(self, images, captions):
        device = images.device
        batch = images.shape[0]
        cond = self.text.encode(captions, device)
        # v3 (Origin run 4): classifier-free guidance training — drop the
        # text conditioning on ~10% of samples so the sampler can steer
        # generation toward the prompt by contrasting both predictions.
        drop = torch.rand(batch, 1, device=device) < 0.1
        cond = cond.masked_fill(drop, 0.0)
        t = torch.randint(0, self.steps, (batch,), device=device)
        noise = torch.randn_like(images)
        a_bar = self.alphas_bar[t].view(batch, 1, 1, 1)
        noisy = a_bar.sqrt() * images + (1 - a_bar).sqrt() * noise
        predicted = self.denoiser(noisy, t, cond)
        return torch.nn.functional.mse_loss(predicted, noise)
