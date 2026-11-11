# Hardware check

Before downloading datasets or attempting serious training, collect:
- exact GPU name and VRAM;
- NVIDIA driver version and CUDA capability, if applicable;
- system RAM;
- CPU model and core count;
- free SSD storage;
- laptop thermal and power limits.

A small CPU smoke test is possible, but meaningful image-model training is generally GPU
intensive. High-quality image models trained from scratch need large datasets and substantial
GPU time. Video generation is considerably more demanding. Do not promise a local laptop
can train a frontier-quality model.
