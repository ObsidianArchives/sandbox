# ⌘ Sandbox Quickstart

Get a three-zone workspace running in under a minute.

## 1. Create a Sandbox

```bash
./sandbox-init.sh
```

This creates `~/Sandbox/` with three empty zones and a valid manifest.

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

```bash
./sync.sh my-project-internal --all
```

This runs the full pipeline: Internal → Sandbox → Live → GitHub (if remote is set).

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

## Next Steps

- Read [PROTOCOL.md](PROTOCOL.md) for the full specification
- Run `./status.py` regularly to check zone health
- Run `./validate.py --check-paths --check-tags` before shipping
- See [LOOM](https://github.com/obsidianarchives/loom) for project tracking
