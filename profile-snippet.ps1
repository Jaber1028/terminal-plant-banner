# Garden plant banner on terminal start. Art lives in ~\.config\pvz-banner (make_big.py rebuilds it).
#   plants               one big plant, picked at random
#   plants garden        the whole row at double size (shows as many plants as the window fits)
#   plants classic       the small original row
#   plants peashooter    or any other plant; "plants list" shows the names
# $PlantsOnStart sets what a new terminal shows: random, garden, classic, a plant name, or off.
$PlantsOnStart = 'random'
# $PlantsTheme: recolour the tab to match the plant shown. "plants reset" restores the normal colours.
$PlantsTheme = $true
function plants {
    param([string]$Which = 'random')
    $dir = "$HOME\.config\pvz-banner"
    $width = $Host.UI.RawUI.WindowSize.Width
    $file = switch ($Which) {
        'random'  {   # only plants short enough for this window, so a tall one never scrolls its top away
            $room = $Host.UI.RawUI.WindowSize.Height - 2
            $fits = Get-ChildItem "$dir\out\big-*.ans" | Where-Object { [IO.File]::ReadAllLines($_.FullName).Count -le $room }
            if (-not $fits) { $fits = Get-ChildItem "$dir\out\big-*.ans" }
            ($fits | Get-Random).FullName
        }
        'garden'  {   # 5 random small plants side by side (about the room of two big ones), one baseline
            $room = $Host.UI.RawUI.WindowSize.Height - 2
            $picks = @(); $used = 0
            foreach ($f in (Get-ChildItem "$dir\out\small-*.ans" | Get-Random -Count 99)) {
                if ($picks.Count -ge 5) { break }
                $lines = [IO.File]::ReadAllLines($f.FullName) | Where-Object { ($_ -replace "`e\[[0-9;]*m", '').Trim() }
                if ($lines.Count -gt $room) { continue }
                $w = ($lines | ForEach-Object { ($_ -replace "`e\[[0-9;]*m", '').Length } | Measure-Object -Maximum).Maximum
                if ($used + $w + 1 -gt $width) { continue }
                $picks += , @{ Lines = @($lines); Width = $w }; $used += $w + 1
            }
            $tall = ($picks | ForEach-Object { $_.Lines.Count } | Measure-Object -Maximum).Maximum
            $out = for ($r = 0; $r -lt $tall; $r++) {
                ($picks | ForEach-Object {
                    $i = $r - ($tall - $_.Lines.Count)
                    $text = if ($i -ge 0) { $_.Lines[$i] } else { '' }
                    $text + "`e[0m" + (' ' * ($_.Width - ($text -replace "`e\[[0-9;]*m", '').Length))
                }) -join ' '
            }
            Write-Host ("`n" + ($out -join "`n") + "`n"); return
        }
        'classic' { "$dir\saved\small-row\banner.ans" }
        'reset'   { Write-Host "`e]110`e\`e]111`e\`e]112`e\" -NoNewline; return }   # back to the terminal's own colours
        'list'    { Write-Host ((Get-ChildItem "$dir\out\big-*.ans").BaseName -replace '^big-' -join ', '); return }
        default   { "$dir\out\big-$Which.ans" }
    }
    if ($file -and (Test-Path $file)) {
        # recolour this tab (background, text, cursor) to suit the plant, when it has a theme
        $theme = [IO.Path]::ChangeExtension($file, '.theme')
        if ($PlantsTheme -and (Test-Path $theme)) { Write-Host ([IO.File]::ReadAllText($theme)) -NoNewline }
        Write-Host ([IO.File]::ReadAllText($file)) -NoNewline
    }
    else { Write-Host "plants: nothing called '$Which'. Try random, garden, classic, or a name from 'plants list'." }
}
# Skipped for scripts, redirected output, Claude Code's own shells and windows under 60 columns.
if ($PlantsOnStart -ne 'off' -and [Environment]::UserInteractive -and -not [Console]::IsOutputRedirected -and -not $env:CLAUDECODE -and
    -not ([Environment]::GetCommandLineArgs() -match '^-(c|command|f|file|e|ec|enc|encodedcommand|noni|noninteractive)$') -and
    $Host.UI.RawUI.WindowSize.Width -ge 60) { plants $PlantsOnStart }
