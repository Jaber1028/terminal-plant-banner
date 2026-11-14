"""Writes out/<banner>.theme next to every out/*.ans: the escape codes that recolour the
terminal (background, text, cursor) to suit that plant. The profile prints it with the art.

The plant's main colour is its most common vivid hue. From it:
    background  a very dark tint      text  a pale tint      cursor  the vivid colour itself
"""
import colorsys
import glob
import os
import re
from collections import Counter

here = os.path.dirname(os.path.abspath(__file__))
ESC = "\x1b"
colour = re.compile(r"\x1b\[[34]8;2;(\d+);(\d+);(\d+)m")


def osc(code, rgb):
    return f"{ESC}]{code};rgb:{rgb[0]:02x}/{rgb[1]:02x}/{rgb[2]:02x}{ESC}\\"


def tint(h, s, v):
    return tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))


for path in sorted(glob.glob(os.path.join(here, "out", "*.ans"))):
    text = open(path, encoding="utf-8").read()
    hues, vivid = Counter(), {}
    for r, g, b in colour.findall(text):
        h, s, v = colorsys.rgb_to_hsv(int(r) / 255, int(g) / 255, int(b) / 255)
        if v < 0.30 or s < 0.12:            # outlines, whites and grays say nothing about the hue
            continue
        bucket = int(h * 24) % 24
        hues[bucket] += 1                    # by area: the colour that covers most of the plant wins
        if bucket not in vivid or s * v > vivid[bucket][0]:
            vivid[bucket] = (s * v, h, s)
    if hues:
        best = hues.most_common(1)[0][0]
        _, h, s = vivid[best]
        strength = min(1.0, s * 1.3)
    else:                                    # a colourless plant gets a neutral slate
        h, strength = 0.62, 0.25
    theme = (osc(11, tint(h, 0.50 * strength, 0.17))      # background: a touch above black so black outlines show
             + osc(10, tint(h, 0.14 * strength, 0.90))    # text
             + osc(12, tint(h, 0.80 * strength, 0.95)))   # cursor
    with open(path[:-4] + ".theme", "w", encoding="utf-8", newline="") as f:
        f.write(theme)
print("themes written for", len(glob.glob(os.path.join(here, "out", "*.theme"))), "banners")
