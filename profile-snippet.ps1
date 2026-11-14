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
    param([string]$Which = 'random', [int]$Columns = 0, [int]$Rows = 0)   # -Columns/-Rows: pretend the window is this big
    $dir = "$HOME\.config\pvz-banner"
    $width = if ($Columns) { $Columns } else { $Host.UI.RawUI.WindowSize.Width }
    $height = if ($Rows) { $Rows } else { $Host.UI.RawUI.WindowSize.Height }
    # One plant is drawn at the biggest size that fits the window: double, normal, then the small sizes.
    $sized = {
        param($name)
        foreach ($kind in 'double', 'big', 'small40', 'small30', 'small20') {
            $f = "$dir\out\$kind-$name.ans"
            if (-not (Test-Path $f)) { continue }
            $lines = [IO.File]::ReadAllLines($f)
            $w = ($lines | ForEach-Object { ($_ -replace "`e\[[0-9;]*m", '').TrimEnd().Length } | Measure-Object -Maximum).Maximum
            if ($w -le $width -and $lines.Count -le $height - 2) { return $f }
        }
        "$dir\out\small20-$name.ans"
    }
    if ($Which -eq 'random') { $Which = (Get-ChildItem "$dir\out\big-*.ans" | Get-Random).BaseName -replace '^big-' }
    $file = switch ($Which) {
        'garden'  {   # 5 random small plants side by side (about the room of two big ones), one baseline
            $room = $height - 2
            $picks = @(); $used = 0
            # the biggest size at which five fit this window: 40, 30 or 20 columns each
            $size = foreach ($s in 40, 30, 20) { if (5 * $s + 4 -le $width) { $s; break } }
            if (-not $size) { $size = 20 }
            foreach ($f in (Get-ChildItem "$dir\out\small$size-*.ans" | Get-Random -Count 99)) {
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
        default   { if (Test-Path "$dir\out\big-$Which.ans") { & $sized $Which } }
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
