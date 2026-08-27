#!/usr/bin/env python3
"""Build the release assets: the installable extension zip and a catalog entry.

The zip contains only what an installed extension needs, with `extension.yml` at
the archive root -- spec-kit's ``install_from_archive`` accepts either a bare
root or a single wrapping directory, and a bare root is the unambiguous form.

Byte-for-byte reproducible: entries are sorted and every timestamp is pinned, so
rebuilding the same commit produces an identical archive and a checksum is worth
comparing.

The catalog file makes ``specify extension add <id>`` and ``specify extension
update`` work, which a bare ``--from <url>`` install cannot -- update resolves
versions through a catalog and skips anything it cannot find in one.

Usage:
    build_assets.py --tag vX.Y.Z --repo owner/name --updated-at ISO8601 [--out dist]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

# Everything an installed extension needs, and nothing else: no .github/, no
# dev tooling, no git metadata. Directories are included recursively.
PAYLOAD = ("extension.yml", "commands", "LICENSE", "README.md", "CHANGELOG.md")

# Pinned so the archive is reproducible. Must be >= 1980, the ZIP epoch.
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def collect_payload() -> list[tuple[Path, str]]:
    """Return (absolute path, archive name) pairs, sorted by archive name."""
    entries: list[tuple[Path, str]] = []
    for name in PAYLOAD:
        path = ROOT / name
        if path.is_file():
            entries.append((path, name))
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file():
                    entries.append((child, child.relative_to(ROOT).as_posix()))
    return sorted(entries, key=lambda pair: pair[1])


def build_zip(entries: list[tuple[Path, str]], dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source, arcname in entries:
            info = zipfile.ZipInfo(arcname, date_time=FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())
    return hashlib.sha256(dest.read_bytes()).hexdigest()


def count_hooks(hooks: object) -> int:
    """Count hook commands. An event maps to one entry or a list of them."""
    if not isinstance(hooks, dict):
        return 0
    total = 0
    for value in hooks.values():
        if isinstance(value, list):
            total += sum(1 for item in value if isinstance(item, dict))
        elif isinstance(value, dict):
            total += 1
    return total


def build_catalog(data: dict, tag: str, repo: str, asset: str, updated_at: str) -> dict:
    ext = data["extension"]
    ext_id = ext["id"]
    download_url = f"https://github.com/{repo}/releases/download/{tag}/{asset}"

    entry = {
        "id": ext_id,
        "name": ext["name"],
        "version": ext["version"],
        "description": ext["description"],
        "author": ext.get("author", ""),
        "download_url": download_url,
        "repository": ext.get("repository", f"https://github.com/{repo}"),
        "homepage": ext.get("homepage", f"https://github.com/{repo}"),
        "documentation": f"https://github.com/{repo}/blob/{tag}/README.md",
        "changelog": f"https://github.com/{repo}/blob/{tag}/CHANGELOG.md",
        "license": ext.get("license", ""),
        "requires": data.get("requires", {}),
        "provides": {
            "commands": len(data.get("provides", {}).get("commands", []) or []),
            "hooks": count_hooks(data.get("hooks")),
        },
        "tags": data.get("tags", []),
        # An entry publishing itself can only ever claim false here: `verified`
        # is the reviewing catalog's assertion to make, not the author's.
        "verified": False,
        "updated_at": updated_at,
    }
    for optional in ("category", "effect"):
        if optional in ext:
            entry[optional] = ext[optional]

    return {
        "schema_version": "1.0",
        "updated_at": updated_at,
        # Stable across releases: GitHub redirects /releases/latest/download/<name>
        # to the newest non-prerelease asset, so registering this URL once keeps
        # resolving to the current version with no further edits.
        "catalog_url": f"https://github.com/{repo}/releases/latest/download/catalog.json",
        "extensions": {ext_id: entry},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--updated-at", required=True, help="ISO 8601 timestamp")
    parser.add_argument("--out", default="dist")
    args = parser.parse_args()

    data = yaml.safe_load((ROOT / "extension.yml").read_text(encoding="utf-8"))
    ext_id = data["extension"]["id"]

    out_dir = ROOT / args.out
    asset_name = f"{ext_id}.zip"

    entries = collect_payload()
    digest = build_zip(entries, out_dir / asset_name)

    catalog = build_catalog(data, args.tag, args.repo, asset_name, args.updated_at)
    (out_dir / "catalog.json").write_text(
        json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / f"{asset_name}.sha256").write_text(f"{digest}  {asset_name}\n", encoding="utf-8")

    print(f"{asset_name}: {len(entries)} files, sha256 {digest}")
    for _, arcname in entries:
        print(f"  {arcname}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
