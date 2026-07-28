#!/usr/bin/env bash
# ⌘ Sandbox Upgrade — version-aware incremental migrations
# Usage: ./upgrade.sh [--dry-run]
# Reads index.json → protocol_version, applies only missing migrations.
# Idempotent. Safe to run on already-upgraded instances.
set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SAND_ROOT="${SAND_ROOT:-$HOME/Sandbox}"
INDEX="$SAND_ROOT/index.json"
CURRENT_VERSION="1.2.0"

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

echo -e "${CYAN}⌘ Sandbox Upgrade${NC}"
echo "  Target: $SAND_ROOT"
echo "  Current protocol: $CURRENT_VERSION"
$DRY_RUN && echo -e "  ${YELLOW}DRY RUN — no changes will be made${NC}"
echo ""

# ── Validate sandbox exists ──
if [[ ! -f "$INDEX" ]]; then
    echo "ERROR: index.json not found at $INDEX"
    echo "Is SAND_ROOT set correctly? Default: ~/Sandbox"
    exit 1
fi

# ── Paths ──
PROTO_DIR="$(dirname "$SCRIPT_DIR")"

# ── Read current version ──
INSTALLED_VERSION=$(python3 -c "
import json, sys
try:
    idx = json.load(open('$INDEX'))
    print(idx.get('protocol_version', '1.0.0'))
except:
    print('unknown')
" 2>/dev/null)

echo "  Installed: $INSTALLED_VERSION"
echo ""

if [[ "$INSTALLED_VERSION" == "$CURRENT_VERSION" ]]; then
    echo -e "  ${GREEN}✓ Mechanical: already at $CURRENT_VERSION. Skipping migrations.${NC}"
    SKIP_MECHANICAL=true
else
    SKIP_MECHANICAL=false
fi

echo ""

# ── Version comparison ──
version_lt() {
    # Returns 0 (true) if $1 < $2
    python3 -c "
import sys
a = tuple(map(int, '$1'.split('.')))
b = tuple(map(int, '$2'.split('.')))
sys.exit(0 if a < b else 1)
"
}

# ── Migration: 1.0.0 → 1.2.0 (or 1.1.0 → 1.2.0) ──
if ! $SKIP_MECHANICAL && version_lt "$INSTALLED_VERSION" "1.2.0"; then
    echo "━━━ Mechanical: $INSTALLED_VERSION → 1.2.0 ━━━"
    echo ""

    # Create drops/ directory
    if [[ ! -d "$SAND_ROOT/drops" ]]; then
        if $DRY_RUN; then
            echo "  [DRY RUN] Would create drops/{images,music,objects}"
        else
            mkdir -p "$SAND_ROOT/drops/images"
            mkdir -p "$SAND_ROOT/drops/music"
            mkdir -p "$SAND_ROOT/drops/objects"
            echo -e "  ${GREEN}✓${NC} drops/ directory created"
        fi
    else
        echo -e "  ${GREEN}✓${NC} drops/ already exists"
    fi

    # Write catalog.json if missing
    if [[ ! -f "$SAND_ROOT/drops/catalog.json" ]]; then
        if $DRY_RUN; then
            echo "  [DRY RUN] Would write drops/catalog.json"
        else
            NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
            cat > "$SAND_ROOT/drops/catalog.json" <<CATALOGEOF
{
  "catalog": "$(python3 -c "import json; print(json.load(open('$INDEX'))['sandbox'])")",
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
            echo -e "  ${GREEN}✓${NC} drops/catalog.json written"
        fi
    else
        echo -e "  ${GREEN}✓${NC} drops/catalog.json already exists"
    fi

    # Copy catalog.schema.json if available
    if [[ -f "$PROTO_DIR/catalog.schema.json" ]]; then
        if $DRY_RUN; then
            echo "  [DRY RUN] Would copy catalog.schema.json to drops/"
        else
            cp "$PROTO_DIR/catalog.schema.json" "$SAND_ROOT/drops/catalog.schema.json"
            echo -e "  ${GREEN}✓${NC} catalog.schema.json copied to drops/"
        fi
    fi

    # Bump protocol_version in index.json
    if $DRY_RUN; then
        echo "  [DRY RUN] Would bump protocol_version → 1.2.0"
    else
        python3 -c "
import json
idx = json.load(open('$INDEX'))
idx['protocol_version'] = '1.2.0'
from datetime import datetime, timezone
idx['updated'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
json.dump(idx, open('$INDEX', 'w'), indent=2)
"
        echo -e "  ${GREEN}✓${NC} protocol_version bumped → 1.2.0"
    fi

    echo ""
fi

# ── Future migrations go here ──
# if version_lt "$INSTALLED_VERSION" "1.3.0"; then ... fi

# ── Cognitive: always sync latest docs + schemas + scripts ──
echo "━━━ Cognitive: syncing latest docs, schemas, scripts ━━━"
echo ""

for doc in PROTOCOL.md README.md SKILL.md QUICKSTART.md index.schema.json; do
    if [[ -f "$PROTO_DIR/$doc" ]]; then
        if $DRY_RUN; then
            echo "  [DRY RUN] Would update $doc"
        else
            cp "$PROTO_DIR/$doc" "$SAND_ROOT/$doc"
            echo -e "  ${GREEN}✓${NC} $doc updated"
        fi
    fi
done
if [[ -f "$PROTO_DIR/catalog.schema.json" ]]; then
    if $DRY_RUN; then
        echo "  [DRY RUN] Would update drops/catalog.schema.json"
    else
        cp "$PROTO_DIR/catalog.schema.json" "$SAND_ROOT/drops/catalog.schema.json"
        echo -e "  ${GREEN}✓${NC} drops/catalog.schema.json updated"
    fi
fi
if [[ -d "$PROTO_DIR/scripts" ]]; then
    if $DRY_RUN; then
        echo "  [DRY RUN] Would copy scripts/"
    else
        cp -r "$PROTO_DIR/scripts" "$SAND_ROOT/scripts"
        echo -e "  ${GREEN}✓${NC} scripts/ copied"
    fi
fi

echo ""

# ── Validate ──
VALIDATE_PY="$SCRIPT_DIR/validate.py"
if [[ -f "$VALIDATE_PY" ]]; then
    if $DRY_RUN; then
        echo "  [DRY RUN] Would validate index.json"
    else
        if SAND_ROOT="$SAND_ROOT" python3 "$VALIDATE_PY" --quiet 2>/dev/null; then
            echo -e "${GREEN}✓${NC} Validation passed"
        else
            echo -e "  ${YELLOW}⚠ Validation failed — check index.json manually${NC}"
        fi
    fi
fi

echo ""
if $DRY_RUN; then
    echo -e "${YELLOW}Dry run complete. Run without --dry-run to apply.${NC}"
else
    echo -e "${GREEN}⌘ Upgrade complete. Sandbox at $CURRENT_VERSION.${NC}"
fi
