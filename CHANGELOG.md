# Changelog

## v1.1.0 (2026-07-18)

### Added
- `status.py` — zone health dashboard with `--json` and `--no-color` output
- `sandbox-init.sh` — bootstrap a fresh sandbox from nothing
- `sandbox-register.py` — register projects without manual JSON editing
- `migrate-v2.py` — convert index.json from v1 nested to v2 flat schema
- `sync.sh --tag` — auto-tag zones after sync
- `sync.sh --sanitize` — per-project sanitization hook support
- `validate.py --check-tags` — git tag consistency verification
- `SKILL.md` — Hermes AI operational knowledge

### Changed
- `QUICKSTART.md` rewritten for 3-command flow with collapsible manual reference
- `PROTOCOL.md` — added §11 Operational Scripts, added v1.0 schema honesty note
- `README.md` — script-based quick example, repo contents table, attribution fix
- `LICENSE` — modified MIT with explicit ObsidianArchives attribution clause
- `PROTOCOL.md` — `.loom` added to documented rsync exclude list

### Fixed
- `sync.sh` — `local` declaration moved inside function (was at case level)
- `index.schema.json` — `deferred` added to content_repos status enum
- `PROTOCOL.md` — §3 now explicitly notes v2 flat schema is aspirational for v1.0

## v1.0.0 (2026-07-18)

Initial release. Three-zone workspace protocol with:

- `PROTOCOL.md` — full specification
- `README.md` — public landing page
- `QUICKSTART.md` — 5-step onboarding
- `index.schema.json` — JSON Schema draft-07
- `sync.sh` — automated rsync pipeline with git integration
- `validate.py` — manifest validation (schema + paths)
- `LICENSE` — MIT
