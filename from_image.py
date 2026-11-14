"""Turns a pixel-art picture into a terminal banner: out/big-<name>.ans

    python from_image.py <picture> <name> [--pitch N] [--tol N] [--colors N] [--png]

The picture should be pixel art on a plain background (a screenshot is fine).
The background is taken from the corners and made see-through; the art is
shrunk back to one terminal pixel per art pixel. --pitch sets the size of one
art pixel in the picture if the automatic guess is off; --png writes a check
image next to the banner.
"""
import os
import sys
from collections import Counter, deque

from PIL import Image

from make_banner import fg, bg, ESC

MARGIN = 2
LAWN = [(64, 150, 50), (88, 176, 62)]


def arg(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


def far(a, b, tol):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]) > tol


def border_colour(img):
    """The background: the most common colour around the picture's edge (a stray speck in a
    corner must not count, or black outlines get treated as background)."""
    w, h = img.size
    px = img.load()
    edge = [px[x, y] for x in range(w) for y in (0, h - 1)] + [px[x, y] for y in range(h) for x in (0, w - 1)]
    return Counter(edge).most_common(1)[0][0]


def background_mask(img, tol):
    """True where the pixel is background: flood from every edge pixel that matches a corner."""
    w, h = img.size
    px = img.load()
    corners = [border_colour(img)]
    mask = [[False] * w for _ in range(h)]
    queue = deque()
    for x in range(w):
        queue.extend(((x, 0), (x, h - 1)))
    for y in range(h):
        queue.extend(((0, y), (w - 1, y)))
    while queue:
        x, y = queue.popleft()
        if not (0 <= x < w and 0 <= y < h) or mask[y][x]:
            continue
        if all(far(px[x, y], c, tol) for c in corners):
            continue
        mask[y][x] = True
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return mask


def edge_profiles(img, box):
    """Colour-change strength between each picture column (and row) and the one before it."""
    x0, y0, x1, y1 = box
    px = img.load()
    cols = [0.0] * (x1 - x0 + 1)
    rows = [0.0] * (y1 - y0 + 1)
    for y in range(y0, y1):
        for x in range(x0 + 1, x1):
            cols[x - x0] += sum(abs(px[x, y][i] - px[x - 1, y][i]) for i in range(3))
    for x in range(x0, x1):
        for y in range(y0 + 1, y1):
            rows[y - y0] += sum(abs(px[x, y][i] - px[x, y - 1][i]) for i in range(3))
    return cols, rows


def boundaries(line, pitch):
    """Where art-pixel edges really fall along one axis. Screenshots scale art by uneven amounts
    (3, 4, 3, 4 picture pixels per art pixel), so a fixed grid drifts onto the seams and samples
    blends. Each next edge is snapped to the strongest colour change near where it is expected."""
    edges = [0]
    end = len(line) - 1
    while edges[-1] + pitch * 0.5 < end:
        guess = edges[-1] + pitch
        lo, hi = int(guess - pitch * 0.35), int(guess + pitch * 0.35) + 1
        near = [i for i in range(max(lo, edges[-1] + 1), min(hi, end) + 1)]
        if not near:
            break
        best = max(near, key=lambda i: line[i])
        edges.append(best if line[best] > 0 else int(round(guess)))
    if edges[-1] < end:
        edges.append(end)
    return edges


def guess_pitch(img, box):
    """Size of one art pixel: the spacing that best lines up with colour edges."""
    x0, y0, x1, y1 = box
    px = img.load()
    cols = [0.0] * (x1 - x0)
    rows = [0.0] * (y1 - y0)
    for y in range(y0, y1, 2):
        for x in range(x0 + 1, x1):
            d = sum(abs(px[x, y][i] - px[x - 1, y][i]) for i in range(3))
            cols[x - x0] += d
    for x in range(x0, x1, 2):
        for y in range(y0 + 1, y1):
            d = sum(abs(px[x, y][i] - px[x, y - 1][i]) for i in range(3))
            rows[y - y0] += d
    found = []
    for tenth in range(40, 400):
        pitch = tenth / 10.0
        score = 0.0
        phases = []
        for line in (cols, rows):
            top = (-1, 0.0)
            for step in range(int(pitch * 2)):
                phase = step / 2.0
                total, n, pos = 0.0, 0, phase
                while pos < len(line) - 1:
                    total += line[int(pos)] + line[min(int(pos) + 1, len(line) - 1)]
                    n += 1
                    pos += pitch
                if n > 3 and total / n > top[0]:
                    top = (total / n, phase)
            score += top[0]
            phases.append(top[1])
        found.append((score, pitch, phases[0], phases[1]))
    peak = max(f[0] for f in found)
    best = next(f for f in found if f[0] >= peak * 0.85)    # multiples score alike: take the smallest
    return best[1], best[2], best[3]


def main():
    src, name = sys.argv[1], sys.argv[2]
    tol, colors = arg("--tol", 60), arg("--colors", 40)
    img = Image.open(src).convert("RGB")
    if "--crop" in sys.argv:                 # left,top,right,bottom in picture pixels
        img = img.crop(tuple(int(v) for v in arg("--crop", "").split(",")))
    w, h = img.size
    mask = background_mask(img, tol)
    xs = [x for y in range(h) for x in range(w) if not mask[y][x]]
    ys = [y for y in range(h) for x in range(w) if not mask[y][x]]
    box = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
    pitch, px_phase, py_phase = guess_pitch(img, box)
    if "--pitch" in sys.argv:
        pitch = arg("--pitch", 8.0)
    cols = round((box[2] - box[0]) / pitch)
    rows = round((box[3] - box[1]) / pitch)
    pitch_x, pitch_y = (box[2] - box[0]) / cols, (box[3] - box[1]) / rows
    snap = "--snap" in sys.argv
    if snap:                      # follow the picture's real pixel edges instead of a fixed grid
        col_line, row_line = edge_profiles(img, box)
        xe, ye = boundaries(col_line, pitch), boundaries(row_line, pitch)
        cols, rows = len(xe) - 1, len(ye) - 1
    px = img.load()
    ground = border_colour(img)
    cells = []
    for r in range(rows):
        line = []
        for c in range(cols):
            cx, cy = box[0] + (c + 0.5) * pitch_x, box[1] + (r + 0.5) * pitch_y
            if snap:
                cx, cy = box[0] + (xe[c] + xe[c + 1]) / 2, box[1] + (ye[r] + ye[r + 1]) / 2
            # the middle of an art pixel is its cleanest part; on small art that is one picture pixel
            # (--reach 1 averages a 3x3 patch instead, which suits a blurry picture)
            reach = arg("--reach", int(min(pitch_x, pitch_y) * 0.22))
            sample, clear = [], 0
            for yy in range(int(cy) - reach, int(cy) + reach + 1):
                for xx in range(int(cx) - reach, int(cx) + reach + 1):
                    if 0 <= xx < w and 0 <= yy < h:
                        if mask[yy][xx]:
                            clear += 1
                        else:
                            sample.append(px[xx, yy])
            if not sample or clear > len(sample):
                line.append(None)
            else:
                sample.sort(key=sum)
                picked = sample[len(sample) // 2]
                # Eye glints: a speck of near-white inside a dark cell is smaller than one art
                # pixel and falls between samples, leaving blank black eyes. Keep it.
                if max(picked) < 80:
                    glint = [px[xx, yy]
                             for yy in range(int(cy - pitch_y / 2), int(cy + pitch_y / 2) + 1)
                             for xx in range(int(cx - pitch_x / 2), int(cx + pitch_x / 2) + 1)
                             if 0 <= xx < w and 0 <= yy < h and min(px[xx, yy]) > 150
                             and max(px[xx, yy]) - min(px[xx, yy]) < 40]
                    if len(glint) >= 2 and not any(far(g, ground, 40) is False for g in glint):
                        picked = max(glint, key=sum)
                line.append(picked)
        cells.append(line)
    # background trapped inside the art (the flood can't reach it), plus any --drop colours
    # such as a drop shadow: --drop 170,146,170   (repeat the flag's value with ; for more)
    # Trapped background is removed by PATCH, not by colour alone: teeth and highlights can be
    # nearly the background colour, so only a connected patch of at least --inner-min cells goes.
    inner, smallest = arg("--inner-tol", 30), arg("--inner-min", 5)
    seen = set()
    for r in range(rows):
        for c in range(cols):
            if (r, c) in seen or not cells[r][c] or far(cells[r][c], ground, inner):
                continue
            patch, todo = [], [(r, c)]
            seen.add((r, c))
            while todo:
                y, x = todo.pop()
                patch.append((y, x))
                for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if (0 <= ny < rows and 0 <= nx < cols and (ny, nx) not in seen
                            and cells[ny][nx] and not far(cells[ny][nx], ground, inner)):
                        seen.add((ny, nx))
                        todo.append((ny, nx))
            if len(patch) >= smallest:
                for y, x in patch:
                    cells[y][x] = None
    unwanted = []
    if "--drop" in sys.argv:
        for chunk in arg("--drop", "").split(";"):
            unwanted.append((tuple(int(v) for v in chunk.split(",")), arg("--drop-tol", 36)))
    cells = [[None if c and any(not far(c, bad, t) for bad, t in unwanted) else c for c in line] for line in cells]
    while cells and not any(cells[-1]):
        cells.pop()
        rows -= 1
    trim = arg("--trim-bottom", 0)        # art rows to cut off the bottom, e.g. a drop shadow
    if trim:
        cells = cells[:-trim]
        rows -= trim
    # tidy the colours: scans and screenshots smear each flat colour into many
    flat = [c for line in cells for c in line if c]
    # Near-identical colours are folded into the commonest one. Unlike a fixed-size palette this
    # never swallows a rare but distinct colour (the two white pixels of an eye).
    merge, chosen, home = arg("--merge", 26), [], {}
    for colour, _ in Counter(flat).most_common():
        near = [k for k in chosen if not far(colour, k, merge)]
        home[colour] = min(near, key=lambda k: sum(abs(a - b) for a, b in zip(colour, k))) if near else None
        if home[colour] is None:
            chosen.append(colour)
            home[colour] = colour
    cells = [[home[c] if c else None for c in line] for line in cells]
    # stray specks (bits of a neighbouring sprite): drop islands smaller than --speck cells
    speck, done, islands = arg("--speck", 6), set(), []
    for r in range(rows):
        for c in range(cols):
            if (r, c) in done or not cells[r][c]:
                continue
            island, todo = [], [(r, c)]
            done.add((r, c))
            while todo:
                y, x = todo.pop()
                island.append((y, x))
                for ny in (y - 1, y, y + 1):
                    for nx in (x - 1, x, x + 1):
                        if 0 <= ny < rows and 0 <= nx < cols and (ny, nx) not in done and cells[ny][nx]:
                            done.add((ny, nx))
                            todo.append((ny, nx))
            islands.append(island)
    biggest = max(islands, key=len)
    for island in islands:      # --main keeps only the biggest piece (cuts off neighbouring sprites)
        if len(island) < speck or ("--main" in sys.argv and island is not biggest):
            for y, x in island:
                cells[y][x] = None
    cells = [line for line in cells if any(line)]                       # close up emptied edges
    used = [x for line in cells for x, c in enumerate(line) if c]
    cells = [line[min(used):max(used) + 1] for line in cells]
    rows, cols = len(cells), len(cells[0])
    # near-black outlines vanish on a dark terminal: --lift-dark raises them to a visible slate
    if "--lift-dark" in sys.argv:
        floor = arg("--lift-dark", 60)
        # Only the rim (dark cells within two cells of open space) is raised. Dark inside the art
        # (eyes, mouths, brows) stays black so it keeps its contrast against the colours around it.

        def near_open(y, x):
            return any(not (0 <= y + dy < rows and 0 <= x + dx < cols) or cells[y + dy][x + dx] is None
                       for dy in (-2, -1, 0, 1, 2) for dx in (-2, -1, 0, 1, 2))

        cells = [[(floor, floor + 4, floor + 14) if c and max(c) < floor and near_open(y, x) else c
                  for x, c in enumerate(line)] for y, line in enumerate(cells)]
    # --halo: a one-pixel dark-slate ring just outside the silhouette. The art (and its black
    # outline) stays exactly as drawn, and the shape still reads on a near-black terminal.
    if "--halo" in sys.argv:
        ring = (52, 55, 64)
        cells = [[None] * (cols + 2)] + [[None] + line + [None] for line in cells] + [[None] * (cols + 2)]
        rows, cols = rows + 2, cols + 2
        cells = [[ring if c is None and any(
                      0 <= y + dy < rows and 0 <= x + dx < cols and cells[y + dy][x + dx] not in (None, ring)
                      for dy in (-1, 0, 1) for dx in (-1, 0, 1)) else c
                  for x, c in enumerate(line)] for y, line in enumerate(cells)]
    if rows % 2:
        cells.insert(0, [None] * cols)
        rows += 1
    reset = f"{ESC}[0m"
    pad = [None] * MARGIN
    lines = [""]
    for y in range(0, rows, 2):
        out = []
        for top, bottom in zip(pad + cells[y], pad + cells[y + 1]):
            if top is None and bottom is None:
                out.append(reset + " ")
            elif bottom is None:
                out.append(reset + fg(top) + "▀")
            elif top is None:
                out.append(reset + fg(bottom) + "▄")
            else:
                out.append(fg(top) + bg(bottom) + "▀")
        lines.append("".join(out) + reset)
    if "--grass" in sys.argv:              # off unless asked for;        # water plants sit on nothing
        lines.append("".join(fg(LAWN[(x // 4) % 2]) + "▀" for x in range(cols + 2 * MARGIN)) + reset)
    lines.append("")
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "out", f"big-{name}.ans"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    if "--png" in sys.argv:
        scale = 8
        check = Image.new("RGB", (cols * scale, rows * scale), (30, 30, 30))   # a typical dark terminal
        for y, line in enumerate(cells):
            for x, c in enumerate(line):
                if c:
                    check.paste(c, (x * scale, y * scale, (x + 1) * scale, (y + 1) * scale))
        check.save(os.path.join(here, f"check-{name}.png"))
    print(f"big-{name}.ans: {cols} x {rows} art pixels, one art pixel = {pitch:.1f} picture pixels, "
          f"{cols + 2 * MARGIN} columns by {rows // 2 + 1} lines")


if __name__ == "__main__":
    main()
