"""Turns ordinary artwork (a drawing or render, not pixel art) into pixel-art banners:
out/big-<name>.ans. For real pixel art use from_image.py, which keeps every pixel.

    python3 from_art.py <picture> <name> [<name> ...] [--height 68] [--colors 32] [--flip] [--png]

The background (plain, or the light checkerboard of a "transparent" screenshot) is removed from
the edges inward. Each separate figure in the picture becomes one banner; give one name per figure,
left to right, and use - to skip one. Each figure is shrunk to --height pixels tall and its
colours reduced, which is what makes it read as pixel art. --flip mirrors it.
"""
import os
import sys
from collections import Counter, deque

from PIL import Image, ImageEnhance, ImageFilter

from make_small import text

here = os.path.dirname(os.path.abspath(__file__))


def arg(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


def main():
    flags_with_value = ("--height", "--colors", "--min")
    plain, skip = [], False
    for a in sys.argv[1:]:
        if skip:
            skip = False
        elif a in flags_with_value:
            skip = True
        elif not a.startswith("--") or a == "-":
            plain.append(a)
    src, names = plain[0], plain[1:]
    height, colors = arg("--height", 68), arg("--colors", 32)
    raw = Image.open(src)
    # A picture with real transparency says exactly where its background is: use that, and guess
    # nothing from colours (a white bucket or a black hat would otherwise look like background).
    clear = None
    if "A" in raw.getbands() or "transparency" in raw.info:
        alpha = raw.convert("RGBA").getchannel("A")
        alpha = alpha.crop((6, 6, alpha.width - 6, alpha.height - 6))
        if alpha.getextrema()[0] < 128:
            clear = alpha.tobytes()
    img = raw.convert("RGB")
    img = img.crop((6, 6, img.width - 6, img.height - 6))       # screenshot frames and edge specks
    w, h = img.size
    px = img.load()
    edge = [px[x, y] for x in range(w) for y in (0, h - 1)] + [px[x, y] for y in range(h) for x in (0, w - 1)]
    ground = Counter(edge).most_common(1)[0][0]

    def backdrop(c):
        near = abs(c[0] - ground[0]) + abs(c[1] - ground[1]) + abs(c[2] - ground[2]) < 40
        pale = min(c) > 195 and max(c) - min(c) < 14           # checkerboard squares, paper white
        return near or pale

    # background = backdrop-coloured pixels reachable from the edge
    back = bytearray(w * h)
    queue = deque()
    for x in range(w):
        queue.extend(((x, 0), (x, h - 1)))
    for y in range(h):
        queue.extend(((0, y), (w - 1, y)))
    while queue:
        x, y = queue.popleft()
        if not (0 <= x < w and 0 <= y < h) or back[y * w + x] or not backdrop(px[x, y]):
            continue
        back[y * w + x] = 1
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    # Background trapped inside a figure (between legs, under an arm): a sizeable patch of
    # backdrop colour the flood couldn't reach. It counts as background only when nearly all of it
    # is in the very colours the real background is made of (both tones of a checkerboard, say), so
    # a pale shirt or the white of an eye, which are other colours, is never mistaken for it.
    # Those colours are read from the background the flood found, not from the picture's edge: a
    # screenshot can have a dark frame there that says nothing about it.
    found_back = Counter()
    for i in range(0, w * h, 7):
        if back[i]:
            c = px[i % w, i // w]
            found_back[(c[0] // 2, c[1] // 2, c[2] // 2)] += 1
    total = sum(found_back.values()) or 1
    real = set()
    for (r, g, b), n in found_back.items():
        if n > 0.004 * total:
            real.update((r + dr, g + dg, b + db) for dr in (-1, 0, 1) for dg in (-1, 0, 1) for db in (-1, 0, 1))
    seen = bytearray(w * h)
    for sy in range(h):
        for sx in range(w):
            i = sy * w + sx
            if back[i] or seen[i] or not backdrop(px[sx, sy]):
                continue
            seen[i] = 1
            todo, patch, matching, near_ground = deque([(sx, sy)]), [], 0, 0
            while todo:
                x, y = todo.popleft()
                patch.append(y * w + x)
                c = px[x, y]
                matching += (c[0] // 2, c[1] // 2, c[2] // 2) in real
                near_ground += abs(c[0] - ground[0]) + abs(c[1] - ground[1]) + abs(c[2] - ground[2]) < 18
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not back[ny * w + nx] and not seen[ny * w + nx] and backdrop(px[nx, ny]):
                        seen[ny * w + nx] = 1
                        todo.append((nx, ny))
            if len(patch) < 0.0002 * w * h:
                continue
            # (a plain but grainy background varies too much to match colour for colour: there,
            # being mostly close to the background colour is enough)
            if matching > 0.8 * len(patch) or near_ground > 0.5 * len(patch):
                for i in patch:
                    back[i] = 1

    if clear is not None:
        back = bytearray(1 if a < 128 else 0 for a in clear)

    # figures: islands of what is left, found on a coarse grid so near-touching parts stay together
    cell = 4
    gw, gh = (w + cell - 1) // cell, (h + cell - 1) // cell
    solid = [[any(not back[yy * w + xx] for yy in range(gy * cell, min(h, gy * cell + cell))
                  for xx in range(gx * cell, min(w, gx * cell + cell))) for gx in range(gw)] for gy in range(gh)]
    label = [[0] * gw for _ in range(gh)]
    figures = []
    for sy in range(gh):
        for sx in range(gw):
            if not solid[sy][sx] or label[sy][sx]:
                continue
            n = len(figures) + 1
            label[sy][sx] = n
            todo, cells = deque([(sx, sy)]), []
            while todo:
                x, y = todo.popleft()
                cells.append((x, y))
                for ny in range(max(0, y - 1), min(gh, y + 2)):
                    for nx in range(max(0, x - 1), min(gw, x + 2)):
                        if solid[ny][nx] and not label[ny][nx]:
                            label[ny][nx] = n
                            todo.append((nx, ny))
            figures.append((n, cells))
    smallest = arg("--min", 0) or max(len(c) for _, c in figures) * 0.2
    figures = [f for f in figures if len(f[1]) >= smallest]
    figures.sort(key=lambda f: min(x for x, _ in f[1]))
    print(f"{len(figures)} figure(s) found; background {ground}")
    os.makedirs(os.path.join(here, "out"), exist_ok=True)

    for (n, cells), name in zip(figures, names):
        if name == "-":
            continue
        x0, x1 = min(x for x, _ in cells) * cell, min(w, (max(x for x, _ in cells) + 1) * cell)
        y0, y1 = min(y for _, y in cells) * cell, min(h, (max(y for _, y in cells) + 1) * cell)
        cut = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
        cp = cut.load()
        for y in range(y0, y1):
            for x in range(x0, x1):
                if not back[y * w + x] and label[y // cell][x // cell] == n:
                    cp[x - x0, y - y0] = px[x, y] + (255,)
        # shave the pale fringe the background leaves around the outline
        alpha = cut.getchannel("A").filter(ImageFilter.MinFilter(3))
        cut.putalpha(alpha)
        # loose bits near the figure but not touching it (a handwritten note, a stray stroke) go:
        # only pieces at least 3% the size of the biggest piece stay
        cw, ch = cut.size
        ap = alpha.load()
        piece = [0] * (cw * ch)
        sizes = [0]
        for sy in range(ch):
            for sx in range(cw):
                if not ap[sx, sy] or piece[sy * cw + sx]:
                    continue
                sizes.append(0)
                k = len(sizes) - 1
                piece[sy * cw + sx] = k
                todo = deque([(sx, sy)])
                while todo:
                    x, y = todo.popleft()
                    sizes[k] += 1
                    for ny in range(max(0, y - 1), min(ch, y + 2)):
                        for nx in range(max(0, x - 1), min(cw, x + 2)):
                            if ap[nx, ny] and not piece[ny * cw + nx]:
                                piece[ny * cw + nx] = k
                                todo.append((nx, ny))
        keep = max(sizes) * 0.03
        for y in range(ch):
            for x in range(cw):
                if ap[x, y] and sizes[piece[y * cw + x]] < keep:
                    ap[x, y] = 0
        cut.putalpha(alpha)
        box = alpha.getbbox()
        if box:
            cut = cut.crop(box)
        if "--flip" in sys.argv:
            cut = cut.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        nh = height
        nw = max(1, round(cut.width * nh / cut.height))
        small = cut.convert("RGBa").resize((nw, nh), Image.Resampling.LANCZOS).convert("RGBA")
        # shrinking washes a drawing out: put back some contrast and colour so it reads as pixel art
        rgb = ImageEnhance.Color(ImageEnhance.Contrast(small.convert("RGB")).enhance(1.25)).enhance(1.25)
        small = Image.merge("RGBA", (*rgb.split(), small.getchannel("A")))
        flat = small.convert("RGB").quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
        grid = [[flat.getpixel((x, y)) if small.getpixel((x, y))[3] >= 110 else None for x in range(nw)]
                for y in range(nh)]
        with open(os.path.join(here, "out", f"big-{name}.ans"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n" + text(grid) + "\n")
        if "--png" in sys.argv:
            scale = 6
            check = Image.new("RGB", (nw * scale, nh * scale), (30, 30, 30))
            for y, row in enumerate(grid):
                for x, c in enumerate(row):
                    if c:
                        check.paste(c, (x * scale, y * scale, (x + 1) * scale, (y + 1) * scale))
            check.save(os.path.join(here, f"check-{name}.png"))
        print(f"big-{name}.ans: {nw} x {nh} pixels")


if __name__ == "__main__":
    main()
