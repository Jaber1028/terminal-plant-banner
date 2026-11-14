# Terminal plant banner

Shows a big, coloured pixel-art plant every time a PowerShell terminal opens, and tints the
tab (background, text, cursor) to match it. Built for Windows Terminal + PowerShell 7.

The art is drawn with truecolor half-block characters, so one character cell holds two pixels.

## Gallery

All 31 plants in the rotation, as they show in the terminal (one is picked at random each time):

![All 31 plants in the rotation](docs/plants.png)

Most are converted from [TomcArts01's pixel art](https://www.newgrounds.com/art/view/tomcarts01/pvz-all-plants-pixel-art)
(see Credits); the peashooter, repeater, wall-nut, potato mine and purple mushroom are drawn by
`make_big.py`. The image is rendered straight from the banner files with `render_ans.py`.

## What's included

- Five original plants, drawn from shapes by `make_big.py`, ready to use in `out/`.
- `from_image.py`, which turns any pixel-art picture into a banner, so you can add your own.
- `make_themes.py`, which works out a matching tab colour theme for every banner.
- `profile-snippet.ps1`, the PowerShell profile code that shows a banner on start-up.

Banners converted from other people's artwork are deliberately not part of this repository.
Bring your own pictures.

## Install

1. Clone this repository to `~\.config\pvz-banner` (the snippet expects that path):

   ```powershell
   git clone https://github.com/Jaber1028/terminal-plant-banner "$HOME\.config\pvz-banner"
   ```

2. Append `profile-snippet.ps1` to your PowerShell profile:

   ```powershell
   Get-Content "$HOME\.config\pvz-banner\profile-snippet.ps1" | Add-Content $PROFILE
   ```

3. Open a new terminal.

## Commands

| Command | Shows |
|---|---|
| `plants` | one plant at random, at normal size (or a smaller copy if the window is too small) |
| `plants <name>` | a specific plant |
| `plants list` | the names available |
| `plants garden` | five random plants side by side, at the biggest size that fits the window |
| `plants classic` | the first, small version of the row |
| `plants reset` | puts the tab's colours back to normal |

In the profile snippet, `$PlantsOnStart` sets what a new terminal shows (`random`, `garden`,
`classic`, a plant name, or `off`) and `$PlantsTheme` turns the tab tinting on or off.

## Adding a plant from a picture

Needs Python 3 and Pillow (`pip install pillow`). Pixel art on a plain background works best.

```
python from_image.py <picture> <name>
python make_themes.py
```

Useful options for `from_image.py`:

| Option | Use |
|---|---|
| `--pitch N` | size of one art pixel in the picture, if the automatic guess is off |
| `--reach 1` | average a 3x3 patch per pixel; better for small or blurry pictures |
| `--main` | keep only the biggest sprite (drops neighbours at the picture's edge) |
| `--drop R,G,B` | remove a colour, such as a ground shadow |
| `--lift-dark 62` | raise the black outer outline to slate so it shows on a dark terminal |
| `--crop l,t,r,b` | use only part of the picture |
| `--png` | also write `check-<name>.png` to inspect the result |

`build_all.sh` shows the options used for a larger personal set and rebuilds everything at once.

## Credits

The pixel art the converted plants come from (made with `from_image.py`; shown in the gallery,
but the source pictures and banner files are not included here) is by [TomcArts01](https://tomcarts01.newgrounds.com/):
[PvZ All Plants Pixel Art](https://www.newgrounds.com/art/view/tomcarts01/pvz-all-plants-pixel-art)
on Newgrounds. Go look at the original.

The plants are characters from *Plants vs. Zombies* by PopCap Games / Electronic Arts. This is
an unofficial fan project with no connection to them.

## Notes

- Tab tinting uses the OSC 10/11/12 escape codes; `plants reset` uses OSC 110/111/112, which
  need a recent Windows Terminal.
- The banner is skipped for scripts, redirected output and windows narrower than 60 columns.
