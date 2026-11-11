# From-scratch roadmap

## Phase 0 — Hardware and feasibility
Record exact GPU, VRAM, RAM, CPU, storage and power/thermal limits. Decide whether local
experiments are feasible or whether dedicated owned/leased compute will be required.

## Phase 1 — Data foundation
Build a rights-cleared image-caption dataset. Validate files, dimensions, duplicates,
caption quality, provenance, licensing and train/validation splits.

## Phase 2 — First research image model
Train the small random-init baseline to validate the end-to-end loop. This is a learning
milestone, not a product-quality milestone. Track loss, sample grids, failure cases and
reproducibility.

## Phase 3 — Architecture research and scale
Experiment with latent representations, stronger text encoders trained from scratch,
diffusion objectives, attention, optimizers and efficient training. Any autoencoder or
text encoder must also be trained from random initialization if the no-pretrained rule
continues to apply.

## Phase 4 — Product inference
Implement checkpoint versioning, model registry, inference workers, request validation,
resource limits, queueing and output storage. Connect only our own trained checkpoints.

## Phase 5 — Video research
Develop a video model from scratch only after the image/data/training stack is stable.
Video models require much more data, memory and compute than the initial image baseline.

## Phase 6 — Production platform
Authentication, database, queue, moderation, observability, backups, deployment and
security hardening.
