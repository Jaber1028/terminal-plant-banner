"""Writes out/double-<name>.ans for every out/big-<name>.ans: the same art with every pixel
drawn twice as wide and twice as tall, so a single plant can fill a big window and stay crisp."""
import glob
import os

from make_small import text
from render_ans import cells

here = os.path.dirname(os.path.abspath(__file__))
count = 0
for path in sorted(glob.glob(os.path.join(here, "out", "big-*.ans"))):
    grid = cells(path)
    width = max(len(r) for r in grid)
    grid = [r + [None] * (width - len(r)) for r in grid]
    double = []
    for row in grid:
        wide = [c for c in row for _ in (0, 1)]
        double += [wide, list(wide)]
    name = os.path.basename(path).replace("big-", "double-")
    with open(os.path.join(here, "out", name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text(double))
    count += 1
print(count, "double-size plants written")
