#!/usr/bin/env bash
# Installs the bash version for this user, from the folder holding plants.sh, art/ and index.tsv
# (bash/build/ after `python3 build.py`, or a copy of it on another machine):
#   bash install.sh
# Copies them to ${XDG_DATA_HOME:-~/.local/share}/pvz-banner and adds one marked block to
# ~/.bashrc (and to ~/.bash_profile where login shells don't read ~/.bashrc, as on macOS).
# Running it again replaces the block and the art; to uninstall, delete the block and that folder.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
dest="${XDG_DATA_HOME:-$HOME/.local/share}/pvz-banner"

# plants.sh needs bash 4.2+; check the bash this user logs in with, not only the one running this
login_bash=bash
[[ ${SHELL:-} == */bash ]] && login_bash=$SHELL
if ! "$login_bash" -c '(( BASH_VERSINFO[0] > 4 || (BASH_VERSINFO[0] == 4 && BASH_VERSINFO[1] >= 2) ))' 2>/dev/null; then
    echo "install.sh: plants needs bash 4.2 or newer; $login_bash is $("$login_bash" -c 'echo $BASH_VERSION')." >&2
    echo "  Install a newer bash (on macOS: brew install bash) and make it your shell, then run this again." >&2
    exit 1
fi
[[ ${SHELL:-} == */bash ]] || echo "install.sh: note, your login shell is ${SHELL:-unknown}; the plant shows in bash sessions."

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
block="# pvz-banner start (added by install.sh; delete through 'pvz-banner end' to uninstall)
# A random plant once per terminal session: interactive shells on a real terminal only, so scp,
# rsync, cron and \`ssh host command\` never see it; shells started inside inherit PLANTS_SHOWN.
if [[ \$- == *i* && -r \"$shown/plants.sh\" ]]; then
    . \"$shown/plants.sh\"
    if [[ -z \${PLANTS_SHOWN:-} && -t 1 && \${TERM:-dumb} != dumb ]] && (( \$(tput cols 2>/dev/null || echo 80) >= 60 )); then
        export PLANTS_SHOWN=1
        plants
        trap 'if [[ -t 1 ]]; then plants reset; fi' EXIT   # the terminal's own colours back on exit
    fi
fi
# pvz-banner end"

strip_old() {   # remove any block an earlier run added (this format, or the older unmarked one)
    local f=$1 tmp line skip=0
    [[ -f $f ]] || return 0
    tmp=$(mktemp)
    while IFS= read -r line || [[ -n $line ]]; do
        if (( skip == 1 )); then [[ $line == '# pvz-banner end' ]] && skip=0; continue; fi
        if (( skip == 2 )); then [[ $line == fi ]] && skip=0; continue; fi
        if (( skip == 3 )); then skip=0; continue; fi
        case $line in
            '# pvz-banner start'*) skip=1; continue ;;
            '# pvz-banner: a random plant'*) skip=2; continue ;;          # older block, ends at "fi"
            '# pvz-banner: give the terminal'*) skip=3; continue ;;       # older .bash_logout line pair
        esac
        printf '%s\n' "$line"
    done < "$f" > "$tmp"
    # drop blank lines left at the end of the file by the removal
    sed -e :a -e '/^\n*$/{$d;N;ba' -e '}' "$tmp" > "$f.pvz-new" && cat "$f.pvz-new" > "$f"
    rm -f "$tmp" "$f.pvz-new"
}

add_block() {
    local f=$1
    [[ -f $f && ! -f $f.bak-pvz ]] && cp -p "$f" "$f.bak-pvz"
    strip_old "$f"
    printf '\n%s\n' "$block" >> "$f"
    echo "hooked $f"
}

add_block "$HOME/.bashrc"
# login shells read ~/.bash_profile (or ~/.bash_login, ~/.profile) and not ~/.bashrc unless told to
profile=""
for f in "$HOME/.bash_profile" "$HOME/.bash_login" "$HOME/.profile"; do [[ -f $f ]] && { profile=$f; break; }; done
if [[ -z $profile ]]; then
    # no login file at all: a login shell would read nothing, so add the usual one that reads ~/.bashrc
    printf '# added by pvz-banner install.sh: login shells read ~/.bashrc too\n[ -f ~/.bashrc ] && . ~/.bashrc\n' > "$HOME/.bash_profile"
    echo "created $HOME/.bash_profile (reads ~/.bashrc)"
elif ! grep -qE '(\.|source)[[:space:]]+.*\.bashrc' "$profile" 2>/dev/null; then
    add_block "$profile"
fi
strip_old "$HOME/.bash_logout"   # older versions added a line there; the trap above does its job now
[[ -f $HOME/.bash_logout && ! -s $HOME/.bash_logout ]] && rm -f "$HOME/.bash_logout"
echo "installed in $dest; $(wc -l < "$dest/index.tsv") banners"
