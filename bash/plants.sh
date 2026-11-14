# shellcheck shell=bash
# Garden plant banner for bash 4.2+ on any Unix-like system. Source it from ~/.bashrc (see install.sh).
#
#   plants              one random plant, as big as the window allows
#   plants <name>       that plant
#   plants garden       random plants side by side at their real pixels, until the row is full
#   plants garden 8     eight plants: fewer than fit stay full size, more are shrunk together
#                       to fit, or as many as the smallest size allows
#   plants list         the names
#   plants reset        put the terminal's own colours back
#
# PLANTS_THEME=0 stops the tab being tinted to match the plant.
# PLANTS_COLS / PLANTS_ROWS pretend the window is that big (for testing).

# Older bash (macOS ships 3.2) lacks what this needs: say so once, instead of failing at every start.
if (( BASH_VERSINFO[0] < 4 || (BASH_VERSINFO[0] == 4 && BASH_VERSINFO[1] < 2) )); then
    plants() { echo "plants: needs bash 4.2 or newer (this is $BASH_VERSION)" >&2; return 1; }
    return 0 2>/dev/null || exit 0
fi

# the art sits next to this file unless told otherwise
PLANTS_DIR="${PLANTS_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
PLANTS_THEME="${PLANTS_THEME:-1}"

# width and height of every banner, keyed "kind-name"
declare -gA _PLANTS_W=() _PLANTS_H=()

_plants_shuffle() {   # shuf where it exists (GNU coreutils), otherwise a random sort in awk
    if command -v shuf >/dev/null 2>&1; then shuf "$@"
    else
        # seeded from bash's $RANDOM and the process id: awk's own srand() only changes once a second
        awk -v seed="$RANDOM$$" 'BEGIN { srand(seed) } { print rand() "\t" $0 }' | sort -n | cut -f2- |
            { if [[ ${1:-} == -n ]]; then head -n "$2"; else cat; fi; }
    fi
}

_plants_load_index() {
    (( ${#_PLANTS_W[@]} )) && return
    local kind name w h
    while IFS=$'\t' read -r kind name w h; do
        [[ -n $name ]] || continue
        _PLANTS_W[$kind-$name]=$w
        _PLANTS_H[$kind-$name]=$h
    done < "$PLANTS_DIR/index.tsv"
}

_plants_names() {
    local key
    for key in "${!_PLANTS_W[@]}"; do [[ $key == big-* ]] && printf '%s\n' "${key#big-}"; done | sort
}

_plants_show() {   # print one banner file, with its tab tint first
    local base=$1
    if [[ $PLANTS_THEME == 1 && -r $PLANTS_DIR/art/$base.theme ]]; then
        cat "$PLANTS_DIR/art/$base.theme"
    fi
    printf '\n'
    cat "$PLANTS_DIR/art/$base.ans"
    printf '\n'
}

# Fill a row from the shuffled names: each plant that still fits goes in, one that doesn't is
# skipped for a narrower one later, and it stops when the names run out, the row is full, or
# `want` plants are in. Leaves the chosen "kind-name" keys in _PLANTS_ROW.
_plants_pack() {
    local kind=$1 want=$2 width=$3 room=$4 used=-2 name key
    _PLANTS_ROW=()
    for name in "${_PLANTS_SHUFFLED[@]}"; do
        (( ${#_PLANTS_ROW[@]} >= want || width - used - 2 < 8 )) && break
        key=$kind-$name
        [[ -n ${_PLANTS_W[$key]} ]] || continue
        (( _PLANTS_H[$key] > room || used + 2 + _PLANTS_W[$key] > width )) && continue
        _PLANTS_ROW+=("$key")
        (( used += 2 + _PLANTS_W[$key] ))
    done
}

_plants_garden() {
    local count=$1 width=$2 room=$3 kind best=() tall=0 key i
    mapfile -t _PLANTS_SHUFFLED < <(_plants_names | _plants_shuffle)
    (( ${#_PLANTS_SHUFFLED[@]} )) || { echo "plants: no plants installed" >&2; return 1; }
    _plants_pack big 9999 "$width" "$room"                     # real pixels, as many as fit
    if (( count > 0 && count < ${#_PLANTS_ROW[@]} )); then
        _plants_pack big "$count" "$width" "$room"            # asked for fewer: just that many
    elif (( count > ${#_PLANTS_ROW[@]} )); then
        best=("${_PLANTS_ROW[@]}")                               # asked for more: shrink together
        for kind in s75 s60 s50 s40; do
            _plants_pack "$kind" "$count" "$width" "$room"
            (( ${#_PLANTS_ROW[@]} > ${#best[@]} )) && best=("${_PLANTS_ROW[@]}")
            (( ${#_PLANTS_ROW[@]} >= count )) && break
        done
        _PLANTS_ROW=("${best[@]}")
    fi
    if (( ${#_PLANTS_ROW[@]} == 0 )); then                      # not even one fits at real size
        for kind in s75 s60 s50 s40; do
            _plants_pack "$kind" 9999 "$width" "$room"
            (( ${#_PLANTS_ROW[@]} )) && break
        done
    fi
    (( ${#_PLANTS_ROW[@]} )) || return 0                         # window too small for any plant

    for key in "${_PLANTS_ROW[@]}"; do (( _PLANTS_H[$key] > tall )) && tall=${_PLANTS_H[$key]}; done
    # each plant becomes a column of exactly `tall` rows, sitting on the shared baseline;
    # paste puts them side by side, the extra space on all but the last makes a two-space gap
    local tmp cols=() last=$(( ${#_PLANTS_ROW[@]} - 1 )) pad gap r line
    tmp=$(mktemp -d) || return 1
    for i in "${!_PLANTS_ROW[@]}"; do
        key=${_PLANTS_ROW[$i]}
        printf -v pad '%*s' "${_PLANTS_W[$key]}" ''
        gap=''; (( i < last )) && gap=' '
        {
            for (( r = _PLANTS_H[$key]; r < tall; r++ )); do printf '%s%s\n' "$pad" "$gap"; done
            while IFS= read -r line; do printf '%s%s\n' "$line" "$gap"; done < "$PLANTS_DIR/art/$key.ans"
        } > "$tmp/$i"
        cols+=("$tmp/$i")
    done
    printf '\n'
    paste -d ' ' "${cols[@]}"
    printf '\n'
    rm -rf "$tmp"
}

plants() {
    local which=${1:-random} count=${2:-0} cols rows width room kind key
    if ! [[ $count =~ ^[0-9]+$ ]]; then count=0; fi
    [[ -r $PLANTS_DIR/index.tsv ]] || { echo "plants: nothing installed in $PLANTS_DIR" >&2; return 1; }
    _plants_load_index
    cols=${PLANTS_COLS:-$(tput cols 2>/dev/null || echo 80)}
    rows=${PLANTS_ROWS:-$(tput lines 2>/dev/null || echo 24)}
    # Sizes are in character cells, so a bigger font is the same as a smaller window. The last
    # column is never used: writing into it makes the terminal wrap and splits every row.
    width=$(( cols - 1 )) room=$(( rows - 2 ))
    case $which in
        list)   _plants_names | paste -sd ' ' | sed 's/ /, /g'; return ;;
        reset)  printf '\033]110\033\\\033]111\033\\\033]112\033\\'; return ;;
        garden) _plants_garden "$count" "$width" "$room"; return ;;
        random)   # a random plant among those that fit this window at some size; none fit, nothing shown
            local name
            while IFS= read -r name; do
                key=$(_plants_fit "$name" "$width" "$room") && { _plants_show "$key"; return; }
            done < <(_plants_names | _plants_shuffle)
            return ;;
    esac
    if [[ -z ${_PLANTS_W[big-$which]} ]]; then
        echo "plants: nothing called '$which'. Try random, garden, or a name from 'plants list'." >&2
        return 1
    fi
    if key=$(_plants_fit "$which" "$width" "$room"); then _plants_show "$key"; return; fi
    # asked for by name but too big for the window at every size it has: the smallest of them
    for kind in s40 s50 s60 s75 big; do
        [[ -n ${_PLANTS_W[$kind-$which]} ]] && { _plants_show "$kind-$which"; return; }
    done
}

_plants_fit() {   # the biggest size of a plant that fits the window, as "kind-name"; fails if none
    local name=$1 width=$2 room=$3 kind key
    for kind in x3 x2 big s75 s60 s50 s40; do
        key=$kind-$name
        [[ -n ${_PLANTS_W[$key]} ]] || continue
        if (( _PLANTS_W[$key] <= width && _PLANTS_H[$key] <= room )); then printf '%s' "$key"; return 0; fi
    done
    return 1
}
