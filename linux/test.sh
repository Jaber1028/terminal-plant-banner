#!/usr/bin/env bash
# Runs plants.sh at many window sizes and checks no row is wider or taller than the window.
#   bash test.sh [folder holding plants.sh, art/ and index.tsv]
PLANTS_DIR=${1:-$HOME/.config/pvz-banner}
. "$PLANTS_DIR/plants.sh"
strip() { sed -e 's/\x1b\[[0-9;]*m//g' -e 's/\x1b\][^\x1b]*\x1b\\//g'; }
bad=0
for size in "30 12" "60 20" "120 30" "240 65"; do
    set -- $size
    for what in "random" "garden" "garden 2" "garden 20" "chomper"; do
        out=$(PLANTS_COLS=$1 PLANTS_ROWS=$2 plants $what 2>&1)
        # characters, not bytes: mawk's length() counts each 3-byte block character as 3
        wide=$(printf '%s\n' "$out" | strip | python3 -c 'import sys; print(max([len(l.rstrip("\n")) for l in sys.stdin] or [0]))')
        tall=$(printf '%s\n' "$out" | strip | grep -c '[^ ]')
        if (( wide >= $1 || tall > $2 )); then bad=$((bad + 1)); echo "TOO BIG: $what in $1x$2 -> $wide x $tall"; fi
        printf '%-10s %4sx%-3s -> %3s x %s\n' "$what" "$1" "$2" "$wide" "$tall"
    done
done
plants nope >/dev/null 2>&1 && { echo "unknown name should fail"; bad=$((bad + 1)); }
echo "names: $(plants list | tr ',' '\n' | wc -l)"
echo "problems: $bad"
