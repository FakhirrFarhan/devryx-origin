import argparse
import os
from pathlib import Path
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from .data import CaptionedImageDataset
from .model import ScratchImageDiffusion


def save_checkpoint(path, model, ema, steps, image_size, vocab):
    """Save a checkpoint atomically (temp file + rename) so a crash mid-write
    never leaves a half-written file behind, and so the serving worker never
    reads a partial checkpoint."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp.pt")
    torch.save({"model": model.state_dict(), "model_ema": ema.state_dict(),
                "steps": steps, "image_size": image_size, "vocab": vocab}, tmp)
    os.replace(tmp, path)


def transplant_embedding(saved_state, model, saved_vocab, new_vocab):
    """Return a copy of a saved state dict whose text-embedding rows are
    remapped onto a new (larger) vocabulary: rows for words present in both
    vocabs are copied verbatim, rows for brand-new words keep the new model's
    random initialization. Every other weight is copied unchanged, so the
    transplanted model keeps all of the old run's learned knowledge."""
    old_ids = {w: i + 2 for i, w in enumerate(saved_vocab)}
    new_emb = model.state_dict()["text.embedding.weight"].clone()
    old_emb = saved_state["text.embedding.weight"]
    copied = []
    for w in new_vocab:
        if w in old_ids:
            new_emb[model.text.word_to_id[w]] = old_emb[old_ids[w]]
            copied.append(w)
    new_state = dict(saved_state)
    new_state["text.embedding.weight"] = new_emb
    return new_state, copied


def main():
    parser = argparse.ArgumentParser(description="Train our own randomly initialized image diffusion baseline.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--image-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--out", default="research/checkpoints")
    parser.add_argument("--init-from", default=None,
                        help="Optional checkpoint to warm-start from (our own weights only). "
                             "Vocab must match the dataset vocab; training continues for "
                             "--steps MORE steps and the saved step count is cumulative.")
    parser.add_argument("--save-every", type=int, default=2000,
                        help="Save a periodic checkpoint every N steps (0 disables). "
                             "Run 7 died at step 7,358/30,000 with no checkpoint saved, "
                             "losing 1h28m of training — periodic saves cap any future "
                             "loss at --save-every steps and let a dead run resume.")
    parser.add_argument("--allow-vocab-transplant", action="store_true",
                        help="On a --init-from vocab mismatch, transplant the shared-word "
                             "embedding rows into the new vocabulary instead of refusing. "
                             "Lets a run warm-start from an older checkpoint on a bigger "
                             "dataset (e.g. run 6 + dataset v0.4). Still our own weights only.")
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
    # Speed lane (Origin run 7 prep): optional warm start from one of our own
    # checkpoints, so training hours compound across runs instead of every
    # run restarting from random noise. Still our own weights only — the
    # checkpoint must have been produced by this same trainer.
    prior_steps = 0
    if args.init_from:
        saved = torch.load(args.init_from, map_location=device, weights_only=False)
        saved_vocab = saved.get("vocab")
        if saved_vocab != vocab:
            if not args.allow_vocab_transplant:
                raise RuntimeError(
                    f"--init-from vocab mismatch: checkpoint {args.init_from} has vocab "
                    f"{saved_vocab}, but this dataset builds vocab {vocab}. Warm start "
                    "requires the exact same vocabulary; refusing to load. Pass "
                    "--allow-vocab-transplant to carry the shared-word embeddings over.")
            model_state, copied = transplant_embedding(
                saved["model"], model, saved_vocab, vocab)
            model.load_state_dict(model_state)
            ema_state, _ = transplant_embedding(
                saved.get("model_ema") or saved["model"], ema, saved_vocab, vocab)
            ema.load_state_dict(ema_state)
            new_words = [w for w in vocab if w not in saved_vocab]
            print(f"Vocab transplant: carried {len(copied)} shared words over from "
                  f"{args.init_from}; {len(new_words)} new words ({new_words}) start "
                  f"from random init.", flush=True)
        else:
            model.load_state_dict(saved["model"])
            # EMA copy resumes from the checkpoint's EMA weights when present.
            ema.load_state_dict(saved.get("model_ema") or saved["model"])
        prior_steps = int(saved.get("steps", 0))
        print(f"Warm start: loaded {args.init_from} ({prior_steps} prior steps); "
              f"training {args.steps} more steps "
              f"(cumulative {prior_steps + args.steps}).", flush=True)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    target = out / "devryx_image_scratch.pt"
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    model.train()
    step = 0
    desc = ("Training (warm start)" if prior_steps else
            "Training from random initialization")
    bar = tqdm(total=args.steps, desc=desc)
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
            if args.save_every and step % args.save_every == 0 and step < args.steps:
                save_checkpoint(target, model, ema, prior_steps + step,
                                args.image_size, vocab)
                print(f"\nPeriodic checkpoint saved at step {prior_steps + step} "
                      f"-> {target}", flush=True)
            if step >= args.steps:
                break
    bar.close()
    save_checkpoint(target, model, ema, prior_steps + step, args.image_size, vocab)
    print(f"Saved our trained checkpoint to {target} "
          f"({prior_steps + step} cumulative steps)")


if __name__ == "__main__":
    main()
