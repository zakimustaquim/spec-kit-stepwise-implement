---
description: "Execute tasks.md one task at a time, pausing for approval after each, recording any human-directed deviations"
scripts:
  sh: ../../scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: ../../scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
  py: ../../scripts/python/check_prerequisites.py --json --require-tasks --include-tasks
---

# Stepwise Implement

Execute the implementation plan **incrementally**, stopping for human approval between units of
work. Where `__SPECKIT_COMMAND_IMPLEMENT__` runs the whole of `tasks.md` in one pass and reports at
the end, this command runs the smallest useful unit — by default a single task — then halts and
waits.

The halt is the feature. Seeing one task's real diff is when a human discovers the plan was wrong,
so this command treats mid-flight redirection as the expected case rather than an error, and records
each redirection in `deviations.md` so the departure survives the session that produced it.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). It may name a starting task
(`T014`), a batch size (`3 tasks`, `the rest of phase 2`), or a constraint that changes how the next
task is built.

## Non-Negotiables

These hold for every iteration. Violating any one of them defeats the purpose of the command.

1. **One unit, then stop.** Never continue past the approved unit's boundary. "Stop" means end the
   turn and wait for a human reply — not print a question and keep working.
2. **`spec.md`, `plan.md`, `research.md`, `data-model.md`, and `contracts/**` are read-only.** They
   are the record of what was planned. Departures are recorded in `deviations.md`, never by editing
   the plan to match what was built.
3. **Never mark a task `[X]` before its unit is approved.** A task marked complete is a claim a
   human accepted the work.
4. **Never silently absorb a redirection.** Any departure from a task's literal text gets a
   `deviations.md` entry in the same turn that implements it.
5. **Verify before claiming.** Run the project's own gates (tests, linters, type checks, build) for
   the files touched and paste real output. "Should work" is not a result.

## Outline

### 1. Establish context

Run `{SCRIPT}` from the repo root and parse `FEATURE_DIR` and `AVAILABLE_DOCS`. All paths are
absolute.

Read, in this order:

- **REQUIRED** `FEATURE_DIR/tasks.md` — the task inventory and its phase/dependency structure
- **REQUIRED** `FEATURE_DIR/plan.md` — tech stack, architecture, file layout
- **REQUIRED IF EXISTS** `FEATURE_DIR/deviations.md` — **read this before touching code.** It
  overrides the planning artifacts for anything already implemented, so a task written against the
  original design may already be obsolete
- **IF EXISTS** `FEATURE_DIR/data-model.md`, `FEATURE_DIR/contracts/`, `FEATURE_DIR/research.md`,
  `FEATURE_DIR/quickstart.md`, `memory/constitution.md`

### 2. Checklist gate (only on the first unit of a session)

If `FEATURE_DIR/checklists/` exists, count `- [ ]` vs `- [X]`/`- [x]` per file and print the table:

```text
| Checklist   | Total | Checked | Unchecked | Status |
|-------------|-------|---------|-----------|--------|
| ux.md       | 12    | 12      | 0         | ✓ PASS |
| security.md | 8     | 5       | 3         | ✗ FAIL |
```

Checklist markers are a **read-only gate** — report their state, never edit them. A `[X]` on a
custom checklist means a reviewer judged a *requirements-quality* criterion satisfied; it says
nothing about implementation progress.

If anything is unchecked, **STOP** and ask whether to proceed anyway. Do not re-run this gate on
subsequent units in the same session.

### 3. Build the task ledger

Parse every task line in `tasks.md` into: ID, checkbox state, phase, `[P]` parallel marker, story
tag, description, and the file paths it names.

Determine the **resume point**: the first task whose checkbox is unchecked, scanning top to bottom.
Ignore struck-through (`~~T015~~`) tasks — those were dropped by an earlier deviation — and skip
tasks already annotated `⏭️ UNPLANNED`.

If the user named a starting task, use it, but if it sits after an unchecked earlier task, say so
and ask before jumping ahead.

If every task is checked, report that the feature is complete and go to **Finishing a run**.

### 4. Choose the unit of work

The unit is **one task** unless the user asked for more. Honour these forms:

| User says | Unit |
|---|---|
| nothing | the single next task |
| `3 tasks` / `next 3` | the next 3 tasks in order |
| `the rest of phase 2` / `all of US1` | every remaining task in that phase or story |
| `T014-T018` | that explicit range |
| `all the [P] tasks in this phase` | the parallel-safe group |

Two hard limits on batching, regardless of what was asked:

- **Never batch across a `**Checkpoint**` line or a phase boundary.** Checkpoints exist to be
  verified. End the unit there and let the human see the checkpoint result.
- **Never batch a task whose dependencies are inside the same batch and unproven** — if T017 needs
  T016's output verified, they are two units.

If the request would cross either limit, build the largest compliant prefix, then say which tasks
you held back and why.

### 5. Announce, then implement

Before writing code, print the unit so the human sees what is about to happen:

```text
## Next: T017 [US2] — <task description, verbatim from tasks.md>

Files:      <paths this will create or modify>
Depends on: <task IDs, and whether their results were verified>
Deviations in force: <deviations.md entries that change this task, or "none">
Plan:       <2-5 lines of what you will actually do>
```

Then implement it. Follow the plan's conventions, the repo's existing idiom, and TDD ordering where
`tasks.md` sequences tests before their implementation.

### 6. Verify, then halt

Run the project's own gates over what changed and paste the real output — exit codes, test counts,
failure text. If a gate fails, do not ask for approval: report the failure, state whether it is
caused by this unit, and stop there.

Then report and **STOP**:

```text
## T017 complete — awaiting review

Changed:  <file:line summaries of what was written>
Verified: <commands run, with their actual output>
Notes:    <anything that surprised you, or that the task text got wrong>

Next up:  T018 — <description>

Approve? (approve / revise <what> / deviate <what instead> / skip / batch N / stop)
```

End the turn. Do not begin the next task, do not mark anything `[X]`, and do not pre-emptively
draft the next unit.

### 7. Act on the reply

| Reply | Action |
|---|---|
| **approve** | Mark the unit's tasks `[X]` per **Annotating tasks.md**, then return to step 3 for the next unit |
| **revise** | Rework in place. This is still the same task, so no deviation entry unless the task's *intent* changed. Re-verify, halt again |
| **deviate** | Record it per **Recording a deviation**, implement the new direction, mark the task per **Annotating tasks.md**, halt again |
| **skip** | Leave unchecked, or mark `⏭️ UNPLANNED` with a deviation entry if the human is dropping it deliberately. Move to the next task |
| **stop** | Go to **Finishing a run** |
| **batch N** | Set the unit size for the following units and continue |

An ambiguous reply is a question, not a licence to continue. Ask.

## Recording a Deviation

A deviation is any departure from what `tasks.md`, `plan.md`, or `contracts/**` literally say —
different interface, different tier, dropped requirement, task done a different way, task not done
at all. Record it **in the same turn you implement it**, at `FEATURE_DIR/deviations.md`.

If the file does not exist, create it with this header:

```markdown
# Deviations from the <feature> planning artifacts

Human-directed departures from `plan.md` / `contracts/*.md` / `tasks.md`, made during
implementation. Those documents are left as originally written (they are the record of what was
planned); this file is the amendment log. Where the two disagree, **this file wins** for anything
already implemented.

---
```

Append one section per deviation, newest last:

```markdown
## <short imperative title naming the thing that changed>

**Where**: <files touched> (<task IDs>).

**What the plan says**: <the original requirement, quoted or cited by artifact and section. If the
task line itself is being rewritten, quote it verbatim here — this becomes its only surviving copy.>

**What we built instead**: <the actual behaviour, stated as fact.>

**Why**: <the human's reasoning. If it is a bet rather than a settled fact, say so plainly.>

**Downstream impact**: <every later task, contract clause, or file that must now be read
differently — by task ID. Omit this heading only if genuinely nothing downstream is affected.>
```

Rules that keep this file trustworthy:

- **Date anything that is a measurement or a bet** — `deviations.md` is a dated record, so
  timestamps belong here even though they do not belong in code comments.
- **Never rewrite a superseded entry.** If a later decision reverses an earlier one, leave the
  original entry exactly as written and prepend a banner to it:

  ```markdown
  > ⚠️ 🔄 **REVERSED <date> — <what turned out to be true instead>.** <One paragraph: the new
  > answer, and which branch of the original entry's downstream-impact clause now applies.>
  >
  > The entry below is left as written on <original date>, when it was a hypothesis.
  ```

  A bet that lost is the most useful thing in the file. Erasing it hides that the decision was ever
  in doubt.
- **One entry per decision**, not per task. If one call changes five tasks, that is one entry whose
  downstream-impact clause names all five.

## Annotating tasks.md

`tasks.md` is the live progress record — it is the one planning artifact this command writes to.
Edit only the task lines it owns.

On plain completion:

```markdown
- [X] T017 [US2] <original description unchanged>
```

Add evidence inline when the task's outcome is itself the interesting part — a measurement, a probe,
a gate that had never run:

```markdown
- [X] T024 [US1] ✅ **Done <date> — <the measured result>.** <original description>
```

When the task was done differently, mark it `🔄` and **preserve the original text** after the
annotation, so the line still records what was planned:

```markdown
- [X] T046 [US4] 🔄 <what was actually built>. See `deviations.md` → "<entry title>".
  Original: <the task's original text, verbatim>
```

When the task was dropped or deliberately not done, strike the ID and mark it `⏭️`:

```markdown
- [ ] ~~T015~~ **⏭️ DROPPED** — <one line on what happened instead>. Original text and full
  rationale in `deviations.md`.
```

Also update the surrounding structure when a deviation invalidates it: strike dropped task IDs out
of `**Checkpoint**` lines and phase-level `⚠️ CRITICAL` notes, adding a short pointer to
`deviations.md`. A checkpoint that still gates on a dropped task is a trap for the next reader.

## Finishing a Run

A run ends when the human says stop or every task is checked. Report:

```text
## Stepwise implementation — run summary

Completed this run: <task IDs>
Remaining:          <count> tasks, next is <ID>
Deviations logged:  <count> — <titles>
Verification:       <gates run and their results>
```

Then dispatch post-implementation hooks — **only when every task in `tasks.md` is complete**, since
`after_implement` consumers assume a finished feature:

- Read `.specify/extensions.yml`. If it is absent, unparseable, or has no `hooks.after_implement`
  entries, skip silently.
- Skip entries where `enabled` is explicitly `false`; treat a missing `enabled` as enabled.
- Skip any entry with a non-empty `condition` — condition evaluation belongs to the HookExecutor,
  not to you.
- For each remaining entry, if `optional: false`, emit `EXECUTE_COMMAND: {command}` and then
  **actually invoke it** and wait for it to finish. Emitting the line does not run the hook, and the
  real invocation may differ from the printed id (a skills-mode agent runs `/skill:speckit-…` or
  `$speckit-…`). If `optional: true`, print the command, its description and prompt, and let the
  human decide.

## Done When

- [ ] Exactly one unit of work was implemented, verified with real output, and reported
- [ ] Every departure from the planning artifacts has a dated `deviations.md` entry
- [ ] `tasks.md` reflects reality: approved tasks `[X]`, changed tasks `🔄` with original text
      preserved, dropped tasks struck and `⏭️`, affected checkpoints updated
- [ ] `spec.md`, `plan.md`, `research.md`, `data-model.md`, and `contracts/**` are unmodified
- [ ] The turn ended on a halt awaiting human review, or on a run summary
