# Dataset format

Create a dataset folder containing:
- `images/` with your image files;
- `captions.jsonl` with one JSON object per line.

Example:
```json
{"file":"images/000001.jpg","caption":"A small ceramic vase on a wooden table"}
{"file":"images/000002.png","caption":"A mountain lake under a cloudy sky"}
```

Maintain a separate provenance spreadsheet containing source, creator, license, consent
where relevant, collection date and allowed uses. Remove duplicates and corrupted images.
Keep validation data separate. Do not use private, sensitive or unlicensed material.
