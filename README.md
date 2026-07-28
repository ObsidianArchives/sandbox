# ⌘ Sandbox v1.2.0 — Three-Zone Workspace Protocol

> **v1.2.0** · shipped 2026-07-29 · [MIT](LICENSE) · [github.com/ObsidianArchives/Sandbox](https://github.com/ObsidianArchives/Sandbox)

```
Build in internal. Stage to sandbox. Ship from live. Drop to catalog.
```

Sandbox is a zero-dependency workspace protocol. It gives every project a structured home with three zones — a working copy with full data, a clean deploy copy, and a public-facing live copy — plus an inbound artifact staging area (`drops/`). A single `index.json` manifest tracks everything.

## Why Sandbox?

Before Sandbox, projects scatter across `~/` with no manifest, no separation between dev and deploy, no way to see everything at a glance. After Sandbox, every project has a known location, a known state, and a known path to shipping.

**The three-zone + drops pattern:**

```
~/Sandbox/
├── Internal_SandBox/     Zone 1 — working copies, full data, free commits
├── git_sandbox/          Zone 2 — clean deploy copies, tagged versions
├── drops/        ◈       Inbound artifact staging (v1.2.0)
└── tools/                Registered tool binaries

~/git_live/               Zone 3 — public-facing repos → GitHub
```

## The Flow

1. **Build** in `Internal_SandBox/` — full data, drafts, caches, archives. Commit freely.
2. **Drop** into `drops/` — external artifacts land here. Catalogued, assessed, curated. (NEW v1.2.0)
3. **Stage** to `git_sandbox/` — rsync excluding internal files. Clean copy. Tag releases.
4. **Ship** from `git_live/` — push to GitHub. The world sees clean, tagged code.

## index.json — The Manifest

A single JSON file at the sandbox root tracks everything:

- `tools[]` — registered binary applications (AppImages, scripts)
- `projects[]` — git-tracked projects with zone paths
- `content_repos[]` — non-code artifacts (canvases, designs, visual content)
- `environments[]` — zone definitions

## drops/ — Inbound Artifact Staging (v1.2.0)

Files downloaded from the internet, exported dashboards, reference materials — they land in `drops/`. Tracked by `catalog.json` at per-file granularity with a 20-field artifact schema covering excavation, hazard, provenance, curation, and stewardship.

```bash
# View the catalog
cat drops/catalog.json

# Render a human-readable table
python3 scripts/render_catalog.py
cat drops/CATALOG.md
```

See `catalog.schema.json` for the formal schema. See `examples/catalog-example.json` for a 3-artifact demo.

## Project Types

| Type | Example | Git-tracked | Ships to public |
|------|---------|-------------|-----------------|
| `tool` | LOOM, arca, Sandbox itself | Yes | Yes (GitHub) |
| `os` | ExampleOS | Yes | Optional |
| `docs` | ExampleBlog, ExampleDocs | Yes | Yes (ICP/GitHub) |
| `visual-content` | tldraw canvases | Yes | Optional |

## Quick Example

```bash
# 1. Create a sandbox
./sandbox-init.sh

# 2. Register a project
./sandbox-register.py --name my-project-internal --type tool --path my-project-internal

# 3. Sync through all zones
./sync.sh my-project-internal --all

# 4. Check health
./status.py

# 5. Drop an artifact (v1.2.0)
#    Copy file to drops/ → register in catalog.json → assess → curate
```

See [QUICKSTART.md](QUICKSTART.md) for the full walkthrough.

**Upgrading from v1.1.0?** Run `./scripts/upgrade.sh` to create `drops/` and update your instance.

## What's in This Repo

| File | Purpose |
|------|---------|
| `PROTOCOL.md` | Full specification — zones, lifecycle, schema, rsync pipeline, drops/ |
| `examples/minimal-sandbox/` | Working demo: sandbox with LOOM tracking + drops/ directory |
| `examples/catalog-example.json` | 3-artifact demo showing all catalog states and hazard levels |
| `QUICKSTART.md` | 3-command onboarding + drops/ bootstrap |
| `SKILL.md` | Hermes AI operational knowledge |
| `index.schema.json` | JSON Schema for manifest validation |
| `catalog.schema.json` | JSON Schema for drops/catalog.json (v1.2.0) |
| `scripts/sync.sh` | Three-zone rsync pipeline with git integration |
| `scripts/validate.py` | Manifest validation (schema, paths, tags) |
| `scripts/status.py` | Zone health dashboard |
| `scripts/sandbox-init.sh` | Bootstrap a fresh sandbox |
| `scripts/sandbox-register.py` | Register projects in the manifest |
| `scripts/render_catalog.py` | Render catalog.json → CATALOG.md table (v1.2.0) |
| `scripts/upgrade.sh` | Version-aware migrations for existing instances (v1.2.0) |

## Protocol Suite

| Protocol | Purpose |
|----------|---------|
| ⌘ **Sandbox** | Workspace organization — where things live, how they flow |
| 🝪 **LOOM** | Project orchestration — what to do, what was done |
| 🗄 **arca** | Backup vault — nothing is lost |

Three protocols. One weave.

## License

MIT. See [LICENSE](LICENSE).

## Attribution

Redistribution requires visible attribution to **ObsidianArchives** (https://github.com/ObsidianArchives) per the [LICENSE](LICENSE) terms. Derivatives must credit the Sandbox Protocol as their origin.
