#!/usr/bin/env python3
"""Origin worker — AI Studio's only engine is Fakhir's own model.

Polls the Origin questions inbox (webhook.site pipe, curl transport like
the self-host stream worker), samples the newest Origin checkpoint with
the from-scratch diffusion model, and posts the finished image back to
the replies inbox as base64. No hosted AI APIs, no pretrained weights:
the checkpoint this serves was trained here, from random init.

Latest checkpoint wins: each job re-scans research/checkpoints_* and
uses the newest devryx_image_scratch.pt, so every new training run goes
live automatically.
"""
import base64
import glob
import io
import json
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
SEEN_FILE = os.path.join(BASE, "origin_worker_seen.json")


def load_tokens():
    toks = {}
    env_path = os.path.join(BASE, "origin_pipe.env")
    if os.path.exists(env_path):
        for line in open(env_path):
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                toks[k.strip()] = v.strip()
    return toks["WH_Q_ORIGIN"], toks["WH_R_ORIGIN"]


WH_Q, WH_R = load_tokens()


def _curl(args, data=None, timeout=60):
    cmd = ["curl", "-sS", "--max-time", str(timeout)] + args
    if data is not None:
        cmd += ["-d", data]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 15)
    if out.returncode != 0:
        raise RuntimeError(f"curl failed: {out.stderr.strip()[:120]}")
    return out.stdout


def wh_get_requests(uuid):
    body = _curl(["-H", "Accept: application/json",
                  f"https://webhook.site/token/{uuid}/requests?sorting=newest"],
                 timeout=30)
    return json.loads(body).get("data", [])


def wh_post(uuid, payload, timeout=60):
    _curl(["-X", "POST", "-H", "Content-Type: application/json",
           f"https://webhook.site/{uuid}"],
          data=json.dumps(payload), timeout=timeout)


def load_seen():
    try:
        return set(json.load(open(SEEN_FILE)))
    except Exception:
        return set()


def save_seen(seen):
    json.dump(sorted(seen)[-500:], open(SEEN_FILE, "w"))


def latest_checkpoint():
    cks = glob.glob(os.path.join(BASE, "research", "checkpoints_*", "devryx_image_scratch.pt"))
    if not cks:
        return None
    return max(cks, key=os.path.getmtime)


def _coverage(im):
    """Fraction of pixels clearly above the dark background."""
    import numpy as np
    a = np.asarray(im, dtype=float)
    return float((a.max(axis=2) > 40).mean())


def sample_image(prompt, job_id):
    """Sample until a non-empty image appears (run 6 finding: some noise
    draws collapse to a blank frame; resampling with a fresh seed is the
    serving-side guard). Returns base64 PNG (upscaled x8)."""
    ckpt = latest_checkpoint()
    if not ckpt:
        raise RuntimeError("no checkpoint trained yet")
    from PIL import Image
    env = dict(os.environ, OMP_NUM_THREADS="2")
    best, best_cov = None, -1.0
    for attempt in range(5):
        seed = 1000 + attempt * 137
        out_png = f"/tmp/origin_job_{job_id}_{attempt}.png"
        r = subprocess.run(
            [os.path.join(BASE, ".research-venv", "bin", "python"),
             "-m", "research.image_model.sample",
             "--checkpoint", ckpt, "--prompt", prompt, "--seed", str(seed),
             "--out", out_png, "--device", "cpu"],
            cwd=BASE, capture_output=True, text=True, timeout=900, env=env)
        if r.returncode != 0:
            raise RuntimeError(f"sampler failed: {r.stderr.strip()[-200:]}")
        im = Image.open(out_png).convert("RGB")
        os.unlink(out_png)
        cov = _coverage(im)
        print(f"[origin] attempt {attempt} seed {seed} coverage {cov:.3f}", flush=True)
        if cov > best_cov:
            best, best_cov = im, cov
        if cov >= 0.05:
            break
    best = best.resize((best.width * 8, best.height * 8), Image.NEAREST)
    buf = io.BytesIO()
    best.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def handle(job):
    job_id = str(job.get("job_id", ""))
    prompt = str(job.get("prompt", "")).strip()
    if not job_id or not prompt:
        return
    print(f"[{job_id}] job: {prompt[:80]}", flush=True)
    try:
        wh_post(WH_R, {"job_id": job_id, "done": False, "status": "working"})
        img = sample_image(prompt, job_id)
        wh_post(WH_R, {"job_id": job_id, "done": True, "image": img})
        print(f"[{job_id}] done ({len(img)} b64 chars)", flush=True)
    except Exception as e:
        print(f"[{job_id}] error: {e}", flush=True)
        try:
            wh_post(WH_R, {"job_id": job_id, "done": True,
                           "error": "Origin is busy training. Try again in a moment."})
        except Exception:
            pass


def main():
    seen = load_seen()
    print(f"origin worker up; Q={WH_Q[:8]} R={WH_R[:8]}; seen={len(seen)}", flush=True)
    while True:
        try:
            reqs = wh_get_requests(WH_Q)
            for q in reversed(reqs):  # oldest first
                try:
                    body = json.loads(q.get("content") or "{}")
                except Exception:
                    continue
                jid = str(body.get("job_id", ""))
                if not jid or jid in seen:
                    continue
                seen.add(jid)
                save_seen(seen)
                handle(body)
        except Exception as e:
            print(f"poll error: {e}", flush=True)
        time.sleep(5)


if __name__ == "__main__":
    main()
