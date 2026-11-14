# Terminal plant banner

![A tangle kelp in pixel art, drawn in a terminal tinted to match it](docs/hero.png)

Shows a big, coloured pixel-art plant when a terminal opens, and tints the terminal (background,
text, cursor) to match it. There is a PowerShell version and a bash/zsh version, so it runs on
Windows, Linux and macOS, locally or over ssh.

The art is drawn with truecolor half-block characters, so one character cell holds two pixels.
It needs a terminal with 24-bit colour and a monospace font that has the block characters (most
modern terminals do).

## Gallery

A set of 50 plants, as they show in the terminal (one is picked at random each time):

![50 pixel-art plants](docs/plants.png)

These were converted with `from_image.py` from [TomcArts01's pixel art](https://www.newgrounds.com/art/view/tomcarts01/pvz-all-plants-pixel-art)
(see Credits), which is not included here. Out of the box you get the five plants `make_big.py`
draws itself (peashooter, repeater, wall-nut, potato mine and a mushroom) and the classic row;
add your own from any pixel art.

## What's included

| File | What it does |
|---|---|
| `install.sh` | one-step install of the bash version on Linux, macOS or any Unix-like system |
| `build.py` | builds every size, theme and the bash bundle into `out/` and `bash/build/` |
| `profile-snippet.ps1` | the PowerShell version |
| `bash/` | the bash version (`plants.sh`), its installer and its test |
| `from_image.py` | turns a pixel-art picture into a banner |
| `split_sheet.py` | cuts a sprite sheet into one picture per sprite, numbered for naming |
| `make_big.py`, `make_banner.py` | the plants drawn in code, and the classic row |
| `make_small.py`, `make_scaled.py` | the smaller copies and the 2x/3x copies |
| `make_themes.py`, `make_bash.py` | a colour theme per banner; the bash bundle |
| `render_ans.py`, `sheet.py` | draw banners as PNG images, and put check images side by side |
| `ps-test.ps1`, `bash/test.sh` | check every view fits a range of window sizes |

Both versions need Python 3 once, to build the banners. Pillow (`pip install pillow`) is
optional: without it plants are never drawn smaller than their real size.

## Install: bash or zsh on Linux, macOS or any Unix-like system

```bash
git clone <this repository's URL> pvz-banner
cd pvz-banner
bash install.sh
```

`install.sh` runs `build.py` (every size, a colour theme per banner, and the bash bundle in
`bash/build/`), then installs it for you. The art goes to `~/.local/share/pvz-banner/`, and one
marked block goes into each shell file that needs it:

- `~/.bashrc`, and `~/.bash_profile` too where login shells don't read `~/.bashrc`;
- `~/.zshrc`, when zsh is your shell or you have a `~/.zshrc` (macOS's default). zsh gets the
  same `plants` command, run through bash behind the scenes.

Running it again updates everything in place. To uninstall, delete each block (from
`# pvz-banner start` to `# pvz-banner end`) and that folder; each file you had is backed up first
as `<file>.bak-pvz`.

A plant shows once per terminal session: in a new local terminal, or when you ssh in. It only
draws in an interactive shell on a real terminal at least 60 columns wide, so `ssh host command`,
scp, rsync and cron never see it, and shells started inside the session don't repeat it. The
terminal's colours are put back when the session ends.

Needs bash 4.2 or newer somewhere on the system (it doesn't have to be your login shell), plus
`tput` and `paste`. The installer looks on your PATH and in the usual Homebrew and MacPorts
places. `shuf` is used when there; without it a random sort in `awk` does the same job. Works with
GNU, BSD and BusyBox tools.

**macOS:** the built-in bash is 3.2, so run `brew install bash` first; your login shell (zsh) can
stay as it is. For the smaller sizes, install Pillow into the same `python3` the build uses:
`python3 -m pip install --user pillow` (add `--break-system-packages` if pip asks for it; a
Homebrew Pillow may belong to a different Python), then run `bash install.sh` again.

To install on a machine without Python, build on another one, copy `bash/build/` over and run its
`install.sh`. `bash test.sh` in the installed folder checks every view fits several window sizes.

## Install: PowerShell 7+ on any OS

1. Clone this repository to `~/.config/pvz-banner` (the snippet expects that path) and build:

   ```powershell
   git clone <this repository's URL> "$HOME/.config/pvz-banner"
   cd "$HOME/.config/pvz-banner"
   python build.py        # or python3 build.py
   ```

2. Append `profile-snippet.ps1` to your PowerShell profile:

   ```powershell
   Get-Content "$HOME/.config/pvz-banner/profile-snippet.ps1" | Add-Content $PROFILE
   ```

3. Open a new terminal. `pwsh -NoProfile -File ps-test.ps1` checks every view fits several
   window sizes.

After adding plants of your own (below), run `build.py` again (and `install.sh` for bash).

## Commands

The same in both versions:

| Command | Shows |
|---|---|
| `plants` | one plant at random, as big as the window allows (3x, 2x, normal or smaller) |
| `plants <name>` | a specific plant |
| `plants list` | the names available |
| `plants garden` | random plants side by side at their real pixels, until the row is full |
| `plants garden 8` | eight plants: fewer than fit stay full size; more are shrunk together to fit, or as many as the smallest size allows |
| `plants reset` | puts the terminal's colours back to normal |
| `plants classic` | (PowerShell) the first, small version of the row |

Sizes are counted in character cells, so a bigger font works the same as a smaller window.

Settings: in PowerShell, `$PlantsOnStart` sets what a new terminal shows (`random`, `garden`,
`classic`, a plant name, or `off`) and `$PlantsTheme` turns the tinting on or off. In bash,
`PLANTS_THEME=0` turns the tinting off.

## Adding a plant from a picture

Needs Python 3 and Pillow (`pip install pillow`). Pixel art on a plain background works best.

```
python3 from_image.py <picture> <name>
python3 build.py
```

Useful options for `from_image.py`:

| Option | Use |
|---|---|
| `--pitch N` | size of one art pixel in the picture, if the automatic guess is off |
| `--snap` | follow the picture's real pixel edges; fixes blur when art pixels are 3 or 4 picture pixels apart |
| `--main` | keep only the biggest sprite (drops neighbours at the picture's edge) |
| `--drop R,G,B` | remove a colour, such as a ground shadow |
| `--merge N` | fold colours closer than N together (default 26); removes screenshot speckle |
| `--crop l,t,r,b` | use only part of the picture |
| `--reach 1` | average a 3x3 patch per pixel |
| `--halo` | add a one-pixel slate ring outside the outline |
| `--lift-dark 62` | turn the black outer outline itself to slate |
| `--png` | also write `check-<name>.png` to inspect the result |

For a whole sprite sheet: `python3 split_sheet.py <sheet>` cuts it into `refs/sheet/NN.png` and
writes `refs/sheet/index.png` with each sprite's number on it; convert each piece with
`from_image.py`. A sheet of screenshotted pixel art usually needs `--snap --main --merge 36` and
a `--pitch` matching its pixel size. The files go in `out/` as `big-<name>.ans`; `build.py` makes
the rest.

## Credits

The pixel art the converted plants come from (made with `from_image.py`; shown in the gallery,
but the source pictures and banner files are not included here) is by [TomcArts01](https://tomcarts01.newgrounds.com/):
[PvZ All Plants Pixel Art](https://www.newgrounds.com/art/view/tomcarts01/pvz-all-plants-pixel-art)
on Newgrounds. Go look at the original.

The plants are characters from *Plants vs. Zombies* by PopCap Games / Electronic Arts. This is
an unofficial fan project with no connection to them.

## Notes

- Tinting uses the OSC 10/11/12 escape codes and `plants reset` uses OSC 110/111/112. Terminals
  that don't support them ignore them; the art still draws.
- On start-up the banner is skipped for scripts, redirected output and windows narrower than
  60 columns.

## Licence

The code is under the MIT licence (see `LICENSE`). The licence doesn't cover the reference pixel
art credited above or the Plants vs. Zombies characters.
