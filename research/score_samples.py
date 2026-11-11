"""Score generated samples objectively: did a non-background shape appear,
and is its dominant color the one the prompt asked for?

Usage: score_samples.py <samples_dir>
Expects files named sample_<color>_<seed>.png in the directory.
Prints one line per sample plus a per-color summary, and writes a
contact-sheet montage to <samples_dir>/contact_sheet.png.
"""
import sys
from pathlib import Path

from PIL import Image

TARGETS = {
    "red": (214, 69, 65),
    "blue": (66, 103, 214),
    "green": (72, 178, 105),
    "amber": (232, 168, 56),
}


def classify(mean_rgb):
    r, g, b = mean_rgb
    dists = {name: sum((a - c) ** 2 for a, c in zip(mean_rgb, rgb)) ** 0.5
             for name, rgb in TARGETS.items()}
    return min(dists, key=dists.get)


def main():
    d = Path(sys.argv[1])
    files = sorted(d.glob("sample_*_*.png"))
    if not files:
        print("no sample_<color>_<seed>.png files found")
        return
    hits = {}
    totals = {}
    results = {}
    thumbs = []
    for f in files:
        want = f.stem.split("_")[1]
        im = Image.open(f).convert("RGB")
        px = list(im.getdata())
        bright = [p for p in px if max(p) > 90]
        coverage = len(bright) / len(px)
        if coverage < 0.01:
            got, mean = "EMPTY", (0, 0, 0)
        else:
            mean = tuple(sum(p[i] for p in bright) / len(bright) for i in range(3))
            got = classify(mean)
        ok = got == want
        results[f.name] = {"want": want, "got": got, "coverage": round(coverage, 3), "ok": ok}
        totals[want] = totals.get(want, 0) + 1
        hits[want] = hits.get(want, 0) + (1 if ok else 0)
        print(f"{f.name}: want={want} got={got} coverage={coverage:.2f} "
              f"meanRGB=({mean[0]:.0f},{mean[1]:.0f},{mean[2]:.0f}) {'OK' if ok else 'MISS'}")
        thumbs.append((f.name, im.resize((64, 64))))
    print("---")
    for color in sorted(totals):
        print(f"{color}: {hits[color]}/{totals[color]} color-correct")
    total_ok = sum(hits.values())
    total_n = sum(totals.values())
    print(f"TOTAL: {total_ok}/{total_n} color-correct")
    import json as _json
    summary = {"total_ok": total_ok, "total_n": total_n,
               "per_color": {c: [hits[c], totals[c]] for c in sorted(totals)},
               "files": results}
    (d / "scores.json").write_text(_json.dumps(summary, indent=1))
    cols = 4
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 64, rows * 64), (10, 10, 10))
    for idx, (_, im) in enumerate(thumbs):
        sheet.paste(im, ((idx % cols) * 64, (idx // cols) * 64))
    sheet = sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST)
    sheet.save(d / "contact_sheet.png")
    print(f"contact sheet: {d / 'contact_sheet.png'}")


if __name__ == "__main__":
    main()
