# One command. Run, Forrest, Run! as the default on this Windows machine.
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = $Root
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) {
    Write-Host "🌲 Run, Forrest, Run! — invoked."
    Write-Host "🌲 I cannot install autonomously. I need Python on PATH."
    exit 1
}
& $py.Source -m pip install -e $Root -q
& $py.Source -m runforrestrun --install
& $py.Source -m runforrestrun --watch
Write-Host "🌲 Reload your IDE. Then any prompt is a trail."
