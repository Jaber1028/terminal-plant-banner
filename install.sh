#!/usr/bin/env bash
# One-step install for Linux, macOS and other Unix-like systems, straight from a clone:
#   bash install.sh
# Builds the banners (Python 3; Pillow optional) and installs the bash version for this user.
# To install on another machine instead, copy bash/build/ there after `python3 build.py` and run
# its install.sh.
set -euo pipefail
cd "$(dirname "$0")"
PY=""
for p in python3 python; do   # the first that is really Python 3.6+
    if command -v "$p" >/dev/null && "$p" -c 'import sys; sys.exit(sys.version_info < (3, 6))' 2>/dev/null; then PY=$p; break; fi
done
[[ -n $PY ]] || { echo "install.sh: Python 3.6+ is needed to build the banners" >&2; exit 1; }
"$PY" build.py
bash bash/build/install.sh
