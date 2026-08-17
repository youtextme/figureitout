# figureitout

**An AI agent finishes work when the checks pass — not when it sounds confident.**

`figureitout` is a small skill (one markdown file) you give Cursor, Devin, Claude, Codex, or any CLI agent. After that, every message is a job: the agent states what “done” looks like, does the work, and proves it with evidence.

It is not a new model. It is not a 30-step framework. It is operating law for an agent that already has tools.

## Why this exists

Chat optimizes for the next reply. Work needs a **boolean**: did the checks pass?

- A plan is a guess about the future.
- A passing test, a file on disk, a command output — those are knowledge.
- `figureitout` treats guesses as unfinished work.

That is the whole idea. Everything else is install.

## Full mental model

The installable skill stays short. The full operating law — every concern, why it exists, and the public GitHub projects it is composed from — is in [`mentalModal.md`](mentalModal.md). `/letscook` means run the objective.

The epistemological core — what it takes to deem something true, three tenets that cannot be split, memory that is not chat — is in [`RUN_FOREST.md`](RUN_FOREST.md). Read that before any skill file if you are building a runner from scratch. **How to build** it from scratch and install it as the default objective runner (Cursor, Devin, Claude, OpenClaw, CLI, anything that reads `AGENTS.md`) is in [`HOW_TO_BUILD.md`](HOW_TO_BUILD.md). The Cursor-specific file tree (one implementation) is in [`figureItOutObjective.md`](figureItOutObjective.md).

## How to build

From scratch, then install as the **default** runner in the IDE and CLI
you actually have: [`HOW_TO_BUILD.md`](HOW_TO_BUILD.md).

That file names the community loops (control graph, multi-agent crew,
typed judges, memory that is not chat) and the paths for Cursor, Devin,
Claude, OpenClaw, `python -m figureitout`, and any `AGENTS.md` host.

## Install the package (clone)

```bash
git clone https://github.com/youtextme/figureitout
cd figureitout
pip install -e ".[dev]"
python -m figureitout --install
python -m figureitout --mock "write hello world"
pytest -q
```

## Install in one prompt

1. Open a new chat in Cursor, Devin, or Claude.
2. Paste the entire contents of [`PROMPT.md`](PROMPT.md).
3. Send it.

The agent writes the skill into the project and follows it from then on. No API keys. No dashboard. No extra product to learn.

Repo: [github.com/youtextme/figureitout](https://github.com/youtextme/figureitout)

## Install by copy (30 seconds)

Clone or download this repo, then copy `SKILL.md`:

| Tool | Put the file here |
|------|-------------------|
| **Cursor** | `.cursor/skills/figureitout/SKILL.md` (this project) and/or `~/.cursor/skills/figureitout/SKILL.md` (all projects). Reload the window. |
| **Devin** | `.devin/skills/figureitout/SKILL.md` |
| **Claude** | `.claude/skills/figureitout/SKILL.md`, or paste `SKILL.md` into project instructions |
| **Codex / any AGENTS.md agent** | copy [`AGENTS.md`](AGENTS.md) into the repo root (merge if one exists) |
| **CLI** | paste [`PROMPT.md`](PROMPT.md) as the system or first user message |

Windows (PowerShell), from this folder:

```powershell
.\install.ps1
```

or:

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.cursor\skills\figureitout" | Out-Null
Copy-Item SKILL.md "$HOME\.cursor\skills\figureitout\SKILL.md"
```

macOS / Linux:

```bash
chmod +x install.sh && ./install.sh
```

## How a run works

```
do not answer first
        ↓
lock the goal and the predicates (unevaluated = false)
        ↓
first principles + live lookup + a real experiment
        ↓
board + steer questions (proceed if no steer)
        ↓
do the work
        ↓
check evidence ──fail──► fix and check again
        ↓ pass
raise the bar once if the result is sloppy
        ↓
checkpoint so any agent can resume
        ↓
report what changed + the proof
```

The agent does not wait for you to approve ordinary tool use. It stops only if a paid secret is missing from the environment, or if the next step would destroy production with no recovery.

To sandbox a run: set `FIGUREITOUT_LOCKDOWN=1`.
To continue a stopped run: `python -m figureitout --resume RUN_ID`.

## Who this is for

**If you use AI to get work done** — paste `PROMPT.md` once. After that, ask for the outcome you want (“add login”, “fix the failing test”, “write the README”). You should get a finished change plus proof, not a tutorial.

**If you build agent systems** — this skill is the contract: objectives, evidence, a loop that cannot end on a plan, and a hard stop list. Drop `SKILL.md` into any IDE that loads agent skills. You do not need a Python stack to use it.

## What you do not need

- No theme codes, phase numbers, or internal nicknames
- No list of libraries to install before the skill works
- No API keys typed into chat (the agent reads the environment)
- No browser clicking unless the job *is* the UI

## Optional Python runner

Some repos ship a `figureitout` package. If yours does:

```bash
python -m figureitout --install
python -m figureitout "your objective"
```

`--install` copies this skill into Cursor/Devin skill folders. The markdown skill is enough on its own.

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, paste it.
