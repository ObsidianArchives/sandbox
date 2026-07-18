#!/usr/bin/env python3
"""🝪 Sub-Loom Render — lightweight project status display.

Reads .loom/loom.json and prints a header + health summary.
Zero dependencies beyond Python stdlib. ~40 lines.

Usage:
    python3 forge/tools/render.py              # reads ./.loom/loom.json
    python3 forge/tools/render.py --header     # header only
    python3 forge/tools/render.py --health     # health one-liner
    python3 forge/tools/render.py --path <dir> # explicit project path
"""

import json, sys, os
from datetime import datetime

def load(path=None):
    if path:
        loom_path = os.path.join(path, ".loom", "loom.json")
    else:
        loom_path = os.path.join(os.getcwd(), ".loom", "loom.json")
    if not os.path.exists(loom_path):
        print(f"ERROR: .loom/loom.json not found at {loom_path}")
        sys.exit(1)
    with open(loom_path) as f:
        return json.load(f)

def header(loom):
    items = loom.get("items", [])
    done = sum(1 for i in items if i.get("status") == "done")
    total = len(items)
    blocked = sum(1 for i in items if i.get("is_blocked"))
    sprint = loom.get("sprints", [])
    active = next((s for s in sprint if s.get("status") == "active"), None)
    sprint_name = active.get("name", "none") if active else "none"
    
    if blocked:
        health = "⛔ blocked"
    elif total == 0:
        health = "🟡 empty"
    elif done == total:
        health = "🟢 complete"
    elif done / total >= 0.8:
        health = "🟢 healthy"
    elif done / total >= 0.4:
        health = "🟡 behind"
    else:
        health = "🔴 early"
    
    ver = loom.get("version", "?")
    name = loom.get("name", "unknown")
    
    print(f"╔══════════════════════════════════════════════════════════════════════")
    print(f"║  🝪 {name}  ·  v{ver}  ·  {health} ({done}/{total} done)  ·  {sprint_name}")
    print(f"╚══════════════════════════════════════════════════════════════════════")

def health(loom):
    items = loom.get("items", [])
    done = sum(1 for i in items if i.get("status") == "done")
    total = len(items)
    blocked = sum(1 for i in items if i.get("is_blocked"))
    sprint = loom.get("sprints", [])
    active = next((s for s in sprint if s.get("status") == "active"), None)
    sprint_name = active.get("name", "none") if active else "none"
    print(f"🝪 {loom.get('name', '?')} | {done}/{total} done | {blocked} blocked | sprint: {sprint_name}")

if __name__ == "__main__":
    args = sys.argv[1:]
    path = None
    
    if "--path" in args:
        idx = args.index("--path")
        if idx + 1 < len(args):
            path = args[idx + 1]
    
    loom = load(path)
    
    if "--health" in args:
        health(loom)
    else:
        header(loom)
