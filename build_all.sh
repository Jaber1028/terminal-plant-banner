#!/usr/bin/env bash
# Rebuilds every banner in out/ from the reference pictures in refs/ plus the drawn plants.
#   bash build_all.sh          rebuild
#   bash build_all.sh --png    also write check-<name>.png for each and sheet.png with all of them
cd "$(dirname "$0")" || exit 1
extra="$1"
# one sprite only, no ground shadow, near-identical shades merged, slate ring outside the black outline;
# --snap follows the picture's real pixel edges (art pixels land 3 or 4 picture pixels apart)
common="--pitch 3.5 --snap --main --drop 97,94,89 --drop-tol 16 --merge 36 --halo"

python make_big.py > /dev/null     # the drawn ones; replaced below where the sheet has the same plant

# Every plant from the full reference sheet (refs/full-sheet.png), cut up by split_sheet.py.
grep -v '^#' refs/sheet/names.txt | while read -r num name; do
    [ "$name" = "-" ] && continue
    python from_image.py "refs/sheet/$num.png" "$name" $common $extra
done
# Three sprites sit too close together on the sheet to be cut apart automatically.
python from_image.py refs/full-sheet.png marigold    --crop 8,1028,145,1225   $common $extra
python from_image.py refs/full-sheet.png flowerpot   --crop 140,1160,308,1315 $common $extra
python from_image.py refs/full-sheet.png gloomshroom --crop 308,1135,508,1315 $common $extra

# The chomper picture is a much bigger, sharper copy than the sheet's, so it wins.
python from_image.py refs/chomper.png chomper --drop 170,146,170 --drop-tol 60 --merge 36 --halo $extra

for s in "20 28" "30 42" "40 56" "50 70" "60 84"; do set -- $s; python make_small.py --width $1 --height $2; done   # sizes for `plants garden`
python make_scaled.py   # 2x and 3x for a single plant in a big window
python make_themes.py
[ "$extra" = "--png" ] && python sheet.py
