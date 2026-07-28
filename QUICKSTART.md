# ⌘ Sandbox Quickstart v1.2.0

Get a three-zone workspace running in under a minute.

## 1. Create a Sandbox

```bash
./sandbox-init.sh
```

This creates `~/Sandbox/` with three zones, a valid manifest, and a `drops/` directory for inbound artifacts.

The script creates:
- `Internal_SandBox/` — Zone 1 (working copies)
- `git_sandbox/` — Zone 2 (deploy copies)
- `drops/` — inbound artifact staging with `catalog.json`
- `tools/` — registered binary applications
- `index.json` — v2 manifest skeleton
- Zone 3 at `~/git_live/` automatically

### Configuration

Set these environment variables (add to `~/.bashrc` for persistence):

```bash
export SAND_ROOT=~/Sandbox        # where your sandbox lives
export LIVE_ROOT=~/git_live       # where public repos live (Zone 3)
```

If unset, scripts default to `~/Sandbox/` and `~/git_live/` respectively.

> **💡 LOOM Integration:** Projects in `Internal_SandBox/` can have `.loom/` directories
> tracked by [🝪 LOOM](https://github.com/ObsidianArchives/LOOM). These stay in Zone 1 —
> they're automatically excluded when syncing to Zone 2+3. Never gitignore `.loom/` in Zone 1.
> See [examples/minimal-sandbox/](examples/minimal-sandbox/) for a working demo.

### Drops: Inbound Artifact Staging

The sandbox includes a `drops/` directory at the root level for inbound artifacts — files downloaded from the internet, exported dashboards, reference materials. These are catalogued in `drops/catalog.json` and can be curated into projects.

```bash
# View catalog
cat ~/Sandbox/drops/catalog.json

# Render human-readable view
python3 sandbox-internal/scripts/render_catalog.py
cat ~/Sandbox/drops/CATALOG.md
```

## 2. Register Your Project

```bash
./sandbox-register.py \
  --name my-project-internal \
  --type tool \
  --path my-project-internal \
  --description "My first sandbox project"
```

Your project directory must already exist inside `Internal_SandBox/`. The script auto-detects git info, file count, and size.

## 3. Sync Through All Zones

First time (sets up Zone 3 git + GitHub remote):
```bash
./sync.sh my-project-internal --first-release --remote https://github.com/you/my-project.git --all
```

After first release (routine sync):
```bash
./sync.sh my-project-internal --all
```

This runs the full pipeline: Internal → Sandbox → Live → GitHub.

## 4. Check Health

```bash
./status.py
```

Shows every project across all zones — synced, behind, missing, or dormant.

## 5. Tag a Release

```bash
./sync.sh my-project-internal --zone1-to-2 --tag --tag-version 0.1.0
```

Tags both Zone 2 and Zone 3 after syncing.

---

## What's Happening Under the Hood?

<details>
<summary>Click to see the manual steps these scripts automate</summary>

### Create the structure manually
```bash
mkdir -p ~/Sandbox/Internal_SandBox ~/Sandbox/git_sandbox ~/Sandbox/tools
```

### Write a minimal index.json
```json
{
  "sandbox": "Sandbox",
  "sigil": "⌘",
  "version": "v2",
  "created": "2026-07-18",
  "updated": "2026-07-18T00:00:00Z",
  "tools": [],
  "content_repos": [],
  "environments": [
    {"name": "Internal_SandBox", "purpose": "Working copies · full data · daily dev", "projects": []},
    {"name": "git_sandbox", "purpose": "Clean deploy copies · tagged versions", "projects": []}
  ],
  "stats": {"total_projects": 0, "total_environments": 2, "total_size_bytes": 0},
  "changelog": []
}
```

### Register a project by editing index.json
Add to `environments[0].projects[]`:
```json
{
  "name": "my-project-internal",
  "type": "internal",
  "path": "Internal_SandBox/my-project-internal",
  "version": "v0-dev",
  "files": 42,
  "size_bytes": 123456,
  "git_commit": "abc1234",
  "status": "active"
}
```

### Sync manually
```bash
# Internal → Sandbox
rsync -av --delete --exclude '.git' --exclude '.loom' --exclude '.icp' \
  --exclude 'node_modules' --exclude 'drafts' --exclude '__pycache__' \
  Internal_SandBox/my-project-internal/ git_sandbox/my-project/

# Sandbox → Live
rsync -av --delete --exclude '.git' \
  git_sandbox/my-project/ ~/git_live/my-project/

# Commit after sync
cd git_sandbox/my-project && git add -A && git commit -m "sync: my-project"
cd ~/git_live/my-project && git add -A && git commit -m "sync: my-project"
```

</details>

---

## Upgrading from v1.1.0

If your sandbox was created with an older version of the protocol (before drops/ existed), upgrade it:

```bash
./scripts/upgrade.sh
```

This creates `drops/{images,music,objects}` + `catalog.json` skeleton. Safe to run multiple times — it detects your current version and only applies missing migrations.

Use `--dry-run` to preview changes without applying them.

---

## Next Steps

- Read [PROTOCOL.md](PROTOCOL.md) for the full specification
- Run `./status.py` regularly to check zone health
- Run `./validate.py --check-paths --check-tags` before shipping
- See [LOOM](https://github.com/ObsidianArchives/LOOM) for project tracking — every sandbox project can be LOOM-tracked
- Check [examples/minimal-sandbox/](examples/minimal-sandbox/) for a working demo with LOOM integration
