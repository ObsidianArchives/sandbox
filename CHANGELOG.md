# Changelog

## v1.2.0 — Drops & Upgrades (2026-07-29)

### Added
- **drops/ — Inbound Artifact Protocol** — root-level directory for external artifacts (browser downloads, exported dashboards, reference materials)
- `catalog.json` — per-file artifact manifest with 20-field schema (excavation, hazard, provenance, curation, stewardship)
- `catalog.schema.json` — formal JSON Schema for catalog.json
- `scripts/render_catalog.py` — render catalog.json → human-readable CATALOG.md table
- `scripts/upgrade.sh` — version-aware incremental migrations for existing sandbox instances
- `examples/catalog-example.json` — 3-artifact demo showing all lifecycle states and hazard levels
- `examples/minimal-sandbox/drops/` — working drops/ directory in the example sandbox
- `protocol_version` field in index.json — enables upgrade.sh version detection

### Changed
- `sandbox-init.sh` — now creates `drops/{images,music,objects}` + `catalog.json` skeleton at bootstrap. Writes `protocol_version: "1.2.0"` into index.json. Copies docs, schemas, and scripts to instance for self-contained operation.
- `upgrade.sh` — version-aware incremental migrations. Copies docs, schemas, and scripts to instance (init ≡ upgrade: identical trees).
- `catalog.schema.json` — lives in `drops/` (with its data), not at instance root.
- `PROTOCOL.md` — added drops/ section to zone architecture (§2), documented upgrade flow (§11.7), render_catalog.py (§11.6)
- `QUICKSTART.md` — drops/ bootstrap section, upgrade section for pre-1.2.0 instances
- `SKILL.md` — drops/ operational patterns (register, assess, curate), upgrade.sh patterns, 5 new triggers
- `upgrade.sh` — split into mechanical (version-guarded) and cognitive (always-sync) layers. Docs, schemas, and scripts always refresh from tool repo on every run.
- `README.md` — v1.2.0 release notes, drops/ feature, updated script inventory, upgrade mention
- `PROTOCOL.md` — version tag bumped to v1.2.0
- `SKILL.md` — version bumped to 1.2.0
- `QUICKSTART.md` — version tag added (v1.2.0)
- `index.schema.json` — added `protocol_version` field
- Instance renamed from `Sandbox_v2` → `Sandbox` (aligns with tool defaults)
- Script default paths: `Sandbox_v2` → `Sandbox` (migrate-v2.py, sandbox-register.py, render_catalog.py)

### Pipeline
- EPIC-006 DROPS: 12 items across docs, schema, scripts, examples, and validation
- sandbox-internal fully dogfoods drops/ via live instance at ~/Sandbox/drops/

## v1.1.0 (2026-07-18)

### Shipped
- Full protocol specification (PROTOCOL.md)
- Public landing page (README.md)
- Quickstart guide (QUICKSTART.md)
- Automated sync pipeline (scripts/sync.sh)
- Zone health dashboard (scripts/status.py)
- Manifest validation (scripts/validate.py)
- Zone bootstrap (scripts/sandbox-init.sh)
- Project registration (scripts/sandbox-register.py)
- V2 migration tool (scripts/migrate-v2.py)
- JSON Schema (index.schema.json)
- AI operational knowledge (SKILL.md)
- MIT License with ObsidianArchives attribution

### Pipeline
- Internal → git_sandbox (fresh orphan, no .loom/ leakage)
- git_sandbox → git_live (clean copy)
- git_live → GitHub (ObsidianArchives/Sandbox)
- Tagged: v1.0.0

### Discovered During Release
- Git history retains .loom/ even after rsync exclusion → PROTOCOL.md §2.1
- sync.sh --tag/--sanitize implemented but not yet dogfooded in production
- Sandbox index.json needs automated freshness validation
- GitHub auth must be documented as protocol prerequisite

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
