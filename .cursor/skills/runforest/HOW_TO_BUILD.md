# How to build

This is the build and install contract. It is **methods**. The three tenets
(atoms, probe, conservation) live in [`RUN_FOREST.md`](RUN_FOREST.md) and do
not change when a library ships a better loop tomorrow.

You are building **Run Forest** (alias **True That**): an objective runner.
The installable package name in this repo is `figureitout`. Same runner.

Done is a check that came back true against a file, a test, a command, or a
page. A plan is not done.

---

## 1. What you are building

Two layers. Build Layer A always. Build Layer B when you want a CLI that
enforces the same law in pytest.

| Layer | What it is | Enough when |
|-------|------------|-------------|
| **A. Skill runner** | Markdown the host agent inhabits | Any folder. No pip. Cursor / Devin / Claude / OpenClaw / Codex already have tools. |
| **B. Package runner** | `python -m figureitout "objective"` | You want a repeatable graph: laboratory → plan → work → judge → raise → report. |

Layer A is the default objective runner in the IDE. Layer B is the same loop
encoded so a terminal and tests can fail closed when the chat agent is not
the one executing.

---

## 2. Community loops (compose them; do not freeze them)

Do not invent an agent religion. The community already maintains the gears.
They keep improving. Pin the **role**, not a version forever. If a better
public loop appears, swap it in procedural memory. Never promote a library
to a tenet.

| Loop you need | Public project (keeps improving) | What we take | Where it lives here |
|---------------|----------------------------------|--------------|---------------------|
| Control loop: plan → work → conditional retry | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | State graph, edges, durable node names | `figureitout/runner.py` `build_graph()` |
| Multi-agent debate / crew | [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI), [microsoft/autogen](https://github.com/microsoft/autogen) | Operator / skeptic / verifier / communicator plus standing seats | `lifecycle.py` board artifacts, not a vendor lock |
| Compile reasoning instead of a bigger prompt | [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) | Program the checks | predicates in `objective_fn.py` |
| Eval as science | [UKGovernmentBEIS/inspect_ai](https://github.com/UKGovernmentBEIS/inspect_ai) | A scorer that never ran is false | `PredicateBoard` |
| Typed verdicts | [567-labs/instructor](https://github.com/567-labs/instructor), [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) | Schemas over “looks good” | `judge.py`, `truth.py` Claim |
| Model-agnostic SDK | [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | Same laboratory regardless of vendor | `llm.py` |
| Code-act workers | [huggingface/smolagents](https://github.com/huggingface/smolagents), [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) | Workers write files; parent reports paths | `worker.py` |
| Tool protocol | [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | CLI/MCP before browser | `tools.py` |
| Last-mile browser | [browser-use/browser-use](https://github.com/browser-use/browser-use), [microsoft/playwright](https://github.com/microsoft/playwright) | Only when the job is the UI | `computer.py` |
| Research fan-out | [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) | Inventory before synthesis | `research_tool.py`, `context_brief.md` |
| Memory that is not chat | [mem0ai/mem0](https://github.com/mem0ai/mem0), [letta-ai/letta](https://github.com/letta-ai/letta) | Episodic + semantic + checkpoint | `memory.py`, `checkpoint.py` |
| Portable skill format | [anthropics/skills](https://github.com/anthropics/skills) | `SKILL.md` + YAML frontmatter | `.cursor/skills/`, `.claude/`, `.devin/`, `.agents/` |
| One proxy, many models | [BerriAI/litellm](https://github.com/BerriAI/litellm), [ollama/ollama](https://github.com/ollama/ollama) | Never ask for keys in chat | `llm.py` |
| Routing fidelity | [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | Papercut vs laboratory is mechanical | `classify_complexity()` |
| Visible progress | [langfuse/langfuse](https://github.com/langfuse/langfuse) | Status while waiting | job `checkpoint.json` |

The live catalog the laboratory writes into `first_principles.md` is
`FRONTIER_CATALOG` in `figureitout/lifecycle.py`. Stars go stale. URLs
are the pointer. Re-sniff stars when you claim a number.

---

## 3. The graph that must exist

This is the control loop. LangGraph is one implementation. A while-loop
with the same nodes is legal. The **order** is not optional.

```
laboratory → planner → worker → evaluator
                                  ├─ fail & retries left  → worker
                                  ├─ more tasks           → worker
                                  ├─ all tasks passed     → bar_raiser
                                  └─ retries exhausted    → synthesizer (partial)

bar_raiser ─ fail → planner (replan remaining)
           ─ pass → synthesizer → END
```

| Node | Must do | Disk proof |
|------|---------|------------|
| **laboratory** | Lock the noun. Split atoms. Cheap-ping warranted atoms. Design *D* for unknowns. Inventory. One real experiment. Board. Flaws. Use brief. Steer questions. Checkpoint. Do not answer. | `objective_lock.md`, `truth.md`, `experiments.md`, `checkpoint.json` |
| **planner** | 3–5 tasks with falsifiable `success_criteria` and `depends_on`. | plan in run state |
| **worker** | Execute with tools. Write artifacts. Empty stdout is not a result. | files under the job dir |
| **evaluator** | Score against `success_criteria`. Empty cannot pass. | judge score + failure_reason |
| **bar_raiser** | If it works but is sloppy, improve once. | bar score |
| **synthesizer** | Evaluate predicates. Unevaluated required ⇒ not done. Write `result.md`. | `result.md`, updated checkpoint |

Papercut routing is **before** this graph spends a laboratory: one lookup,
one pointer, stop. Self-labeling “just research” is forbidden.

---

## 4. Build from scratch (blank folder)

Do this in order. If you start at the skill file, you will freeze methods
as if they were tenets.

1. Write a failing test: unevaluated claim is not true.
2. Write a failing test: prose (“I read that…”) is not a warrant.
3. Write a failing test: pink vs blue is preference; conversion lift is a fact-claim.
4. Write a failing test: a citation is not already-proven; a cheap ping must re-contact a **stored** pointer; a job folder is not that pointer.
5. Implement `Claim`, kinds, `TruthStore` (semantic), `episodic.jsonl`, `checkpoint.json` (working). Procedural memory is the runner source — preview-only proposals, no mid-run mutation.
6. Implement laboratory **before** any synthesizer: lock, atoms, probe, conserve.
7. Implement the graph in §3. Prefer composing [LangGraph](https://github.com/langchain-ai/langgraph) rather than a private state machine.
8. Only then wrap it in `SKILL.md` with `alwaysApply: true` (hosts that support that flag) and an `AGENTS.md` block (hosts that do not).
9. `pytest` green. Then `--install` so it is the **default** runner, not an optional slash command.

Clone instead of typing if the network is up:

```bash
git clone https://github.com/youtextme/figureitout
cd figureitout
pip install -e ".[dev]"
python -m figureitout --install
python -m figureitout --mock "write hello world"
pytest -q
```

---

## 5. Install as the default objective runner

**Default** means: every prompt is an objective unless the host has no
skill/AGENTS mechanism. The agent must not wait for `/runforest` to start
the loop.

One command from this repo (does every host it can see):

```bash
python -m figureitout --install
```

Skill-only (no Python graph), from this folder:

```bash
chmod +x install.sh && ./install.sh          # macOS / Linux
.\install.ps1                                # Windows
```

Or paste [`PROMPT.md`](PROMPT.md) into a new chat and send it.

### Cursor

| Path | Why |
|------|-----|
| `.cursor/skills/figureitout/SKILL.md` | Project skill, `alwaysApply: true` |
| `~/.cursor/skills/figureitout/SKILL.md` | All projects on this machine |
| `.cursor/rules/figureitout.mdc` | `alwaysApply: true` rule |
| `.cursor/skills/runforest/` and `true-that/` | Invoke names |
| `AGENTS.md` | Mandate block merged, not replaced |

Reload the Cursor window after copy. Trusted full access: do not stop the
loop for Allow. Kill switch: `FIGUREITOUT_LOCKDOWN=1`.

### Devin

| Path | Why |
|------|-----|
| `.devin/skills/figureitout/SKILL.md` | Project |
| Devin app-data `AGENTS.md` | `--install` upserts this when the folder exists |

### Claude Code

| Path | Why |
|------|-----|
| `.claude/skills/figureitout/SKILL.md` | Project skill |
| Claude project instructions | Paste `SKILL.md` if the host has no skills folder |

### OpenClaw

OpenClaw has no `alwaysApply` flag. **Default** is the workspace `AGENTS.md`
plus a skill on the load path ([skills loading order](https://docs.openclaw.ai/tools/skills)).

| Path | Why |
|------|-----|
| `<workspace>/skills/figureitout/SKILL.md` | Highest-precedence workspace skill (default workspace `~/.openclaw/workspace`) |
| `~/.openclaw/skills/figureitout/SKILL.md` | Managed / local |
| `.agents/skills/figureitout/SKILL.md` | Project Agent Skills path |
| `~/.agents/skills/figureitout/SKILL.md` | Personal Agent Skills path (any host that follows the spec) |
| `~/.openclaw/workspace/AGENTS.md` | Merge the figureitout block so every session is an objective |

`--install` writes the Agent Skills paths always, and the OpenClaw paths
when `~/.openclaw` exists (or `OPENCLAW_HOME` is set). Then start a new
OpenClaw session (`/new`) or restart the gateway so the skill is picked up.

### CLI (anything with Python on the machine)

```bash
pip install -e ".[dev]"
python -m figureitout --install
python -m figureitout "your objective"
python -m figureitout --runforest "your objective"
python -m figureitout --true-that "is this warranted"
python -m figureitout --resume RUN_ID
```

`--install` drops a `figureitout` shim on `PATH` when it can
(`~/.local/bin` on Unix).

### Codex, Aider, and any `AGENTS.md` agent

Merge [`AGENTS.md`](AGENTS.md) into the repo root (do not delete other
sections). That file is the portable default when the host has no skill
directory.

### Anything else installed on the computer

1. Copy `SKILL.md` into **every** skills directory that host documents
   (project + user). YAML: `name: figureitout`, `alwaysApply: true` when
   the host supports it.
2. Merge the `AGENTS.md` block at the workspace root the agent actually
   reads (repo root, `~/.openclaw/workspace/AGENTS.md`, Devin app-data).
3. Put the CLI on `PATH` if the host can shell out.
4. Prove default: a new chat given “add a failing test then make it pass”
   does the work instead of describing it.

---

## 6. Files a run must write

Job folder (default `~/.letscook/cursor-jobs/<run_id>/`, or
`FIGUREITOUT_JOBS_DIR`, or lockdown sandbox):

```
objective_lock.md    working memory — the noun and done-sentence
truth.md             atoms, conserved vs unknown, designed D
first_principles.md  irreducible + frontier URLs
context_brief.md     candidates; notes are hypotheses
experiments.md       hypothesis + observation (not “I read that”)
board.md             standing seats + domain crew
flaws.md             how models cheat on this job
use.md               who acts, next action, what to ignore
steer.md             questions; no-steer ⇒ proceed
checkpoint.json      any agent can resume without the chat
predicates.json      unevaluated required = false
result.md            status + evidence
```

Semantic warrants: `semantic_truth.jsonl` under the runner home.
Episodes: `episodic.jsonl`. Procedure does not mutate mid-run.

---

## 7. Acceptance — it is built and default only when

- [ ] `SKILL.md` exists in the host’s project skills dir **and** the user
      skills dir, with `alwaysApply: true` where that flag exists
- [ ] `AGENTS.md` (or OpenClaw workspace `AGENTS.md`) contains the
      figureitout block
- [ ] Cursor: `.cursor/rules/figureitout.mdc` is `alwaysApply: true`
- [ ] OpenClaw: skill visible on `openclaw skills list` (or equivalent)
      after a new session
- [ ] CLI: `python -m figureitout --status` runs; `--mock "write hello world"`
      prints a non-empty result
- [ ] `pytest -q` is green
- [ ] A new chat does not wait for a slash command to treat a prompt as work

Companion files: [`RUN_FOREST.md`](RUN_FOREST.md) (tenets),
[`mentalModal.md`](mentalModal.md) (why each concern exists),
[`figureItOutObjective.md`](figureItOutObjective.md) (Cursor file tree).
