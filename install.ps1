# Copy SKILL.md into Cursor, Devin, and OpenClaw. Run from this folder.
$dests = @(
  (Join-Path $HOME ".cursor\skills\figureitout"),
  (Join-Path $HOME ".openclaw\skills\figureitout"),
  (Join-Path $HOME ".agents\skills\figureitout")
)
foreach ($dest in $dests) {
  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  Copy-Item -Force SKILL.md (Join-Path $dest "SKILL.md")
  Copy-Item -Force PROMPT.md (Join-Path $dest "PROMPT.md")
  Write-Host "Installed figureitout to $dest"
}
Write-Host "Reload the Cursor window (Ctrl+Shift+P, Reload Window)."
