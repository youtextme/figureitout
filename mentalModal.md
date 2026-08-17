# figureitout mental model

This file is the detailed operating law behind the small skill in [`SKILL.md`](SKILL.md). The skill is what you install. This document is what an agent should *inhabit* when a human types `/letscook` or otherwise treats a prompt as a figureitout objective.

It does not retell any one company’s dashboard build. It teaches how to run **any** objective as a laboratory whose definition of done can be checked by someone who does not trust the model.

`/letscook` means: run **figureitout** on the rest of the prompt. There is no second product name.

Stars below were read from GitHub on 2026-08-16.

---

## Opening frame

Picture an agent that writes fluent Markdown for forty minutes and still leaves the human unable to act: no frozen success sentence, no live query, no proof that a control was clicked, a **public** paste of internal numbers, and a transcript that vanishes when the window fills. That is chat improvisation beating outcome risk.

Serious work treats truth as **predicates over evidence**, not as the model’s confidence. The skill is the law. The figureitout runner is the instrument that enforces the law when helpful instincts would otherwise cheat — answering inline, inventing a number, stopping at a plan.

## Why thirty-five themes stay unmerged

Overlap of *mention* is allowed. Ownership of the *failure mode* is exclusive. Merging themes would let one owner waive another’s hard fail.

| Group | Owns the failure mode |
|-------|------------------------|
| **Ingress** | Whether and where work may run |
| **What may be believed** | What is allowed to count as knowledge before compute |
| **Path choice** | Which specialist route |
| **Execution and memory** | How work proceeds over time |
| **Evidence ethics** | How facts are obtained and sniffed |
| **Artifact and human use** | How outputs become usable and promotable |
| **Acceptance and recovery** | What counts as done, and what happens on empty/fail |
| **Ship hygiene** | Verify, publish, evolve |
| **Synthesis** | Mapping to public projects, and internalization, without stealing earlier ownership |

This document’s job is coverage: every concern has one primary owner. A later section lists fifty-one atoms so no row is left without a home.

---

## Ingress — whether and where work may run

### Frame

When a human types `/letscook`, they are not asking for a clever reply that evaporates when context fills. They are declaring that an outcome is at risk if the work stays improvisational: a dashboard someone will act on, a research pack someone will defend, a change that must survive skepticism. Chat optimizes for sounding helpful on the next turn. figureitout optimizes for a **boolean definition of done** that can be checked against files, query rows, clicks that stayed on-page, and predicates that evaluate to true. Truth is not “the model felt finished.” An agent should feel the difference: this is a laboratory run, not a salon conversation.

In practice the frame is a skill plus a CLI that fires the same law in Cursor, Devin, Claude, and the terminal: `python -m figureitout "<objective>"`. The public idea of “compose a control loop rather than invent a new agent religion” lives in [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) (~39.8k stars — state-machine orchestration) and the packaging pattern in [anthropics/skills](https://github.com/anthropics/skills) (~170k stars). figureitout’s customization is that the skill is not optional theater: lock the working directory and branch, keep job folders on disk (under `~/.letscook/cursor-jobs/` when that layout is in use), and treat acceptance as predicates, not vibes. Exit: the human can point to a path and a done-sentence **before** any worker spins.

### Force the run

The deadliest failure is not a bad worker. It is a smart parent answering inline “because this looks small.” Force-routing exists so non-trivial prompts cannot bypass the runner by self-classification (“just research,” “just a summary”). The pre-answer filter is mechanical: fits in two sentences or fewer, needs zero lookup, produces zero artifacts. Fail any gate and the prompt must enter figureitout. What is measured as true is routing fidelity: did this prompt invoke the runner, or did the agent freestyle? An agent should feel slight guilt at the urge to be helpful immediately — that urge is the bypass.

Mechanisms: always-on project rules, the skill’s route table, and CI-style prompt evaluation as in [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) (~24.3k stars — tests that fail when routing is skipped). figureitout’s customization: when in doubt, run figureitout; banned self-classifications are written so agents cannot argue around the gate. Exit: non-trivial work has a run id and a job folder; trivial Q&A is the only documented exception. Routing errors compound: once inline, there is no judge, no lock, no memory write.

### Host and backends

Long work needs compute, but asking the human for API keys turns the agent into a credential beggar and freezes progress. Host affinity: the place the run started defines which CLIs are legal. Cursor must not silently shell out to another product’s binaries as if they were local helpers. Backend order: try the configured MCP app-runner first, then Devin CLI, then an already-authenticated Claude CLI, then a Cursor agent only if a key already exists in the environment — never prompt. Truth here is operational continuity without secrets appearing in chat.

Public idea: one proxy, many providers, as in [BerriAI/litellm](https://github.com/BerriAI/litellm) (~56.4k stars), plus optional local models via [ollama/ollama](https://github.com/ollama/ollama) (~179k stars). figureitout pins the same runtime, scores backends, and reads tokens only from env/MCP. Exit: work proceeds without any key request; missing credentials report **blocked** with out-of-chat setup, never “paste your key.”

### Thin parent

A prior session died after generating a huge HTML file in the parent context — “prompt too long” is not theoretical. The parent stays under a hard token budget and never becomes the builder. Workers hold the large context; the parent plans, spawns, reads short summaries, and reports status. If you are about to write a large artifact in the orchestrator session, you are already violating the skill.

Public embodiment: LangGraph fan-out and research fan-out akin to [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) (~29.0k stars), plus optional code-act workers like [huggingface/smolagents](https://github.com/huggingface/smolagents) (~28.8k stars). figureitout hard rule: never build inline; keep parent turns short; pass file paths, not blobs; keep state on disk (`worker` + memory bus). Exit: artifacts live under the run directory written by workers; parent chat contains status and pointers only.

### Status while waiting

Multi-minute autonomy without status feels like a hung process and destroys trust. Emit a visible **Status:** line before a tool, spawn, or wait, and refresh every 60–90 seconds while waiting. Silence during long work is a protocol violation equal in spirit to dropping a handoff. What is true: the human can narrate which phase is active without asking whether the run is stuck.

Public analogy: make the run visible, as traces do in [langfuse/langfuse](https://github.com/langfuse/langfuse) (~33.2k stars). figureitout customization: skill-mandated status lines plus a watchable `run_log.jsonl` — lighter than a full telemetry stack, aimed at chat UX. Exit: every wait interval has a human-visible pulse; no silent multi-minute gaps.

---

## What may be believed — before compute

### Objective lock

Spawning workers before the success sentence exists is how teams burn tokens on the wrong deliverable. Freeze the goal, the quality bar, the binary forks, and a boolean definition of done **before** the planner runs. Creative freedom moves inside that contract, not outside it. Truth = a lock file exists and done-predicates can attach to the final phase.

Public idea: clear success contracts before spawn (LangGraph plan node + skill contracts; structured schemas via [567-labs/instructor](https://github.com/567-labs/instructor) (~13.7k stars)). figureitout enforces lock-before-plan, optional auto-seed of the source brief, and boolean done lines such as “file exists: …”. Exit: one sentence “This run succeeds when …”; acceptance criteria, time budget, and quality tier are frozen.

### First-principles defaults

Without defaults, every phase becomes cosmetic polish or cold-start amnesia. Force three habits: first principles (irreducible truths, assumptions to test, reuse inventory, frontier methods); a substantial critic (pass only for new capability, a killed wrong assumption, real reuse, or a measured jump — nits are not a pass); continuity (load checkpoint, lessons, preferences, recent locks). Truth is whether the phase changed the evidence set, not whether prose got prettier.

Public inspiration: memory retrieval from [mem0ai/mem0](https://github.com/mem0ai/mem0) (~63.3k stars) and structured critique (Instructor). figureitout ships these defaults with opt-outs that are explicitly **off** unless set. Exit: first-principles brief present; continuity pack loaded; a substantial critic would pass the phase delta.

### Standing governance

Domain experts change per question; governance seats must not. A permanent board — forensic investigator, pragmatic linguist, specification architect, verification scientist, meta-observer, plus a first-principles director and the substantial critic — owns cross-cutting quality so a rotating domain board cannot waive locks, counterfactuals, or “work backwards from use.” There is always a jury that does not care about your favorite metric noun.

Public idea: standing multi-agent debate roles as in [microsoft/autogen](https://github.com/microsoft/autogen) (~60.4k stars) or [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) (~57.1k stars). figureitout: immutable meta seats in the skill; the domain board is a separate theme. Exit: meta seats are consulted for lock, context, counterfactual, and evolution signals even when domain experts rotate.

### Source inventory

Answering before inventorying sources is how off-domain tables sneak in. First gate: tools and wiki (follow links), candidate sources and queries, and a context brief — question restated, in-scope domain, candidates, out-of-scope systems. Wiki notes and scratch notes are **hypotheses**. They name what to query; they do not terminate fact-checks. Truth = a brief exists with at least one on-domain source candidate.

Public idea: research recon before synthesis (GPT-Researcher) and doc ingest via [microsoft/markitdown](https://github.com/microsoft/markitdown) (~174k stars) for PDF/Office into Markdown. figureitout: `context_brief.md` is a hard gate; auto-seed when configured; wiki/ticket text stays hypothesis until a live query. Exit: on-domain candidates named, or a handoff for recon — never answer-first.

### Prove the method wrong

A method that cannot be proven wrong is not science — it is storytelling. Second gate: propose the calculation or decision, then three or four counterfactual / prove-yourself-wrong tests (alternate definitions, tables, null hypotheses, order-of-magnitude sanity), consult at least three experts, and log dissent as evidence. Relish the attempt to break your own plan before compute spends money.

Public idea: adversarial / multi-perspective review (AutoGen/CrewAI) and eval harnesses (Promptfoo). figureitout: expert-board gate wired into the worker checklist; proofs of concept must pair with explicit hypotheses and real data before lock. Exit: method + counterfactual plan + at least three reviews with a dissent log, or a handoff with a gap list.

### Expert board

Rubber-stamp boards produce confident wrongness. Third gate: form a board for **this** question — domain operator, data/analytics, skeptic/counterfactual, communication. The answer locks only after a provisional pass with who voted, what they saw, and the proof-of-concept results written down. You are presenting to directors who can fire the method, not an audience that wants slides.

Public embodiment: AutoGen GroupChat or CrewAI Crew as debate substrate; Instructor for typed verdict aggregation. figureitout: fixed role table in the skill; provisional pass artifact required before compute; a “trend” shortcut does not waive the board. Exit: written provisional pass or handoff — no publish on reject.

### Noun match

Classic contamination: the user asks for one noun (orders to replan); the agent publishes another noun’s funnel because a query was handy. Reject off-noun substitution even when SQL runs cleanly. Truth = every cited system, table, and metric matches the ask’s noun; otherwise **blocked** with a path to on-domain data.

Public analogy: schema/constraint validation before accept ([tobymao/sqlglot](https://github.com/tobymao/sqlglot) (~9.5k stars) for SQL shape; Promptfoo for assert-on-output). figureitout: this is a hard fail, equal in spirit to invented numbers; trajectory/judge checks reinforce it. Exit: noun-match checklist all pass; contamination is a hard fail.

---

## Path choice

### Route by intent

One runner for everything creates the wrong tool for the job. Trend/metric questions route to a trend analyzer; “explain / I don’t understand” routes to explain mode (a gist, skip the heavy runner); build/research/ship stays on figureitout. Noun-match and the expert board still apply on the trend path. Truth = intent class matches execution path.

Public idea: specialist research agents (GPT-Researcher) vs general LangGraph build loops; skill packaging ([anthropics/skills](https://github.com/anthropics/skills)) for portable routing text. figureitout: route-before-runner table in the skill; explain-mode section; trend-analyzer registry. Exit: correct skill invoked; do not use the full runner for “how many yesterday” when a trend pipeline exists.

### Known queries first

Inventing SQL from memory is how wrong grains become “official.” For metric or table-backed asks: load the known-query skill, search known query banks first, re-run via the warehouse MCP, then trust-label. Never treat wiki, a scratch note, or a BI screenshot as source. Truth = lineage from a known query to a live re-run.

Public idea: parse/validate with [tobymao/sqlglot](https://github.com/tobymao/sqlglot) before execution; SQL-in-docs thinking from [evidence-dev/evidence](https://github.com/evidence-dev/evidence) (~6.9k stars). figureitout: hard rule pointing at the query-bank skill; charts validate, they do not originate. Exit: bank hit or documented miss plus live SQL; no invented “probably this table.”

---

## Execution and memory

### Plan, work, judge, replan

Linear chat cannot recover from a dead strategy. Plan phases with success signals, execute fresh workers, judge with multiple lenses, recover or replan on fail, overrun, or empty. Failure is a routing signal, not an ending. Truth = phase criteria met or an explicit replan of remaining work.

Public core: [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) plan → execute → conditional edge, with reflexion-style retry. figureitout: `planner.py`, `worker.py`, `judge.py`, `runner.py`; max recovery depth; empty or inconclusive is not done. Exit: pass writes lessons and the next phase; fail after two recovers → replan remaining — never silent continue.

### Memory that is not chat

Chat history is not memory. Constitutive lessons, per-run key/value, sliding phase summaries, and session checkpoints keep truth portable across tools. Load at start, write at end; parents read summaries only. You inherit scars (failure modes) without pasting essays into context.

Public: [mem0ai/mem0](https://github.com/mem0ai/mem0). figureitout: lessons log, memory bus, job `memory.json`, last-five phase summaries, a short checkpoint file. Exit: run starts with pointers loaded; ends with a lesson append if a reusable failure or recovery was learned.

---

## Evidence ethics

### Data cascade

Asking the human to open a URL and paste is abdication. Order: CLI/MCP → workspace cache → Playwright (Chrome) → one new-window Chrome sign-in ask → **blocked**. If CLI/MCP can obtain it, never open a browser. Truth = strongest reliable path used; browser is last resort.

Public: [microsoft/playwright](https://github.com/microsoft/playwright) (~94.6k stars) as the last mile, not the first. figureitout: CLI/MCP before Playwright; do not hijack the user’s existing windows; do not use Edge as the automation browser. Exit: attempt log shows cascade order; blocked only after prior paths fail.

### No invented numbers

Fake KPIs that “make the UI look done” are fraud dressed as craftsmanship. Every cell is live, omitted, or **blocked** — never mock/sample/placeholder presented as operational truth. An empty honest UI beats pretty lies. Truth = provenance exists for every number shown.

Public: judge fields that forbid invented KPIs (Instructor schemas + Promptfoo fixtures). figureitout: no-dummy-data hard rule; a fixture banner only for non-ship evidence; same severity as a public gist of internals. Exit: no invented metrics in deliverables; blocked template with why and how to unblock.

### Warehouse proves

Compute runs only after the board’s provisional pass — no “quick SQL first, justify later.” Visualization tools **validate**. Warehouses **prove**. Guessed dashboard query language has caused billion-scale bugs; discovery protocols exist so agents do not invent PromQL. Truth = tier-1 SQL/MCP (or labeled unverified), not a dashboard scrape as source. See also [grafana/grafana](https://github.com/grafana/grafana) for the product whose query language must be discovered, not guessed.

Public: SQLGlot validation; [chartjs/Chart.js](https://github.com/chartjs/Chart.js) (~67.6k stars) and Evidence for rendering from query results; Playwright only for auth gaps. figureitout: first-principles data; viz is not source; warehouse MCPs (Presto/Hive/Redshift or whatever the workspace actually has). Exit: cite table plus SQL; a viz may say “validated against …” only.

### Sniff every number

A query that runs is not a number that is right. Sniff: order-of-magnitude, counter vs delta, baselines, cross-check, three experts (data scientist, business analyst, zero-context exec), rate/count confusion, reset artifacts. Feel terror at 1.79 billion “orders.” Truth = sanity-passed, or labeled unverified, or sniff-fail removed.

Public: eval assertions (Promptfoo) + multi-persona review (AutoGen/CrewAI). figureitout: common-sense sniff hard rule plus a data-skepticism gate (seven or more angles); PromQL anti-patterns documented. Exit: every published metric has a sniff classification; fail → fix or remove, never ship known-wrong.

---

## Artifact and human use

### Lineage under the chart

Executives distrust pages that hide lineage. Source control must look like a real hyperlink, bottom-left under the chart, labeled in a few words with the warehouse name, expand on-page — never a navigation widget, never a bare “Source,” never an email as the page source. Truth = a skeptic can re-run from the strip.

Public UI charting: [chartjs/Chart.js](https://github.com/chartjs/Chart.js) and [evidence-dev/evidence](https://github.com/evidence-dev/evidence). figureitout: provenance hard rule for public metrics UI. Exit: every KPI/chart has a compliant source link; extra validation lives inside the panel, secondary.

### Light UI, proven done

Dark neon “executive dashboards” and untested UIs destroy adoption. Light Material-like aesthetic is mandatory. “Validated done” forbids calling the work done without live data (or a labeled gap) and UX evidence. Render checks cover diagrams ([mermaid-js/mermaid](https://github.com/mermaid-js/mermaid)), links, and 390px plus desktop. Ship only what a mobile VP can trust in two seconds.

Public: Chart.js, Evidence, Playwright for click proof; Mermaid for diagram render. figureitout: light UI tenet, progressive disclosure, validated-done, render-validation hard rule. Exit: live-or-labeled data + click evidence + render checks green. Communication for a reader with zero context (structure the story so a new exec can act) lives here as part of “usable,” not as a separate religion.

### Work backwards from use

“Correct but unusable” is failure. Every result opens with how a human will **use** it: their job, the next action, trust evidence, follow-ups pre-empted, a cheap experiment with an observation, labeled variants if uses conflict. Finding-out beats answering. Truth = a skeptic can re-run the proof and take the next action.

Public: planner+judge boolean fields (Instructor); experiment logging (Langfuse). figureitout: work-backwards-from-use tenet and a brief at the top of `result.md`. Exit: brief present; experiment observed or cost-skipped; no waiting for the human’s obvious follow-up.

### Preview before default

One lucky run must not silently flip the org’s default query, API, or repo. Stay in preview until the run finished, at least three rematches of the same job, at least three of four signals (win rate, quality, cost/time, behavior), and no veto. This is a promotion board, not fad chasing.

Public: A/B eval culture (Promptfoo) + memory tags (Mem0). figureitout: promote receipts stored in memory, not silent default flips. Exit: written 3-of-4 receipt or still preview; handoff if something flipped without a receipt.

---

## Acceptance and recovery

### Predicate truth

LLM narrative scores are advisory only. Truth is: all required predicates true, and pass rate at or above the bar for this quality tier. Feedback loops remediate until true or a max attempt count. Bars (standard / high / exhaustive) have numeric thresholds: hedges, minimum words, same-runtime, hard evidence when claimed. The board of predicates, not the vibes of the prose.

Public: structured outputs ([567-labs/instructor](https://github.com/567-labs/instructor) / [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) (~19.3k stars)) instead of markdown parsing. figureitout: objective-function module as constitutive law; LLM scores never alone flip true. Exit: predicate board logged; advisory scores may only shape remediation text after false.

### Multi-lens judge

First appearance is not acceptance. Eight validation methods score structure, trust, completeness, and related lenses; failures trigger targeted remediation, max depth two — not a full restart. Empty or inconclusive cannot pass. Harsh but fair before success.

Public: multi-lens CrewAI/AutoGen personas × Instructor verdict objects. figureitout: `judge.py` plus a quality validator and a small remediation patch; still fail → replan or handoff. Exit: methods run; remediate at most twice; never “pass by inconclusive.”

### Recover missing output

Silent drop of a handoff wastes the whole run. The orchestrator acts immediately on a missing `result.md`, tool gaps, auth failures — max two auto-recoveries (fallback MCP, recon naming variants, stdout copied into `result.md`) before a human escalation template. Recovery is the job, not apology.

Public: LangGraph retry policies; LiteLLM failover. figureitout: recovery matrix plus “human is last resort” after two fails on the critical path. Exit: recovery attempts logged; human only after two fails with the required template.

### Continue if the runner is sick

When the figureitout spawn path is unhealthy, do not freeze the objective. Escalate to Cursor Task `generalPurpose` workers with the same objective lock, write part files, synthesize, and enqueue a self-improve note that the spawn path is sick. The skill is larger than the binary.

Public: alternate worker runtimes ([huggingface/smolagents](https://github.com/huggingface/smolagents) / Task tools) when the primary graph fails. figureitout: never ask for keys as a “fix.” Exit: objective continues via Task; an improvement-log note is filed.

---

## Ship hygiene

### Click the customer path

Code review is not done for interactive controls. Click the path (Playwright/browser); stay-on-page; wait for busy indicators to clear; attach URL before/after pass/fail. Untested = incomplete. You are the first customer.

Public: [microsoft/playwright](https://github.com/microsoft/playwright). figureitout: customer-path click is a hard rule in the skill. Exit: click evidence attached before success on UI objectives.

### Claims need links

Ticket comments are hypotheses. “Deployed / shipped / live” requires a merged PR, a closed review, or a live URL — else claimed/unverified. Every ticket key and PR number must be a markdown hyperlink; bare keys fail a pre-publish self-grep. A skeptic with a link budget.

Public: GitHub API patterns ([cli/cli](https://github.com/cli/cli) (~45.8k stars)). figureitout: trust-but-verify plus ticket-keys-as-links hard rules. Exit: status claims classified; zero bare keys in output.

### Private publish only

Public gists leak internal analysis onto browsable indexes. Every gist is created private; a public create is a hard-fail equal to invented numbers. Share by URL, never by directory listing.

Public: GitHub gist API with an explicit private flag ([cli/cli](https://github.com/cli/cli)). figureitout: wrappers that refuse public create. Exit: secret gist only; assert scripts pass.

### Engineering excellence

Build/ship without failure-mode analysis, operational readiness, delivery metrics, and QA/rollback is how incidents become culture. For ship work: top-three failure modes with mitigation; readiness reviewed on a recent clock; delivery metrics instrumentable; QA/rollback under ten minutes — block success when required. Research surfaces risks but is not blocked the same way. Staff+ gate before dial-up.

Public: SRE checklists encoded as judge predicates (Instructor). figureitout: engineering-excellence tenet and a four-check table. Exit: four checks pass or labeled gaps per policy; failure-mode or QA fail → handoff on build/ship.

### Learn after the run

Learning must not delay the objective or silently rewrite the runner mid-flight. Post-run enqueue; a periodic scan of run logs produces proposals only; lessons are one-liners; promote only via the preview-before-default board. Evolution with receipts.

Public: Mem0 + Langfuse for traces; Promptfoo for regression. figureitout: self-improve module; no auto-patch without tests and human opt-in. Exit: proposals queued; no silent mid-run code mutation. Cross-tool skill sync belongs here: the same law is copied to Cursor, Devin, and Claude skill folders, not rewritten in flight.

---

## Synthesis

### Public composition

This skill is not a proprietary religion. It is a composition of public ideas forced into an operating law:

| Public project | Role in the instrument |
|----------------|------------------------|
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | Control loop |
| [microsoft/autogen](https://github.com/microsoft/autogen) / [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | Boards |
| [567-labs/instructor](https://github.com/567-labs/instructor) | Typed truth |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | Memory |
| [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) | Research fan-out |
| [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | Routing CI |
| [langfuse/langfuse](https://github.com/langfuse/langfuse) | Traces |
| [BerriAI/litellm](https://github.com/BerriAI/litellm) | Backends |
| [tobymao/sqlglot](https://github.com/tobymao/sqlglot) | SQL safety |
| [microsoft/markitdown](https://github.com/microsoft/markitdown) | Ingest |
| [huggingface/smolagents](https://github.com/huggingface/smolagents) | Code-act workers |
| [chartjs/Chart.js](https://github.com/chartjs/Chart.js) / [evidence-dev/evidence](https://github.com/evidence-dev/evidence) | Charts from data |
| [microsoft/playwright](https://github.com/microsoft/playwright) | Last-mile browser |
| [anthropics/skills](https://github.com/anthropics/skills) | Packaging |
| [cli/cli](https://github.com/cli/cli) | Publish and link hygiene |
| [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) | Structured agents beside Instructor |
| [ollama/ollama](https://github.com/ollama/ollama) | Local models when a cloud key must not be requested |
| [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) | Compile reasoning instead of hand-written prompts |
| [UKGovernmentBEIS/inspect_ai](https://github.com/UKGovernmentBEIS/inspect_ai) | Agent evals as science (dataset → solver → scorer) |
| [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | Model-agnostic agent SDK |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | Tool protocol |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | Last-mile browser when CLI/MCP cannot |
| [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) | Software-engineering worker pattern |
| [letta-ai/letta](https://github.com/letta-ai/letta) | Long-horizon state that is not chat |

figureitout’s customization is the glue: always-on force-routing, epistemic locks, predicate truth, a data cascade that does not publish corporate URLs as the teaching backbone. Exit: every major theme maps to at least one public repo in the ledger — no “secret sauce only” claim.

### Internalize the cascade

Reading this file as literature is insufficient. Internalize as operating law: route → lock → brief → proofs of concept → board → compute → sniff → communicate → work backwards from use → judge → recover → verify UX → publish privately → write lessons. One scientific instrument with many lenses, not a buffet of optional tips.

Checklist the agent runs mentally on every `/letscook`: (1) Did the pre-answer filter fail? (2) Can the lock sentence be written? (3) Does the context brief name at least one source? (4) Is the ask’s noun intact? (5) Live or blocked? (6) Source link under charts? (7) Work-backwards brief present? (8) Are predicates true? (9) Clicked if UI? (10) Private gist only? Public scaffolding: skills format + LangGraph discipline. The worker checklist in [`SKILL.md`](SKILL.md) is the canonical exam. Exit: the agent can recite the cascade without opening the file — then still opens the file when stakes are high.

---

## Prompt lifecycle — study every prompt as a laboratory run

A prompt is not a turn. It is a run with a beginning that can be named, a middle that writes evidence, and an end that another agent can resume. The lifecycle is the same whether the host is Cursor, Devin, Claude, or `python -m figureitout`. Model-agnostic means the laboratory does not care which weights sit behind the tools; it does require search and slow reasoning. It is not ready to answer immediately. It spends tokens on datasets, reviews, counterfactuals, and opinions that survived an attempt to prove them wrong. Speed is not a virtue. Usable, tested output is.

Phases, in order, with the file that proves the phase happened:

1. **Ingress** — force the run; create `~/.letscook/cursor-jobs/<run_id>/` (or the lockdown sandbox). Trivial two-sentence Q&A with zero lookup and zero artifacts is the only skip.
2. **Lock** — `objective_lock.md`: one sentence “This run succeeds when …”, quality tier, binary forks. No worker before this file exists.
3. **First principles** — `first_principles.md`: irreducible truths, assumptions to test, reuse inventory, frontier methods from public GitHub.
4. **Inventory** — `context_brief.md`: question restated, on-domain candidates, out-of-scope systems. Notes are hypotheses.
5. **Experiments** — `experiments.md`: hypothesis, method, **observation**. Learning is forbidden unless an experiment or a failed check or user feedback produced that observation. Text is not learning.
6. **Board** — `board.md`: standing seats plus an operator, skeptic, verifier, communicator recruited for *this* noun. Provisional pass or handoff.
7. **Flaws** — `flaws.md`: how models go wrong on this job (hallucination, plan-as-done, noun swap, sycophancy, reward hacking, context stuffing) and the mechanical filter that rules each out.
8. **Use** — `use.md`: who acts, the next action, what to ignore. 100% of the shipped text must be ready to use. Filler is a fail.
9. **Steer** — `steer.md`: the three to five questions that would change the plan, written *after* research. If the human does not steer, proceed with the best evidenced path. Do not freeze the run on a click.
10. **Compute** — plan → work → sniff → judge (remediate at most twice) → raise once. Workers write files. Parent reports paths.
11. **Checkpoint** — `checkpoint.json`: run id, lock sentence, phase, predicates, next action. Turn the runner off and on. A different agent must be able to continue without rereading the chat.
12. **Report and learn** — `result.md` leads with use. One lesson is queued as **preview** from an experiment; the runner code is not rewritten mid-flight.

What is measured as true at each phase is a **predicate** that starts false and can become true only when evidence is on disk. An unevaluated required predicate is false. That is how subjectivity is removed.

---

## Nine tenets — mapped onto owners, not merged into them

These are the human's operating tenets. They do not become a thirty-sixth theme. Each already has an owner in the matrix above; this table is the routing slip so a later writer cannot invent a parallel religion.

| Tenet | Primary owner | What “true” looks like |
|-------|----------------|------------------------|
| 1. Scientific objective functions | Predicate truth | `PredicateBoard.all_required_true()` is impossible unless every required check ran and passed |
| 2. First-principles thinking | First-principles defaults | Irreducible / assumptions / reuse / frontier brief exists before compute |
| 3. Self-evolving, self-learning, self-improving | Learn after the run | Proposals queued; promote only with a preview receipt; no mid-run mutation |
| 4. Learn by experiments, proofs of concept, user feedback | Prove the method wrong | A lesson has an observation; “I read that…” is rejected as learning |
| 5. Use what is already built; find the cutting edge | Public composition + source inventory | Frontier catalog is public GitHub; reuse inventory before a new stack |
| 6. AI-researcher lens on how models go wrong | Multi-lens judge + no invented numbers | Named flaws with the filter that suppresses them |
| 7. Work backwards from use; 100% readily useful | Work backwards from use | `use.md` names who, next action, and the noise to keep the reader away from |
| 8. Questions after research so the human can steer | Source inventory + objective lock | `steer.md` written; no-steer ⇒ proceed with the best evidenced path |
| 9. Recruit teams who apply their thinking | Expert board + standing governance | Domain seats for this noun; standing seats cannot waive epistemic law |
| 10. Turn off/on with crisp state any agent can resume | Memory that is not chat | `checkpoint.json` is sufficient to continue |

Tenet 5 appears twice in the human's list (cutting-edge resources, then the researcher lens). Both rows are kept. Overlap of mention is allowed; ownership of the fail stays with the theme in the first column's owner.

---

## Coverage matrix (one owner per atom)

Each atom has exactly one primary theme. Mention elsewhere is allowed; ownership of the fail is not shared.

| Atom | Concern | Primary theme |
|------|---------|----------------|
| A01 | Working directory + branch lock | Frame |
| A02 | CLI/MCP before Playwright | Data cascade |
| A03 | Autonomous data + Chrome sign-in cascade | Data cascade |
| A04 | Never ask LLM API keys | Host and backends |
| A05 | Preferred MCP runner / backend order | Host and backends |
| A06 | Same-runtime host pinning | Host and backends |
| A07 | No dummy / blocked template | No invented numbers |
| A08 | Private gists only | Private publish only |
| A09 | Public metrics source-link UX | Lineage under the chart |
| A10 | Viz validates only / warehouse is source | Warehouse proves |
| A11 | Metrics discovery protocol (do not guess PromQL) | Warehouse proves |
| A12 | Zero-data honest labeling | No invented numbers |
| A13 | Sniff test, order-of-magnitude + three experts | Sniff every number |
| A14 | PromQL anti-patterns | Sniff every number |
| A15 | Ticket keys must be links | Claims need links |
| A16 | Trust-but-verify status claims | Claims need links |
| A17 | Customer UX click path | Click the customer path |
| A18 | World-class light UI | Light UI, proven done |
| A19 | Validated-done | Light UI, proven done |
| A20 | Render validation (Mermaid, links, mobile) | Light UI, proven done |
| A21 | Never build inline / thin parent | Thin parent |
| A22 | Status streaming | Status while waiting |
| A23 | Pre-answer / force-routing | Force the run |
| A24 | Route trend vs explain vs build | Route by intent |
| A25 | Query bank before inventing SQL | Known queries first |
| A26 | Context brief before answering | Source inventory |
| A27 | Counterfactual proofs of concept | Prove the method wrong |
| A28 | Expert board of directors | Expert board |
| A29 | Compute only after provisional pass | Warehouse proves |
| A30 | Communication a new exec can act on | Light UI, proven done |
| A31 | Standing seat: recruit better experts | Standing governance |
| A32 | Noun match | Noun match |
| A33 | Failure-mode / readiness / delivery / QA | Engineering excellence |
| A34 | Work backwards from use + cheap experiment | Work backwards from use |
| A35 | Preview before flipping a default | Preview before default |
| A36 | Objective lock | Objective lock |
| A37 | First-principles / critic / continuity | First-principles defaults |
| A38 | Permanent meta-governance seats | Standing governance |
| A39 | Reflexion plan–judge–replan | Plan, work, judge, replan |
| A40 | Multi-lens judge + remediation depth 2 | Multi-lens judge |
| A41 | Memory lessons + sliding summaries | Memory that is not chat |
| A42 | Empty-output recovery | Recover missing output |
| A43 | Runner-broken → Cursor Task | Continue if the runner is sick |
| A44 | Periodic self-improve, propose-only | Learn after the run |
| A45 | Human last resort after recovery | Recover missing output |
| A46 | Objective-function predicates | Predicate truth |
| A47 | Explain-mode gist path | Route by intent |
| A48 | Cross-tool skill sync | Learn after the run |
| A49 | Public composition mapping | Public composition |
| A50 | Agent internalization | Internalize the cascade |
| A51 | Frame: outcome risk vs chat improvisation | Frame |

Zero uncovered rows. Overlap of mention is allowed; ownership of the failure mode is exclusive.

---

## Customization ledger (public idea → figureitout ratchet → why)

| Public idea | figureitout customization | Scientific reason |
|-------------|---------------------------|-------------------|
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) (~39.8k) — plan→execute→judge graph | `runner.py` / `planner.py` / `worker.py` reflexion loop + job folders | Durable state on disk; parent context must not hold the graph |
| [microsoft/autogen](https://github.com/microsoft/autogen) (~60.4k) / [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) (~57.1k) — multi-agent debate | Expert board + immutable meta seats | Domain board is dynamic; meta seats cannot waive epistemic law |
| [567-labs/instructor](https://github.com/567-labs/instructor) (~13.7k) — typed LLM outputs | `judge.py` + predicate truth | Markdown “looks good” cannot flip truth; schemas can |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) (~63.3k) — agent memory | lessons log + memory bus + checkpoints | Cross-tool one brain; pointers, not full dumps |
| [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) (~29.0k) — research fan-out | Thin parent + trend/explain routes | Research blobs stay in worker files; parent reads summaries |
| [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) (~24.3k) — prompt regression | Pre-answer checklist + always-on force-routing | Routing fidelity is measurable; self-classification is not |
| [langfuse/langfuse](https://github.com/langfuse/langfuse) (~33.2k) — traces | Status streaming + `run_log.jsonl` | Human-visible progress without installing full telemetry mid-objective |
| [BerriAI/litellm](https://github.com/BerriAI/litellm) (~56.4k) — LLM router | Backends: MCP-first, never ask keys, same-runtime pin | Continuity without credential begging; host affinity prevents cross-tool CLI chaos |
| [tobymao/sqlglot](https://github.com/tobymao/sqlglot) (~9.5k) — SQL validate | Query-bank + first-principles SQL | Invalid or off-domain SQL must fail before publish |
| [microsoft/markitdown](https://github.com/microsoft/markitdown) (~174k) — docs→Markdown | Context brief ingest path | Sources become inventoryable text, still hypotheses until SQL |
| [huggingface/smolagents](https://github.com/huggingface/smolagents) (~28.8k) — code-act | Worker tool sessions; Task escalation | Empty stdout is not a result; tools write `result.md` |
| [chartjs/Chart.js](https://github.com/chartjs/Chart.js) (~67.6k) / [evidence-dev/evidence](https://github.com/evidence-dev/evidence) (~6.9k) — charts from data | Source-link UX + light Material UI | Trust UI is part of truth: lineage under the graph |
| [microsoft/playwright](https://github.com/microsoft/playwright) (~94.6k) — browser automation | Last in cascade; new-window Chrome; UX click proof | Browser is unreliable vs CLI/MCP; still mandatory for customer-path proof |
| [anthropics/skills](https://github.com/anthropics/skills) (~170k) — skill packaging | [`SKILL.md`](SKILL.md) + Cursor/Devin/Claude mirrors | Portable operating law across IDEs |
| [cli/cli](https://github.com/cli/cli) (~45.8k) — GitHub CLI | Private-gist wrappers + ticket/PR link hygiene | Publish and verify without trusting comments alone |
| [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) (~19.3k) — structured agents | Complements Instructor for typed judge boards | Advisory prose cannot be the acceptance mechanism |
| [ollama/ollama](https://github.com/ollama/ollama) (~179k) — local models | Default local route when a router is running | Work continues when cloud keys must not be requested |
| [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) (~37.3k) — program, don't prompt | First-principles briefs + typed predicates instead of a bigger system prompt | Prompt text cannot be the acceptance mechanism; compiled checks can |
| [UKGovernmentBEIS/inspect_ai](https://github.com/UKGovernmentBEIS/inspect_ai) (~2.6k) — LLM/agent evals | Predicate board + multi-lens judge | A scorer that never ran is false; narrative "looks good" is not a score |
| [openai/openai-agents-python](https://github.com/openai/openai-agents-python) (~28.7k) — model-agnostic SDK | Same laboratory regardless of local / Anthropic / OpenAI | Host affinity + never ask keys; the loop is not a vendor |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) (~24.0k) — tools | Data cascade: CLI/MCP before browser | Strongest reliable path first |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) (~109k) — browser agents | Last in the cascade; customer-path click proof | Browser is unreliable vs CLI/MCP; still mandatory for UI proof |
| [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) (~84.2k) — coding agents | Thin parent + job folders | Workers hold context; parent reports paths |
| [letta-ai/letta](https://github.com/letta-ai/letta) (~24.3k) — stateful agents | `checkpoint.json` any agent can resume | Turn off/on without losing the lock |

---

## Closing — one scientific instrument

An agent that internalizes figureitout stops treating the skill as a menu of tips and starts treating it as a single instrument: force the prompt into a locked run, inventory sources as hypotheses, prove methods wrong, compute only on-domain live evidence, sniff every number, communicate for zero-context action, verify use and clicks, accept only when predicates are true, recover twice before asking a human, publish privately, and write one lesson so the next run is less naive.

Public GitHub projects supply the gears. figureitout’s customizations supply the ratchet that prevents helpful improvisation from defeating truth. When `/letscook` is invoked, you are not “being an agent.” You are operating a laboratory whose definition of done can be checked by someone who does not trust you — and that is the point.

**This document is complete when** all thirty-five themes above are present with two story paragraphs each, the fifty-one atoms have exactly one owner and zero uncovered rows, and every public learning link is a `github.com` URL.
