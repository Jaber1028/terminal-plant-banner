"""Builds every banner size, theme and the bash bundle from what is in out/. Any OS, Python 3.

    python3 build.py

Run it once after cloning (and again after adding plants with from_image.py). It:
  1. draws the original plants (make_big.py) and the classic row (make_banner.py), keeping any
     plant you already have in out/
  2. makes 75/60/50/40 percent copies (make_small.py)
  3. makes 2x and 3x copies (make_scaled.py)
  4. writes a colour theme per banner (make_themes.py)
  5. writes bash/build/, the bundle the bash version installs from (make_bash.py)

Needs nothing beyond Python 3. If Pillow is installed, step 2 uses its (slightly smoother) resize.
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile

here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "out")


def run(script, *args):
    print(f"-- {script} {' '.join(args)}".rstrip())
    subprocess.run([sys.executable, os.path.join(here, script), *args], cwd=here, check=True)


def main():
    os.makedirs(out, exist_ok=True)
    # make_big.py writes its plants straight into out/; set aside the ones already there and put
    # them back afterwards (even if it fails), so a plant you converted under the same name stays
    have = {os.path.basename(p) for p in glob.glob(os.path.join(out, "big-*.ans"))}
    keep = tempfile.mkdtemp()
    try:
        for name in have:
            shutil.copy2(os.path.join(out, name), keep)
        run("make_big.py")
    finally:
        for name in have:
            shutil.copy2(os.path.join(keep, name), out)
        shutil.rmtree(keep, ignore_errors=True)

    run("make_banner.py")     # `plants classic`
    for factor in ("0.75", "0.6", "0.5", "0.4"):   # uses Pillow when installed, plain Python otherwise
        run("make_small.py", "--factor", factor)
    run("make_scaled.py")
    run("make_themes.py")
    run("make_bash.py")
    count = len(glob.glob(os.path.join(out, "big-*.ans")))
    print(f"done: {count} plants")


if __name__ == "__main__":
    main()
