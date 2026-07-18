# ⌘ Sandbox Protocol Specification v1.0

## 1. Overview

Sandbox is a three-zone workspace protocol. It provides a structured filesystem layout, a manifest format (`index.json`), and a lifecycle for projects moving from development to deployment.

**Core principle:** Build in internal. Stage to sandbox. Ship from live.

## 2. Zone Architecture

```
ZONE 1: Internal_SandBox/    Working copies · full data · free commits
ZONE 2: git_sandbox/         Clean deploy copies · tagged versions · gitignored files excluded
ZONE 3: ~/git_live/          Public-facing repos · GitHub remotes · tagged releases
```

### Zone 1 — Internal_SandBox

- **Purpose:** Daily development. All data lives here — drafts, caches, archives, notes.
- **Git:** Full history. Free commits. No sanitization needed.
- **Naming convention:** `<project-name>-internal/` for protocols, `<Project_Name>/` for applications.
- **Contains:** `.loom/` tracker, `forge/` artifacts, `drafts/`, `archives/`, full `node_modules/` if needed.

### Zone 2 — git_sandbox

- **Purpose:** Clean deploy copies. Ready for tagging and release.
- **Git:** Clean history. Tagged versions only (v1.0.0, v1.1.0, etc.).
- **Sync:** `rsync -av --delete` from Zone 1, excluding `.git/`, `.icp/`, `node_modules/`, `drafts/`.
- **Sanitization:** Gitignored files are naturally excluded by rsync. Additional content sanitization (stripping private paths, generic council seats) applied after sync if project is public-facing.
- **Naming:** `<project-name>/` (no `-internal` suffix).


### 2.1 Critical Pitfall: Git History vs rsync Exclusion

**rsync `--exclude .loom/` only affects NEW syncs. It does NOT remove `.loom/` from existing git history.**

If `.loom/` was ever committed to a zone's git repository before the exclusion
was added, those files persist in git history indefinitely. Every `git clone`
will retrieve them. Every `git log` will show them.

**Detection:** Check if `.loom/` is tracked in git history:
```bash
git log --all --full-history -- .loom/
```

**Fix:** Two options:
1. **Orphan branch** (preferred): `git checkout --orphan main && git add -A && git commit -m "fresh start"`
   Removes all history. Cleanest. Use for public releases.
2. **Filter-branch**: `git filter-branch --index-filter 'git rm --cached -r --ignore-unmatch .loom/' HEAD`
   Preserves other history but surgically removes `.loom/`. Fragile.

**Prevention:** Always exclude `.loom/` in the initial zone setup. Never commit it
to zone 2 or 3. The rsync exclude is a belt; the git history is the suspenders.
Both must be correct.

### Zone 3 — git_live

- **Purpose:** The public face. What the world sees on GitHub.
- **Sync:** `rsync -av --delete` from Zone 2.
- **Push:** `git push origin main --tags`
- **Naming:** Matches the GitHub repo name. Typically `~/git_live/<project-name>/`.

## 3. The index.json Manifest

The manifest lives at the sandbox root (`~/Sandbox/index.json`). It is the single source of truth for what exists, where it lives, and what state it's in.

### Schema v2

> **⚠️ Version Note (v1.0):** The current `index.json` uses a nested schema
> where projects are listed under `environments[].projects[]`. The flat
> `projects[]` array with per-project zone paths (shown below) is the
> **v1.2 roadmap** — planned. v1.0 shipped 2026-07-19. v1.1 tooling built. See §11 for the
> migration plan. Both schemas are valid; v1.0 ships the nested form.

```json
{
  "sandbox": "Sandbox_v2",
  "sigil": "⌘",
  "version": "v2",
  "created": "2026-07-06",
  "updated": "2026-07-19",

  "tools": [
    {
      "name": "string",
      "type": "appimage|script|binary",
      "path": "tools/<filename>",
      "version": "string",
      "size_mb": 0,
      "source_url": "url",
      "installed": "ISO date",
      "platform": "linux-x86_64|...",
      "runtime": ["dep1", "dep2"],
      "produces": [".ext1", ".ext2"],
      "status": "active|archived"
    }
  ],

  "projects": [
    {
      "id": "unique-id",
      "name": "Project Name",
      "type": "tool|os|docs",
      "internal_path": "Internal_SandBox/<dir>",
      "sandbox_path": "git_sandbox/<dir>",
      "live_path": "~/git_live/<dir>",
      "version": "1.0.0",
      "status": "active|complete|deferred|archived",
      "health": "healthy|behind|early|blocked",
      "loom_id": "loom-project-id",
      "git_remote": "github.com/user/repo",
      "description": "One-line description",
      "tags": ["tag1", "tag2"]
    }
  ],

  "content_repos": [
    {
      "name": "repo-name",
      "type": "visual-content|design|docs",
      "format": "tldr+json|png|svg|md",
      "internal_path": "Internal_SandBox/canvases/<dir>",
      "sandbox_path": "git_sandbox/canvases/<dir>",
      "live_path": "~/git_live/canvases-<name>",
      "version": "v0.1.0",
      "files": 0,
      "status": "active",
      "loom_id": "loom-epic-id"
    }
  ],

  "environments": [
    {
      "name": "Internal_SandBox",
      "purpose": "Working copies · full data · daily dev"
    },
    {
      "name": "git_sandbox",
      "purpose": "Clean deploy copies · tagged versions"
    }
  ]
}
```

### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `sandbox` | Yes | Instance name |
| `sigil` | No | Visual identifier (⌘) |
| `version` | Yes | Schema version (v2) |
| `tools[]` | No | Registered binary applications |
| `tools[].name` | Yes | Human-readable name |
| `tools[].type` | Yes | `appimage`, `script`, or `binary` |
| `tools[].path` | Yes | Relative path from sandbox root |
| `tools[].produces` | No | File extensions this tool creates |
| `projects[]` | Yes | Git-tracked projects |
| `projects[].id` | Yes | Unique identifier |
| `projects[].type` | Yes | `tool`, `os`, or `docs` |
| `projects[].loom_id` | No | Cross-reference to LOOM master_loom.json |
| `content_repos[]` | No | Non-code artifact repositories |
| `content_repos[].format` | Yes | Primary file format |

## 4. Tool Registry

Binary applications (AppImages, scripts, standalone binaries) live in `tools/` at the sandbox root. They are NOT projects — they don't have zones, git history, or LOOM tracking. They are registered in `index.json` for discoverability.

**Example:** tldraw AppImage → `tools/tldraw-offline-linux-x86_64.AppImage`

Tools declare what file types they produce (`produces: [".tldr"]`), linking them to content repos.

## 5. Content Repos

Non-code artifacts (whiteboards, design files, diagrams) that are versionable and go through the zone pipeline but aren't traditional "projects." Content repos:

- Live under `canvases/` or similar in each zone
- Are git-tracked
- Have LOOM epics tracking their artifacts
- Ship through the same three-zone pipeline

**Example:** tldraw canvases → `Internal_SandBox/canvases/tldraw/`

## 6. The Sync Pipeline

### Internal → Sandbox

```bash
rsync -av --delete \
  --exclude '.git' --exclude '.loom' --exclude '.icp' --exclude 'node_modules' \
  --exclude 'drafts' --exclude '__pycache__' \
  Internal_SandBox/<project>/ git_sandbox/<project>/
```

### Sandbox → Live

```bash
rsync -av --delete \
  --exclude '.git' \
  git_sandbox/<project>/ ~/git_live/<project>/
```

### Commit after sync

```bash
cd git_sandbox/<project> && git add -A && git commit -m "sync: <description>"
cd ~/git_live/<project> && git add -A && git commit -m "sync: <description>"
```

## 7. Project Lifecycle

```
created → active → complete|deferred|archived
               ↓
           blocked (temporary)
```

- **active:** Under active development. Has open items in LOOM.
- **complete:** All items done. Shipped. No open work.
- **deferred:** Paused. May resume later.
- **blocked:** Has blockers (missing deps, version drift, external dependency).
- **archived:** Done and no longer relevant. Moved to legacy.

## 8. Relationship to LOOM

Sandbox organizes WHERE. LOOM tracks WHAT. Together:

- Sandbox `index.json` has a `loom_id` field pointing to LOOM's `master_loom.json` project entry.
- LOOM items can reference sandbox paths via `file_path`.
- Projects registered in Sandbox MUST also be registered in LOOM (and vice versa).
- The sandbox instance itself is LOOM-tracked (`sandbox-protocol` project).

## 9. Relationship to arca

arca backs up the sandbox. The backup scope includes:

- `Internal_SandBox/` — full data, all projects
- `index.json` — the manifest
- `tools/` — tool binaries (if versioned)

Backup excludes `git_sandbox/` and `git_live/` (derived from internal).

## 10. Design Decisions

1. **Why rsync, not symlinks?** Symlinks create confusion about which copy is canonical. rsync makes the flow explicit: internal is always source of truth.

2. **Why three zones, not two?** Zone 2 (git_sandbox) exists because internal has data you never want to ship (drafts, archives, notes). Zone 3 (git_live) exists because git_sandbox is still local. The three zones map to: dev → staging → production.

3. **Why index.json, not a database?** Zero dependencies. Human-readable. Git-diffable. A single JSON file that any tool can parse.

4. **Why flat projects[] instead of nested under environments[]?** Projects span environments — they exist in all three zones simultaneously. Nesting under a single environment obscures this. Flat with zone paths is clearer.

## 11. Operational Scripts

The Sandbox Protocol ships with scripts that automate every documented operation. Run any script with `--help` for full usage.

### 11.1 sandbox-init.sh — Bootstrap

Creates a new sandbox from nothing. One command.

```bash
./sandbox-init.sh [--name <name>] [--path <path>]
```

Creates `Internal_SandBox/`, `git_sandbox/`, `tools/` directories and writes a valid `index.json` skeleton. Copies `index.schema.json` if accessible. Validates the skeleton on creation.

### 11.2 sandbox-register.py — Project Registration

Adds a project to `index.json` without manual JSON editing.

```bash
./sandbox-register.py --name <name> --type <tool|os|docs> --path <dir>
                      [--description "..."] [--tags tag1,tag2]
                      [--with-loom] [--dry-run]
```

Auto-detects git commit hash, file count, and directory size. Validates path existence and uniqueness. Optionally creates `.loom/` skeleton with `--with-loom`.

### 11.3 sync.sh — Sync Pipeline

Automates the three-zone rsync pipeline with git integration.

```bash
./sync.sh <project> [--zone1-to-2|--zone2-to-3|--push|--all]
                    [--tag] [--tag-version X] [--dry-run] [--no-commit]
```

Default `--all` runs the full pipeline: Internal → Sandbox → Live → GitHub push.
Use `--tag` to auto-tag after sync (reads version from index.json).
Use `--dry-run` to preview without executing.

### 11.4 status.py — Zone Health Dashboard

Read-only health check across all projects and zones.

```bash
./status.py [--project <name>] [--json] [--no-color] [--verbose]
```

Reports per-project: zone existence, git drift (days behind), tag status, remote presence.
Exit codes: 0 = healthy, 1 = warnings, 2 = errors (missing zones).

### 11.5 validate.py — Manifest Validation

Validates `index.json` against `index.schema.json` with optional filesystem checks.

```bash
./validate.py [--check-paths] [--check-tags] [--verbose] [--quiet]
```

`--check-paths` verifies all registered projects exist on disk.
`--check-tags` verifies git tag consistency across Zone 2 and Zone 3.
Exit code 1 on schema errors. Warnings don't block.

### 11.6 CLI Contract (Planned — v1.2)

These scripts are designed to be wrapped by a unified `sandbox` CLI in a future version:

```
sandbox init [path]          → sandbox-init.sh
sandbox register <project>   → sandbox-register.py
sandbox sync <project>       → sync.sh
sandbox status               → status.py
sandbox validate             → validate.py
```

Individual scripts remain the stable interface for v1.0 and v1.1.

## 12. Archive & References

### 12.1 Project Archive

When a project reaches end-of-life or is deferred indefinitely, move it to the archive rather than deleting it. Archived projects are preserved but excluded from syncing and health checks.

**Location:** `Internal_SandBox/.archive/<project>/`

**Process:**
1. Move the project directory: `mv Internal_SandBox/<project> Internal_SandBox/.archive/<project>`
2. Remove from `index.json` (or update status to `archived`)
3. Archive is a cold-storage zone — no syncing, no health checks, no git operations

**Restoration:** Move back to `Internal_SandBox/` and re-register in `index.json`.

### 12.2 Per-Project References

Projects accumulate research material — PDFs, screenshots, competitor analysis, design references. These live in each project's own `references/` directory.

**Location:** `Internal_SandBox/<project>/references/`

**Conventions:**
- Excluded from Zone 2 sync (rsync excludes `references/`)
- Not versioned in git by default (add to `.gitignore`)
- LOOM forge references serve a different purpose — those are design artifacts tied to specific epics. Project references are general research.

### 12.3 Sync Excludes

Both `.archive/` and `references/` are added to the rsync exclude list. They exist only in Zone 1 — never staged or shipped.

## 13. Multi-Machine Sync

Sandbox lives on one machine by default. When working across multiple machines (laptop + desktop), designate one as the **primary**. The secondary mirrors the primary via rsync.

### 13.1 Mirror from Primary

```bash
# On secondary machine, pull from primary:
rsync -av --delete primary-machine:~/Sandbox_v2/Internal_SandBox/ ~/Sandbox_v2/Internal_SandBox/
rsync -av primary-machine:~/Sandbox_v2/index.json ~/Sandbox_v2/index.json
```

Zone 2 and Zone 3 are derived — they don't need syncing. Rebuild them on the secondary by running `sync.sh` after the mirror.

### 13.2 Limitations

- **One-way only.** The secondary is a read-only mirror. Make changes on the primary, pull to secondary.
- **No bidirectional sync.** Two-way sync (both machines making changes) is not supported. If needed, evaluate Syncthing or a network share — but expect git conflicts.
- **index.json integrity.** If both machines register projects independently, a mirror will overwrite one set of registrations. Designate one machine as the canonical registrar.
