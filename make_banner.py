"""Builds out/classic.ans (`plants classic`): the first version, a small row of pixel-art
garden plants with their names. build.py runs it.

Edit the sprites or palette below, then run:
    python3 make_banner.py            (writes out/classic.ans)
    python3 make_banner.py --png      (also writes preview.png, needs Pillow)

Each sprite is 16 rows of 16 characters; '.' is see-through.
Two pixel rows become one terminal row, so a sprite is 8 lines tall.
"""
import os
import sys

PALETTE = {
    "k": (24, 40, 20),      # dark outline / pupils
    "G": (126, 200, 60),    # pea green
    "H": (170, 228, 100),   # pea highlight
    "d": (40, 90, 30),      # mouth shadow
    "g": (60, 140, 50),     # stem
    "L": (90, 175, 60),     # leaf
    "w": (250, 250, 250),   # eye white
    "Y": (255, 214, 40),    # petal
    "o": (226, 140, 20),    # petal edge
    "B": (150, 92, 40),     # sunflower face
    "N": (200, 136, 68),    # nut shell
    "h": (228, 176, 110),   # nut highlight
    "n": (106, 62, 22),     # nut outline
    "R": (222, 44, 44),     # cherry
    "p": (255, 130, 130),   # cherry highlight
    "r": (120, 16, 24),     # cherry outline
    "S": (150, 215, 245),   # snow pea
    "T": (205, 240, 255),   # snow pea highlight
    "s": (40, 100, 150),    # snow pea outline
    "i": (235, 250, 255),   # ice crystal
}

PEASHOOTER = [
    "................",
    "....kkkkk.......",
    "...kGHHGGk......",
    "..kGHGGGGGk.kk..",
    ".kGGGwwGGGGkGGk.",
    ".kGGGwkGGGGGGdk.",
    ".kGGGGGGGGGGGdk.",
    ".kGGGGGGGGGkGGk.",
    "..kGGGGGGGk.kk..",
    "...kGGGGGk......",
    "....kkgkk.......",
    "......g.........",
    "..kk..g..kk.....",
    ".kLLk.g.kLLk....",
    "..kLLkgkLLk.....",
    "...kkLgLkk......",
]

SUNFLOWER = [
    "....oYYooYYo....",
    "..oYoYYYYYYoYo..",
    ".oYYYooooooYYYo.",
    ".oYYoBBBBBBoYYo.",
    "oYYoBBBBBBBBoYYo",
    "oYoBBkBBBBkBBoYo",
    "oYoBBkBBBBkBBoYo",
    "oYoBBBBBBBBBBoYo",
    "oYYoBkBBBBkBoYYo",
    ".oYYoBkkkkBoYYo.",
    ".oYYYooooooYYYo.",
    "..oYoYYYYYYoYo..",
    "....oooggooo....",
    "..kk...gg..kk...",
    ".kLLkk.gg.kLLk..",
    "..kkLLkggkLLk...",
]

WALLNUT = [
    "................",
    ".....nnnnnn.....",
    "...nnNNNNNNnn...",
    "..nNNhhNNNNNNn..",
    ".nNNhNNNNNNNNNn.",
    ".nNNNNNNNNNNNNn.",
    ".nNNwwwNNwwwNNn.",
    ".nNNwkwNNwkwNNn.",
    ".nNNwwwNNwwwNNn.",
    ".nNNNNNNNNNNNNn.",
    ".nNNNkNNNNkNNNn.",
    ".nNNNNkkkkNNNNn.",
    ".nNNNNNNNNNNNNn.",
    "..nNNNNNNNNNNn..",
    "...nnNNNNNNnn...",
    ".....nnnnnn.....",
]

CHERRIES = [
    ".......gg.......",
    "......gLLg......",
    ".....g.gg.g.....",
    "....g......g....",
    "...g........g...",
    "..rrrr....rrrr..",
    ".rRRRRr..rRRRRr.",
    "rRpRRRRrrRpRRRRr",
    "rRkRRkRrrRkRRkRr",
    "rRwkRkwrrRwkRkwr",
    "rRRRRRRrrRRRRRRr",
    "rRRkkRRrrRRkkRRr",
    "rRkRRkRrrRkRRkRr",
    ".rRRRRr..rRRRRr.",
    "..rrrr....rrrr..",
    "................",
]

SNOWPEA = [
    "..i.............",
    ".iii.sssss......",
    "..i.sSTTSSs.....",
    "..ssSTSSSSSs.ss.",
    ".sSSSSwwSSSSsSSs",
    ".sSSSSwkSSSSSSds",
    ".sSSSSSSSSSSSSds",
    ".sSSSSSSSSSSsSSs",
    "..sSSSSSSSSs.ss.",
    "...sSSSSSSs.....",
    "....sssgss......",
    "......g.........",
    "..kk..g..kk.....",
    ".kLLk.g.kLLk....",
    "..kLLkgkLLk.....",
    "...kkLgLkk......",
]

ROW = [
    ("Sunflower", SUNFLOWER, "Y"),
    ("Peashooter", PEASHOOTER, "G"),
    ("Snow Pea", SNOWPEA, "S"),
    ("Wall-nut", WALLNUT, "N"),
    ("Cherries", CHERRIES, "R"),
]
GAP = 3
MARGIN = 2
LAWN = [(64, 150, 50), (88, 176, 62)]   # two-tone mown stripes
ESC = "\x1b"


def check():
    for name, rows, _ in ROW:
        assert len(rows) == 16, f"{name}: {len(rows)} rows"
        for n, row in enumerate(rows):
            assert len(row) == 16, f"{name} row {n}: {len(row)} wide"
            for ch in row:
                assert ch == "." or ch in PALETTE, f"{name} row {n}: unknown '{ch}'"


def canvas():
    """The whole picture as a grid of RGB tuples (None = see-through)."""
    width = MARGIN + len(ROW) * 16 + (len(ROW) - 1) * GAP
    grid = [[None] * width for _ in range(16)]
    for index, (_, rows, _) in enumerate(ROW):
        left = MARGIN + index * (16 + GAP)
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch != ".":
                    grid[y][left + x] = PALETTE[ch]
    return grid


def fg(c):
    return f"{ESC}[38;2;{c[0]};{c[1]};{c[2]}m"


def bg(c):
    return f"{ESC}[48;2;{c[0]};{c[1]};{c[2]}m"


def render(grid):
    reset = f"{ESC}[0m"
    lines = [""]
    for y in range(0, len(grid), 2):
        out = []
        for top, bottom in zip(grid[y], grid[y + 1]):
            if top is None and bottom is None:
                out.append(reset + " ")
            elif bottom is None:
                out.append(reset + fg(top) + "▀")
            elif top is None:
                out.append(reset + fg(bottom) + "▄")
            else:
                out.append(fg(top) + bg(bottom) + "▀")
        lines.append("".join(out).rstrip() + reset)
    width = len(grid[0]) + MARGIN
    lawn = "".join(fg(LAWN[(x // 4) % 2]) + "▀" for x in range(width))
    lines.append(lawn + reset)
    caption = " " * MARGIN
    for index, (name, _, key) in enumerate(ROW):
        caption += fg(PALETTE[key]) + name.center(16) + " " * GAP
    lines.append(caption.rstrip() + reset)
    lines.append("")
    return "\n".join(lines) + "\n"


def preview(grid, path):
    from PIL import Image
    scale = 10
    back = (12, 12, 12)
    img = Image.new("RGB", (len(grid[0]) * scale, len(grid) * scale), back)
    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            if c is not None:
                for dy in range(scale):
                    for dx in range(scale):
                        img.putpixel((x * scale + dx, y * scale + dy), c)
    img.save(path)


def main():
    check()
    here = os.path.dirname(os.path.abspath(__file__))
    grid = canvas()
    os.makedirs(os.path.join(here, "out"), exist_ok=True)
    with open(os.path.join(here, "out", "classic.ans"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render(grid))
    if "--png" in sys.argv:
        preview(grid, os.path.join(here, "preview.png"))
    print(f"out/classic.ans written: {len(grid[0]) + MARGIN} columns wide")


if __name__ == "__main__":
    main()
