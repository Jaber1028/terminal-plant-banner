"""Cuts a sprite sheet into one picture per sprite: refs/sheet/NN.png, plus refs/sheet/index.png
with each sprite's number drawn on it, for naming.

    python split_sheet.py <sheet.png> [--join 6] [--min 900]

Sprites are found as islands of non-background pixels; islands closer than --join pixels are
treated as one sprite (sparkles, separate leaves), and anything under --min pixels is dropped.
"""
import os
import sys
from collections import Counter, deque

from PIL import Image, ImageDraw

here = os.path.dirname(os.path.abspath(__file__))


def arg(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


src = sys.argv[1]
join, smallest = arg("--join", 6), arg("--min", 900)
img = Image.open(src).convert("RGB")
w, h = img.size
px = img.load()
# sampled a little inside the edge: a sheet may have a thin frame around it
edge = [px[x, y] for x in range(w) for y in (12, h - 13)] + [px[x, y] for y in range(h) for x in (12, w - 13)]
ground = Counter(edge).most_common(1)[0][0]


def solid(c):
    return abs(c[0] - ground[0]) + abs(c[1] - ground[1]) + abs(c[2] - ground[2]) > 24


border = 8           # ignore the frame, or every sprite near it joins one giant island
fill = [[border <= x < w - border and border <= y < h - border and solid(px[x, y]) for x in range(w)]
        for y in range(h)]
seen = [[False] * w for _ in range(h)]
boxes = []
for sy in range(h):
    for sx in range(w):
        if not fill[sy][sx] or seen[sy][sx]:
            continue
        queue, count = deque([(sx, sy)]), 0
        seen[sy][sx] = True
        x0 = x1 = sx
        y0 = y1 = sy
        while queue:
            x, y = queue.popleft()
            count += 1
            x0, x1, y0, y1 = min(x0, x), max(x1, x), min(y0, y), max(y1, y)
            for ny in range(max(0, y - join), min(h, y + join + 1)):
                for nx in range(max(0, x - join), min(w, x + join + 1)):
                    if fill[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        queue.append((nx, ny))
        if count >= smallest:
            boxes.append((x0, y0, x1 + 1, y1 + 1, count))

# a frame line around the whole sheet would be one huge island: drop anything near sheet size
boxes = [b for b in boxes if (b[2] - b[0]) < w * 0.6 and (b[3] - b[1]) < h * 0.6]
boxes.sort(key=lambda b: (round(b[1] / 120), b[0]))
out = os.path.join(here, "refs", "sheet")
os.makedirs(out, exist_ok=True)
index = img.copy()
draw = ImageDraw.Draw(index)
for n, (x0, y0, x1, y1, count) in enumerate(boxes, 1):
    pad = 8
    crop = Image.new("RGB", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), ground)
    crop.paste(img.crop((x0, y0, x1, y1)), (pad, pad))
    # wipe pixels of neighbouring sprites that fall inside this box
    cp = crop.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            pass
    crop.save(os.path.join(out, f"{n:02d}.png"))
    draw.rectangle((x0, y0, x1, y1), outline=(255, 0, 0))
    draw.rectangle((x0, y0, x0 + 26, y0 + 18), fill=(0, 0, 0))
    draw.text((x0 + 3, y0 + 3), f"{n:02d}", fill=(255, 255, 255))
index.save(os.path.join(out, "index.png"))
print(len(boxes), "sprites; background", ground)
