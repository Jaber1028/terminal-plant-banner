"""Draws banner files as one PNG, the way a dark terminal shows them.

    python render_ans.py <output.png> <banner.ans> [<banner.ans> ...] [--per N] [--scale N]

Each character cell is two pixels tall (half blocks), so a banner renders exactly as drawn.
"""
import re
import sys

from PIL import Image

BACK = (30, 30, 30)
token = re.compile(r"\x1b\[([0-9;]*)m|(.)", re.S)


def cells(path):
    """The banner as rows of pixels (RGB or None), two rows per text line."""
    rows = []
    for line in open(path, encoding="utf-8").read().split("\n"):
        top, bottom, fg, bg = [], [], None, None
        for code, ch in token.findall(line):
            if code is not None and ch == "":
                parts = [int(p) for p in code.split(";") if p] or [0]
                if parts[0] == 0:
                    fg = bg = None
                elif parts[:2] == [38, 2]:
                    fg = tuple(parts[2:5])
                elif parts[:2] == [48, 2]:
                    bg = tuple(parts[2:5])
                continue
            if ch == "▀":
                top.append(fg), bottom.append(bg)
            elif ch == "▄":
                top.append(bg), bottom.append(fg)
            else:
                top.append(bg), bottom.append(bg)
        rows += [top, bottom]
    while rows and not any(rows[-1]):
        rows.pop()
    while rows and not any(rows[0]):
        rows.pop(0)
    return rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    per = int(sys.argv[sys.argv.index("--per") + 1]) if "--per" in sys.argv else 99
    scale = int(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 6
    args = [a for a in args if not a.isdigit()]
    out, paths = args[0], args[1:]
    art = [cells(p) for p in paths]
    gap = 6
    lines = [art[i:i + per] for i in range(0, len(art), per)]
    widths = [sum(max(len(r) for r in a) + gap for a in line) + gap for line in lines]
    heights = [max(len(a) for a in line) + gap for line in lines]
    img = Image.new("RGB", (max(widths) * scale, (sum(heights) + gap) * scale), BACK)
    y0 = gap
    for line, h in zip(lines, heights):
        x0 = gap
        for a in line:
            w = max(len(r) for r in a)
            top = y0 + (h - gap - len(a))          # sit every plant on the same baseline
            for y, row in enumerate(a):
                for x, c in enumerate(row):
                    if c:
                        img.paste(c, ((x0 + x) * scale, (top + y) * scale,
                                      (x0 + x + 1) * scale, (top + y + 1) * scale))
            x0 += w + gap
        y0 += h
    img.save(out)
    print(out, img.size)


if __name__ == "__main__":
    main()
