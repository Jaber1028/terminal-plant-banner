"""Writes, next to every out/*.ans, the escape codes that recolour the terminal to suit that plant:

    <banner>.theme   standard codes most terminals understand: background, text and cursor
                     (OSC 11, 10, 12) and the selection's background and text (OSC 17, 19)
    <banner>.iterm   iTerm2's own SetColors codes for what the standard ones don't reach there:
                     selection, cursor, the text under the cursor, and the tab colour

The plant's main colour is its most common vivid hue. From it:
    background  a very dark tint      text  a pale tint      cursor and tab  the vivid colour
    selection   a mid-dark tint behind pale text
"""
import colorsys
import glob
import os
import re
from collections import Counter

here = os.path.dirname(os.path.abspath(__file__))
ESC = "\x1b"
ST = ESC + "\\"
colour = re.compile(r"\x1b\[[34]8;2;(\d+);(\d+);(\d+)m")


def osc(code, rgb):
    return f"{ESC}]{code};rgb:{rgb[0]:02x}/{rgb[1]:02x}/{rgb[2]:02x}{ST}"


def iterm(key, rgb):
    return f"{ESC}]1337;SetColors={key}={rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}{ST}"


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
    back = tint(h, 0.50 * strength, 0.17)    # a touch above black, so black outlines show
    text_c = tint(h, 0.14 * strength, 0.90)
    cursor = tint(h, 0.80 * strength, 0.95)
    sel_bg = tint(h, 0.60 * strength, 0.42)
    sel_fg = tint(h, 0.08 * strength, 0.98)
    theme = osc(11, back) + osc(10, text_c) + osc(12, cursor) + osc(17, sel_bg) + osc(19, sel_fg)
    extra = (iterm("selbg", sel_bg) + iterm("selfg", sel_fg) + iterm("curbg", cursor)
             + iterm("curfg", back) + iterm("tab", cursor))
    for suffix, codes in ((".theme", theme), (".iterm", extra)):
        with open(path[:-4] + suffix, "w", encoding="utf-8", newline="") as f:
            f.write(codes)
print("themes written for", len(glob.glob(os.path.join(here, "out", "*.theme"))), "banners")
