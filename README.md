# DEVRYX AI — From-Scratch Research Platform

This is a **research and engineering starter**, not a trained generative AI product.
The interface is the cinematic liquid-glass creative studio. The backend is a local API
starter. The `research/image_model` directory contains an independently initialized,
small text-conditioned diffusion research model and a training pipeline.

## Non-negotiable model policy
- No hosted AI APIs.
- No downloaded pretrained model checkpoints.
- Model parameters are initialized randomly.
- Training uses datasets you own, create, or are properly licensed to use.
- PyTorch is used as a numerical/deep-learning framework, not as an AI service.
- The starter model is intentionally small for learning and pipeline validation. It will
  not produce Google Flow-level results. Large-scale quality requires major compute,
  curated data, extensive experiments and engineering.

## Project layout
- `frontend/` — Next.js liquid-glass creative studio interface.
- `backend/` — FastAPI development API.
- `research/image_model/` — our first randomly initialized text-conditioned diffusion model.
- `research/data/` — dataset format and preparation notes.
- `research/experiments/` — training configs and experiment notes.
- `docs/` — architecture, compute, data and milestone plans.

## Windows 11 setup
Install Python 3.12, Node.js LTS and Git. For GPU training, install the correct PyTorch
build for your exact NVIDIA GPU and CUDA driver using the official PyTorch installation
selector. Do not assume CUDA is available.

### 1. Start the frontend
```powershell
cd frontend
npm install
npm run dev
```
Open http://localhost:3000

### 2. Start the backend
```powershell
cd backend
py -3.12 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Set up the research environment
From the project root:
```powershell
py -3.12 -m venv .research-venv
.\\.research-venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r research/requirements.txt
```
For GPU training, replace the generic PyTorch install with the correct CUDA-enabled command
from the official PyTorch selector, then install the remaining requirements.

### 4. Prepare a dataset
Create your own dataset folder, for example `research/data/my_dataset/images/`.
Create `research/data/my_dataset/captions.jsonl`, one JSON object per line:
```json
{"file":"images/sample001.jpg","caption":"A red bicycle leaning against a brick wall"}
```
Use only images you created, have permission to use, or are licensed for your intended use.
Keep provenance and license records. Never scrape private or copyrighted datasets without rights.

### 5. Run a tiny smoke test
```powershell
python -m research.image_model.train --data research/data/my_dataset --steps 10 --batch-size 1 --image-size 64 --device cpu
```
This checks that the data/model/training loop works. It does not create a useful commercial model.
For actual experiments use a CUDA GPU and substantially more data/compute.

## Important model limitations
The first research model is a compact educational diffusion baseline:
- randomly initialized byte-level text embedding and pooled text conditioning;
- randomly initialized convolutional U-Net denoiser;
- simple noise-prediction objective and a basic sampler;
- no pretrained weights or external inference calls.

It is a foundation for experiments, not a state-of-the-art architecture. Do not advertise it as a competitive
image or video generator until it has been trained, evaluated and validated.

## Next milestones
1. Inspect hardware (GPU model/VRAM, RAM, CPU and free disk).
2. Build a clean, licensed, captioned dataset and data-quality pipeline.
3. Establish repeatable experiments, checkpoints, metrics and evaluation.
4. Improve the image model architecture and training scale.
5. Build a robust inference service and connect it to the studio.
6. Research video generation only after the image pipeline is technically sound.
7. Add authentication, database, queues, safety systems, monitoring and production deployment.
