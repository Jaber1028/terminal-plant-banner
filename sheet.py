"""Pastes check-*.png files side by side into sheet.png so several conversions can be eyeballed at once."""
import glob
import os

from PIL import Image

here = os.path.dirname(os.path.abspath(__file__))
shots = [Image.open(p) for p in sorted(glob.glob(os.path.join(here, "check-*.png")))]
sheet = Image.new("RGB", (sum(s.width + 16 for s in shots), max(s.height for s in shots)), (30, 30, 30))
x = 0
for s in shots:
    sheet.paste(s, (x, sheet.height - s.height))
    x += s.width + 16
sheet.save(os.path.join(here, "sheet.png"))
print(len(shots), "pictures")
