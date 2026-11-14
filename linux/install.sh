#!/usr/bin/env bash
# Run on the Linux box, from the folder holding plants.sh, art/ and index.tsv:
#   bash install.sh
# Copies them to ~/.config/pvz-banner and hooks ~/.bashrc so an interactive login shows a plant,
# and ~/.bash_logout so the tab's colours go back to normal when you log out.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
dest="$HOME/.config/pvz-banner"
mkdir -p "$dest"
if [[ $here != "$dest" ]]; then
    rm -rf "$dest/art"
    cp -r "$here/art" "$here/index.tsv" "$here/plants.sh" "$dest/"
fi

marker='# pvz-banner'
if ! grep -qF "$marker" "$HOME/.bashrc" 2>/dev/null; then
    [[ -f $HOME/.bashrc ]] && cp -p "$HOME/.bashrc" "$HOME/.bashrc.bak-pvz"
    cat >> "$HOME/.bashrc" <<'EOF'

# pvz-banner: a random plant when you log in. Interactive shells on a real terminal only, so scp,
# rsync, cron and `ssh box command` never see it; once per session (shells started inside it
# inherit PLANTS_SHOWN). A login shell, or the first shell of an ssh session: some NAS systems
# start that one through a wrapper as a plain interactive shell, not a login shell.
# `plants` itself is there in every interactive shell.
if [[ $- == *i* && -r "$HOME/.config/pvz-banner/plants.sh" ]]; then
    . "$HOME/.config/pvz-banner/plants.sh"
    if [[ -z $PLANTS_SHOWN && -t 1 && ${TERM:-dumb} != dumb ]] && { shopt -q login_shell || [[ -n $SSH_TTY ]]; }; then
        export PLANTS_SHOWN=1
        plants
        # give the terminal its own colours back on exit (.bash_logout only runs for login shells)
        trap 'if [[ -t 1 ]]; then plants reset; fi' EXIT
    fi
fi
EOF
fi
if ! grep -qF "$marker" "$HOME/.bash_logout" 2>/dev/null; then
    [[ -f $HOME/.bash_logout ]] && cp -p "$HOME/.bash_logout" "$HOME/.bash_logout.bak-pvz"
    cat >> "$HOME/.bash_logout" <<'EOF'

# pvz-banner: give the terminal its own colours back after a plant tinted it
if [[ -t 1 && ${TERM:-dumb} != dumb ]]; then printf '\033]110\033\\\033]111\033\\\033]112\033\\'; fi
EOF
fi
echo "installed in $dest; $(wc -l < "$dest/index.tsv") banners"
