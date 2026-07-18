#!/usr/bin/env python3
"""⌘ Sandbox Status v1.0.0 — zone health dashboard."""
"""⌘ Sandbox Status — zone health dashboard

Reads index.json, checks filesystem and git state, reports per-project health.
Usage: status.py [--project <name>] [--json] [--no-color] [--verbose]
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SAND_ROOT = Path(os.environ.get("SAND_ROOT", os.path.expanduser("~/Sandbox_v2")))
LIVE_ROOT = Path(os.environ.get("LIVE_ROOT", os.path.expanduser("~/git_live")))
INDEX_PATH = SAND_ROOT / "index.json"

GREEN = "\033[0;32m"; YELLOW = "\033[1;33m"; RED = "\033[0;31m"
CYAN = "\033[0;36m"; WHITE = "\033[1;37m"; GREY = "\033[2;37m"; BOLD = "\033[1m"; NC = "\033[0m"
CHECK = "✅"; CROSS = "❌"; DASH = "—"


def parse_args():
    args = {"project": None, "json_out": False, "no_color": False, "verbose": False}
    argv = sys.argv[1:]; i = 0
    while i < len(argv):
        if argv[i] == "--project" and i+1 < len(argv): args["project"] = argv[i+1]; i += 2
        elif argv[i] == "--json": args["json_out"] = True; i += 1
        elif argv[i] == "--no-color": args["no_color"] = True; i += 1
        elif argv[i] == "--verbose": args["verbose"] = True; i += 1
        elif argv[i] in ("--help","-h"): print(__doc__); sys.exit(0)
        else: i += 1
    return args

def c(color, text, args): return text if args["no_color"] else f"{color}{text}{NC}"

def git_latest(repo):
    try:
        out = subprocess.check_output(["git","-C",str(repo),"log","-1","--format=%aI %h"], stderr=subprocess.DEVNULL, text=True).strip()
        if out: ts, h = out.split(" ",1); return ts, h
    except: pass
    return None, None

def git_tags(repo):
    try:
        out = subprocess.check_output(["git","-C",str(repo),"tag","--sort=-creatordate"], stderr=subprocess.DEVNULL, text=True).strip()
        return [t for t in out.split("\n") if t] if out else []
    except: return []

def git_remote(repo):
    try: return subprocess.check_output(["git","-C",str(repo),"remote","get-url","origin"], stderr=subprocess.DEVNULL, text=True).strip()
    except: return ""

def drift_days(ts1, ts2):
    if not ts1 or not ts2: return None
    try:
        d = (datetime.fromisoformat(ts1) - datetime.fromisoformat(ts2)).days
        return max(d, 0)  # never negative — Z1 is always source of truth
    except: return None

def load_index():
    if not INDEX_PATH.exists():
        print(f"index.json not found at {INDEX_PATH}", file=sys.stderr); sys.exit(2)
    with open(INDEX_PATH) as f: return json.load(f)

def find_z2_path(idx, z1_name):
    """Find matching Zone 2 project by name similarity."""
    for env in idx.get("environments", []):
        if env.get("name") == "git_sandbox":
            for p in env.get("projects", []):
                pname = p.get("name","")
                base = z1_name.replace("-internal","").replace("_internal","")
                pbase = pname.replace("_git","").replace("-git","")
                if base == pbase or pname == z1_name or pbase == z1_name:
                    return SAND_ROOT / p.get("path","")
    # Fallback: derive from name
    base = z1_name
    if base.endswith("-internal"): base = base[:-9]
    elif base.endswith("_internal"): base = base[:-9]
    return SAND_ROOT / "git_sandbox" / base


def check_project(idx, proj, args):
    name = proj.get("name","unnamed")
    status = proj.get("status","active")
    z1_path = SAND_ROOT / proj.get("path","") if proj.get("path") else None
    z2_path = find_z2_path(idx, name)
    base = name.replace("-internal","").replace("_internal","").replace("_git","")
    z3_path = LIVE_ROOT / base

    z1_ok = z1_path and z1_path.is_dir()
    z2_ok = z2_path.is_dir() if z2_path else False
    z3_ok = z3_path.is_dir()

    z1_ts, z1_h = git_latest(z1_path) if z1_ok else (None, None)
    z2_ts, z2_h = git_latest(z2_path) if z2_ok else (None, None)
    z3_ts, z3_h = git_latest(z3_path) if z3_ok else (None, None)

    drift = drift_days(z2_ts, z1_ts) if (z1_ts and z2_ts) else None

    z2_tags = git_tags(z2_path) if z2_ok else []
    z3_tags = git_tags(z3_path) if z3_ok else []
    latest_tag = z2_tags[0] if z2_tags else (z3_tags[0] if z3_tags else DASH)
    tags_match = (z2_tags[:1] == z3_tags[:1]) if (z2_tags or z3_tags) else True
    tags_label = "MISMATCH" if (z2_tags and z3_tags and not tags_match) else latest_tag

    remote = git_remote(z3_path) if z3_ok else ""
    remote_short = "github" if "github" in remote else ("none" if z3_ok and not remote else DASH)

    if status in ("deferred","archived"): health = "dormant"
    elif not z1_ok: health = "missing"
    elif not z2_ok and not z3_ok: health = "missing"
    elif drift is not None and drift > 0: health = "behind"
    elif z3_ok and not remote: health = "no-remote"
    elif not (z2_ts or z3_ts): health = "no-git"
    else: health = "synced"

    return {
        "name": name, "z1": z1_ok, "z2": z2_ok, "z3": z3_ok,
        "drift_str": f"{drift}d" if drift is not None else DASH,
        "tags_label": tags_label, "remote": remote_short, "health": health,
        "v": {"z1_h":z1_h or DASH,"z1_ts":z1_ts or DASH,"z2_h":z2_h or DASH,"z2_ts":z2_ts or DASH,"z3_h":z3_h or DASH,"z3_ts":z3_ts or DASH} if args["verbose"] else None
    }


def print_table(results, args):
    # strip ANSI for width calc
    hdr = f"{'PROJECT':<24} {'Z1':<4} {'Z2':<4} {'Z3':<4} {'DRIFT':<7} {'TAGS':<12} {'REMOTE':<10}"
    sep = "─" * 72
    sandbox = "Sandbox_v2"
    try:
        with open(INDEX_PATH) as f: sandbox = json.load(f).get("sandbox", sandbox)
    except: pass

    print(f"\n{c(CYAN,'🝪 SANDBOX HEALTH',args)} · {sandbox} · {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    print(sep); print(hdr); print(sep)

    for r in results:
        z1_s = CHECK if r["z1"] else CROSS
        z2_s = CHECK if r["z2"] else CROSS
        z3_s = CHECK if r["z3"] else CROSS
        d = r["drift_str"]; t = r["tags_label"]; rem = r["remote"]
        if r["health"] == "dormant": d = c(GREY,d,args); t = c(GREY,t,args)
        print(f"{r['name']:<24} {z1_s:<4} {z2_s:<4} {z3_s:<4} {d:<7} {t:<12} {rem:<10}")

    print(sep)
    cnt = {}; [cnt.update({r['health']: cnt.get(r['health'],0)+1}) for r in results]
    labels = {"synced": c(GREEN,"synced",args), "behind": c(YELLOW,"behind",args),
              "missing": c(RED,"missing",args), "no-remote": c(WHITE,"no-remote",args),
              "dormant": c(GREY,"dormant",args), "no-git": c(GREY,"no-git",args)}
    parts = [f"{cnt[k]} {labels[k]}" for k in ["synced","behind","missing","no-remote","dormant","no-git"] if cnt.get(k)]
    print(f"SUMMARY: {' · '.join(parts)}\n")

    if args["verbose"]:
        for r in results:
            if not r.get("v"): continue
            v = r["v"]
            print(f"{c(BOLD,r['name'],args)}:")
            print(f"  Z1: {v['z1_h']} @ {v['z1_ts']}")
            print(f"  Z2: {v['z2_h']} @ {v['z2_ts']}")
            print(f"  Z3: {v['z3_h']} @ {v['z3_ts']}\n")


def print_json(results):
    out = {"sandbox":"Sandbox_v2","checked_at":datetime.now(timezone.utc).isoformat(),"projects":[],"summary":{}}
    for r in results:
        out["projects"].append({"name":r["name"],"zones":{"z1":r["z1"],"z2":r["z2"],"z3":r["z3"]},"drift_days":r.get("drift"),"tags":r["tags_label"],"remote":r["remote"],"health":r["health"]})
    cnt = {}; [cnt.update({r['health']:cnt.get(r['health'],0)+1}) for r in results]
    out["summary"] = cnt
    print(json.dumps(out, indent=2))


def main():
    args = parse_args()
    idx = load_index()
    projects = []
    for env in idx.get("environments",[]):
        for p in env.get("projects",[]):
            p["_env"] = env.get("name","")
            projects.append(p)

    if args["project"]:
        projects = [p for p in projects if p.get("name") == args["project"]]
        if not projects:
            print(f"Project '{args['project']}' not found", file=sys.stderr); sys.exit(2)

    results = [check_project(idx, p, args) for p in projects]

    if args["json_out"]: print_json(results)
    else: print_table(results, args)

    has_err = any(r["health"]=="missing" for r in results)
    has_warn = any(r["health"] in ("behind","no-remote","no-git") for r in results)
    sys.exit(2 if has_err else 1 if has_warn else 0)

if __name__ == "__main__": main()
