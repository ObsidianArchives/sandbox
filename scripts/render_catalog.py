#!/usr/bin/env python3
"""render_catalog.py — Render catalog.json → CATALOG.md

Reads ~/Sandbox/drops/catalog.json and writes a human-readable
CATALOG.md table in the same directory. Follows the pattern established
by LOOM's render.py → KANBAN.md.

Usage:
    python3 scripts/render_catalog.py
"""

import json
import os
from datetime import datetime, timezone

DROPS_DIR = os.path.expanduser("~/Sandbox/drops")
CATALOG_JSON = os.path.join(DROPS_DIR, "catalog.json")
CATALOG_MD = os.path.join(DROPS_DIR, "CATALOG.md")

HAZARD_BADGES = {
    "trivial":    "🟢 trivial",
    "low":        "🟡 low",
    "medium":     "🟠 medium",
    "high":       "🔴 high",
    "critical":   "⚫ critical",
    "unscanned":  "⬜ unscanned",
}

STATUS_MARKS = {
    "acquired":  "📥 acquired",
    "assessed":  "🔍 assessed",
    "curated":   "📤 curated",
    "shelved":   "📌 shelved",
    "released":  "✗ released",
    "vaulted":   "🏛 vaulted",
}


def load_catalog(path: str) -> dict | None:
    if not os.path.exists(path):
        print(f"ERROR: catalog.json not found at {path}")
        return None
    with open(path) as f:
        return json.load(f)


def render(catalog: dict) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    version = catalog.get("version", "?")
    curator = catalog.get("curator", "?")
    total = catalog.get("total_artifacts", len(catalog.get("artifacts", [])))

    # Count states
    states = {}
    for a in catalog.get("artifacts", []):
        s = a.get("catalog_status", {}).get("state", "unknown")
        states[s] = states.get(s, 0) + 1

    state_summary = " · ".join(
        f"{count} {STATUS_MARKS.get(state, state)}"
        for state, count in sorted(states.items())
    ) if states else "no artifacts"

    lines = []
    lines.append(f"# 🝪 drops/ · Inbound Artifact Catalog")
    lines.append("")
    lines.append(f"> **{catalog['catalog']}** · v{version} · curator: {curator}")
    lines.append(f"> {state_summary} · Rendered {ts}")
    lines.append("")

    # Cabinets
    cabinets = catalog.get("cabinets", {})
    if cabinets:
        lines.append("## Cabinets")
        lines.append("")
        for name, cab in cabinets.items():
            count = cab.get("count", 0)
            lines.append(f"- **{name}/** — {count} files")
        lines.append("")

    # Artifacts table
    artifacts = catalog.get("artifacts", [])
    if artifacts:
        lines.append("## Artifacts")
        lines.append("")
        lines.append("| ID | File | Kind | Hazard | Status | Target | Acquired |")
        lines.append("|----|------|------|--------|--------|--------|----------|")

        for a in artifacts:
            aid = a.get("id", "?")
            fname = a.get("filename", "?")
            kind = a.get("kind", "?")
            hazard_level = a.get("hazard", {}).get("level", "unscanned")
            hazard_badge = HAZARD_BADGES.get(hazard_level, hazard_level)
            status = a.get("catalog_status", {}).get("state", "?")
            status_mark = STATUS_MARKS.get(status, status)
            target = a.get("curation", {}).get("target_project_id") or a.get("curation", {}).get("status", "?")
            acquired = (a.get("catalog_status", {}).get("acquired") or "")[:10]

            lines.append(f"| {aid} | {fname} | {kind} | {hazard_badge} | {status_mark} | {target} | {acquired} |")

        lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"🝪 drops/ · catalog v{version} · {total} artifact(s)")

    return "\n".join(lines)


def main():
    catalog = load_catalog(CATALOG_JSON)
    if catalog is None:
        return 1

    md = render(catalog)
    with open(CATALOG_MD, "w") as f:
        f.write(md)
    print(f"RENDERED: {CATALOG_MD}")
    return 0


if __name__ == "__main__":
    exit(main())
