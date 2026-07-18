# ⌘ Sandbox v1.0.0 — Three-Zone Workspace Protocol

> **v1.0.0** · shipped 2026-07-19 · [MIT](LICENSE) · [github.com/ObsidianArchives/sandbox-protocol](https://github.com/ObsidianArchives/sandbox-protocol)

```
Build in internal. Stage to sandbox. Ship from live.
```

Sandbox is a zero-dependency workspace protocol. It gives every project a structured home with three zones: a working copy with full data, a clean deploy copy, and a public-facing live copy. A single `index.json` manifest tracks everything.

## Why Sandbox?

Before Sandbox, projects scatter across `~/` with no manifest, no separation between dev and deploy, no way to see everything at a glance. After Sandbox, every project has a known location, a known state, and a known path to shipping.

**The three-zone pattern:**

```
~/Sandbox/
├── Internal_SandBox/     Zone 1 — working copies, full data, free commits
├── git_sandbox/          Zone 2 — clean deploy copies, tagged versions
└── tools/                Registered tool binaries

~/git_live/               Zone 3 — public-facing repos → GitHub
```

## The Flow

1. **Build** in `Internal_SandBox/` — full data, drafts, caches, archives. Commit freely.
2. **Stage** to `git_sandbox/` — rsync excluding gitignored files. Clean copy. Tag releases.
3. **Ship** from `git_live/` — push to GitHub. The world sees clean, tagged code.

## index.json — The Manifest

A single JSON file at the sandbox root tracks everything:

- `tools[]` — registered binary applications (AppImages, scripts)
- `projects[]` — git-tracked projects with zone paths
- `content_repos[]` — non-code artifacts (canvases, designs, visual content)
- `environments[]` — zone definitions

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
```

See [QUICKSTART.md](QUICKSTART.md) for the full walkthrough with what's happening under the hood.

## What's in This Repo

| File | Purpose |
|------|---------|
| `PROTOCOL.md` | Full specification — zones, lifecycle, schema, rsync pipeline |
| `examples/minimal-sandbox/` | Working demo: sandbox project with LOOM tracking and own tooling |
| `QUICKSTART.md` | 3-command onboarding |
| `SKILL.md` | Hermes AI operational knowledge |
| `index.schema.json` | JSON Schema for manifest validation |
| `scripts/sync.sh` | Three-zone rsync pipeline with git integration |
| `scripts/validate.py` | Manifest validation (schema, paths, tags) |
| `scripts/status.py` | Zone health dashboard |
| `scripts/sandbox-init.sh` | Bootstrap a fresh sandbox |
| `scripts/sandbox-register.py` | Register projects in the manifest |

## Protocol Suite

Sandbox is part of the protocol suite:

| Protocol | Purpose |
|----------|---------|
| ⌘ **Sandbox** | Workspace organization — where things live, how they flow |
| 🝪 **LOOM** | Project tracking — what to do, what was done |
| 🗄 **arca** | Backup vault — nothing is lost |

Three protocols. Three concerns. One weave.

## License

MIT. See [LICENSE](LICENSE).

## Attribution

Redistribution requires visible attribution to **ObsidianArchives** (https://github.com/ObsidianArchives) per the [LICENSE](LICENSE) terms. Derivatives must credit the Sandbox Protocol as their origin.
