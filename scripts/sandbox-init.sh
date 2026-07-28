#!/usr/bin/env bash
# ⌘ Sandbox Init — bootstrap a fresh sandbox from nothing
# Usage: ./sandbox-init.sh [--name <name>] [--path <path>]
set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

NAME="Sandbox"
PARENT="$HOME"

usage() {
    cat <<EOF
⌘ Sandbox Init — Create a new sandbox instance

Usage: ./sandbox-init.sh [--name <name>] [--path <path>]

  --name   Sandbox instance name (default: "Sandbox")
  --path   Parent directory (default: \$HOME)
           Sandbox is created at <path>/<name>/

EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) usage ;;
        --name) NAME="$2"; shift 2 ;;
        --path) PARENT="$2"; shift 2 ;;
        *) echo "Unknown: $1"; usage ;;
    esac
done

SAND_ROOT="$PARENT/$NAME"
SCHEMA_SRC="$(dirname "$0")/../index.schema.json"

echo -e "${CYAN}⌘ Sandbox Init${NC}"
echo "  Name: $NAME"
echo "  Path: $SAND_ROOT"
echo ""

# ── Create structure ──
mkdir -p "$SAND_ROOT/Internal_SandBox"
mkdir -p "$SAND_ROOT/git_sandbox"
mkdir -p "$SAND_ROOT/tools"
echo -e "${GREEN}✓${NC} Directory structure created"

# ── Timestamps ──
TODAY=$(date -u +"%Y-%m-%d")
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── Create drops/ (inbound artifact staging) ──
mkdir -p "$SAND_ROOT/drops/images"
mkdir -p "$SAND_ROOT/drops/music"
mkdir -p "$SAND_ROOT/drops/objects"
cat > "$SAND_ROOT/drops/catalog.json" <<CATALOGEOF
{
  "catalog": "$NAME",
  "version": "1.0.0",
  "curator": "operator",
  "created": "$NOW",
  "updated": "$NOW",
  "total_artifacts": 0,
  "cabinets": {
    "images": { "path": "images/", "count": 0, "formats": {} },
    "music": { "path": "music/", "count": 0, "formats": {} }
  },
  "artifacts": []
}
CATALOGEOF
echo -e "${GREEN}✓${NC} drops/ created (images, music, objects, catalog.json)"

# ── Write index.json skeleton ──

cat > "$SAND_ROOT/index.json" <<JSONEOF
{
  "sandbox": "$NAME",
  "sigil": "⌘",
  "version": "v2",
  "protocol_version": "1.2.0",
  "created": "$TODAY",
  "updated": "$NOW",
  "tools": [],
  "content_repos": [],
  "environments": [
    {
      "name": "Internal_SandBox",
      "purpose": "Working copies · full data · daily dev",
      "projects": []
    },
    {
      "name": "git_sandbox",
      "purpose": "Clean deploy copies · tagged versions",
      "projects": []
    }
  ],
  "stats": {
    "total_projects": 0,
    "total_environments": 2,
    "total_size_bytes": 0,
    "served_by_projects": []
  },
  "changelog": [
    {
      "version": "v1",
      "date": "$TODAY",
      "what": "Sandbox initialized by sandbox-init.sh"
    }
  ]
}
JSONEOF
echo -e "${GREEN}✓${NC} index.json written (valid v2 skeleton)"

# ── Copy schema ──
if [[ -f "$SCHEMA_SRC" ]]; then
    cp "$SCHEMA_SRC" "$SAND_ROOT/index.schema.json"
    echo -e "${GREEN}✓${NC} index.schema.json copied from protocol"
else
    echo -e "  ⚠ index.schema.json not found at $SCHEMA_SRC — skipping"
fi

# ── Copy reference docs ──
PROTO_DIR="$(dirname "$(dirname "$0")")"
for doc in PROTOCOL.md README.md SKILL.md QUICKSTART.md; do
    if [[ -f "$PROTO_DIR/$doc" ]]; then
        cp "$PROTO_DIR/$doc" "$SAND_ROOT/$doc"
        echo -e "${GREEN}✓${NC} $doc copied"
    fi
done
if [[ -f "$PROTO_DIR/catalog.schema.json" ]]; then
    cp "$PROTO_DIR/catalog.schema.json" "$SAND_ROOT/drops/catalog.schema.json"
    echo -e "${GREEN}✓${NC} catalog.schema.json copied to drops/"
fi
if [[ -d "$PROTO_DIR/scripts" ]]; then
    cp -r "$PROTO_DIR/scripts" "$SAND_ROOT/scripts"
    echo -e "${GREEN}✓${NC} scripts/ copied"
fi

# ── Create Zone 3 (live) ──
LIVE_ROOT="${LIVE_ROOT:-$HOME/git_live}"
mkdir -p "$LIVE_ROOT"
echo -e "${GREEN}✓${NC} Zone 3 directory created at $LIVE_ROOT"

# ── Validate ──
VALIDATE_PY="$(dirname "$0")/validate.py"
if [[ -f "$VALIDATE_PY" ]]; then
    if SAND_ROOT="$SAND_ROOT" python3 "$VALIDATE_PY" --quiet 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Validation passed"
    else
        echo -e "  ⚠ Validation failed — check index.json manually"
    fi
fi

# ── Print next steps ──
echo ""
echo -e "${GREEN}⌘ Sandbox ready at $SAND_ROOT${NC}"
echo ""
echo "Next steps:"
echo "  1. sandbox-register.py --name <project> --type tool --path <dir>"
echo "  2. sync.sh <project> --all"
echo "  3. status.py"
echo "  4. Drop files into drops/ → python3 scripts/render_catalog.py"
