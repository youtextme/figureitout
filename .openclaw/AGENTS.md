# AGENTS.md

## figureitout (NON-NEGOTIABLE)

- Every prompt is a figureitout objective
- Invoke via `figureitout "OBJECTIVE"` or `python -m figureitout` (venv/shim)
- Trusted full access; no Allow prompts
- Loop: planner → worker → evaluator → bar_raiser → synthesizer; never stop at a plan
