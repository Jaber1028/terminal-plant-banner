#!/usr/bin/env bash
# Rebuilds every banner in out/ from the pictures in refs/ plus the drawn plants.
#   bash build_all.sh          rebuild
#   bash build_all.sh --png    also write check-<name>.png for each and sheet.png with all of them
cd "$(dirname "$0")" || exit 1
extra="$1"
common="--main --drop 97,94,89 --drop-tol 16 --merge 45"   # black outlines as drawn, one sprite only, no ground shadow, flat colours

python make_big.py > /dev/null     # the drawn ones: peashooter, wallnut, repeater, potatomine, mushroom, garden rows

python from_image.py refs/chomper.png chomper --drop 170,146,170 --drop-tol 60 $extra
python from_image.py refs/cactus.png cactus --crop 8,14,240,302 --pitch 3.5 --speck 12 $extra

for name in threepeater peapod stump tallnut icestump torchwood twinsunflower gatlingpea kernelpult \
            ; do
    python from_image.py "refs/$name.png" "$name" --pitch 3.5 $common $extra
done
# small, blurry screenshots: art pixels land 3 or 4 picture pixels apart, so snap to the real edges
for name in sunflower mimenut starfruit magnetshroom doomshroom squash cherries jalapeno snowpea sunshroom cattail cabbagepult melonpult spikeweed; do
    python from_image.py "refs/$name.png" "$name" --pitch 3.5 --snap $common $extra
done
for name in tanglekelp; do
    python from_image.py "refs/$name.png" "$name" --pitch 3.5 $common $extra
done
[ "$extra" = "--png" ] && python sheet.py
for s in "20 28" "30 42" "40 56" "50 70" "60 84"; do set -- $s; python make_small.py --width $1 --height $2; done   # sizes for `plants garden`
python make_scaled.py   # 2x and 3x for a single plant in a big window
python make_themes.py
