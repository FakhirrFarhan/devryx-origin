# Own-model policy

The goal is to create and train our own models from random initialization.
We do not download pretrained checkpoints or call third-party AI inference APIs.

Permitted engineering foundations include programming languages, CUDA, PyTorch, NumPy,
Pillow and other ordinary software libraries. Using a deep-learning framework does not
mean using someone else's trained model.

For every training run, record:
- model architecture revision and source commit;
- dataset version, provenance, licenses and preprocessing;
- random seed and initialization method;
- optimizer, learning rate, schedule, batch size and image resolution;
- hardware, runtime, checkpoint hash and validation results.

A model is not "ours" merely because we fine-tuned it. The initial weights in this project
are randomly initialized and the training pipeline starts from scratch.
