#!/usr/bin/env python3
"""Assemble the self-contained Kaggle training kernel for Origin.

Embeds the current research sources (base64) into one script that:
  1. writes the research package into ./origin_src
  2. generates dataset v0.3 (code-drawn, rights-clean)
  3. trains on the GPU (checkpoints to /kaggle/working/checkpoints_gpu)
  4. samples the 3 standard prompts x 4 seeds and scores them objectively
  5. copies checkpoint + samples + scores to the kernel output root

Output: ~/workspace/kaggle-origin/{train_kernel.py, kernel-metadata.json}
Push with: kaggle kernels push -p ~/workspace/kaggle-origin
"""
import base64
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.expanduser("~/workspace/kaggle-origin")
os.makedirs(OUT, exist_ok=True)

FILES = [
    "research/__init__.py",
    "research/image_model/__init__.py",
    "research/image_model/model.py",
    "research/image_model/data.py",
    "research/image_model/train.py",
    "research/image_model/sample.py",
    "research/make_tiny_dataset_v3.py",
    "research/score_samples.py",
]

STEPS = 15000
BATCH = 32

blobs = {}
for rel in FILES:
    with open(os.path.join(BASE, rel), "rb") as f:
        blobs[rel] = base64.b64encode(f.read()).decode()

script = '''#!/usr/bin/env python3
"""Origin GPU training run (Kaggle) — assembled by build_kernel.py.
Trains Devryx Origin's from-scratch diffusion model on a free GPU.
No pretrained weights, no hosted AI APIs; dataset is code-drawn.
"""
import base64, os, shutil, subprocess, sys

import torch
print("torch", torch.__version__, "cuda_available:", torch.cuda.is_available(),
      "device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NONE",
      flush=True)
if not torch.cuda.is_available():
    raise SystemExit("CUDA not available in this kernel session - GPU accelerator not attached")

FILES = __BLOBS__
ROOT = "/tmp/origin_src"
for rel, b64 in FILES.items():
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(base64.b64decode(b64))
print("sources written to", ROOT, flush=True)

def run(cmd, **kw):
    print("+", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT, **kw)
    if r.returncode != 0:
        raise SystemExit(f"command failed ({r.returncode}): {' '.join(cmd)}")

PY = sys.executable
run([PY, "research/make_tiny_dataset_v3.py"])
run([PY, "-m", "research.image_model.train",
     "--data", "research/data/tiny_shapes3",
     "--steps", "__STEPS__", "--batch-size", "__BATCH__",
     "--image-size", "64", "--lr", "3e-4", "--device", "cuda",
     "--out", "/kaggle/working/checkpoints_gpu"])

WORK = "/kaggle/working"
EVAL = os.path.join(WORK, "eval")
os.makedirs(EVAL, exist_ok=True)
CKPT = os.path.join(WORK, "checkpoints_gpu", "devryx_image_scratch.pt")
PROMPTS = {"red": "A red circle on a dark background",
           "blue": "A blue square on a dark background",
           "green": "A green triangle on a dark background"}
for color, prompt in PROMPTS.items():
    for seed in (11, 22, 33, 44):
        run([PY, "-m", "research.image_model.sample",
             "--checkpoint", CKPT, "--prompt", prompt,
             "--seed", str(seed), "--device", "cuda",
             "--out", os.path.join(EVAL, f"sample_{color}_{seed}.png")])
run([PY, "research/score_samples.py", EVAL])
shutil.copy(CKPT, os.path.join(WORK, "devryx_image_scratch.pt"))
print("DONE — checkpoint, eval samples and scores in", WORK, flush=True)
'''
script = script.replace("__BLOBS__", json.dumps(blobs, indent=1))
script = script.replace("__STEPS__", str(STEPS)).replace("__BATCH__", str(BATCH))

nb = {
    "nbformat": 4, "nbformat_minor": 0,
    "metadata": {"kernelspec": {"language": "python", "display_name": "Python 3", "name": "python3"},
                 "language_info": {"name": "python", "version": "3.12"}},
    "cells": [{"cell_type": "code", "execution_count": 0, "metadata": {}, "outputs": [],
               "source": script.splitlines(keepends=True)}],
}
with open(os.path.join(OUT, "train_kernel.ipynb"), "w") as f:
    json.dump(nb, f)

meta = {
    "id": "fakhirfarhan/devryx-origin-train",
    "title": "Devryx Origin Train",
    "code_file": "train_kernel.ipynb",
    "language": "python",
    "kernel_type": "notebook",
    "is_private": True,
    "enable_gpu": True,
    "enable_tpu": False,
    "enable_internet": False,
    "machine_shape": "NvidiaTeslaT4",
    "dataset_sources": [],
    "competition_sources": [],
    "kernel_sources": [],
    "model_sources": [],
}
with open(os.path.join(OUT, "kernel-metadata.json"), "w") as f:
    json.dump(meta, f, indent=2)

stale = os.path.join(OUT, "train_kernel.py")
if os.path.exists(stale):
    os.remove(stale)

print(f"kernel package written to {OUT} (notebook, script {len(script)} bytes, steps {STEPS}, batch {BATCH})")
