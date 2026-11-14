# Garden plant banner on terminal start. Art lives in ~/.config/pvz-banner (make_big.py rebuilds it).
#   plants               one big plant, picked at random
#   plants garden        random plants at full size across the window; "plants garden 8" asks for eight
#   plants classic       the small original row
#   plants peashooter    or any other plant; "plants list" shows the names
# $PlantsOnStart sets what a new terminal shows: random, garden, classic, a plant name, or off.
$PlantsOnStart = 'random'
# $PlantsTheme: recolour the tab to match the plant shown. "plants reset" restores the normal colours.
$PlantsTheme = $true
function plants {
    # plants garden 8: ask for 8 plants (see the garden below). -Columns/-Rows: pretend the window is this big.
    param([string]$Which = 'random', [int]$Count = 0, [int]$Columns = 0, [int]$Rows = 0)
    $dir = "$HOME/.config/pvz-banner"
    # Sizes are in character cells, so a bigger or smaller font (fewer or more cells) is handled the
    # same way as a smaller or bigger window. The last column is never used: writing into it makes
    # the terminal wrap, which splits every row of the art in two.
    $width = $(if ($Columns) { $Columns } else { $Host.UI.RawUI.WindowSize.Width }) - 1
    $height = if ($Rows) { $Rows } else { $Host.UI.RawUI.WindowSize.Height }
    $visible = { param($s) ($s -replace "`e\[[0-9;]*m", '').Length }
    # A banner file as lines with the empty cells at the end of each row cut off, plus its width.
    $load = {
        param($f)
        $lines = @([IO.File]::ReadAllLines($f) | Where-Object { ($_ -replace "`e\[[0-9;]*m", '').Trim() } |
                   ForEach-Object { ($_ -replace "(`e\[0m )+(`e\[0m)?$", '') + "`e[0m" })
        @{ Lines = $lines; Width = ($lines | ForEach-Object { & $visible $_ } | Measure-Object -Maximum).Maximum }
    }
    # x3/x2: enlarged; big: the real pixels; s75..s40: every plant shrunk by the same amount
    $sizes = 'x3', 'x2', 'big', 's75', 's60', 's50', 's40'
    # One plant on its own is drawn as big as the window allows; the garden stops at normal size,
    # so a single plant is always the bigger one.
    $fits = {   # the biggest size of a plant that fits the window, or nothing
        param($name)
        foreach ($kind in $sizes) {
            $f = "$dir/out/$kind-$name.ans"
            if (-not (Test-Path $f)) { continue }
            $art = & $load $f
            if ($art.Width -le $width -and $art.Lines.Count -le $height - 2) { return $f }
        }
    }
    $sized = {   # as $fits, but a plant asked for by name always shows: the smallest size there is
        param($name)
        $f = & $fits $name
        if ($f) { return $f }
        foreach ($kind in 's40', 's50', 's60', 's75', 'big') { if (Test-Path "$dir/out/$kind-$name.ans") { return "$dir/out/$kind-$name.ans" } }
    }
    if ($Which -eq 'random') {   # a random plant among those that fit this window; none fit, nothing shown
        foreach ($n in ((Get-ChildItem "$dir/out/big-*.ans" | Get-Random -Count 999).BaseName -replace '^big-')) {
            $f = & $fits $n
            if ($f) { $Which = $n; break }
        }
        if (-not $f) { return }
    }
    $file = switch ($Which) {
        'garden'  {   # random plants side by side on one baseline, until the window is full. Every plant
                      # in a garden is drawn at the same scale, so they keep their real sizes relative to each other.
            $room = $height - 2
            $all = @((Get-ChildItem "$dir/out/big-*.ans" | Get-Random -Count 999).BaseName -replace '^big-')
            # Fill the row left to right from the shuffled list: every plant that still fits goes in,
            # one that doesn't is skipped (a narrower one later may fit), and it stops when the list
            # runs out or the space left is too small for any plant.
            $pack = {
                param($kind, $want = 999)
                $row = @(); $used = -2
                foreach ($n in $all) {
                    if ($row.Count -ge $want -or $width - $used - 2 -lt 8) { break }
                    $f = "$dir/out/$kind-$n.ans"
                    if (-not (Test-Path $f)) { continue }
                    $art = & $load $f
                    if ($art.Lines.Count -gt $room -or $used + 2 + $art.Width -gt $width) { continue }
                    $row += , $art; $used += 2 + $art.Width
                }
                , $row
            }
            $picks = & $pack 'big'   # the plants' real pixels, never shrunk: as many as fit
            if ($Count -gt 0 -and $Count -lt $picks.Count) {
                # asked for fewer than fit: just that many
                $picks = & $pack 'big' $Count
            }
            elseif ($Count -gt $picks.Count) {
                # asked for more than fit at real size: shrink them all together until that many fit;
                # if even the smallest size can't hold that many, show as many as it can
                $best = $picks
                foreach ($kind in 's75', 's60', 's50', 's40') {
                    $row = & $pack $kind $Count
                    if ($row.Count -gt $best.Count) { $best = $row }
                    if ($row.Count -ge $Count) { break }
                }
                $picks = $best
            }
            if ($picks.Count -eq 0) {   # only when not even one fits at real size: the biggest shrink that holds one
                foreach ($kind in 's75', 's60', 's50', 's40') {
                    $picks = & $pack $kind
                    if ($picks.Count -ge 1) { break }
                }
            }
            if ($picks.Count -eq 0) { $picks = @(& $load (& $sized $all[0])) }
            $tall = ($picks | ForEach-Object { $_.Lines.Count } | Measure-Object -Maximum).Maximum
            $out = for ($r = 0; $r -lt $tall; $r++) {
                $row = for ($p = 0; $p -lt $picks.Count; $p++) {
                    $art = $picks[$p]
                    $i = $r - ($tall - $art.Lines.Count)
                    $text = if ($i -ge 0) { $art.Lines[$i] } else { '' }
                    # pad every plant but the last to its full width, so the next one starts in line
                    if ($p -lt $picks.Count - 1) { $text + (' ' * ($art.Width - (& $visible $text))) } else { $text }
                }
                $row -join '  '
            }
            Write-Host ("`n" + ($out -join "`n") + "`n"); return
        }
        'classic' {   # the first, fixed-size row; a garden instead when the window is too narrow for it
            if ($width -ge 96) { "$dir/saved/small-row/banner.ans" } else { plants garden -Columns ($width + 1) -Rows $height; return }
        }
        'reset'   { Write-Host "`e]110`e\`e]111`e\`e]112`e\" -NoNewline; return }   # back to the terminal's own colours
        'list'    { Write-Host ((Get-ChildItem "$dir/out/big-*.ans").BaseName -replace '^big-' -join ', '); return }
        default   { if (Test-Path "$dir/out/big-$Which.ans") { & $sized $Which } }
    }
    if ($file -and (Test-Path $file)) {
        # recolour this tab (background, text, cursor) to suit the plant, when it has a theme
        $theme = [IO.Path]::ChangeExtension($file, '.theme')
        if ($PlantsTheme -and (Test-Path $theme)) { Write-Host ([IO.File]::ReadAllText($theme)) -NoNewline }
        Write-Host ("`n" + ((& $load $file).Lines -join "`n") + "`n")
    }
    else { Write-Host "plants: nothing called '$Which'. Try random, garden, classic, or a name from 'plants list'." }
}
# Skipped for scripts, redirected output, Claude Code's own shells and windows under 60 columns.
if ($PlantsOnStart -ne 'off' -and [Environment]::UserInteractive -and -not [Console]::IsOutputRedirected -and -not $env:CLAUDECODE -and
    -not ([Environment]::GetCommandLineArgs() -match '^-(c|command|f|file|e|ec|enc|encodedcommand|noni|noninteractive)$') -and
    $Host.UI.RawUI.WindowSize.Width -ge 60) { plants $PlantsOnStart }
