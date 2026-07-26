#!/usr/bin/env python3
"""⌘ Sandbox Register — add a project to index.json

Usage: sandbox-register.py --name <name> --type <tool|os|docs> --path <dir>
                           [--description "..."] [--tags tag1,tag2]
                           [--with-loom] [--dry-run]
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SAND_ROOT = Path(os.environ.get("SAND_ROOT", os.path.expanduser("~/Sandbox_v2")))
INDEX_PATH = SAND_ROOT / "index.json"

GREEN = "\033[0;32m"; YELLOW = "\033[1;33m"; RED = "\033[0;31m"; CYAN = "\033[0;36m"; NC = "\033[0m"


def parse_args():
    args = {"name": None, "type": None, "path": None, "description": "",
            "tags": [], "with_loom": False, "dry_run": False}
    argv = sys.argv[1:]; i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--name" and i+1 < len(argv): args["name"] = argv[i+1]; i += 2
        elif a == "--type" and i+1 < len(argv): args["type"] = argv[i+1]; i += 2
        elif a == "--path" and i+1 < len(argv): args["path"] = argv[i+1]; i += 2
        elif a == "--description" and i+1 < len(argv): args["description"] = argv[i+1]; i += 2
        elif a == "--tags" and i+1 < len(argv): args["tags"] = [t.strip() for t in argv[i+1].split(",")]; i += 2
        elif a == "--with-loom": args["with_loom"] = True; i += 1
        elif a == "--dry-run": args["dry_run"] = True; i += 1
        elif a in ("--help","-h"): print(__doc__); sys.exit(0)
        else: i += 1
    return args


def validate(args):
    errors = []
    if not args["name"]: errors.append("--name is required")
    if args["type"] not in ("tool","os","docs"): errors.append("--type must be: tool, os, or docs")
    if not args["path"]: errors.append("--path is required")
    elif not (SAND_ROOT / "Internal_SandBox" / args["path"]).is_dir():
        errors.append(f"Path not found: Internal_SandBox/{args['path']}")
    if not INDEX_PATH.exists():
        errors.append(f"No sandbox found at {SAND_ROOT}. Run sandbox-init.sh first.")
    return errors


def auto_detect(proj_dir):
    info = {"git_commit": None, "files": 0, "size_bytes": 0}
    try:
        out = subprocess.check_output(["git","-C",str(proj_dir),"rev-parse","--short","HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
        if out: info["git_commit"] = out
    except: pass
    try:
        out = subprocess.check_output(["find",str(proj_dir),"-not","-path","*/.git/*","-type","f"], text=True)
        info["files"] = len([l for l in out.split("\n") if l])
    except: pass
    try:
        out = subprocess.check_output(["du","-sb",str(proj_dir)], text=True)
        info["size_bytes"] = int(out.split()[0])
    except: pass
    return info


def create_loom_skeleton(proj_dir, name, ptype):
    loom_dir = proj_dir / ".loom"
    loom_dir.mkdir(exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    skeleton = {
        "app": "LOOM", "version": "1.4.0", "level": "sub-loom",
        "project": {
            "id": name.lower().replace(" ","-").replace("_","-"),
            "name": name, "path": str(proj_dir), "type": ptype,
            "status": "active", "created": today
        },
        "items": [], "epics": [], "sprints": []
    }
    with open(loom_dir / "loom.json", "w") as f:
        json.dump(skeleton, f, indent=2)
    return loom_dir / "loom.json"


def main():
    args = parse_args()
    errors = validate(args)
    if errors:
        for e in errors: print(f"{RED}✗{NC} {e}")
        sys.exit(1)

    proj_dir = SAND_ROOT / "Internal_SandBox" / args["path"]
    info = auto_detect(proj_dir)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"{CYAN}⌘ Sandbox Register{NC}")
    print(f"  Name: {args['name']}")
    print(f"  Type: {args['type']}")
    print(f"  Path: Internal_SandBox/{args['path']}")
    if info["git_commit"]: print(f"  Git:  {info['git_commit']}")
    print(f"  Files: {info['files']}")
    if args["description"]: print(f"  Desc: {args['description']}")
    if args["tags"]: print(f"  Tags: {', '.join(args['tags'])}")
    print()

    # Load index
    with open(INDEX_PATH) as f: idx = json.load(f)

    # Check duplicate
    for env in idx.get("environments", []):
        for p in env.get("projects", []):
            if p.get("name") == args["name"]:
                print(f"{RED}✗{NC} Project '{args['name']}' already registered in {env.get('name')}")
                sys.exit(1)

    # Build entry
    entry = {
        "name": args["name"],
        "type": "internal",
        "path": f"Internal_SandBox/{args['path']}",
        "version": "v0-dev",
        "files": info["files"],
        "size_bytes": info["size_bytes"],
        "domains": args["tags"] if args["tags"] else [],
        "git_commit": info["git_commit"],
        "status": "active",
        "notes": args["description"]
    }

    if args["dry_run"]:
        print(f"{YELLOW}[dry-run]{NC} Would add to Internal_SandBox:")
        print(json.dumps(entry, indent=2))
        if args["with_loom"]:
            print(f"\n{YELLOW}[dry-run]{NC} Would create .loom/ skeleton at {proj_dir}/.loom/")
        sys.exit(0)

    # Insert into Internal_SandBox
    for env in idx["environments"]:
        if env.get("name") == "Internal_SandBox":
            env.setdefault("projects", []).append(entry)
            break

    # Update stats
    stats = idx.setdefault("stats", {})
    stats["total_projects"] = stats.get("total_projects", 0) + 1
    stats.setdefault("served_by_projects", []).append(args["name"])
    stats["total_size_bytes"] = stats.get("total_size_bytes", 0) + info["size_bytes"]
    if not stats.get("newest") or today > stats["newest"]:
        stats["newest"] = today
    if not stats.get("oldest"): stats["oldest"] = today

    # Changelog
    idx.setdefault("changelog", []).append({
        "version": "v1", "date": today,
        "what": f"Registered {args['name']} ({args['type']}) via sandbox-register.py"
    })
    idx["updated"] = now

    with open(INDEX_PATH, "w") as f:
        json.dump(idx, f, indent=2)

    print(f"{GREEN}✓{NC} Registered '{args['name']}' in Internal_SandBox")
    print(f"  index.json updated ({len(idx['environments'][0]['projects'])} projects total)")

    # Loom skeleton
    if args["with_loom"]:
        loom_file = create_loom_skeleton(proj_dir, args["name"], args["type"])
        print(f"{GREEN}✓{NC} .loom/ skeleton created at {loom_file}")
        # Git init if not already a repo
        git_dir = proj_dir / ".git"
        if not git_dir.exists():
            try:
                subprocess.run(["git", "-C", str(proj_dir), "init"], check=True, capture_output=True)
                subprocess.run(["git", "-C", str(proj_dir), "add", "-A"], check=True, capture_output=True)
                subprocess.run(["git", "-C", str(proj_dir), "commit", "-m", f"⌘ Sandbox init · {args['name']}"], check=True, capture_output=True)
                print(f"{GREEN}✓{NC} Git repo initialized")
            except subprocess.CalledProcessError as e:
                print(f"{YELLOW}⚠{NC} Git init failed: {e.stderr.decode() if e.stderr else e}")

    print(f"\nNext: sync.sh {args['path']} --all")


if __name__ == "__main__":
    main()
