# Stepwise Implement

A Spec Kit extension that implements `tasks.md` **one task at a time**, stopping for human approval
between units of work.

`/speckit.implement` runs the entire task list in one pass and reports at the end. That is the right
shape when the plan is trusted. It is the wrong shape when the plan is a hypothesis — by the time
you see the result, forty tasks were built on a decision you would have made differently at task
three.

This command inverts that. It implements the next task, verifies it, shows you the diff, and stops.

## Install

From a published release:

```bash
specify extension add stepwise-implement \
  --from https://github.com/zakimustaquim/spec-kit-stepwise-implement/releases/latest/download/stepwise-implement.zip
```

Or register the catalog once, which additionally makes `specify extension update` work — a `--from`
install is pinned forever, because update resolves versions through a catalog and skips anything it
cannot find in one:

```bash
specify extension catalog add \
  https://github.com/zakimustaquim/spec-kit-stepwise-implement/releases/latest/download/catalog.json \
  --name mine --install-allowed
specify extension add stepwise-implement
```

For local development:

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

## Releasing

The tag is the source of truth for the version — there is no manifest to bump by hand.
`.github/workflows/release.yml` runs on any `v*` tag and will:

1. Stamp `extension.yml`'s version and a `CHANGELOG.md` section from the tag, promoting anything
   under `## [Unreleased]` into the new version's section.
2. Validate the manifest structurally (PyYAML only, so a network failure cannot block a release),
   then again with spec-kit's real validator. An unavailable validator is reported as *skipped*; a
   validator that rejects the manifest fails the job. The tag/version check still runs — it now
   guards the stamper rather than the author.
3. Build `<id>.zip` reproducibly — sorted entries, pinned timestamps — containing only
   `extension.yml`, `commands/`, `LICENSE`, `README.md`, and `CHANGELOG.md`, with `extension.yml`
   at the archive root. The published `.sha256` is therefore worth comparing.
4. Assert the archive's shape before publishing, since a wrong shape otherwise fails at the user's
   install rather than in CI.
5. Publish the release with notes from this version's `CHANGELOG.md` section, attaching the zip, its
   checksum, and `catalog.json`.
6. Commit the stamped version back to the default branch, so the repo never disagrees with what was
   published. This runs only after a successful publish — a failed release must not leave a bump
   behind — and is authenticated with `GITHUB_TOKEN`, whose pushes do not trigger workflows, so it
   cannot loop.

So a release is just:

```bash
# optionally add notes under ## [Unreleased] first
git tag v1.1.0 && git push origin v1.1.0
```

Run the workflow manually (`workflow_dispatch`) to exercise everything except publishing and the
commit-back — assets land on the run as `dry-run-assets`. Tags are hard to retract once someone has
installed from them.

A tag containing a hyphen (`v1.1.0-rc1`) publishes as a pre-release. GitHub keeps those out of
`/releases/latest/`, so the catalog URL above keeps resolving to the last stable version; the
changelog promotion and the commit-back are both skipped, since a pre-release should not consume the
next stable release's notes or move the default branch's version.

> [!IMPORTANT]
> A tag-triggered workflow runs the version of itself that exists **at that tag's commit**. Changing
> `release.yml` on the default branch does not change what an existing tag does — delete and re-push
> the tag so it points at a commit containing the new workflow.

## Reference

Spec Kit's extension docs are the authority on manifest schema, hooks, and publishing:
`extensions/EXTENSION-DEVELOPMENT-GUIDE.md` and `EXTENSION-API-REFERENCE.md` in the
[spec-kit repo](https://github.com/github/spec-kit).

## License

MIT — see [LICENSE](LICENSE).
