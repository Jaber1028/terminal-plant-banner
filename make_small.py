"""Shrinks every out/big-<name>.ans by one shared factor into out/s<percent>-<name>.ans.

    python make_small.py --factor 0.5      (writes out/s50-*.ans)

Every plant is shrunk by the same amount, so a garden keeps the plants' real sizes relative to
each other. The shrink is a smooth resize whose pixels are then snapped back to the plant's own
colours, so no new, muddy colours appear.
"""
import glob
import os
import sys

from make_banner import fg, bg, ESC
from render_ans import cells

here = os.path.dirname(os.path.abspath(__file__))


def arg(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


FACTOR = arg("--factor", 0.5)


def shrink(grid):
    from PIL import Image
    h = len(grid)
    w = max(len(r) for r in grid)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y, r in enumerate(grid):
        for x, c in enumerate(r):
            if c:
                img.putpixel((x, y), c + (255,))
    palette = list({c for r in grid for c in r if c})
    nw, nh = max(1, round(w * FACTOR)), max(1, round(h * FACTOR))
    # premultiplied so see-through pixels don't drag black into the edges
    small = img.convert("RGBa").resize((nw, nh), Image.Resampling.LANCZOS).convert("RGBA")
    out = []
    for y in range(nh):
        row = []
        for x in range(nw):
            r, g, b, a = small.getpixel((x, y))
            if a < 80:          # keep edge pixels, so outlines don't break into gaps
                row.append(None)
                continue
            row.append(min(palette, key=lambda p: (p[0] - r) ** 2 * 3 + (p[1] - g) ** 2 * 4 + (p[2] - b) ** 2 * 2))
        out.append(row)
    return out


def text(grid):
    if len(grid) % 2:
        grid = [[None] * len(grid[0])] + grid
    reset = f"{ESC}[0m"
    lines = []
    for y in range(0, len(grid), 2):
        parts = []
        for top, bottom in zip(grid[y], grid[y + 1]):
            if top is None and bottom is None:
                parts.append(reset + " ")
            elif bottom is None:
                parts.append(reset + fg(top) + "▀")
            elif top is None:
                parts.append(reset + fg(bottom) + "▄")
            else:
                parts.append(fg(top) + bg(bottom) + "▀")
        lines.append("".join(parts) + reset)
    return "\n".join(lines) + "\n"


def main():
    count = 0
    tag = f"s{round(FACTOR * 100)}"
    for path in sorted(glob.glob(os.path.join(here, "out", "big-*.ans"))):
        name = os.path.basename(path).replace("big-", f"{tag}-")
        with open(os.path.join(here, "out", name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text(shrink(cells(path))))
        count += 1
    print(f"{count} plants shrunk to {round(FACTOR * 100)}%")


if __name__ == "__main__":
    main()
