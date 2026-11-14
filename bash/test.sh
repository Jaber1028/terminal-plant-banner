#!/usr/bin/env bash
# Runs plants.sh at many window sizes and checks no row is wider or taller than the window.
#   bash test.sh [folder holding plants.sh, art/ and index.tsv]
PLANTS_DIR=${1:-$HOME/.config/pvz-banner}
. "$PLANTS_DIR/plants.sh"
# measuring needs a UTF-8 locale; take whichever one this system has
if [[ ${LC_ALL:-${LANG:-}} != *[Uu][Tt][Ff]* ]]; then
    utf=$(locale -a 2>/dev/null | grep -i -m1 -E '^(C|en_US)\.utf-?8$') && export LC_ALL=$utf
fi
esc=$'\033'
# colour codes and the theme's OSC codes out; a literal ESC keeps this portable to BSD sed
strip() { sed -e "s/${esc}\[[0-9;]*m//g" -e "s/${esc}][^${esc}]*${esc}.//g"; }
bad=0
first=$(plants list | cut -d, -f1)    # a plant this install has, by name
for size in "30 12" "60 20" "120 30" "240 65"; do
    set -- $size
    for what in "random" "garden" "garden 2" "garden 20" "$first"; do
        out=$(PLANTS_COLS=$1 PLANTS_ROWS=$2 plants $what 2>&1)
        # characters, not bytes (some awks count each 3-byte block character as 3): bash's own
        # ${#line} counts characters under a UTF-8 locale
        wide=0
        while IFS= read -r line; do (( ${#line} > wide )) && wide=${#line}; done < <(printf '%s\n' "$out" | strip)
        tall=$(printf '%s\n' "$out" | strip | grep -c '[^ ]')
        if (( wide >= $1 || tall > $2 )); then bad=$((bad + 1)); echo "TOO BIG: $what in $1x$2 -> $wide x $tall"; fi
        printf '%-10s %4sx%-3s -> %3s x %s\n' "$what" "$1" "$2" "$wide" "$tall"
    done
done
plants nope >/dev/null 2>&1 && { echo "unknown name should fail"; bad=$((bad + 1)); }
echo "names: $(plants list | tr ',' '\n' | wc -l)"
echo "problems: $bad"
