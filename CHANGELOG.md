# Changelog

All notable changes to this extension are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The release workflow reads the section matching the tag being built, so each version needs its own
`## [X.Y.Z]` heading before it is tagged.

## [Unreleased]

## [0.1.0]

### Added

- `/speckit.stepwise-implement` — incremental alternative to `/speckit.implement`: one task per
  turn, halt for approval, batch on request, and record human-directed departures in
  `deviations.md` while leaving the planning artifacts untouched.
- Release workflow: validates the manifest (structurally, and against spec-kit's own validator),
  builds a reproducible extension archive, and publishes a catalog file so
  `specify extension add`/`update` resolve without a `--from` URL.
