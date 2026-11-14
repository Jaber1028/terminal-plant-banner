"""Puts a reference picture (scaled up, no smoothing) next to its converted banner, for checking."""
import sys

from PIL import Image

from render_ans import cells

src, banner, out = sys.argv[1], sys.argv[2], sys.argv[3]
ref = Image.open(src).convert("RGB")
grid = cells(banner)
w = max(len(r) for r in grid)
scale = 8
art = Image.new("RGB", (w * scale, len(grid) * scale), (30, 30, 30))
for y, row in enumerate(grid):
    for x, c in enumerate(row):
        if c:
            art.paste(c, (x * scale, y * scale, (x + 1) * scale, (y + 1) * scale))
k = art.height / ref.height
ref = ref.resize((int(ref.width * k), art.height), Image.NEAREST)
sheet = Image.new("RGB", (ref.width + art.width + 20, art.height), (30, 30, 30))
sheet.paste(ref, (0, 0))
sheet.paste(art, (ref.width + 20, 0))
sheet.save(out)
