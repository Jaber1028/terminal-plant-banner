# Garden plant banner on terminal start. Art lives in ~\.config\pvz-banner (make_big.py rebuilds it).
#   plants               one big plant, picked at random
#   plants garden        the whole row at double size (shows as many plants as the window fits)
#   plants classic       the small original row
#   plants peashooter    or any other plant; "plants list" shows the names
# $PlantsOnStart sets what a new terminal shows: random, garden, classic, a plant name, or off.
$PlantsOnStart = 'random'
# $PlantsTheme: recolour the tab to match the plant shown. "plants reset" restores the normal colours.
$PlantsTheme = $true
# $PlantsGarden: 'quality' keeps the garden's plants big (three to five, as many as fit);
# 'quantity' always shows five, shrinking them to fit.
$PlantsGarden = 'quality'
function plants {
    param([string]$Which = 'random', [int]$Columns = 0, [int]$Rows = 0)   # -Columns/-Rows: pretend the window is this big
    $dir = "$HOME\.config\pvz-banner"
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
    $sizes = 'x3', 'x2', 'big', 'small60', 'small50', 'small40', 'small30', 'small20'
    # One plant on its own is drawn as big as the window allows; the garden stops at normal size,
    # so a single plant is always the bigger one.
    $sized = {
        param($name)
        foreach ($kind in $sizes) {
            $f = "$dir\out\$kind-$name.ans"
            if (-not (Test-Path $f)) { continue }
            $art = & $load $f
            if ($art.Width -le $width -and $art.Lines.Count -le $height - 2) { return $f }
        }
        "$dir\out\small20-$name.ans"
    }
    if ($Which -eq 'random') { $Which = (Get-ChildItem "$dir\out\big-*.ans" | Get-Random).BaseName -replace '^big-' }
    $file = switch ($Which) {
        'garden'  {   # random plants side by side on one baseline: five at the biggest size that fits,
                      # or fewer when even the smallest five are too wide for the window
            $room = $height - 2
            $names = @((Get-ChildItem "$dir\out\big-*.ans" | Get-Random -Count 5).BaseName -replace '^big-')
            $kinds = 'big', 'small60', 'small50', 'small40', 'small30', 'small20'
            # $PlantsGarden 'quality': the biggest size at which at least three fit (up to five);
            # 'quantity': always five, shrinking them as far as needed. Either way, fewer only as a last resort.
            $tries = if ($PlantsGarden -eq 'quantity') {
                foreach ($count in 5, 4, 3, 2, 1) { foreach ($kind in $kinds) { , @($kind, $count) } }
            } else {
                foreach ($kind in $kinds) { foreach ($count in 5, 4, 3) { , @($kind, $count) } }
                foreach ($count in 2, 1) { foreach ($kind in $kinds) { , @($kind, $count) } }
            }
            $picks = $null
            foreach ($t in $tries) {
                $kind, $count = $t
                $try = @(foreach ($n in $names[0..($count - 1)]) { & $load "$dir\out\$kind-$n.ans" })
                $used = ($try | ForEach-Object { $_.Width } | Measure-Object -Sum).Sum + 2 * ($try.Count - 1)
                $tall = ($try | ForEach-Object { $_.Lines.Count } | Measure-Object -Maximum).Maximum
                if ($used -le $width -and $tall -le $room) { $picks = $try; break }
            }
            if (-not $picks) { $picks = @(& $load "$dir\out\small20-$($names[0]).ans") }
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
            if ($width -ge 96) { "$dir\saved\small-row\banner.ans" } else { plants garden -Columns ($width + 1) -Rows $height; return }
        }
        'reset'   { Write-Host "`e]110`e\`e]111`e\`e]112`e\" -NoNewline; return }   # back to the terminal's own colours
        'list'    { Write-Host ((Get-ChildItem "$dir\out\big-*.ans").BaseName -replace '^big-' -join ', '); return }
        default   { if (Test-Path "$dir\out\big-$Which.ans") { & $sized $Which } }
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
