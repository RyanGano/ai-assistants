# Junctions imported skill sets into the user-level skills folder. Safe to re-run.
#
#   link-skills.ps1                      link every imported set (folders beside the
#                                        skills folder that hold an .upstream.json)
#   link-skills.ps1 -ImportDir <path>    link one set
#
# The skills folder is ~/.claude/skills, or the folder it is a junction/symlink to.
# Each skill folder in a set gets a junction at <skills>\<name>. When the skills
# folder sits in a git repo, each junction is also added to that repo's .gitignore.
# Existing entries are never replaced: a name already taken by something else is
# reported as a collision and skipped.
param([string]$ImportDir)
$ErrorActionPreference = 'Stop'

$userSkills = Join-Path $HOME '.claude\skills'
$item = Get-Item $userSkills
$skillsDir = if ($item.LinkType) { (Resolve-Path ($item.Target | Select-Object -First 1)).Path } else { $item.FullName }
$root = Split-Path $skillsDir -Parent

$sets = if ($ImportDir) { @(Get-Item (Resolve-Path $ImportDir)) }
        else { Get-ChildItem $root -Directory | Where-Object { Test-Path (Join-Path $_.FullName '.upstream.json') } }

$gitignore = Join-Path $root '.gitignore'
$inRepo = Test-Path (Join-Path $root '.git')
$ignored = if ($inRepo -and (Test-Path $gitignore)) { Get-Content $gitignore } else { @() }
$newIgnores = @()
$skillsRel = Split-Path $skillsDir -Leaf

foreach ($set in $sets) {
    Get-ChildItem $set.FullName -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } | ForEach-Object {
        $link = Join-Path $skillsDir $_.Name
        $existing = Get-Item $link -ErrorAction SilentlyContinue
        if ($existing -and $existing.LinkType -eq 'Junction' -and ((Resolve-Path $existing.Target).Path -eq $_.FullName)) {
            Write-Host "ok        $($_.Name)"
        } elseif ($existing) {
            Write-Warning "collision $($_.Name): $link already exists and does not point to $($_.FullName)"
            return
        } else {
            New-Item -ItemType Junction -Path $link -Target $_.FullName | Out-Null
            Write-Host "linked    $($_.Name)  ->  $($set.Name)\$($_.Name)"
        }
        $pattern = "$skillsRel/$($_.Name)/"
        if ($inRepo -and $ignored -notcontains $pattern -and $ignored -notcontains $pattern.TrimEnd('/')) { $newIgnores += $pattern }
    }
}

if ($newIgnores) {
    $block = @('', "# Junctions to imported skill sets (real files are tracked in the set's folder).") + $newIgnores
    Add-Content -Path $gitignore -Value $block -Encoding utf8
    Write-Host "gitignored $($newIgnores.Count) junction(s) in $gitignore"
}
