#!/usr/bin/env python3
"""⌘ Sandbox Migrate — convert index.json from v1 (nested) to v2 (flat)

Usage: migrate-v2.py [--dry-run] [--force]

Reads index.json, matches Internal + Sandbox projects by name similarity,
merges them into flat v2 entries. Backs up original as index.json.v1.bak.
"""

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SAND_ROOT = Path(os.environ.get("SAND_ROOT", os.path.expanduser("~/Sandbox")))
INDEX_PATH = SAND_ROOT / "index.json"
BACKUP_PATH = SAND_ROOT / "index.json.v1.bak"
LIVE_ROOT = Path(os.environ.get("LIVE_ROOT", os.path.expanduser("~/git_live")))

GREEN = "\033[0;32m"; YELLOW = "\033[1;33m"; RED = "\033[0;31m"; CYAN = "\033[0;36m"; NC = "\033[0m"


def strip_suffix(name: str) -> str:
    """Strip known suffixes to get base project name."""
    for s in ("-internal", "_internal", "_git", "-git"):
        if name.endswith(s):
            return name[:-len(s)]
    return name


def detect_live_zone(proj_name: str) -> dict | None:
    """Check if a live zone exists for this project."""
    base = strip_suffix(proj_name)
    for candidate in (base, base.replace("-", "_"), base.replace("_", "-")):
        live_path = LIVE_ROOT / candidate
        if live_path.is_dir():
            import subprocess
            remote = ""
            try:
                remote = subprocess.check_output(
                    ["git", "-C", str(live_path), "remote", "get-url", "origin"],
                    stderr=subprocess.DEVNULL, text=True
                ).strip()
            except:
                pass
            return {"path": str(live_path), "remote": remote if remote else None}
    return None


def migrate(dry_run=False, force=False):
    if not INDEX_PATH.exists():
        print(f"{RED}✗{NC} index.json not found at {INDEX_PATH}")
        sys.exit(1)

    with open(INDEX_PATH) as f:
        v1 = json.load(f)

    # Check if already v2
    if "projects" in v1 and not v1.get("environments"):
        print(f"{YELLOW}⚠{NC} Already v2 format. Nothing to migrate.")
        if force:
            print("  --force: re-running anyway")
        else:
            sys.exit(0)

    print(f"{CYAN}⌘ Sandbox Migrate · v1 → v2{NC}")
    print(f"  Manifest: {INDEX_PATH}")
    print()

    # ── Extract all projects ──
    internal_projects = {}
    sandbox_projects = {}

    for env in v1.get("environments", []):
        env_name = env.get("name", "")
        for p in env.get("projects", []):
            if "Internal" in env_name:
                internal_projects[p["name"]] = p
            elif "git_sandbox" in env_name or "sandbox" in env_name.lower():
                sandbox_projects[p["name"]] = p

    # ── Match and merge ──
    v2_projects = []
    matched_sandbox = set()
    matched_internal = set()

    for int_name, int_proj in internal_projects.items():
        base = strip_suffix(int_name)

        # Find matching sandbox project
        sandbox_match = None
        for sand_name, sand_proj in sandbox_projects.items():
            if sand_name in matched_sandbox:
                continue
            sand_base = strip_suffix(sand_name)
            if sand_base == base or sand_name == int_name.replace("-internal", "_git"):
                sandbox_match = sand_proj
                matched_sandbox.add(sand_name)
                break

        matched_internal.add(int_name)

        # Build v2 entry
        entry = {
            "id": base.lower().replace("_", "-").replace(" ", "-"),
            "name": base,
            "type": int_proj.get("type", "tool"),
            "zones": {
                "internal": {
                    "path": int_proj.get("path", ""),
                    "version": int_proj.get("version", "v0-dev"),
                    "git_commit": int_proj.get("git_commit"),
                    "files": int_proj.get("files", 0),
                    "size_bytes": int_proj.get("size_bytes", 0),
                },
                "sandbox": None,
                "live": None,
            },
            "status": int_proj.get("status", "active"),
            "health": int_proj.get("health", "early"),
            "tags": int_proj.get("domains", int_proj.get("tags", [])),
            "description": int_proj.get("notes", int_proj.get("description", "")),
            "loom_id": int_proj.get("loom_id"),
        }

        # Sandbox zone
        if sandbox_match:
            entry["zones"]["sandbox"] = {
                "path": sandbox_match.get("path", ""),
                "version": sandbox_match.get("version", "v0-dev"),
                "git_commit": sandbox_match.get("git_commit"),
                "git_tag": sandbox_match.get("git_tag"),
                "files": sandbox_match.get("files", 0),
            }

        # Live zone
        live = detect_live_zone(int_name)
        if live:
            entry["zones"]["live"] = live

        # Health
        if not sandbox_match and not live:
            entry["health"] = "missing-zones"
        elif sandbox_match and not live:
            entry["health"] = "no-live"
        elif live and not live.get("remote"):
            entry["health"] = "no-remote"
        else:
            entry["health"] = "healthy"

        v2_projects.append(entry)

    # ── Unmatched sandbox projects (orphans) ──
    for sand_name, sand_proj in sandbox_projects.items():
        if sand_name not in matched_sandbox:
            base = strip_suffix(sand_name)
            v2_projects.append({
                "id": base.lower().replace("_", "-"),
                "name": base,
                "type": sand_proj.get("type", "tool"),
                "zones": {
                    "internal": None,
                    "sandbox": {
                        "path": sand_proj.get("path", ""),
                        "version": sand_proj.get("version", "v0-dev"),
                        "git_commit": sand_proj.get("git_commit"),
                    },
                    "live": None,
                },
                "status": sand_proj.get("status", "active"),
                "health": "sandbox-only",
                "tags": sand_proj.get("domains", []),
                "description": sand_proj.get("notes", ""),
            })

    # ── Build v2 manifest ──
    v2 = {
        "sandbox": v1.get("sandbox", "Sandbox"),
        "sigil": v1.get("sigil", "⌘"),
        "version": "v2",
        "created": v1.get("created", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "projects": v2_projects,
        "tools": v1.get("tools", []),
        "content_repos": v1.get("content_repos", []),
        "stats": {
            "total_projects": len(v2_projects),
            "total_tools": len(v1.get("tools", [])),
            "total_content_repos": len(v1.get("content_repos", [])),
        },
        "changelog": v1.get("changelog", []) + [{
            "version": "v2",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "what": f"Migrated from v1 nested to v2 flat schema. {len(v2_projects)} projects merged."
        }],
    }

    # ── Output ──
    print(f"  Internal projects:  {len(internal_projects)}")
    print(f"  Sandbox projects:   {len(sandbox_projects)}")
    print(f"  Merged entries:     {len(v2_projects)}")
    print(f"  Orphans (sandbox-only): {len(sandbox_projects) - len(matched_sandbox)}")
    print()

    if dry_run:
        print(f"{YELLOW}[dry-run]{NC} Would write v2 manifest:")
        print(json.dumps(v2, indent=2))
        sys.exit(0)

    # Backup
    shutil.copy2(INDEX_PATH, BACKUP_PATH)
    print(f"{GREEN}✓{NC} Backup: {BACKUP_PATH}")

    # Write v2
    with open(INDEX_PATH, "w") as f:
        json.dump(v2, f, indent=2)
    print(f"{GREEN}✓{NC} Migrated: {INDEX_PATH} → v2 flat schema")
    print(f"  {len(v2_projects)} projects, {len(v1.get('tools',[]))} tools, {len(v1.get('content_repos',[]))} content repos")
    print()
    print("Next: validate.py to verify, status.py to check health.")


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)
    dry = "--dry-run" in sys.argv
    force = "--force" in sys.argv
    migrate(dry_run=dry, force=force)
