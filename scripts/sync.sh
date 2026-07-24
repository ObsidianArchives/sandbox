#!/usr/bin/env bash
# ⌘ Sandbox Sync v1.0.0 — rsync pipeline: Internal → Sandbox → Live
# Usage: ./sync.sh <project> [--zone1-to-2|--zone2-to-3|--push|--all]
# Default: --all (sync through all zones, commit, but don't push)

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SAND_ROOT="${SAND_ROOT:-$HOME/Sandbox}"
LIVE_ROOT="${LIVE_ROOT:-$HOME/git_live}"

# ── Exclude patterns for Zone 1 → Zone 2 ──
RSYNC_EXCLUDES=(
    --exclude '.git'
    --exclude '.loom'
    --exclude '.icp'
    --exclude 'node_modules'
    --exclude 'drafts'
    --exclude '.archive'
    --exclude 'references'
    --exclude '__pycache__'
    --exclude '*.pyc'
    --exclude '.env'
    --exclude '.env.*'
    --exclude '.DS_Store'
)

usage() {
    cat <<EOF
⌘ Sandbox Sync — Three-zone rsync pipeline

Usage: ./sync.sh <project> [FLAGS]

Projects are matched by Zone 1 directory name (without path).
Example: ./sync.sh sandbox-internal --all

FLAGS:
  --zone1-to-2    Internal → Sandbox only (sync + commit)
  --zone2-to-3    Sandbox → Live only (sync + commit)
  --push          Push Zone 3 to GitHub (after sync)
  --all           Full pipeline: Zone1→2→3, commit each, push (default)
  --tag           Auto-tag after sync (reads version from index.json)
  --tag-version X  Use specific version string for the tag
  --sanitize       Run project's sanitize.sh hook after rsync
  --remote URL     Set git remote origin for Zone 3 (first-time setup)
  --first-release  Use orphan branch for clean git history (per §6b)
  --dry-run       Show what would happen without doing it
  --no-commit     Skip git commit after rsync

EOF
    exit 0
}

log()  { echo -e "${CYAN}[sync]${NC} $1"; }
ok()   { echo -e "${GREEN}[  ok]${NC} $1"; }
warn() { echo -e "${YELLOW}[warn]${NC} $1"; }
err()  { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

# ── Parse args ──
PROJECT=""
MODE="all"
DRY_RUN=false
NO_COMMIT=false
TAG_MODE=false
TAG_VERSION=""
SANITIZE_MODE=false
REMOTE_URL=""
FIRST_RELEASE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) usage ;;
        --zone1-to-2) MODE="zone1-to-2"; shift ;;
        --zone2-to-3) MODE="zone2-to-3"; shift ;;
        --push) MODE="push"; shift ;;
        --all) MODE="all"; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        --no-commit) NO_COMMIT=true; shift ;;
        --tag) TAG_MODE=true; shift ;;
        --tag-version) TAG_VERSION="$2"; shift 2 ;;
        --sanitize) SANITIZE_MODE=true; shift ;;
        --remote) REMOTE_URL="$2"; shift 2 ;;
        --first-release) FIRST_RELEASE=true; shift ;;
        *) PROJECT="$1"; shift ;;
    esac
done

if [[ -z "$PROJECT" ]]; then
    err "No project specified. Usage: ./sync.sh <project> [--all]"
fi

# ── Resolve zone paths ──
# Strip -internal suffix if present, then derive Zone 2 name
ZONE1_DIR="$SAND_ROOT/Internal_SandBox/$PROJECT"

if [[ ! -d "$ZONE1_DIR" ]]; then
    err "Zone 1 not found: $ZONE1_DIR"
fi

# Derive Zone 2 name: strip -internal suffix
ZONE2_NAME="${PROJECT%-internal}"
ZONE2_DIR="$SAND_ROOT/git_sandbox/$ZONE2_NAME"

# Zone 3 name matches Zone 2
ZONE3_DIR="$LIVE_ROOT/$ZONE2_NAME"

log "Project: $PROJECT"
log "Zone 1:  $ZONE1_DIR"
log "Zone 2:  $ZONE2_DIR"
log "Zone 3:  $ZONE3_DIR"
echo ""

# ── Helper: check git dirty ──
check_git_clean() {
    local dir="$1"
    local label="$2"
    if [[ -d "$dir/.git" ]]; then
        if ! git -C "$dir" diff-index --quiet HEAD -- 2>/dev/null; then
            warn "$label has uncommitted changes"
            git -C "$dir" status --short
            return 1
        fi
    fi
    return 0
}

# ── Helper: apply git tag ──
apply_tag() {
    local dst="$1"
    local label="$2"
    if ! $TAG_MODE; then return 0; fi
    local version="${TAG_VERSION}"
    if [[ -z "$version" ]]; then
        # Try to read version from index.json for this project
        version=$(python3 -c "
import json, sys
try:
    idx = json.load(open('$SAND_ROOT/index.json'))
    for env in idx.get('environments', []):
        for p in env.get('projects', []):
            if p.get('name') in ('$ZONE2_NAME', '$PROJECT'):
                print(p.get('version', ''))
                sys.exit(0)
    print('')
except: pass
" 2>/dev/null || echo "")
    fi
    if [[ -z "$version" || "$version" == "v0-dev" ]]; then
        warn "Cannot auto-tag: no version found. Use --tag-version X"
        return 1
    fi
    local tag="v${version#v}"
    if $DRY_RUN; then
        echo "  [dry-run] git -C $dst tag $tag -m 'sync: $ZONE2_NAME $tag'"
    else
        git -C "$dst" tag "$tag" -m "sync: $ZONE2_NAME $tag" 2>/dev/null || true
        ok "Tagged: $label — $tag"
    fi
}

# ── Helper: rsync + commit ──
sync_and_commit() {
    local src="$1"
    local dst="$2"
    local label="$3"
    local extra_excludes=("${@:4}")

    if [[ ! -d "$src" ]]; then
        err "Source not found: $src"
    fi

    # Create destination if needed
    if [[ ! -d "$dst" ]]; then
        log "Creating $dst"
        $DRY_RUN || mkdir -p "$dst"
    fi
    if [[ ! -d "$dst/.git" ]]; then
        log "Initializing git in $dst"
        $DRY_RUN || git -C "$dst" init --quiet
        # First release: use orphan branch for clean history (§6b)
        if $FIRST_RELEASE && [[ "$label" == "Zone 3" ]]; then
            log "First release: creating orphan branch (clean history per §6b)"
            $DRY_RUN || git -C "$dst" checkout --orphan main
        fi
    fi

    # Set remote if provided (first-time Zone 3 setup)
    if [[ -n "$REMOTE_URL" ]] && [[ "$label" == "Zone 3" ]]; then
        local existing_remote
        existing_remote=$(git -C "$dst" remote get-url origin 2>/dev/null || echo "")
        if [[ -z "$existing_remote" ]]; then
            log "Setting remote origin: $REMOTE_URL"
            $DRY_RUN || git -C "$dst" remote add origin "$REMOTE_URL"
        else
            log "Remote already set: $existing_remote"
        fi
    fi

    # Check destination cleanliness
    if ! $DRY_RUN && ! $NO_COMMIT; then
        check_git_clean "$dst" "$label" || warn "Continuing despite dirty state in $label"
    fi

    # Rsync
    local rsync_cmd="rsync -av --delete ${RSYNC_EXCLUDES[*]} ${extra_excludes[*]} \"$src/\" \"$dst/\""
    log "Syncing: $src/ → $dst/"
    if $DRY_RUN; then
        echo "  [dry-run] $rsync_cmd"
    else
        eval "$rsync_cmd"
        ok "rsync complete: $label"
    fi

    # Sanitize hook
    if $SANITIZE_MODE; then
        local sanitize_script="$src/sanitize.sh"
        if [[ -x "$sanitize_script" ]]; then
            log "Running sanitize hook: $sanitize_script → $dst"
            if $DRY_RUN; then
                echo "  [dry-run] $sanitize_script $dst"
            else
                "$sanitize_script" "$dst" && ok "Sanitized: $label" || warn "Sanitize hook failed for $label"
            fi
        else
            log "No sanitize.sh found in $src — skipping"
        fi
    fi

    # Git commit
    if ! $NO_COMMIT && [[ -d "$dst/.git" ]]; then
        local changed
        changed=$($DRY_RUN && echo "would change" || git -C "$dst" status --porcelain)
        if [[ -n "$changed" ]]; then
            local ts
            ts=$(date -u +"%Y-%m-%d %H:%M")
            local msg="sync: $ZONE2_NAME — $ts"
            if $DRY_RUN; then
                echo "  [dry-run] git -C $dst add -A && git commit -m \"$msg\""
            else
                git -C "$dst" add -A
                git -C "$dst" commit -m "$msg"
                ok "Committed: $label — $msg"
                apply_tag "$dst" "$label"
            fi
        else
            log "No changes in $label — skipping commit"
        fi
    fi
    echo ""
}

# ── Execute ──
case "$MODE" in
    zone1-to-2)
        log "=== PHASE 1: Internal → Sandbox ==="
        sync_and_commit "$ZONE1_DIR" "$ZONE2_DIR" "Zone 2"
        ;;
    zone2-to-3)
        log "=== PHASE 2: Sandbox → Live ==="
        if [[ ! -d "$ZONE2_DIR" ]]; then
            err "Zone 2 not found: $ZONE2_DIR. Run --zone1-to-2 first."
        fi
        sync_and_commit "$ZONE2_DIR" "$ZONE3_DIR" "Zone 3" "--exclude" ".git"
        ;;
    push)
        log "=== PHASE 3: Live → GitHub ==="
        if [[ ! -d "$ZONE3_DIR/.git" ]]; then
            err "Zone 3 not found or not a git repo: $ZONE3_DIR"
        fi
        local remote
        remote=$(git -C "$ZONE3_DIR" remote get-url origin 2>/dev/null || echo "")
        if [[ -z "$remote" ]]; then
            err "No git remote 'origin' in Zone 3. Set it first: git -C $ZONE3_DIR remote add origin <url>"
        fi
        log "Pushing to: $remote"
        if $DRY_RUN; then
            echo "  [dry-run] git -C $ZONE3_DIR push origin main --tags"
        else
            git -C "$ZONE3_DIR" push origin main --tags
            ok "Pushed to GitHub"
        fi
        ;;
    all)
        log "=== FULL PIPELINE: Zone 1 → Zone 2 → Zone 3 → GitHub ==="
        echo ""

        # Phase 1
        log "=== PHASE 1: Internal → Sandbox ==="
        sync_and_commit "$ZONE1_DIR" "$ZONE2_DIR" "Zone 2"

        # Phase 2
        log "=== PHASE 2: Sandbox → Live ==="
        sync_and_commit "$ZONE2_DIR" "$ZONE3_DIR" "Zone 3" "--exclude" ".git"

        # Phase 3
        log "=== PHASE 3: Live → GitHub ==="
        if [[ -d "$ZONE3_DIR/.git" ]]; then
            remote=$(git -C "$ZONE3_DIR" remote get-url origin 2>/dev/null || echo "")
            if [[ -n "$remote" ]]; then
                log "Pushing to: $remote"
                if $DRY_RUN; then
                    echo "  [dry-run] git -C $ZONE3_DIR push origin main --tags"
                else
                    git -C "$ZONE3_DIR" push origin main --tags
                    ok "Pushed to GitHub"
                fi
            else
                warn "No git remote 'origin' in Zone 3. Sync complete but not pushed."
                warn "Set remote: git -C $ZONE3_DIR remote add origin <url>"
            fi
        else
            warn "Zone 3 not a git repo. Sync complete but not pushed."
        fi
        ;;
esac

echo ""
ok "Sandbox sync complete: $PROJECT"
