# Stepwise Implement

A Spec Kit extension that implements `tasks.md` **one task at a time**, stopping for human approval
between units of work.

`/speckit.implement` runs the entire task list in one pass and reports at the end. That is the right
shape when the plan is trusted. It is the wrong shape when the plan is a hypothesis — by the time
you see the result, forty tasks were built on a decision you would have made differently at task
three.

This command inverts that. It implements the next task, verifies it, shows you the diff, and stops.

## Install

```bash
cd /path/to/your/spec-kit-project
specify extension add --dev /path/to/spec-kit-stepwise-implement
specify extension list
```

Restart your AI agent so it picks up the new command.

## Usage

```text
/speckit.stepwise-implement                      # implement the next unchecked task, then halt
/speckit.stepwise-implement 3 tasks              # batch the next three
/speckit.stepwise-implement the rest of phase 2  # batch to the next checkpoint
/speckit.stepwise-implement T014                 # start at a specific task
```

Re-run it to continue — the resume point is the first unchecked task in `tasks.md`, so the workflow
survives session boundaries with no state of its own.

After each unit it halts with:

```text
Approve? (approve / revise <what> / deviate <what instead> / skip / batch N / stop)
```

`deviate` is the interesting one. Redirecting mid-implementation is expected, not an error — see
below.

## Deviations

When you change direction after seeing a task built, the command records the departure in
`specs/<feature>/deviations.md` rather than editing the plan to match. `spec.md`, `plan.md`,
`research.md`, `data-model.md`, and `contracts/**` stay exactly as written — they are the record of
what was *planned*, and `deviations.md` is the amendment log that wins where the two disagree.

Each entry states where, what the plan said, what was built instead, why, and which later tasks now
have to be read differently. A decision that is later reversed keeps its original entry intact under
a reversal banner: a bet that lost is the most useful thing in the file, and erasing it hides that
the call was ever in doubt.

`tasks.md` is the one planning artifact the command does write to, because it is the live progress
record. Completed tasks get `[X]`; tasks done differently get `🔄` with their original text
preserved on the line; dropped tasks get struck through and marked `⏭️`. Checkpoints that gated on a
dropped task are updated too.

## Guarantees

- One unit per turn — never continues past the approved boundary
- Never batches across a `**Checkpoint**` line or phase boundary
- Never marks a task `[X]` before that unit is approved
- Never claims success without pasting real gate output
- Never edits the frozen planning artifacts

## Layout

```text
extension.yml                              # manifest
commands/speckit.stepwise-implement.run.md # the command prompt
```

The primary command name is `speckit.stepwise-implement.run` because the manifest validator requires
the `speckit.{extension-id}.{command}` three-segment form. `speckit.stepwise-implement` is
registered as an alias, and is the name you type.

## Reference

Spec Kit's extension docs are the authority on manifest schema, hooks, and publishing:
`extensions/EXTENSION-DEVELOPMENT-GUIDE.md` and `EXTENSION-API-REFERENCE.md` in the
[spec-kit repo](https://github.com/github/spec-kit).

## License

MIT — see [LICENSE](LICENSE).
