# Experiment 007 — first GPU run (Kaggle Tesla T4)

- Date: Nov 15, 2026
- Kernel: fakhirfarhan/devryx-origin-train, Version 4 (website editor, Accelerator GPU T4 x2)
- Dataset: v0.3 (research/data/tiny_shapes3, 1,200 images)
- Config: 15,000 steps, batch 32, image-size 64, lr 3e-4, device cuda
- Hardware: Tesla T4 (torch 2.11.0+cu130, cuda_available: True)
- Runtime: ~25 min training, final loss ~0.0036
- Checkpoint: research/checkpoints_gpu_v4/devryx_image_scratch.pt (8.3 MB, md5 b010d9d195fcbd3c45e66782945e4ed6; checkpoints stay out of git)
- Eval: 12 seeded samples (3 prompts x 4 seeds, generated on the GPU), scored with research/score_samples.py

## Score: 11/12 color-correct (run 6: 4/12)

- blue 4/4, red 4/4, green 3/4
- Only miss: green seed 11, blank draw (coverage 0.00)
- Red finally stays red (no amber drift); coverages mostly 0.24–0.81

## Notes

- The blank-draw failure is nearly gone, not just worked around: 11/12 draws
  formed a shape, vs about half blank in run 6.
- The live serving worker picks this checkpoint up automatically (newest
  research/checkpoints_* by mtime).
- Next: the v0.4 dataset (10,000 images, 10 colors x 8 shapes) with the
  run-6 embedding transplant is ready for the following run.
