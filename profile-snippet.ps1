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
        'garden'  { foreach ($n in 5, 4, 3, 2, 1) { if ($width -ge 36 * $n) { "$dir\out\garden-$n.ans"; break } } }
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
