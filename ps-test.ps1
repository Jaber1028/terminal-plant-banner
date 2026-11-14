# Tests the PowerShell version: every view at many window sizes must fit, and a few edge cases.
#   pwsh -NoProfile -File ps-test.ps1        (loads the profile snippet next to this file)
. "$PSScriptRoot/profile-snippet.ps1"
$PSStyle.OutputRendering = 'Ansi'
$codes = "`e\[[0-9;]*m|`e\][^`e]*`e\\"
$bad = 0
$Error.Clear()
$first = ((plants list 6>&1 | Out-String).Trim() -split ', ')[0]
foreach ($size in @(@(30, 12), @(60, 20), @(120, 30), @(240, 65))) {
    foreach ($what in @('random'), @('garden'), @('garden', 2), @('garden', 20), @($first), @('classic')) {
        $o = if ($what.Count -gt 1) { plants $what[0] $what[1] -Columns $size[0] -Rows $size[1] 6>&1 | Out-String }
             else { plants $what[0] -Columns $size[0] -Rows $size[1] 6>&1 | Out-String }
        $lines = @($o -split "`r?`n" | ForEach-Object { $_ -replace $codes, '' })
        $wide = ($lines | Measure-Object -Property Length -Maximum).Maximum
        $tall = @($lines | Where-Object { $_.Trim() }).Count
        $named = $what.Count -eq 1 -and $what[0] -eq $first   # a named plant may exceed a tiny window
        if (-not $named -and ($wide -ge $size[0] -or $tall -gt $size[1])) { $bad++; "TOO BIG: $($what -join ' ') in $($size[0])x$($size[1]) -> $wide x $tall" }
        '{0,-12} {1,4}x{2,-3} -> {3,3} x {4}' -f ($what -join ' '), $size[0], $size[1], $wide, $tall
    }
}
$o = plants nope 6>&1 | Out-String
if ($o -notmatch 'nothing called') { $bad++; 'unknown name should say so' }
"names: $(((plants list 6>&1 | Out-String).Trim() -split ', ').Count)"
"problems: $bad, errors: $($Error.Count)"
