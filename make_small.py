"""Shrinks every out/big-*.ans into out/small-*.ans for `plants garden`.

Five small plants side by side take about the room of two big ones. Each is fitted into a box
of WIDTH columns by HEIGHT pixels (two pixels per text line), keeping its proportions.

    python make_small.py [--width 20] [--height 28]

Shrinking pixel art by averaging blurs it, so each small pixel takes the commonest colour of
the block it covers instead; dark outline pixels get a little extra weight so the edges survive.
"""
import glob
import os
import sys
from collections import Counter

from make_banner import fg, bg, ESC
from render_ans import cells

here = os.path.dirname(os.path.abspath(__file__))


def arg(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


WIDTH, HEIGHT = arg("--width", 20), arg("--height", 28)
# --factor 0.5: shrink every plant by the same amount instead of fitting it into a box, so a
# garden keeps the plants' real sizes relative to each other (out/s50-<name>.ans)
FACTOR = arg("--factor", 0.0)


def shrink(grid):
    h = len(grid)
    w = max(len(r) for r in grid)
    grid = [r + [None] * (w - len(r)) for r in grid]
    scale = FACTOR or min(WIDTH / w, HEIGHT / h, 1.0)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    out = []
    for y in range(nh):
        y0, y1 = int(y * h / nh), max(int(y * h / nh) + 1, int((y + 1) * h / nh))
        row = []
        for x in range(nw):
            x0, x1 = int(x * w / nw), max(int(x * w / nw) + 1, int((x + 1) * w / nw))
            block = [grid[yy][xx] for yy in range(y0, y1) for xx in range(x0, x1)]
            solid = [c for c in block if c]
            if len(solid) * 2 < len(block):          # mostly see-through: leave it see-through
                row.append(None)
                continue
            votes = Counter()
            for c in solid:
                votes[c] += 1.6 if max(c) < 90 else 1.0   # keep outlines and eyes
            row.append(votes.most_common(1)[0][0])
        out.append(row)
    return out


def shrink_smooth(grid):
    """Smooth resize, then snap every pixel back to the plant's own colours (no new, muddy ones)."""
    from PIL import Image
    h = len(grid)
    w = max(len(r) for r in grid)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y, r in enumerate(grid):
        for x, c in enumerate(r):
            if c:
                img.putpixel((x, y), c + (255,))
    palette = list({c for r in grid for c in r if c})
    scale = FACTOR or min(WIDTH / w, HEIGHT / h, 1.0)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
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
    for path in sorted(glob.glob(os.path.join(here, "out", "big-*.ans"))):
        small = (shrink if "--blocks" in sys.argv else shrink_smooth)(cells(path))
        name = os.path.basename(path).replace("big-", f"s{round(FACTOR * 100)}-" if FACTOR else f"small{WIDTH}-")
        with open(os.path.join(here, "out", name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text(small))
        count += 1
    print(f"{count} small plants written, each at most {WIDTH} columns by {HEIGHT // 2} lines")


if __name__ == "__main__":
    main()
