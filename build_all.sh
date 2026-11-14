#!/usr/bin/env bash
# Rebuilds every banner in out/ from the reference pictures in refs/ plus the drawn plants.
#   bash build_all.sh          rebuild
#   bash build_all.sh --png    also write check-<name>.png for each and sheet.png with all of them
# Works anywhere bash and Python 3 with Pillow run (Linux, macOS, Windows with Git Bash or WSL).
cd "$(dirname "$0")" || exit 1
extra="$1"
# python3 on most systems, python where that is the only name (often on Windows)
PY=$(command -v python3 || command -v python) || { echo "Python 3 not found" >&2; exit 1; }
"$PY" -c 'import sys; sys.exit(sys.version_info < (3,))' 2>/dev/null || PY=$(command -v python)
# one sprite only, no ground shadow, near-identical shades merged, black outlines exactly as drawn;
# --snap follows the picture's real pixel edges (art pixels land 3 or 4 picture pixels apart)
common="--pitch 3.5 --snap --main --drop 97,94,89 --drop-tol 16 --merge 36"

"$PY" make_big.py > /dev/null     # the drawn ones; replaced below where the sheet has the same plant

# Every plant from the full reference sheet (refs/full-sheet.png), cut up by split_sheet.py.
grep -v '^#' refs/sheet/names.txt | while read -r num name; do
    [ "$name" = "-" ] && continue
    "$PY" from_image.py "refs/sheet/$num.png" "$name" $common $extra
done
# Three sprites sit too close together on the sheet to be cut apart automatically.
"$PY" from_image.py refs/full-sheet.png marigold    --crop 8,1028,145,1225   $common $extra
"$PY" from_image.py refs/full-sheet.png flowerpot   --crop 140,1160,308,1315 $common $extra
"$PY" from_image.py refs/full-sheet.png gloomshroom --crop 308,1135,508,1315 $common $extra

# The chomper picture is a much bigger, sharper copy than the sheet's, so it wins.
"$PY" from_image.py refs/chomper.png chomper --drop 170,146,170 --drop-tol 60 --merge 36 $extra

for f in 0.75 0.6 0.5 0.4; do "$PY" make_small.py --factor $f; done   # every plant shrunk by the same amount
"$PY" make_scaled.py   # 2x and 3x for a single plant in a big window
"$PY" make_themes.py
[ "$extra" = "--png" ] && "$PY" sheet.py
"$PY" make_bash.py     # the bash version's bundle in bash/build/ (copy it to the machine and run install.sh)
