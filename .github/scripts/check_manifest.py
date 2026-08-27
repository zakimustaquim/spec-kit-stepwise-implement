#!/usr/bin/env python3
"""Validate extension.yml before a release is published.

Two layers, deliberately separate:

1. Structural checks that only need PyYAML, so a release is never blocked by a
   network failure. These mirror the rules spec-kit's own ``ExtensionManifest``
   enforces at install time -- required keys, id format, semantic version,
   the ``speckit.{extension-id}.{command}`` command-name pattern, and the
   existence of every declared command file.
2. Optionally, spec-kit's real validator (``--with-speckit``), which is
   authoritative and catches schema rules this file does not restate. A missing
   or renamed upstream import is reported as "could not validate", not as a
   validation failure: being unable to check is not the same as being invalid.

Usage:
    check_manifest.py [--tag vX.Y.Z] [--with-speckit]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "extension.yml"

SCHEMA_VERSION = "1.0"
ID_PATTERN = re.compile(r"^[a-z0-9-]+$")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
COMMAND_PATTERN = re.compile(r"^speckit\.([a-z0-9-]+)\.([a-z0-9-]+)$")

errors: list[str] = []
notes: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def check_structure(data: dict, tag: str | None) -> None:
    for key in ("schema_version", "extension", "requires", "provides"):
        if key not in data:
            fail(f"missing top-level key: {key}")
    if errors:
        return

    if data["schema_version"] != SCHEMA_VERSION:
        fail(f"schema_version must be {SCHEMA_VERSION!r}, got {data['schema_version']!r}")

    ext = data["extension"]
    if not isinstance(ext, dict):
        fail("extension must be a mapping")
        return

    for field in ("id", "name", "version", "description"):
        if not isinstance(ext.get(field), str) or not ext[field].strip():
            fail(f"extension.{field} must be a non-empty string")

    ext_id = ext.get("id")
    if isinstance(ext_id, str) and not ID_PATTERN.match(ext_id):
        fail(f"extension.id {ext_id!r} must be lowercase alphanumeric with hyphens only")

    version = ext.get("version")
    if isinstance(version, str) and not SEMVER_PATTERN.match(version):
        fail(f"extension.version {version!r} is not a semantic version")

    # The tag is the release's identity; the manifest is what users see after
    # install. A mismatch ships an extension that misreports its own version.
    if tag and isinstance(version, str):
        expected = tag[1:] if tag.startswith("v") else tag
        if expected != version:
            fail(
                f"tag {tag!r} implies version {expected!r} but extension.yml "
                f"declares {version!r} -- bump the manifest or retag"
            )

    provides = data["provides"]
    if not isinstance(provides, dict):
        fail("provides must be a mapping")
        return

    commands = provides.get("commands")
    if not isinstance(commands, list) or not commands:
        fail("provides.commands must be a non-empty list")
        return

    for cmd in commands:
        if not isinstance(cmd, dict):
            fail(f"command entry must be a mapping, got {type(cmd).__name__}")
            continue
        name, rel = cmd.get("name"), cmd.get("file")
        if not isinstance(name, str) or not isinstance(rel, str):
            fail(f"command entry needs string 'name' and 'file': {cmd!r}")
            continue

        match = COMMAND_PATTERN.match(name)
        if not match:
            fail(
                f"command {name!r} must match speckit.{{extension-id}}.{{command}} "
                "-- a two-segment name belongs in 'aliases', which is free-form"
            )
        elif match.group(1) != ext_id:
            fail(f"command {name!r} does not carry extension id {ext_id!r} as its middle segment")

        if not (ROOT / rel).is_file():
            fail(f"command {name!r} declares missing file: {rel}")

        aliases = cmd.get("aliases", []) or []
        if not isinstance(aliases, list) or any(not isinstance(a, str) for a in aliases):
            fail(f"aliases for {name!r} must be a list of strings")
            continue
        for alias in aliases:
            if alias.startswith("/") or ".." in alias:
                fail(f"alias {alias!r} for {name!r} must be a safe relative name")


def check_with_speckit() -> None:
    try:
        from specify_cli.extensions import ExtensionManifest, ValidationError
    except Exception as exc:  # noqa: BLE001 - any import failure is "cannot check"
        notes.append(f"skipped spec-kit validation: {type(exc).__name__}: {exc}")
        return

    try:
        manifest = ExtensionManifest(MANIFEST)
    except ValidationError as exc:
        fail(f"spec-kit validator rejected the manifest: {exc}")
        return

    notes.append("spec-kit validator accepted the manifest")
    for warning in getattr(manifest, "warnings", []) or []:
        notes.append(f"spec-kit warning: {warning}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default=None, help="Release tag to check the manifest version against")
    parser.add_argument("--with-speckit", action="store_true", help="Also run spec-kit's own validator")
    args = parser.parse_args()

    if not MANIFEST.is_file():
        print(f"::error::no extension.yml at {MANIFEST}", file=sys.stderr)
        return 1

    try:
        data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"::error::extension.yml is not valid YAML: {exc}", file=sys.stderr)
        return 1

    if not isinstance(data, dict):
        print("::error::extension.yml must be a YAML mapping", file=sys.stderr)
        return 1

    check_structure(data, args.tag)
    if args.with_speckit:
        check_with_speckit()

    for note in notes:
        print(f"note: {note}")
    for error in errors:
        print(f"::error::{error}", file=sys.stderr)

    if errors:
        print(f"\n{len(errors)} problem(s) found.", file=sys.stderr)
        return 1

    print(f"\nextension.yml is valid (version {data['extension']['version']}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
