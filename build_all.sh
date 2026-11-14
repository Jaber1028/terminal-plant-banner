#!/usr/bin/env bash
# Rebuilds every banner in out/ from the pictures in refs/ plus the drawn plants.
#   bash build_all.sh          rebuild
#   bash build_all.sh --png    also write check-<name>.png for each and sheet.png with all of them
cd "$(dirname "$0")" || exit 1
extra="$1"
common="--lift-dark 62 --main --drop 97,94,89 --drop-tol 16"   # slate outlines, one sprite only, no ground shadow

python make_big.py > /dev/null     # the drawn ones: peashooter, wallnut, repeater, potatomine, mushroom, garden rows

python from_image.py refs/chomper.png chomper --drop 170,146,170 --drop-tol 60 $extra
python from_image.py refs/cactus.png cactus --crop 8,14,240,302 --pitch 3.5 --lift-dark 62 --speck 12 $extra

for name in threepeater peapod stump tallnut icestump torchwood twinsunflower gatlingpea kernelpult \
            sunflower; do
    python from_image.py "refs/$name.png" "$name" --pitch 3.5 $common $extra
done
# small, blurry pictures: a finer grid and a 3x3 average read better than single-pixel sampling
for name in mimenut starfruit magnetshroom doomshroom squash cherries jalapeno snowpea sunshroom cattail cabbagepult melonpult spikeweed; do
    python from_image.py "refs/$name.png" "$name" --pitch 2.8 --reach 1 $common $extra
done
for name in tanglekelp; do
    python from_image.py "refs/$name.png" "$name" --pitch 3.5 $common $extra
done
[ "$extra" = "--png" ] && python sheet.py
python make_themes.py
