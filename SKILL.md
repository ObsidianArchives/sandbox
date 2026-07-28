---
name: sandbox
description: "Operate the Sandbox three-zone workspace protocol — sync, validate, register, init, and check zone health."
version: 1.2.0
author: Hermes Agent × Mercury
triggers:
  - sandbox
  - zone
  - rsync
  - deploy
  - ship
  - index.json
  - Internal_SandBox
  - git_sandbox
  - git_live
  - sandbox-init
  - sandbox-register
  - status.py
  - validate.py
  - three-zone
  - content_repos
  - tools registry
  - drops
  - catalog.json
  - catalog
  - artifact
  - upgrade
---

# Sandbox Protocol · Hermes Operations Guide

## Quick Reference

```
ZONE 1: Internal_SandBox/    Working copies · full data · daily dev
ZONE 2: git_sandbox/         Clean deploy copies · tagged versions
ZONE 3: ~/git_live/          Public repos · GitHub remotes

FLOW: Internal → (rsync) → Sandbox → (rsync) → Live → (git push) → GitHub
        NEVER REVERSE. Zone 1 is always source of truth.

KEY FILES:
  ~/Sandbox/index.json              Manifest — single source of truth
  ~/Sandbox/index.schema.json       JSON Schema for manifest validation
  ~/Sandbox/Internal_SandBox/       Where all projects live (dev)
  ~/Sandbox/git_sandbox/            Clean copies (staging)
  ~/git_live/                          Public copies (production)
  ~/Sandbox/drops/                     Inbound artifact staging
  ~/Sandbox/drops/catalog.json         Artifact manifest (per-file granularity)

SCRIPTS (in sandbox-internal/scripts/):
  sync.sh              rsync pipeline
  validate.py          manifest validation
  status.py            zone health dashboard
  sandbox-init.sh      bootstrap new sandbox
  sandbox-register.py  add project to manifest
  render_catalog.py    catalog.json → CATALOG.md renderer
  upgrade.sh           version-aware incremental migrations
```

## Zone Architecture

Three zones with unidirectional data flow:

| Zone | Directory | Purpose | Contains |
|------|-----------|---------|----------|
| 1 | `Internal_SandBox/` | Daily dev | Everything — drafts, caches, .loom/, forge/, node_modules |
| 2 | `git_sandbox/` | Staging | Clean copies, tagged versions, excludes: .git .loom .icp node_modules drafts |
| 3 | `~/git_live/` | Production | Public repos, GitHub remotes, tagged releases |

**Rules:**
- Never sync reverse (Zone 2→1, Zone 3→2). Zone 1 is always canonical.
- `.loom/` never ships to Zone 2 or 3 (excluded in rsync).
- Git commit after every sync. Tag after milestones.
- Zone 2 and Zone 3 are derived — they can be deleted and rebuilt from Zone 1.

## Naming Conventions

| Zone | Convention | Example |
|------|-----------|---------|
| Zone 1 | `<project>-internal/` or `<Project_Name>/` | `sandbox-internal`, `Project_Apollon` |
| Zone 2 | `<project>/` or `<project>_git/` | `sandbox`, `loom_git` |
| Zone 3 | `<project>/` | `sandbox`, `loom` |

## Commands

### sync.sh — Sync Pipeline

```bash
./sync.sh <project> [FLAGS]
```

| Flag | Effect |
|------|--------|
| `--zone1-to-2` | Internal → Sandbox only |
| `--zone2-to-3` | Sandbox → Live only |
| `--push` | Push Zone 3 to GitHub |
| `--all` | Full pipeline (default) |
| `--tag` | Auto-tag after sync (reads version from index.json) |
| `--tag-version X` | Use specific version string for tag |
| `--dry-run` | Preview without executing |
| `--no-commit` | Skip git commit after rsync |

**Project matching:** the `<project>` argument must match a Zone 1 directory name. The script strips `-internal` suffix to derive Zone 2 and Zone 3 paths.

### validate.py — Manifest Validation

```bash
python3 validate.py [--check-paths] [--check-tags] [--verbose] [--quiet]
```

| Flag | Effect |
|------|--------|
| `--check-paths` | Verify registered projects exist on disk |
| `--check-tags` | Verify git tag consistency across Zone 2 and Zone 3 |
| `--verbose` | Show all details |
| `--quiet` | Only output on errors |

Exit codes: 1 = schema errors, 0 = valid (warnings don't block).

### status.py — Zone Health Dashboard

```bash
python3 status.py [--project <name>] [--json] [--no-color] [--verbose]
```

Exit codes: 0 = healthy, 1 = warnings (behind, no-remote), 2 = errors (missing zones).

### sandbox-init.sh — Bootstrap

```bash
./sandbox-init.sh [--name <name>] [--path <path>]
```

Creates a new sandbox instance. Post-creation output includes next steps.

### sandbox-register.py — Project Registration

```bash
python3 sandbox-register.py --name <name> --type <tool|os|docs> --path <dir>
                            [--description "..."] [--tags tag1,tag2]
                            [--with-loom] [--dry-run]
```

Auto-detects: git commit, file count, size. Validates: path exists, not duplicate.

### render_catalog.py — Drops Catalog Renderer

```bash
python3 render_catalog.py
```

Reads `~/Sandbox/drops/catalog.json`, writes `~/Sandbox/drops/CATALOG.md`. Human-readable table with hazard badges (🟢 trivial → ⚫ critical), status marks, and cabinet stats. Always run after modifying catalog.json.

### upgrade.sh — Version-Aware Migrations

```bash
./upgrade.sh [--dry-run]
```

Upgrades existing sandbox instances to current protocol version. Reads `protocol_version` from `index.json`, applies only missing migrations. Idempotent — safe to run on already-upgraded instances. Use `--dry-run` to preview.

## Working with drops/

drops/ is root-level infrastructure at `~/Sandbox/drops/`. It is NEVER inside any project. It does NOT sync to Zone 2 or Zone 3. It is instance-specific.

### Registering a New Artifact

When a file is dropped into `drops/`:

1. Compute sha256: `sha256sum ~/Sandbox/drops/<file>`
2. Check for Windows Zone.Identifier ADS: `cat ~/Sandbox/drops/<file>:Zone.Identifier`
3. Add entry to `drops/catalog.json` with all populated fields
4. Copy to `drops/objects/<sha256>/` for content-addressed archive
5. Run `python3 scripts/render_catalog.py` to update CATALOG.md

### Assessing Hazard

When triaging an artifact:

1. Check `excavation.stratum.zone_marker` — ZoneId=3 (Internet) → add "internet_origin" to hazard vectors
2. Grep for PII: `grep -r '/home/' drops/<file>` (for text files)
3. Grep for secrets: `grep -E 'BEGIN.*PRIVATE KEY|sk-[a-zA-Z0-9]{20,}' drops/<file>`
4. Set `hazard.level` based on findings: trivial → low → medium → high → critical
5. Update `catalog_status.state` to "assessed"

### Curating into a Project

When an artifact is ready to move to a project:

1. Set `curation.target_project_id` to match `index.json` project ID
2. Set `curation.status` to "targeted"
3. Copy/move file from `drops/` to target project path
4. If `loom_bridge.spawn_item` is true, create LOOM item in target project
5. Update `catalog_status.state` to "curated"
6. Run `python3 scripts/render_catalog.py`

### Upgrading Pre-1.2.0 Instances

When a user's sandbox was created before drops/ existed:

```bash
./scripts/upgrade.sh
```

This creates `drops/{images,music,objects}` + `catalog.json` skeleton. Idempotent — detects `protocol_version` in `index.json` and only applies missing migrations. Use `--dry-run` first to preview.

## Rules & Discipline

1. **Source of truth.** Zone 1 (Internal_SandBox) is always canonical. All development happens there.
2. **One-way flow.** Internal → Sandbox → Live. Never reverse. Never edit Zone 2 or 3 directly.
3. **Sync before ship.** Always run `validate.py --check-paths` before syncing to Zone 2.
4. **Commit after sync.** Every sync should result in a git commit in the target zone.
5. **Tag milestones.** Tag Zone 2 and Zone 3 after significant releases. Use `--tag` flag.
6. **.loom/ stays internal.** The LOOM tracker never ships to public zones.
7. **index.json is the map.** Always check it before making assumptions about project locations.
8. **Content repos follow same pipeline.** Canvases, designs — same three-zone flow.

## Pitfalls

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| Editing files in Zone 2 or 3 directly | Changes lost on next sync | Edit in Zone 1, sync again |
| Syncing before committing Zone 1 | Dirty state propagates | Commit Zone 1 first |
| Forgetting `.loom` in rsync excludes | LOOM tracker leaks to public | Added `.loom` to excludes (done) |
| Leaving `.env` files in Zone 1 | Credentials leak to Zone 2 | `.env*` is in rsync excludes |
| Not running `status.py` for weeks | Drift accumulates unnoticed | Run `status.py` regularly |
| Forgetting to tag | Can't track which version shipped | Use `sync.sh --tag` |
| Reverse sync (Zone 2→1) | Zone 1 overwritten by derived data | Never. Zone 1 is source of truth. |

## Conventions

- **Paths in index.json:** relative to sandbox root (e.g. `Internal_SandBox/loom_internal`)
- **Content repos:** live under `canvases/` in each zone, registered in index.json `content_repos[]`
- **Tools:** AppImages and binaries in `tools/` at sandbox root, registered in index.json `tools[]`
- **Forge artifacts:** live in `.loom/forge/` (internal only, excluded from sync)
- **Schema file:** `index.schema.json` ships with the protocol, copied to sandbox root on init

## Relationship to LOOM + arca

```
LOOM     → tracks WHAT (items, epics, sprints, progress)
Sandbox  → organizes WHERE (zones, manifest, sync pipeline)
arca     → protects AGAINST LOSS (backups, verification, recovery)
```

- LOOM items reference sandbox paths via `file_path`
- Sandbox index.json has `loom_id` field linking to master_loom.json
- arca backs up Internal_SandBox + index.json (not derived zones)
- All three are LOOM-tracked projects in master_loom.json

## Verification Checklist

Before declaring a sync complete:

- [ ] `validate.py --quiet` passes (schema valid)
- [ ] `validate.py --check-paths` passes (all paths exist)
- [ ] `status.py` shows target project as 🟢 synced
- [ ] Zone 2 git log shows recent commit
- [ ] Zone 3 git log matches Zone 2
- [ ] No `.loom/` or `forge/` in Zone 2 or Zone 3
- [ ] Tags match across Zone 2 and Zone 3 (if applicable)
