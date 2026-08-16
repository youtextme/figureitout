# Copy SKILL.md into Cursor (all projects). Run from this folder.
$dest = Join-Path $HOME ".cursor\skills\figureitout"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item -Force SKILL.md (Join-Path $dest "SKILL.md")
Copy-Item -Force PROMPT.md (Join-Path $dest "PROMPT.md")
Write-Host "Installed figureitout to $dest"
Write-Host "Reload the Cursor window (Ctrl+Shift+P, Reload Window)."
