#!/usr/bin/env bash
# One-step install for Linux, macOS and other Unix-like systems, straight from a clone:
#   bash install.sh
# Builds the banners (needs Python 3; Pillow optional) and installs the bash version for this user.
# To install on another machine instead, copy bash/build/ there after building and run its install.sh.
set -euo pipefail
cd "$(dirname "$0")"
PY=$(command -v python3 || command -v python || true)
if [[ -z $PY ]] || ! "$PY" -c 'import sys; sys.exit(sys.version_info < (3, 6))' 2>/dev/null; then
    echo "install.sh: Python 3.6+ is needed to build the banners" >&2
    exit 1
fi
if (( BASH_VERSINFO[0] < 4 || (BASH_VERSINFO[0] == 4 && BASH_VERSINFO[1] < 2) )); then
    echo "install.sh: note, plants needs bash 4.2+ in your login shell (this is bash $BASH_VERSION;" >&2
    echo "  on macOS install a newer bash, e.g. with Homebrew)" >&2
fi
"$PY" build.py
bash bash/build/install.sh
