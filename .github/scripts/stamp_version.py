#!/usr/bin/env python3
"""Make the tag the source of truth for the extension version.

The tag decides what gets published, so the manifest and changelog are stamped
from it rather than being kept in sync by hand. ``check_manifest.py``'s
tag/version gate stays in force behind this — it now guards the stamper instead
of the human.

Edits are line-targeted rather than a YAML round-trip: ``yaml.safe_dump`` would
reformat the manifest and drop every comment in it.

Two things are stamped:

* ``extension.version`` in ``extension.yml`` — the version an installed
  extension reports.
* A ``## [X.Y.Z]`` section in ``CHANGELOG.md``, which the release workflow reads
  for its notes. Content sitting under ``## [Unreleased]`` is promoted into it,
  which is the Keep a Changelog release step.

Changelog promotion is skipped for pre-releases: promoting `Unreleased` into a
`-rc` heading would consume the notes the eventual stable release needs.

Usage:
    stamp_version.py --tag vX.Y.Z [--check]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "extension.yml"
CHANGELOG = ROOT / "CHANGELOG.md"


def version_from_tag(tag: str) -> str:
    return tag[1:] if tag.startswith("v") else tag


def stamp_manifest(version: str, apply: bool) -> bool:
    """Rewrite extension.version. Returns True when the file needs a change."""
    lines = MANIFEST.read_text(encoding="utf-8").splitlines(keepends=True)

    # Only the version under the top-level `extension:` key: `requires.tools[]`
    # entries carry their own `version:` and must not be touched.
    in_extension = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not in_extension:
            if re.match(r"^extension:\s*$", line):
                in_extension = True
            continue
        # A non-indented, non-blank, non-comment line ends the block.
        if line[:1] not in (" ", "\t", "\n", "#") and stripped:
            break
        match = re.match(r"^(\s*version:\s*)(.*?)(\s*)$", line)
        if match:
            replacement = f'{match.group(1)}"{version}"{match.group(3)}'
            if line == replacement:
                return False
            if apply:
                lines[index] = replacement
                MANIFEST.write_text("".join(lines), encoding="utf-8")
                # The point of stamping is that the parsed value is right; assert it
                # rather than trusting the regex.
                parsed = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
                actual = parsed["extension"]["version"]
                if actual != version:
                    raise SystemExit(
                        f"::error::stamped extension.yml but it parses as {actual!r}, not {version!r}"
                    )
            return True

    raise SystemExit("::error::no version: line found under extension: in extension.yml")


def stamp_changelog(version: str, apply: bool) -> bool:
    """Ensure a `## [version]` section exists, promoting Unreleased into it."""
    if not CHANGELOG.is_file():
        return False

    text = CHANGELOG.read_text(encoding="utf-8")
    if re.search(rf"^## \[{re.escape(version)}\]", text, re.MULTILINE):
        return False

    match = re.search(r"^## \[Unreleased\][^\n]*\n(.*?)(?=^## \[|\Z)", text, re.MULTILINE | re.DOTALL)
    if not match:
        return False

    body = match.group(1).strip()
    promoted = f"## [Unreleased]\n\n## [{version}]\n"
    if body:
        promoted += f"\n{body}\n"
    promoted += "\n"

    if apply:
        CHANGELOG.write_text(text[: match.start()] + promoted + text[match.end() :], encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report whether a stamp is needed without writing anything",
    )
    parser.add_argument(
        "--skip-changelog",
        action="store_true",
        help="Stamp the manifest only (used for pre-releases)",
    )
    args = parser.parse_args()

    version = version_from_tag(args.tag)
    apply = not args.check

    manifest_changed = stamp_manifest(version, apply)
    changelog_changed = False if args.skip_changelog else stamp_changelog(version, apply)

    verb = "needs stamping" if args.check else "stamped"
    print(f"extension.yml: {verb if manifest_changed else 'already at ' + version}")
    if not args.skip_changelog:
        print(f"CHANGELOG.md: {verb if changelog_changed else 'already has a section for ' + version}")

    changed = manifest_changed or changelog_changed
    # Consumed by the workflow to decide whether a commit is worth making.
    print(f"changed={'true' if changed else 'false'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
