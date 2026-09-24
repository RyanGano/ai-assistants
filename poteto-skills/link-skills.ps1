# Creates a directory junction in ..\skills for every skill folder here, so
# Claude Code discovers them through ~/.claude/skills. Safe to re-run.
$ErrorActionPreference = 'Stop'
$skillsDir = Join-Path $PSScriptRoot '..\skills' | Resolve-Path

Get-ChildItem $PSScriptRoot -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } | ForEach-Object {
    $link = Join-Path $skillsDir $_.Name
    $existing = Get-Item $link -ErrorAction SilentlyContinue
    if ($existing -and $existing.LinkType -eq 'Junction' -and $existing.Target -eq $_.FullName) {
        Write-Host "ok      $($_.Name)"
    } elseif ($existing) {
        Write-Warning "skipped $($_.Name): $link already exists and is not a junction to $($_.FullName)"
    } else {
        New-Item -ItemType Junction -Path $link -Target $_.FullName | Out-Null
        Write-Host "linked  $($_.Name)"
    }
}
