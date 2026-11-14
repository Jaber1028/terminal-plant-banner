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


def resize_pillow(grid, w, h, nw, nh):
    """Lanczos resize with Pillow: RGBA pixels, premultiplied so see-through pixels don't drag
    black into the edges."""
    from PIL import Image
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y, r in enumerate(grid):
        for x, c in enumerate(r):
            if c:
                img.putpixel((x, y), c + (255,))
    small = img.convert("RGBa").resize((nw, nh), Image.Resampling.LANCZOS).convert("RGBA")
    return [[small.getpixel((x, y)) for x in range(nw)] for y in range(nh)]


def resize_plain(grid, w, h, nw, nh):
    """The same job in plain Python, for systems without Pillow: each new pixel is the
    area-weighted average of the source pixels it covers (premultiplied, as above)."""
    sx, sy = w / nw, h / nh
    out = []
    for oy in range(nh):
        y0, y1 = oy * sy, (oy + 1) * sy
        row = []
        for ox in range(nw):
            x0, x1 = ox * sx, (ox + 1) * sx
            tr = tg = tb = ta = 0.0
            for y in range(int(y0), min(h, int(y1 + 0.999999))):
                wy = min(y + 1, y1) - max(y, y0)
                for x in range(int(x0), min(w, int(x1 + 0.999999))):
                    c = grid[y][x]
                    if c is None:
                        continue
                    weight = wy * (min(x + 1, x1) - max(x, x0))
                    tr += c[0] * weight
                    tg += c[1] * weight
                    tb += c[2] * weight
                    ta += weight
            if ta:
                row.append((tr / ta, tg / ta, tb / ta, 255 * ta / (sx * sy)))
            else:
                row.append((0, 0, 0, 0))
        out.append(row)
    return out


def shrink(grid):
    h = len(grid)
    w = max(len(r) for r in grid)
    grid = [r + [None] * (w - len(r)) for r in grid]
    palette = list({c for r in grid for c in r if c})
    nw, nh = max(1, round(w * FACTOR)), max(1, round(h * FACTOR))
    try:
        small = resize_pillow(grid, w, h, nw, nh)
    except ImportError:
        small = resize_plain(grid, w, h, nw, nh)
    out = []
    for line in small:
        row = []
        for r, g, b, a in line:
            if a < 80:          # keep edge pixels, so outlines don't break into gaps
                row.append(None)
                continue
            # snap back to the plant's own colours, so no new, muddy ones appear
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
