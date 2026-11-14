"""Writes out/x2-<name>.ans and out/x3-<name>.ans for every out/big-<name>.ans, so a single plant
can fill a big window. The garden never uses these, so a plant on its own is always the bigger one.

Plain enlarging only makes each pixel a bigger square: the stair-steps on curves and diagonals get
louder. Scale2x / Scale3x (the EPX family, made for pixel art) fill those steps in where two
neighbouring edges agree, so curves come out smoother at 2x and 3x. They never invent new colours,
so the art stays crisp.
"""
import glob
import os

from make_small import text
from render_ans import cells

here = os.path.dirname(os.path.abspath(__file__))


def at(grid, y, x):
    y = min(max(y, 0), len(grid) - 1)
    x = min(max(x, 0), len(grid[0]) - 1)
    return grid[y][x]


def scale2x(grid):
    out = []
    for y in range(len(grid)):
        top, bottom = [], []
        for x in range(len(grid[0])):
            e = grid[y][x]
            b, d, f, h = at(grid, y - 1, x), at(grid, y, x - 1), at(grid, y, x + 1), at(grid, y + 1, x)
            top += [d if d == b and b != f and d != h else e,
                    f if b == f and b != d and f != h else e]
            bottom += [d if d == h and d != b and h != f else e,
                       f if h == f and d != h and b != f else e]
        out += [top, bottom]
    return out


def scale3x(grid):
    out = []
    for y in range(len(grid)):
        rows = [[], [], []]
        for x in range(len(grid[0])):
            a, b, c = at(grid, y - 1, x - 1), at(grid, y - 1, x), at(grid, y - 1, x + 1)
            d, e, f = at(grid, y, x - 1), grid[y][x], at(grid, y, x + 1)
            g, h, i = at(grid, y + 1, x - 1), at(grid, y + 1, x), at(grid, y + 1, x + 1)
            if b != h and d != f:
                e0 = d if d == b else e
                e1 = b if (d == b and e != c) or (b == f and e != a) else e
                e2 = f if b == f else e
                e3 = d if (d == b and e != g) or (d == h and e != a) else e
                e5 = f if (b == f and e != i) or (h == f and e != c) else e
                e6 = d if d == h else e
                e7 = h if (d == h and e != i) or (h == f and e != g) else e
                e8 = f if h == f else e
            else:
                e0 = e1 = e2 = e3 = e5 = e6 = e7 = e8 = e
            rows[0] += [e0, e1, e2]
            rows[1] += [e3, e, e5]
            rows[2] += [e6, e7, e8]
        out += rows
    return out


count = 0
for path in sorted(glob.glob(os.path.join(here, "out", "big-*.ans"))):
    grid = cells(path)
    width = max(len(r) for r in grid)
    grid = [r + [None] * (width - len(r)) for r in grid]
    for k, scale in ((2, scale2x), (3, scale3x)):
        name = os.path.basename(path).replace("big-", f"x{k}-")
        with open(os.path.join(here, "out", name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text(scale(grid)))
    count += 1
print(count, "plants written at 2x and 3x (Scale2x / Scale3x)")
