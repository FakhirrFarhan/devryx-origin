import json
from pathlib import Path
from PIL import Image
from torch.utils.data import Dataset
import torchvision.transforms as T


class CaptionedImageDataset(Dataset):
    def __init__(self, root, image_size=64):
        self.root = Path(root)
        manifest = self.root / "captions.jsonl"
        if not manifest.exists():
            raise FileNotFoundError(f"Missing dataset manifest: {manifest}")
        self.records = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.transform = T.Compose([
            T.Resize(image_size, interpolation=T.InterpolationMode.BICUBIC),
            T.CenterCrop(image_size),
            T.ToTensor(),
            T.Normalize([0.5] * 3, [0.5] * 3),
        ])

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):
        record = self.records[index]
        path = self.root / record["file"]
        with Image.open(path) as im:
            image = self.transform(im.convert("RGB"))
        return image, str(record["caption"])
