"""Builds bash/build/: everything a Unix-like machine needs for `plants`, ready to copy to
~/.config/pvz-banner/ there.

    bash/build/plants.sh          the bash version of `plants` (copied from bash/plants.sh)
    bash/build/art/<kind>-<name>.ans and .theme
    bash/build/index.tsv          kind, name, width, height of every banner

Each banner is tidied for bash, which has no cheap way to measure text that holds colour codes:
blank rows are dropped, and every row is cut to its last drawn cell and then padded with plain
spaces to the plant's full width. So every row of a plant is exactly `width` cells, and the
script can line plants up from the numbers in index.tsv alone.
"""
import glob
import os
import re
import shutil

here = os.path.dirname(os.path.abspath(__file__))
codes = re.compile(r"\x1b\[[0-9;]*m")
blank_tail = re.compile(r"(?:\x1b\[0m )+(?:\x1b\[0m)?$")
build = os.path.join(here, "bash", "build")
art = os.path.join(build, "art")
shutil.rmtree(build, ignore_errors=True)
os.makedirs(art)
kinds = ("x3", "x2", "big", "s75", "s60", "s50", "s40")
rows = []
for path in sorted(glob.glob(os.path.join(here, "out", "*.ans"))):
    base = os.path.basename(path)[:-4]
    kind, name = base.split("-", 1)
    if kind not in kinds:
        continue
    lines = [l for l in open(path, encoding="utf-8").read().split("\n") if codes.sub("", l).strip()]
    lines = [blank_tail.sub("", l) + "\x1b[0m" for l in lines]
    width = max(len(codes.sub("", l)) for l in lines)
    lines = [l + " " * (width - len(codes.sub("", l))) for l in lines]
    with open(os.path.join(art, base + ".ans"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    theme = path[:-4] + ".theme"
    if os.path.exists(theme):
        shutil.copyfile(theme, os.path.join(art, base + ".theme"))
    rows.append(f"{kind}\t{name}\t{width}\t{len(lines)}")
with open(os.path.join(build, "index.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(rows) + "\n")
for script in ("plants.sh", "install.sh", "test.sh"):
    shutil.copyfile(os.path.join(here, "bash", script), os.path.join(build, script))
print(f"{len(rows)} banners in {build}")
