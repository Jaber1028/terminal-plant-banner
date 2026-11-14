"""Builds the big banners in out/:

    out/big-<plant>.ans   one large shaded plant each (56 x 48 pixels, 24 lines tall)

Plants that also exist on the reference sheet are replaced by the sheet's version when
build_all.sh runs; only the purple mushroom stays from here.

Run:  python make_big.py           (add --png for out/preview.png, needs Pillow)

The big plants are drawn from shapes (blobs, lines, polygons) rather than typed
grids, so tweak the numbers in the plant functions to change them.
"""
import math
import os
import sys

from make_banner import fg, bg, ESC

W, H = 56, 48
INK = (18, 22, 18)
WHITE = (250, 250, 250)

# tones: (outline, shadow, base, highlight)
GREEN = ((26, 66, 22), (70, 148, 40), (122, 198, 58), (178, 234, 106))
STEM = ((22, 58, 20), (40, 112, 40), (62, 150, 52), (104, 192, 72))
LEAF = ((22, 62, 20), (48, 128, 42), (84, 176, 58), (134, 212, 88))
PETAL_A = ((168, 88, 8), (232, 158, 18), (255, 206, 40), (255, 238, 124))
PETAL_B = ((168, 88, 8), (212, 128, 12), (244, 178, 26), (255, 218, 88))
FACE = ((80, 44, 14), (118, 68, 26), (156, 98, 44), (188, 130, 68))
NUT = ((82, 46, 14), (158, 98, 42), (204, 142, 72), (234, 188, 124))
RED = ((96, 8, 18), (158, 20, 30), (224, 46, 46), (255, 124, 112))
DEEP = ((18, 54, 18), (48, 118, 34), (92, 166, 46), (140, 206, 82))
POTATO = ((96, 62, 20), (176, 128, 60), (222, 178, 98), (244, 214, 150))
DIRT = ((50, 30, 14), (84, 52, 24), (116, 74, 36), (146, 100, 54))
PURPLE = ((58, 24, 96), (112, 60, 170), (156, 96, 214), (200, 156, 240))
CREAM = ((120, 100, 70), (200, 184, 150), (236, 224, 196), (252, 246, 230))
SQUASH = ((40, 70, 16), (96, 150, 36), (150, 196, 60), (200, 230, 110))
CACT = ((20, 70, 40), (40, 130, 70), (70, 170, 90), (120, 210, 130))
PINK = ((130, 30, 80), (200, 70, 130), (240, 120, 170), (255, 180, 210))
STEEL = ((40, 44, 52), (100, 106, 116), (150, 156, 166), (206, 210, 218))
ICE = ((28, 78, 128), (94, 158, 210), (150, 212, 245), (216, 243, 255))


class Canvas:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.px = [[None] * w for _ in range(h)]

    def put(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def blob(self, cx, cy, rx, ry, tones, angle=0.0, edge=True, light=(-0.40, -0.45)):
        """A shaded ellipse with a dark rim; angle in radians tilts it."""
        outline, dark, base, hi = tones
        ca, sa = math.cos(angle), math.sin(angle)
        lu = light[0] * ca + light[1] * sa
        lv = -light[0] * sa + light[1] * ca
        reach = int(max(rx, ry)) + 3
        for y in range(int(cy) - reach, int(cy) + reach + 1):
            for x in range(int(cx) - reach, int(cx) + reach + 1):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                u, v = dx * ca + dy * sa, -dx * sa + dy * ca
                if (u / rx) ** 2 + (v / ry) ** 2 <= 1:
                    t = math.hypot(u / rx - lu, v / ry - lv)
                    self.put(x, y, hi if t < 0.42 else base if t < 1.08 else dark)
                elif edge and (u / (rx + 1.2)) ** 2 + (v / (ry + 1.2)) ** 2 <= 1:
                    self.put(x, y, outline)

    def ellipse(self, cx, cy, rx, ry, color):
        self.blob(cx, cy, rx, ry, (color,) * 4, edge=False)

    def line(self, x0, y0, x1, y1, width, color):
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(steps + 1):
            t = i / steps
            self.ellipse(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, width / 2, width / 2, color)

    def stalk(self, x0, y0, x1, y1, width=3.0):
        self.line(x0, y0, x1, y1, width + 2.2, STEM[0])
        self.line(x0, y0, x1, y1, width, STEM[2])
        self.line(x0 - 0.6, y0, x1 - 0.6, y1, 1.0, STEM[3])

    def merged(self, shapes, tones):
        """Several blobs fused into one body: rims only on the outside."""
        for shape in shapes:      # (cx, cy, rx, ry) or (cx, cy, rx, ry, angle)
            self.blob(*shape[:4], tones, angle=shape[4] if len(shape) > 4 else 0.0)
        for shape in shapes:
            self.blob(*shape[:4], tones, angle=shape[4] if len(shape) > 4 else 0.0, edge=False)

    def poly(self, pts, color, rim=None, clip=False):
        ys = [p[1] for p in pts]
        xs = [p[0] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            for x in range(int(min(xs)), int(max(xs)) + 1):
                px, py, inside = x + 0.5, y + 0.5, False
                for i in range(len(pts)):
                    (ax, ay), (bx, by) = pts[i], pts[(i + 1) % len(pts)]
                    if (ay > py) != (by > py) and px < (bx - ax) * (py - ay) / (by - ay) + ax:
                        inside = not inside
                if inside and (not clip or (0 <= x < self.w and 0 <= y < self.h and self.px[y][x] is not None)):
                    self.put(x, y, color)
        if rim:
            for i in range(len(pts)):
                (ax, ay), (bx, by) = pts[i], pts[(i + 1) % len(pts)]
                self.line(ax, ay, bx, by, 1.0, rim)

    def leaf(self, cx, cy, rx, ry, angle):
        self.blob(cx, cy, rx, ry, LEAF, angle=angle)
        dx, dy = math.cos(angle) * (rx - 1.5), math.sin(angle) * (rx - 1.5)
        self.line(cx - dx, cy - dy, cx + dx, cy + dy, 0.9, LEAF[1])

    def eye(self, cx, cy, rx=2.5, ry=4.0):
        self.ellipse(cx, cy, rx, ry, INK)
        self.put(cx - 1, cy - ry + 1, WHITE)
        self.put(cx - 1, cy - ry + 2, WHITE)
        self.put(cx, cy - ry + 1, WHITE)


def base_leaves(c, cx, spread=1.0):
    c.leaf(cx - 10 * spread, 41.5, 8.5, 3.6, 0.28)
    c.leaf(cx + 10 * spread, 41.5, 8.5, 3.6, -0.28)
    c.leaf(cx - 6 * spread, 45, 7.5, 2.8, -0.12)
    c.leaf(cx + 6 * spread, 45, 7.5, 2.8, 0.12)


def shooter(tones, frost):
    c = Canvas()
    if frost:
        for pts in ([(3, 4), (14, 10), (10, 15)], [(0, 15), (10, 15), (9, 21)],
                    [(8, 0), (17, 6), (12, 10)], [(2, 25), (10, 21), (11, 26)]):
            c.poly(pts, ICE[3], rim=ICE[0])
        for sx, sy in ((48, 5), (52, 32), (3, 34)):          # sparkles
            c.line(sx - 2, sy, sx + 2, sy, 1.0, ICE[3])
            c.line(sx, sy - 2, sx, sy + 2, 1.0, ICE[3])
    else:
        c.leaf(7, 8, 6.5, 3.2, 0.75)
    c.stalk(22, 28, 25, 43)
    base_leaves(c, 25)
    c.blob(38, 19, 9, 6, tones)                 # snout
    c.blob(22, 17, 14, 13, tones)               # head
    c.blob(47, 19, 4, 8, tones)                 # lip
    c.ellipse(48, 19, 2.2, 5.6, (18, 48, 16) if not frost else (20, 56, 96))
    c.eye(28, 13)
    c.line(25, 6.5, 31, 7.5, 1.4, tones[0])     # brow
    return c


def peashooter():
    return shooter(GREEN, False)


def snowpea():
    return shooter(ICE, True)


def sunflower():
    c = Canvas()
    c.stalk(28, 28, 28, 44)
    base_leaves(c, 28, 1.1)
    for layer in (1, 0):
        for i in range(layer, 16, 2):
            a = 2 * math.pi * i / 16
            c.blob(28 + 13.5 * math.cos(a), 19 + 12.5 * math.sin(a), 5.6, 3.3,
                   PETAL_B if layer else PETAL_A, angle=a)
    c.blob(28, 19, 10.5, 10, FACE)
    c.eye(24, 17, 1.7, 3.0)
    c.eye(32, 17, 1.7, 3.0)
    for x in range(23, 34):                     # smile
        y = 22 + (1 - ((x - 28) / 5.0) ** 2) * 2.6
        c.put(x, y, INK)
    c.ellipse(21, 21.5, 1.6, 1.0, (198, 118, 70))   # cheeks
    c.ellipse(35, 21.5, 1.6, 1.0, (198, 118, 70))
    return c


def wallnut():
    c = Canvas()
    c.blob(28, 25, 17, 21, NUT)
    for x0, y0, x1, y1 in ((18, 8, 15, 19), (31, 5, 34, 11), (41, 28, 39, 41),
                           (15, 33, 18, 42), (26, 40, 27, 45), (37, 9, 40, 15)):
        c.line(x0, y0, x1, y1, 1.0, NUT[1])     # shell creases
    for ex in (21, 35):
        c.ellipse(ex, 20, 4.8, 5.8, NUT[0])
        c.ellipse(ex, 20, 3.8, 4.8, WHITE)
        c.ellipse(ex + 1, 21, 1.8, 2.3, INK)
        c.put(ex, 19, WHITE)
    c.line(16, 12.5, 23, 11.5, 1.3, NUT[0])     # brows
    c.line(33, 11.5, 40, 12.5, 1.3, NUT[0])
    for x in range(24, 33):                     # small wobbly mouth
        c.put(x, 32 + (0.8 if x % 4 < 2 else 0), INK)
    return c


def cherries():
    c = Canvas()
    c.stalk(17, 20, 29, 5, 2.2)
    c.stalk(40, 21, 29, 5, 2.2)
    c.leaf(37, 5, 7, 3, 0.2)
    c.blob(41, 33, 12, 12, RED)
    c.blob(16, 32, 13, 13, RED)
    angry(c, 16.5, 32)
    angry(c, 41.5, 33)
    return c


def angry(c, fx, fy):
    """Scowling face centred on (fx, fy): slanted brows, small eyes, gritted teeth."""
    c.line(fx - 7.5, fy - 6, fx - 1.5, fy - 3, 1.7, INK)
    c.line(fx + 7.5, fy - 6, fx + 1.5, fy - 3, 1.7, INK)
    for side in (-1, 1):
        c.ellipse(fx + 4 * side, fy - 0.5, 2.5, 2.0, WHITE)
        c.ellipse(fx + 3.4 * side, fy - 0.3, 1.0, 1.0, INK)
    for x in range(int(fx - 4.5), int(fx + 5.5)):
        c.put(x, fy + 4, INK)
        c.put(x, fy + 5, WHITE if x % 2 else INK)
        c.put(x, fy + 6, INK)


def smile(c, cx, cy, half=5.0, depth=2.6):
    for x in range(int(cx - half), int(cx + half) + 1):
        c.put(x, cy + (1 - ((x - cx) / half) ** 2) * depth, INK)


def repeater():
    c = Canvas()
    c.leaf(6, 7, 6.5, 3.2, 0.75)
    c.leaf(4.5, 15, 6, 3, 0.15)
    c.leaf(7, 23, 6, 3, -0.55)
    c.stalk(22, 28, 25, 43)
    base_leaves(c, 25)
    c.blob(38, 19, 9, 6, DEEP)
    c.blob(22, 17, 14, 13, DEEP)
    c.blob(47, 19, 4, 8, DEEP)
    c.ellipse(48, 19, 2.2, 5.6, (14, 40, 14))
    c.eye(28, 14, 2.4, 3.4)
    c.line(23, 6, 32, 10, 1.8, DEEP[0])         # heavy scowl
    return c


def potatomine():
    c = Canvas()
    c.line(28, 24, 28, 12, 3.6, STEEL[0])       # antenna
    c.line(28, 24, 28, 12, 1.8, STEEL[2])
    c.blob(28, 9, 4, 4, RED)
    for gx, gy in ((21, 6), (35, 6), (28, 1)):  # blink rays
        c.put(gx, gy, RED[3])
    c.blob(28, 33, 18, 11, POTATO)
    for ex in (21, 35):
        c.ellipse(ex, 30, 4.4, 4.8, POTATO[0])
        c.ellipse(ex, 30, 3.4, 3.8, WHITE)
        c.ellipse(ex + (1 if ex < 28 else -1), 31, 1.6, 1.8, INK)
    for x in range(23, 34):
        c.put(x, 37, INK)
    for tx in (25, 29):                         # buck teeth
        for x in range(tx, tx + 3):
            for y in (38, 39, 40):
                c.put(x, y, WHITE)
    for sx, sy in ((12, 30), (43, 27), (38, 39), (16, 38)):
        c.ellipse(sx, sy, 1.2, 0.9, POTATO[1])  # eyes of the potato
    c.blob(9, 44, 8, 3.4, DIRT)
    c.blob(47, 44, 8, 3.4, DIRT)
    c.blob(28, 45.5, 13, 2.6, DIRT)
    return c


def mushroom():
    c = Canvas()
    c.blob(28, 21, 21, 15, PURPLE)                              # cap
    for sx, sy, rx, ry in ((16, 14, 3.4, 2.6), (30, 10, 3.0, 2.2), (41, 17, 2.8, 2.2),
                           (10, 23, 2.2, 1.8), (23, 19, 2.2, 1.6), (36, 24, 2.4, 1.6)):
        c.ellipse(sx, sy, rx, ry, PURPLE[1])                    # dark spots
        c.ellipse(sx - 0.6, sy - 0.6, rx * 0.45, ry * 0.45, PURPLE[0])
    c.ellipse(28, 31, 17, 4.5, PURPLE[0])                       # shaded underside of the cap
    c.blob(28, 37, 11, 9.5, CREAM)                              # stubby stalk in front
    for ex in (23, 32):                                         # sleepy eyes
        c.ellipse(ex, 35, 2.3, 3.2, INK)
        c.put(ex - 1, 33, WHITE)
        c.put(ex, 33, WHITE)
        c.put(ex - 1, 34, WHITE)
        c.line(ex - 3, 31.5, ex + 3, 31.5, 1.2, CREAM[1])       # heavy lids
    c.blob(27.5, 42, 2.6, 2.0, CREAM)                           # puckered mouth
    c.ellipse(27.5, 42, 1.3, 1.0, INK)
    return c


def jalapeno():
    c = Canvas()
    c.line(27, 9, 31, 2, 3.8, STEM[0])
    c.line(27, 9, 31, 2, 2.0, STEM[2])
    c.merged([(27, 21, 10.5, 12), (29, 32, 8, 9), (31.5, 40, 5, 5.5)], RED)
    c.blob(27, 9.5, 6.5, 2.6, GREEN)
    angry(c, 27, 22)
    for fx, fy in ((6, 30), (49, 24), (10, 14), (46, 38)):      # heat flecks
        c.line(fx, fy + 2, fx, fy - 2, 1.4, (255, 150, 30))
        c.put(fx, fy - 3, (255, 220, 80))
    return c


def squash():
    c = Canvas()
    c.line(28, 8, 25, 2, 4.0, STEM[0])
    c.line(28, 8, 25, 2, 2.2, STEM[2])
    c.merged([(28, 31, 18, 14), (28, 17, 12, 10)], SQUASH)
    for x0, x1 in ((19, 14), (37, 42)):         # ribs
        c.line(x0 + (2 if x0 < 28 else -2), 10, x1, 40, 1.0, SQUASH[1])
    angry(c, 28, 26)
    return c


def jaw_teeth(c, cx, cy, rx, ry, angle, inward, places):
    """White fangs along one edge of a tilted jaw blob, pointing into the mouth."""
    ax, ay = math.cos(angle), math.sin(angle)
    nx, ny = (-ay, ax) if inward > 0 else (ay, -ax)
    for t in places:
        reach = (ry - 0.5) * math.sqrt(1 - t * t)
        ex, ey = cx + ax * rx * t + nx * reach, cy + ay * rx * t + ny * reach
        c.poly([(ex - ax * 1.9, ey - ay * 1.9), (ex + ax * 1.9, ey + ay * 1.9),
                (ex + nx * 4.6, ey + ny * 4.6)], WHITE)


def chomper():
    c = Canvas()
    for pts in ([(0, 9), (12, 13), (9, 19)], [(0, 21), (10, 18), (10, 25)],
                [(1, 33), (11, 24), (14, 30)], [(8, 3), (16, 10), (11, 13)]):
        c.poly(pts, LEAF[2], rim=LEAF[0])                       # spiky collar
    c.stalk(20, 30, 24, 44)
    base_leaves(c, 24)
    c.poly([(17, 20), (47, 6), (47, 35)], (74, 10, 46))         # inside of the mouth
    c.ellipse(34, 22, 7, 2.6, (236, 104, 144))                  # tongue
    c.ellipse(31, 22, 3, 1.0, (198, 64, 108))
    up, low = (31, 9.5, 16, 6.5, -0.38), (31, 31, 16, 6.0, 0.38)
    c.merged([(19, 20, 10, 11), up, low], PURPLE)
    for sx, sy, rx, ry in ((14, 14, 2.4, 1.8), (24, 8, 2.6, 1.6), (34, 5, 2.2, 1.4), (12, 25, 2.0, 1.5),
                           (24, 33, 2.4, 1.4), (35, 35, 2.0, 1.2), (19, 19, 1.6, 1.2)):
        c.ellipse(sx, sy, rx, ry, PURPLE[3])                    # speckles
    jaw_teeth(c, *up, 1, (-0.1, 0.2, 0.48, 0.74, 0.93))
    jaw_teeth(c, *low, -1, (-0.1, 0.2, 0.48, 0.74, 0.93))
    return c


def needles(c, cx, cy, rx, ry, angles, length=3.4):
    for deg in angles:
        a = math.radians(deg)
        x0, y0 = cx + math.cos(a) * (rx + 1), cy + math.sin(a) * (ry + 1)
        c.line(x0, y0, x0 + math.cos(a) * length, y0 + math.sin(a) * length, 1.0, (238, 232, 184))


def cactus():
    c = Canvas()
    needles(c, 12.5, 25, 3.2, 6.5, (180, 225, 270, 315))        # arm spines
    needles(c, 43.5, 22, 3.2, 6.5, (0, 225, 270, 315))
    needles(c, 28, 17, 12, 10.5, (150, 180, 205, 235, 305, 335, 0, 30))
    needles(c, 28, 33, 9.5, 12, (160, 195, 345, 20))
    c.merged([(17, 32, 6, 3.3), (12.5, 26, 3.3, 6.5)], CACT)    # left arm
    c.merged([(39, 29, 6, 3.3), (43.5, 23, 3.3, 6.5)], CACT)    # right arm
    c.merged([(28, 33, 9.5, 12.5), (28, 17, 12, 10.5)], CACT)   # column and head
    for x in (23, 28, 33):                                      # ribs
        c.line(x, 29, x, 43, 0.9, CACT[1])
    c.blob(27, 5.5, 4.2, 3.0, PINK)                             # flower bud
    c.ellipse(27, 5.5, 1.5, 1.2, (255, 226, 90))
    c.eye(24, 15, 2.0, 3.2)
    c.eye(31.5, 15, 2.0, 3.2)
    c.blob(34.5, 22, 3.4, 3.4, CACT)                            # round spike-shooting mouth
    c.ellipse(35, 22, 2.0, 2.2, (14, 46, 26))
    c.blob(28, 45.5, 15, 2.4, DIRT)
    return c


BIG = [
    ("peashooter", "Peashooter", peashooter, GREEN[2]),
    ("wallnut", "Wall-nut", wallnut, NUT[2]),
    ("repeater", "Repeater", repeater, DEEP[2]),
    ("potatomine", "Potato Mine", potatomine, POTATO[2]),
    ("mushroom", "Mushroom", mushroom, PURPLE[2]),
]
LAWN = [(64, 150, 50), (88, 176, 62)]
MARGIN = 2


def render(grid, captions):
    """grid: rows of RGB-or-None. Names are kept in the data but not printed."""
    reset = f"{ESC}[0m"
    pad = [None] * MARGIN
    lines = [""]
    for y in range(0, len(grid), 2):
        out = []
        for top, bottom in zip(pad + grid[y], pad + grid[y + 1]):
            if top is None and bottom is None:
                out.append(reset + " ")
            elif bottom is None:
                out.append(reset + fg(top) + "▀")
            elif top is None:
                out.append(reset + fg(bottom) + "▄")
            else:
                out.append(fg(top) + bg(bottom) + "▀")
        lines.append("".join(out) + reset)
    lines.append("")
    return "\n".join(lines) + "\n"


def save(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    canvases = []
    for slug, name, draw, color in BIG:
        c = draw()
        canvases.append(c)
        save(os.path.join(out, f"big-{slug}.ans"), render(c.px, [(name, color, 0, c.w)]))
    if "--png" in sys.argv:
        from PIL import Image
        scale = 6
        per = 6
        img = Image.new("RGB", (per * (W + 2) * scale, -(-len(canvases) // per) * (H + 2) * scale), (12, 12, 12))
        for n, c in enumerate(canvases):
            ox, oy = (n % per) * (W + 2), (n // per) * (H + 2)
            for y, line in enumerate(c.px):
                for x, color in enumerate(line):
                    if color:
                        img.paste(color, ((ox + x) * scale, (oy + y) * scale,
                                          (ox + x + 1) * scale, (oy + y + 1) * scale))
        img.save(os.path.join(out, "preview.png"))
    print(f"wrote {len(BIG)} drawn plants to {out}")


if __name__ == "__main__":
    main()
