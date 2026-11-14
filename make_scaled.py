"""Writes out/x2-<name>.ans and out/x3-<name>.ans for every out/big-<name>.ans: the same art with
each pixel drawn 2 or 3 times as wide and tall, so a single plant can fill a big window.
Whole-number scaling keeps pixel art crisp; the garden never uses these, so one plant on its own
is always bigger than the same plant in the garden."""
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
    for k in (2, 3):
        scaled = []
        for row in grid:
            wide = [c for c in row for _ in range(k)]
            scaled += [list(wide) for _ in range(k)]
        name = os.path.basename(path).replace("big-", f"x{k}-")
        with open(os.path.join(here, "out", name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text(scaled))
    count += 1
print(count, "plants written at 2x and 3x")
