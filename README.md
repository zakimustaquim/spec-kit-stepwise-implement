# Stepwise Implement

Placeholder Spec Kit extension. Rename the `stepwise-implement` id across
`extension.yml`, `commands/`, and this file before doing any real work — the
command namespace `speckit.{extension-id}.{command}` is validated against the id.

## Install (local development)

```bash
cd /path/to/a/spec-kit-project
specify extension add --dev /path/to/spec-kit-stepwise-implement
specify extension list
```

## Commands

| Command | Description |
|---------|-------------|
| `/speckit.stepwise-implement.example` | Placeholder command |

## Layout

```text
extension.yml        # manifest: identity, requirements, provided commands
commands/example.md  # one markdown file per command; body is the agent prompt
```

## Adding a command

1. Add `commands/<name>.md` with YAML frontmatter containing `description`.
2. Add a matching entry under `provides.commands` in `extension.yml`, named
   `speckit.stepwise-implement.<name>` (lowercase, hyphens only).
3. Reinstall with `specify extension add --dev .` and verify with
   `specify extension list`.

## Reference

Spec Kit's own guides are the authority for manifest schema, hooks, config,
skills, and publishing: `extensions/EXTENSION-DEVELOPMENT-GUIDE.md`,
`EXTENSION-API-REFERENCE.md`, and `EXTENSION-PUBLISHING-GUIDE.md` in the
[spec-kit repo](https://github.com/github/spec-kit).

## License

MIT — see [LICENSE](LICENSE).
