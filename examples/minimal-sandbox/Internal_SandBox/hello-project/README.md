# Hello Project

A minimal project demonstrating the ⌘ Sandbox + 🝪 LOOM workflow.

## What's Here
> **Note:** `.loom/loom.json` is excluded from public repos by sandbox protocol.
> In a real project, LOOM's tracker lives here. Clone [LOOM](https://github.com/ObsidianArchives/LOOM)
> and run `render.py --input <path> --header` to see project status.


- `.loom/loom.json` — tracked by LOOM (3 items)
- `scripts/hello.sh` — this project's own tooling
- `index.json` — registered in the sandbox manifest

## The Flow

1. LOOM tracks WHAT to build (items, epics, sprints)
2. Sandbox organizes WHERE it lives (3-zone pipeline)
3. This project has its own scripts — it's a sub-loom with tooling

## Try It

```bash
# Check LOOM health
cd ../../..  # LOOM root
python3 forge/tools/render.py --input examples/minimal-sandbox/Internal_SandBox/hello-project --header

# Sync through sandbox zones
cd sandbox
./scripts/sync.sh hello-project --zone1-to-2

# Run this project's own tooling
./scripts/hello.sh
```
