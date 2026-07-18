# Hello Project

A minimal project demonstrating the ⌘ Sandbox + 🝪 LOOM workflow.

## What's Here

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
cd sandbox-protocol
./scripts/sync.sh hello-project --zone1-to-2

# Run this project's own tooling
./scripts/hello.sh
```
