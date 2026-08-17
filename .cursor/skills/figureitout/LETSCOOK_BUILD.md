# /letscook — build an objective runner from scratch

**Audience:** any model, any human, any stack.  
**Product name:** figureitout. `/letscook` means: run figureitout on the rest of the prompt. There is no second product name.  
**Companion repo:** https://github.com/youtextme/figureitout  
**Hosted copy (fetch this):** https://raw.githubusercontent.com/youtextme/figureitout/cursor/laboratory-lifecycle-8e62/LETSCOOK_BUILD.md  
**License:** MIT. Rebuild with your own flavor. Do not waive the predicates.

This file is the rebuild contract. It is not a vibe. When this file and the checks in §12 are true, you have an objective runner. Until then you have a chatbot with extra markdown.

A **flavor** is your choice of graph library, skill folder layout, or model vendor. A **tenet** is not a flavor. Tenets are predicates. If a required predicate was never evaluated, it is **false**.

---

## 0. Read this first — what you are building

Two layers. Always build Layer A. Build Layer B when you want a CLI and tests that can fail a lying model.

| Layer | What it is | When it is enough |
|-------|------------|-------------------|
| **A. Skill** | Markdown the host agent inhabits (`alwaysApply: true`) | Any repo. No pip. Cursor / Claude / Devin / Codex *is* the worker. |
| **B. Package** | `python -m figureitout "objective"` (or your binary) | Repeatable graph + `--install` + pytest. |

Done is not confidence. Done is a check that came back true against a **file**, a **test**, a **command**, or a **page**.

You will be tempted to answer this document by writing a 40-minute essay and calling it a runner. That is the failure mode this whole instrument exists to kill. Implement. Then point at evidence.

### 0.1 Irreducible truths (do not skip)

1. A plan is not done.
2. A number not retrieved is omitted or **blocked**, never invented.
3. The parent session does not hold the artifact. Workers write files. Parents report paths.
4. Chat history is not memory. A checkpoint on disk is memory.
5. Learning is an observation from an experiment, a failed check, or user feedback. Prose is not learning.
6. Simple prompts must stay cheap. Heavy prompts must stay slow and scientific. **Routing is mechanical.** Self-labeling “just a quick research” to skip the runner is cheating.

---

## 1. Implement complexity routing FIRST

If you build the laboratory before the router, every “where is this function?” will burn a board, a first-principles brief, and a thousand tokens. That violates the user’s tenet as hard as shipping dummy KPIs.

### 1.1 Mechanical classifier (copy this, then write tests)

Do **not** ask the model “is this complex?”. Models self-classify as small to be helpful. Use gates.

```python
import re

HEAVY = (
    "build", "implement", "refactor", "rewrite", "migrate", "ship",
    "rebuild", "architecture", "dashboard", "production", "from scratch",
    "test suite", "pull request", "multi-file", "objective runner",
    "skill", "framework", "playbook", "gist",
)

PAPERCUT_HINTS = (
    "where is", "where are", "which file", "find ", "locate ",
    "grep ", "what does", "what is", "explain this",
    "search the web", "look up", "how many stars",
    "quote ", "show me the", "open ",
)

def classify_complexity(objective: str) -> str:
    """Return trivial | papercut | standard | exhaustive."""
    text = (objective or "").strip()
    lower = text.lower()
    words = lower.split()
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]

    if "hello world" in lower:
        return "trivial"
    if "exhaustive" in lower:
        return "exhaustive"
    if any(tok in lower for tok in ("executive", "board pack", "production")) and any(
        tok in lower for tok in ("research", "dashboard", "analysis", "analyse", "analyze", "ship")
    ):
        return "standard"

    heavy = any(tok in lower for tok in HEAVY)
    if heavy:
        return "standard"

    short = len(words) <= 40 and len(sentences) <= 2
    hint = any(h in lower for h in PAPERCUT_HINTS)
    if hint and short:
        return "papercut"
    if len(words) <= 4:
        return "trivial"
    return "standard"
```

### 1.2 Test vectors (these must stay true)

| Prompt | Class | Why |
|--------|-------|-----|
| `where is run_objective defined` | papercut | one lookup, no artifact |
| `what does FIGUREITOUT_LOCKDOWN do` | papercut | one file, short answer |
| `find SKILL.md and quote the loop` | papercut | one file |
| `search the web for GitHub stars of inspect_ai` | papercut | one search, one number with source |
| `write hello world` | trivial | toy; still needs a real deliverable if you claim done |
| `add a failing test then make it pass` | standard | code + evidence |
| `build an executive research pack with live sources` | standard | someone will act |
| `rebuild figureitout from scratch as a skill` | standard | this document |
| `exhaustive production dashboard for execs` | exhaustive | defendable + usable |

### 1.3 What each class is allowed to spend

| Class | Lock sentence | Live lookup | Board / first principles / steer | Checkpoint | Token posture |
|-------|---------------|-------------|-----------------------------------|------------|---------------|
| **trivial** | one line | only if needed | skip | skip | answer; do not philosophize |
| **papercut** | one line | **exactly one** file or one search | skip | skip | do the lookup, cite, stop |
| **standard** | full lock + predicates | inventory + experiments | mandatory | mandatory | slow, scientific, usable |
| **exhaustive** | full lock + predicates | inventory + experiments + extra sniff | mandatory + standing seats | mandatory | token-heavy on purpose |

### 1.4 Hard fail on routing

If **any** of these is true, it is **not** a papercut, even if the prose looks casual:

- A new file will be created that the user will keep (other than a scratch note).
- More than one system must change.
- A test must be written or a command must stay green.
- An executive / customer will act on the output.
- The user said build / ship / rebuild / from scratch / playbook.

Banned self-classifications (write these into the skill so the agent cannot argue around them):

- “just research”
- “just a summary”
- “this looks small”
- “I’ll answer inline because it’s faster”

When in doubt, **upgrade** the class (papercut → standard). Never downgrade to save tokens.

### 1.5 Papercut execution (the thin path)

1. Write one sentence: `This run succeeds when <the file is found / the number is cited / the question is answered from a live source>.`
2. Do the **one** lookup (workspace file **or** one web/CLI search).
3. Answer with the fact and the path/URL.
4. If the lookup failed: say **blocked**, what you tried, how to unblock. Do not invent.
5. Stop. Do not recruit a board. Do not write `first_principles.md`.

---

## 2. Tenets → objective functions

These are the human’s tenets. Each row has a predicate that is **impossible** to be true unless the criterion was met. Implement the predicate. Do not “keep the tenet in mind”.

| # | Tenet | Predicate (must be code or a grep, not a promise) | Evidence |
|---|-------|-----------------------------------------------------|----------|
| 1 | Scientific; remove subjectivity | `PredicateBoard.all_required_true()` is false until every required predicate `evaluated=True` and `passed=True` | `predicates.json` |
| 2 | First principles | File `first_principles.md` contains four headings: Irreducible, Assumptions to test, Reuse, Frontier | job folder |
| 3 | Self-evolving | Lessons append to a preview queue. Runner source is bit-identical during the run | `proposals.jsonl` with `"status": "preview"` |
| 4 | Learn by experiments, not text | `queue_lesson(..., source=)` raises unless source ∈ {`experiment`, `failed_check`, `user_feedback`} and observation is non-empty | tests |
| 5 | Use what is already built; cutting edge | Reuse inventory lists real paths that `exists()`. Frontier URLs are `https://github.com/...` | `first_principles.md`, `frontier.json` |
| 6 | AI-researcher lens | `flaws.md` names ≥6 failure modes, each with “Ruled out by” pointing at a mechanical filter | `flaws.md` |
| 7 | 100% usable; work backwards from use | `use.md` contains `Next action:` and names who acts. Result **leads** with that, not a process diary | `use.md`, `result.md` |
| 8 | Steer after research | `steer.md` has ≥3 questions. File also says: if no steer, proceed. Run does not block on a click | `steer.md` |
| 9 | Recruit teams | `board.md` names operator, skeptic, verifier, communicator + standing seats. Verdict is `provisional pass` or handoff | `board.md` |
| 10 | Turn off / on | `checkpoint.json` has `run_id`, `done_sentence`, `phase`, `predicates`, `next_action`. `load_checkpoint(run_id)` restores them | `--resume RUN_ID` |

**Papercut/trivial exception:** rows 2, 3, 5–9 may be skipped **only** when `classify_complexity` returned `trivial` or `papercut` **and** the routing tests in §1.2 still pass. Rows 1 (a single predicate), 4 (do not fake a lesson), and 10 (optional skip) still apply in spirit: one lock sentence, live-or-blocked, stop.

### 2.1 Predicate object (Layer B)

```python
class Predicate:
    id: str
    statement: str          # "This run succeeds when tests/test_foo.py exists"
    kind: str               # file_exists | text_contains | ...
    target: str
    required: bool = True
    evaluated: bool = False # starts False
    passed: bool = False    # starts False
    evidence: str = ""
```

Law: `all_required_true()` loops required predicates; if `not evaluated or not passed: return False`. An empty board is also false. LLM scores are advisory and must not flip `passed`.

---

## 3. Flavor vs law

You **may** pick any of these for the control loop (pick one, do not invent a fourth religion without a reason):

| Capability | Public GitHub (look these up; stars move) |
|------------|-------------------------------------------|
| Control loop | https://github.com/langchain-ai/langgraph |
| Compile reasoning | https://github.com/stanfordnlp/dspy |
| Agent evals as science | https://github.com/UKGovernmentBEIS/inspect_ai |
| Model-agnostic SDK | https://github.com/openai/openai-agents-python |
| Typed outputs | https://github.com/567-labs/instructor and https://github.com/pydantic/pydantic-ai |
| Memory that is not chat | https://github.com/mem0ai/mem0 or https://github.com/letta-ai/letta |
| Research fan-out | https://github.com/assafelovic/gpt-researcher |
| Tool protocol | https://github.com/modelcontextprotocol/python-sdk |
| Code-act workers | https://github.com/huggingface/smolagents |
| Software-engineering worker | https://github.com/OpenHands/OpenHands |
| Last-mile browser | https://github.com/microsoft/playwright or https://github.com/browser-use/browser-use |
| Skill packaging | https://github.com/anthropics/skills |
| Many models, one proxy | https://github.com/BerriAI/litellm |
| Local models | https://github.com/ollama/ollama |
| Prompt regression on routing | https://github.com/promptfoo/promptfoo |

Your flavor is which of those you actually import. The law is §1–§2 and §6. A rebuild that copies LangGraph but lets `done` become true from an unevaluated predicate has failed.

---

## 4. Layer A — skill (do this in every rebuild)

This is what makes **every later prompt** in Cursor (or Claude, Devin) an objective. Without `alwaysApply: true`, you built a document nobody inhabits.

### 4.1 Files to write

```
.cursor/skills/figureitout/SKILL.md     # alwaysApply: true
~/.cursor/skills/figureitout/SKILL.md   # same bytes; all projects on this machine
.cursor/skills/letscook/SKILL.md        # thin alias: /letscook = figureitout
.cursor/rules/figureitout.mdc           # alwaysApply: true
AGENTS.md                               # merge, do not wipe other sections
.devin/skills/figureitout/SKILL.md      # if Devin exists
.claude/skills/figureitout/SKILL.md     # if Claude Code exists
```

Copy `mentalModal.md` and this file next to the skill so a high-stakes run can open them.

### 4.2 Skill body (keep it short; ≤120 lines)

The skill must contain, in plain language (no internal code-names):

- Every prompt is an objective. A plan is not done.
- **Do not answer immediately** unless §1 says papercut/trivial.
- **Complexity** section with the mechanical gates (copy §1.3 table in compressed form).
- Loop: lock → first principles → look up → experiment → board → steer → use → do → check → raise → checkpoint → report.
- Autonomy: do not ask the human to click Allow. Stop only for a missing paid secret or irreversible production destroy.
- Kill switch: `FIGUREITOUT_LOCKDOWN=1`.
- Hard rules: predicates not confidence; live/omitted/blocked; no API keys in chat; browser last; name model flaws; use public tools; report blocked with evidence.

`/letscook` skill must stay thin: “run figureitout on everything after the slash.” Do not invent a second framework.

### 4.3 Cursor rule

```markdown
---
description: figureitout — every prompt is an objective
alwaysApply: true
---
Every prompt is an objective. Follow .cursor/skills/figureitout/SKILL.md.
Classify complexity first. Papercuts: one lookup, then stop.
Otherwise the laboratory loop. Kill switch: FIGUREITOUT_LOCKDOWN=1.
```

### 4.4 Install once

```bash
# from a clone
pip install -e ".[dev]"          # only if building Layer B
python -m figureitout --install  # copies skill + rule + AGENTS.md
```

Or copy `SKILL.md` by hand. Then **Reload Window** in Cursor. The agent does not wait on that click to keep writing files.

After install, a new chat given “add a failing test then make it pass” must **do the work**, not describe it.

---

## 5. Layer B — package (your flavor of graph)

Build this when you want pytest to catch a lying synthesizer.

### 5.1 Minimum modules (names may change; jobs may not)

| Job | Suggested name | Must do |
|-----|----------------|---------|
| Config / kill switch | `config.py` | trusted default ON; lockdown sandboxes writes |
| Complexity router | `lifecycle.py` | §1 classifier; tests in §1.2 green |
| Predicates | `objective_fn.py` | unevaluated = false |
| Laboratory | `lifecycle.py` | writes job folder **before** compute on standard/exhaustive |
| Planner | `planner.py` | 3–5 tasks, falsifiable `success_criteria`, research first |
| Worker | `worker.py` | tools; empty stdout is not a result |
| Judge | `judge.py` | pass/fail + `failure_reason`; empty cannot pass |
| Bar raise | `bar_raiser.py` | improve once if merely adequate |
| Fail closed | `fail_closed.py` | HTTP 500, example.com stubs, “Worker fallback” cannot be `done` |
| Checkpoint | `checkpoint.py` | save/load; `--resume RUN_ID` |
| Runner | `runner.py` | laboratory → planner → worker → judge → raise → synthesizer |
| Install | `install.py` | copies Layer A |
| CLI | `__main__.py` | `python -m figureitout "…"`, `--install`, `--resume`, `--mock` |

Suggested graph (implement with LangGraph, a `while` loop, or another SDK — flavor):

```
laboratory → planner → worker → evaluator ─┬─ fail & retries left → worker
                                           ├─ more tasks            → worker
                                           ├─ all tasks passed      → bar_raiser
                                           └─ retries exhausted     → synthesizer
bar_raiser ─ fail → planner (replan remaining)
           ─ pass → synthesizer → END
```

On **papercut/trivial**, laboratory writes a one-line lock (optional) and the worker does the one lookup. Do not fan out five tasks.

### 5.2 Job folder

```
~/.letscook/cursor-jobs/<run_id>/     # trusted
~/.myrunner/runs/<run_id>/            # lockdown
```

Standard/exhaustive files:

```
objective_lock.md
first_principles.md
context_brief.md
experiments.md
board.md
flaws.md
use.md
steer.md
checkpoint.json
predicates.json
frontier.json
result.md
```

`result.md` **starts** with the use brief, then the artifact. Process diary is below the fold or omitted.

### 5.3 Model agnosticism

Try, in order, whatever already exists in the environment. **Never print “paste your API key.”**

1. Configured MCP / local router (`LLM_PROVIDER=local`)
2. Already-authenticated CLI
3. `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` if present
4. Mock in tests (`FIGUREITOUT_MOCK=1`)
5. Missing paid secret → status **blocked** with out-of-band setup notes

Same-runtime pin: a Cursor-started run uses tools in this process. Do not shell out to another product’s CLI as if it were local.

### 5.4 Data cascade

CLI/MCP → workspace files → browser last → **blocked**. If CLI can obtain it, do not open a browser.

---

## 6. Laboratory phases (standard / exhaustive only)

Execute in order. Each phase has an exit file. If the file is missing, the phase did not happen.

1. **Ingress** — create `run_id` and the job folder. Apply §1. If papercut, jump to thin path (§1.5).
2. **Lock** — one sentence “This run succeeds when …”. Freeze the noun. Quality tier frozen.
3. **First principles** — irreducible / assumptions to test / reuse (real paths) / frontier (GitHub URLs).
4. **Inventory** — `context_brief.md`. Notes are hypotheses. Need ≥1 on-domain candidate.
5. **Experiments** — hypothesis, method, **observation**. A cheap experiment: glob the workspace; write what exists. That is learning. “I recall that…” is not.
6. **Board** — standing seats + operator/skeptic/verifier/communicator. Dissent is evidence. `provisional pass` or handoff. No compute on reject.
7. **Flaws** — ≥6 model failure modes and the filter that suppresses each.
8. **Use** — who, next action, what to ignore. 100% of shipped text must be ready to use. No filler. If presenting to executives, no “as an AI”.
9. **Steer** — 3–5 questions that would change the plan, written **after** inventory. If the human does not answer, proceed with the best evidenced path. Do not wait.
10. **Compute** — plan → work → sniff every number → judge (remediate ≤2) → raise once.
11. **Checkpoint** — after laboratory and after synthesizer. Another agent must resume without the chat.
12. **Report + learn** — `result.md` leads with use. One lesson queued as preview from an experiment or failed check.

---

## 7. Step-by-step rebuild (do in this order)

A model rebuilding from a blank folder should literally tick these.

1. Create a git repo. Add MIT license if you want. Name the skill `figureitout`. Alias `/letscook`.
2. Write **failing** tests for §1.2 (complexity) and for “unevaluated predicate is false”.
3. Implement `classify_complexity`. Make those tests pass.
4. Write Layer A files (§4). `alwaysApply: true`. Copy to `~/.cursor/skills/figureitout/`.
5. Merge `AGENTS.md`. Write the Cursor rule.
6. Write `objective_fn.py`. Prove unevaluated ⇒ false with pytest.
7. Write `lifecycle.py` job-folder writer. On a **standard** objective, all files in §5.2 exist and are non-empty.
8. Write planner / worker / judge / fail-closed. Mock path: `FIGUREITOUT_MOCK=1 python -m figureitout "write hello world"` returns non-empty output and does not claim done on HTTP 500.
9. Wire the graph with laboratory as **entry** (except papercut thin path).
10. Checkpoint save/load + `--resume`.
11. `install.py` copies the skill. `--install` never prints “paste your API key”.
12. Run the full test set. Fix until green.
13. Point at evidence: pytest output, skill paths, one job folder listing.
14. Stop. Do not add a second product name.

Never stop after step 1–6 with a plan of 7–14. Re-plan only after a failed check.

---

## 8. Tests you must have (write these first)

Minimum. Names can change; behavior cannot.

1. Skill YAML has `name: figureitout` and `alwaysApply: true`.
2. Complexity vectors in §1.2.
3. Unevaluated required predicate ⇒ `all_required_true() is False`.
4. File-exists predicate fails until the file is written, then passes.
5. `queue_lesson(..., source="I read a blog")` raises.
6. Hello-world mock run status ∈ {`done`, `partial`} and output is not plan-only prose.
7. Judge fail increments retries and re-invokes the worker with `failure_reason`.
8. Fail-closed: “Worker fallback” + “Error code: 500” cannot be `done`.
9. Lockdown writes under the sandbox dir.
10. Checkpoint round-trip: save, load, same `run_id` and `done_sentence`.
11. Standard laboratory writes `use.md` containing `next action`.
12. No install/run stdout contains `paste your API key`.

---

## 9. How a model should think while rebuilding (your flavor)

You are not copying figureitout byte-for-byte unless the human asked for a clone. You are satisfying §1–§8.

1. **Classify this rebuild.** It is **standard** (heavy verbs: build, from scratch). Full laboratory. Do not papercut it.
2. **Lock.** “This run succeeds when a skill with `alwaysApply: true` exists, complexity tests pass, unevaluated predicates cannot be true, and `pytest` is green.”
3. **First principles.** Done is evidence. Routing is mechanical. Flavor is libraries. Tenets are predicates.
4. **Reuse.** If `https://github.com/youtextme/figureitout` is reachable, clone it or read `SKILL.md` / `mentalModal.md` / `figureItOutObjective.md`. Do not re-invent a skill format; use https://github.com/anthropics/skills.
5. **Experiment.** Create a temp dir, write a failing test for unevaluated predicates, watch it fail, then implement until it passes. That observation is the lesson.
6. **Board.** You are operator (ship the skill), skeptic (will papercuts still skip?), verifier (pytest), communicator (result leads with how to install).
7. **Flaws.** Hallucinated APIs, answering with a plan, skipping `alwaysApply`, letting hello-world skip fail-closed. Each needs a test.
8. **Use.** The next human/model will paste this file or clone the repo and rebuild. Your output must be followable without you in the room.
9. **Steer questions** (proceed if unanswered): Which host (Cursor only vs CLI)? Which model vendor already has keys? Python or another language?
10. **Compute.** Tests first. Then skill. Then package. Then install. Then evidence.
11. **Checkpoint** after each module goes green so a crashed session can `--resume`.
12. **Report** with paths and pytest.

---

## 10. `/letscook` specifically

```markdown
---
name: letscook
description: Starts figureitout on the rest of the prompt.
---
# /letscook
`/letscook` means: run **figureitout** on everything after the slash.
Follow the figureitout skill. Classify complexity first. Finish with evidence.
```

That is the entire alias. If you add a second loop here, you have forked the religion.

---

## 11. Reference implementation

When you want to see one flavor that already satisfies this contract:

- Repo: https://github.com/youtextme/figureitout
- Skill: `SKILL.md` (always on)
- Why: `mentalModal.md`
- Cursor rebuild playbook: `figureItOutObjective.md`
- Package: `figureitout/` (`objective_fn.py`, `lifecycle.py`, `checkpoint.py`, `runner.py`)
- Tests: `tests/test_figureitout_*.py`

Clone, `pip install -e ".[dev]"`, `python -m figureitout --install`, `pytest -q`. Then change flavor (swap LangGraph for a while-loop, swap Instructor for another typed layer) **without** deleting predicates or the complexity router.

---

## 12. Acceptance — rebuild is done only when all are true

Tick with evidence (path or command output). Unticked = not done.

**Routing**

- [ ] §1.2 vectors pass in pytest
- [ ] Skill text tells the agent to papercut one-lookup asks
- [ ] “just research” is not a valid skip

**Tenets**

- [ ] Unevaluated predicate cannot be true
- [ ] Standard run writes all §5.2 files, non-empty
- [ ] `use.md` has a next action; `result.md` leads with use
- [ ] `steer.md` says proceed if no steer
- [ ] `board.md` names the four domain seats
- [ ] `flaws.md` maps failure modes to filters
- [ ] Lessons reject non-experiment sources
- [ ] `--resume RUN_ID` loads the same lock sentence

**Skill**

- [ ] `.cursor/skills/figureitout/SKILL.md` exists, `alwaysApply: true`
- [ ] `~/.cursor/skills/figureitout/SKILL.md` exists (after `--install` or copy)
- [ ] `/letscook` is a thin alias
- [ ] `AGENTS.md` contains the figureitout block

**Package (if built)**

- [ ] `pytest` green
- [ ] Mock hello-world not empty plan-only
- [ ] Fail-closed cannot report `done`
- [ ] No key begging in install/run output

**Human / next model**

- [ ] This file is reachable (repo and/or gist URL)
- [ ] A stranger can follow §7 without you
- [ ] No second product name

Until every box has evidence, replan remaining work. Do not declare victory on a sketched tree.

---

## 13. Paste prompt (give this to a blank-folder model)

```
You are rebuilding an objective runner from
https://github.com/youtextme/figureitout
and the contract LETSCOOK_BUILD.md (this file).

1. Classify this job: it is standard, not a papercut.
2. Write failing tests for complexity vectors and unevaluated predicates.
3. Implement classify_complexity, then Layer A skill (alwaysApply: true),
   then Layer B if this is a Python workspace.
4. Flavor is yours (graph library, vendors). Tenets are not.
5. Never stop at a plan. Do not ask for API keys. Read the environment.
6. Done when §12 of LETSCOOK_BUILD.md is all true with evidence.
```

That prompt is enough to start. This file is the contract the agent must satisfy.
