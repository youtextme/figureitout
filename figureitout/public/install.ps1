# Install figureitout as the default objective runner on this machine.
function Copy-Skill([string]$Dest) {
    New-Item -ItemType Directory -Force -Path $Dest | Out-Null
    Copy-Item -Force SKILL.md (Join-Path $Dest "SKILL.md")
    if (Test-Path PROMPT.md) { Copy-Item -Force PROMPT.md (Join-Path $Dest "PROMPT.md") }
    if (Test-Path HOW_TO_BUILD.md) { Copy-Item -Force HOW_TO_BUILD.md (Join-Path $Dest "HOW_TO_BUILD.md") }
    if (Test-Path RUN_FOREST.md) { Copy-Item -Force RUN_FOREST.md (Join-Path $Dest "RUN_FOREST.md") }
    Write-Host "Installed figureitout to $Dest"
}
Copy-Skill (Join-Path $HOME ".cursor\skills\figureitout")
Copy-Skill (Join-Path $HOME ".agents\skills\figureitout")
$openclaw = Join-Path $HOME ".openclaw"
if (Test-Path $openclaw) {
    Copy-Skill (Join-Path $openclaw "workspace\skills\figureitout")
    Copy-Skill (Join-Path $openclaw "skills\figureitout")
}
Write-Host "Reload the IDE / start a new OpenClaw session. Or: python -m figureitout --install"
