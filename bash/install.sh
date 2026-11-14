#!/usr/bin/env bash
# Installs the bash version for this user, from the folder holding plants.sh, art/ and index.tsv
# (bash/build/ after `python3 build.py`, or a copy of it on another machine):
#   bash install.sh
# Copies them to ${XDG_DATA_HOME:-~/.local/share}/pvz-banner and adds one marked block to
# ~/.bashrc (and to ~/.bash_profile where login shells don't read ~/.bashrc), and to ~/.zshrc
# when zsh is your shell or has a ~/.zshrc (zsh runs plants through bash 4.2+).
# Running it again replaces the blocks and the art; to uninstall, delete the blocks and the folder.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
dest="${XDG_DATA_HOME:-$HOME/.local/share}/pvz-banner"

# plants.sh needs bash 4.2+. Find one: the bash on PATH, then the usual Homebrew/MacPorts places
# (macOS's own /bin/bash is 3.2).
new_bash=""
for b in "$(command -v bash || true)" /opt/homebrew/bin/bash /usr/local/bin/bash /opt/local/bin/bash /bin/bash; do
    [[ -n $b && -x $b ]] || continue
    if "$b" -c '(( BASH_VERSINFO[0] > 4 || (BASH_VERSINFO[0] == 4 && BASH_VERSINFO[1] >= 2) ))' 2>/dev/null; then
        new_bash=$b; break
    fi
done
if [[ -z $new_bash ]]; then
    echo "install.sh: plants needs bash 4.2 or newer, and none was found." >&2
    echo "  Install one (on macOS: brew install bash), then run this again; your login shell can stay as it is." >&2
    exit 1
fi

mkdir -p "$dest"
if [[ $here != "$dest" ]]; then
    rm -rf "$dest/art"
    cp -r "$here/art" "$here/index.tsv" "$here/plants.sh" "$here/test.sh" "$dest/"
fi
# an earlier version installed to ~/.config/pvz-banner; remove that copy if it is ours (not a clone)
old="$HOME/.config/pvz-banner"
if [[ $old != "$dest" && -f $old/index.tsv && -d $old/art && ! -e $old/.git ]]; then rm -rf "$old"; fi

# the path as written into the shell files: relative to $HOME when it is under it
shown=$dest
[[ $dest == "$HOME"/* ]] && shown="\$HOME/${dest#"$HOME"/}"

# @DIR@ and @BASH@ are filled in below. Both blocks: a random plant once per terminal session,
# only in interactive shells on a real terminal at least 60 columns wide, so scp, rsync, cron and
# `ssh host command` never see it; shells started inside inherit PLANTS_SHOWN and stay quiet.
read -r -d '' bash_block <<'EOF' || true
# pvz-banner start (added by install.sh; delete through 'pvz-banner end' to uninstall)
# A random plant once per terminal session (interactive shells on a real terminal only).
if [[ $- == *i* && -r "@DIR@/plants.sh" ]]; then
    . "@DIR@/plants.sh"
    # declare -F: plants.sh loads fully only in bash 4.2+ (an older bash gets a stub, and no plant)
    if declare -F _plants_fit >/dev/null && [[ -z ${PLANTS_SHOWN:-} && -t 1 && ${TERM:-dumb} != dumb ]] &&
            (( $(tput cols 2>/dev/null || echo 80) >= 60 )); then
        export PLANTS_SHOWN=1
        plants
        trap 'if [[ -t 1 ]]; then plants reset; fi' EXIT   # the terminal's own colours back on exit
    fi
fi
# pvz-banner end
EOF
read -r -d '' zsh_block <<'EOF' || true
# pvz-banner start (added by install.sh; delete through 'pvz-banner end' to uninstall)
# A random plant once per terminal session. zsh runs plants through bash 4.2+.
if [[ -o interactive && -r "@DIR@/plants.sh" && -x "@BASH@" ]]; then
    plants() { "@BASH@" -c '. "$1"; shift; plants "$@"' plants "@DIR@/plants.sh" "$@"; }
    if [[ -z ${PLANTS_SHOWN:-} && -t 1 && ${TERM:-dumb} != dumb ]] && (( $(tput cols 2>/dev/null || echo 80) >= 60 )); then
        export PLANTS_SHOWN=1
        plants
        _pvz_reset() { [[ -t 1 ]] && plants reset; }      # the terminal's own colours back on exit
        autoload -Uz add-zsh-hook && add-zsh-hook zshexit _pvz_reset
    fi
fi
# pvz-banner end
EOF
bash_block=${bash_block//@DIR@/$shown}
zsh_block=${zsh_block//@DIR@/$shown}
zsh_block=${zsh_block//@BASH@/$new_bash}

strip_old() {   # remove any block an earlier run added (this format, or the older unmarked one)
    local f=$1 line skip=0 out=()
    [[ -f $f ]] || return 0
    while IFS= read -r line || [[ -n $line ]]; do
        if (( skip == 1 )); then [[ $line == '# pvz-banner end' ]] && skip=0; continue; fi
        if (( skip == 2 )); then [[ $line == fi ]] && skip=0; continue; fi
        if (( skip == 3 )); then skip=0; continue; fi
        case $line in
            '# pvz-banner start'*) skip=1; continue ;;
            '# pvz-banner: a random plant'*) skip=2; continue ;;          # older block, ends at "fi"
            '# pvz-banner: give the terminal'*) skip=3; continue ;;       # older .bash_logout line pair
        esac
        out+=("$line")
    done < "$f"
    # drop the blank lines the removal leaves at the end of the file
    while (( ${#out[@]} )) && [[ -z ${out[-1]//[[:space:]]/} ]]; do unset 'out[-1]'; done
    if (( ${#out[@]} )); then printf '%s\n' "${out[@]}" > "$f"; else : > "$f"; fi
}

add_block() {   # add_block <file> <block text>
    local f=$1
    [[ -f $f && ! -f $f.bak-pvz ]] && cp -p "$f" "$f.bak-pvz"
    strip_old "$f"
    printf '\n%s\n' "$2" >> "$f"
    echo "hooked $f"
}

add_block "$HOME/.bashrc" "$bash_block"
# login shells read ~/.bash_profile (or ~/.bash_login, ~/.profile) and not ~/.bashrc unless told to
profile=""
for f in "$HOME/.bash_profile" "$HOME/.bash_login" "$HOME/.profile"; do [[ -f $f ]] && { profile=$f; break; }; done
if [[ -z $profile ]]; then
    # no login file at all: a login shell would read nothing, so add the usual one that reads ~/.bashrc
    printf '# added by pvz-banner install.sh: login shells read ~/.bashrc too\n[ -f ~/.bashrc ] && . ~/.bashrc\n' > "$HOME/.bash_profile"
    echo "created $HOME/.bash_profile (reads ~/.bashrc)"
elif ! grep -qE '(\.|source)[[:space:]]+.*\.bashrc' "$profile" 2>/dev/null; then
    add_block "$profile" "$bash_block"
fi
if [[ ${SHELL:-} == */zsh || -f $HOME/.zshrc ]]; then
    add_block "$HOME/.zshrc" "$zsh_block"
fi
strip_old "$HOME/.bash_logout"   # older versions added a line there; the trap above does its job now
[[ -f $HOME/.bash_logout && ! -s $HOME/.bash_logout ]] && rm -f "$HOME/.bash_logout"
echo "installed in $dest; $(wc -l < "$dest/index.tsv") banners; using $new_bash"
