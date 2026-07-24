#!/usr/bin/env python3
"""⌘ Sandbox Validate v1.1.0 — validate index.json against index.schema.json

Usage:
    python3 validate.py [--check-paths] [--check-tags] [--check-zones] [--verbose]

Options:
    --check-paths   Also verify that registered projects exist on disk
    --check-tags    Verify git tag consistency across Zone 2 and Zone 3
    --check-zones   Verify Zone 2 and Zone 3 directories exist
    --verbose       Show all validation details
    --quiet         Only output on errors (exit code 1 if invalid)
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# ── Paths ──
SAND_ROOT = Path(os.environ.get("SAND_ROOT", os.path.expanduser("~/Sandbox")))
INDEX_PATH = SAND_ROOT / "index.json"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "index.schema.json"

# ── ANSI ──
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
NC = "\033[0m"


def load_json(path: Path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        return {"_error": str(e)}


def validate_schema(data: dict, schema: dict) -> list[str]:
    """Minimal JSON Schema draft-07 validator for our subset."""
    errors = []

    if not isinstance(data, dict):
        errors.append("Root must be an object")
        return errors

    # Required top-level
    for field in schema.get("required", []):
        if field not in data:
            errors.append(f"Missing required field: {field}")

    props = schema.get("properties", {})
    for key, spec in props.items():
        if key not in data:
            continue
        value = data[key]

        # Type check
        expected = spec.get("type")
        if expected == "array" and not isinstance(value, list):
            errors.append(f"'{key}': expected array, got {type(value).__name__}")
            continue
        elif expected == "string" and not isinstance(value, str):
            errors.append(f"'{key}': expected string, got {type(value).__name__}")
            continue
        elif expected == "object" and not isinstance(value, dict):
            errors.append(f"'{key}': expected object, got {type(value).__name__}")
            continue
        elif expected == "number" and not isinstance(value, (int, float)):
            errors.append(f"'{key}': expected number, got {type(value).__name__}")
            continue

        # Arrays: validate items
        if expected == "array" and "items" in spec:
            item_schema = spec["items"]
            for i, item in enumerate(value):
                if not isinstance(item, dict):
                    errors.append(f"'{key}[{i}]': expected object, got {type(item).__name__}")
                    continue
                # Check required fields
                for req in item_schema.get("required", []):
                    if req not in item:
                        errors.append(f"'{key}[{i}].{req}': missing required field")
                # Check enum constraints
                for fname, fspec in item_schema.get("properties", {}).items():
                    if fname not in item:
                        continue
                    if "enum" in fspec and item[fname] not in fspec["enum"]:
                        errors.append(
                            f"'{key}[{i}].{fname}': '{item[fname]}' not in {fspec['enum']}"
                        )

    return errors


def check_paths(data: dict) -> list[str]:
    """Verify registered projects and content repos exist on disk."""
    warnings = []

    # Check projects (v1 nested format)
    for env in data.get("environments", []):
        env_name = env.get("name", "unknown")
        for proj in env.get("projects", []):
            name = proj.get("name", "unnamed")
            path_str = proj.get("path", "")
            full_path = SAND_ROOT / path_str
            if not full_path.exists():
                warnings.append(f"Project '{name}' in {env_name}: path not found: {path_str}")

    # Check tools
    for tool in data.get("tools", []):
        name = tool.get("name", "unnamed")
        path_str = tool.get("path", "")
        full_path = SAND_ROOT / path_str
        if not full_path.exists():
            warnings.append(f"Tool '{name}': file not found: {path_str}")

    # Check content repos
    for repo in data.get("content_repos", []):
        name = repo.get("name", "unnamed")
        path_str = repo.get("internal_path", "")
        full_path = SAND_ROOT / path_str
        if not full_path.exists():
            warnings.append(f"Content repo '{name}': path not found: {path_str}")

    return warnings


def check_tags(data: dict) -> list[str]:
    """Verify git tag consistency across zones."""
    warnings = []
    LIVE_ROOT = Path(os.environ.get("LIVE_ROOT", os.path.expanduser("~/git_live")))

    for env in data.get("environments", []):
        for proj in env.get("projects", []):
            name = proj.get("name", "unnamed")
            base = name
            for suffix in ("-internal", "_internal", "_git"):
                if base.endswith(suffix):
                    base = base[:-len(suffix)]
                    break

            z2_path = SAND_ROOT / "git_sandbox" / base
            z3_path = LIVE_ROOT / base

            z2_tags = _git_tags(z2_path)
            z3_tags = _git_tags(z3_path)

            if (z2_path / ".git").is_dir() and (z3_path / ".git").is_dir():
                if not z2_tags and not z3_tags:
                    warnings.append(f"Tags: '{name}' — no tags in Zone 2 or Zone 3")
                elif z2_tags and not z3_tags:
                    warnings.append(f"Tags: '{name}' — Zone 3 untagged (Zone 2: {z2_tags[0]})")
                elif not z2_tags and z3_tags:
                    warnings.append(f"Tags: '{name}' — Zone 2 untagged (Zone 3: {z3_tags[0]})")
                elif z2_tags[0] != z3_tags[0]:
                    warnings.append(f"Tags: '{name}' — mismatch: Z2={z2_tags[0]} Z3={z3_tags[0]}")

    return warnings


def _git_tags(repo: Path) -> list[str]:
    """Return sorted list of git tags, newest first."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo), "tag", "--sort=-creatordate"],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        return [t for t in out.split("\n") if t] if out else []
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def check_zones(data: dict) -> list[str]:
    """Verify Zone 2 and Zone 3 directories exist for each project."""
    warnings = []
    LIVE_ROOT = Path(os.environ.get("LIVE_ROOT", os.path.expanduser("~/git_live")))

    for env in data.get("environments", []):
        for proj in env.get("projects", []):
            name = proj.get("name", "unnamed")
            base = name
            for suffix in ("-internal", "_internal", "_git"):
                if base.endswith(suffix):
                    base = base[:-len(suffix)]
                    break

            z2_path = SAND_ROOT / "git_sandbox" / base
            z3_path = LIVE_ROOT / base

            if not z2_path.is_dir():
                warnings.append(f"Zones: '{name}' — Zone 2 missing: {z2_path}")
            if not z3_path.is_dir():
                warnings.append(f"Zones: '{name}' — Zone 3 missing: {z3_path}")

    return warnings


def main():
    check_paths_flag = "--check-paths" in sys.argv
    check_tags_flag = "--check-tags" in sys.argv
    check_zones_flag = "--check-zones" in sys.argv
    verbose = "--verbose" in sys.argv
    quiet = "--quiet" in sys.argv

    # Load
    data = load_json(INDEX_PATH)
    schema = load_json(SCHEMA_PATH)

    if data is None:
        print(f"{RED}✗{NC} index.json not found at {INDEX_PATH}")
        sys.exit(1)

    if "_error" in data:
        print(f"{RED}✗{NC} index.json is invalid JSON: {data['_error']}")
        sys.exit(1)

    if schema is None:
        print(f"{YELLOW}⚠{NC} index.schema.json not found at {SCHEMA_PATH} — skipping schema validation")
        errors = []
    elif "_error" in schema:
        print(f"{YELLOW}⚠{NC} index.schema.json is invalid JSON — skipping schema validation")
        errors = []
    else:
        errors = validate_schema(data, schema)

    warnings = check_paths(data) if check_paths_flag else []
    tag_warnings = check_tags(data) if check_tags_flag else []
    zone_warnings = check_zones(data) if check_zones_flag else []

    # Merge warnings for reporting
    all_warnings = warnings + tag_warnings + zone_warnings

    # Report
    if not quiet:
        print(f"\n{CYAN}⌘ Sandbox Validate{NC}")
        print(f"  Manifest: {INDEX_PATH}")
        print(f"  Schema:   {SCHEMA_PATH}")
        print()

    if errors:
        print(f"{RED}✗ Schema validation FAILED ({len(errors)} errors):{NC}")
        for e in errors:
            print(f"  {RED}→{NC} {e}")
        print()

    if all_warnings:
        print(f"{YELLOW}⚠ Warnings ({len(all_warnings)}):{NC}")
        for w in all_warnings:
            print(f"  {YELLOW}→{NC} {w}")
        print()

    if not errors and not all_warnings:
        if not quiet:
            version = data.get("version", "unknown")
            projects = sum(len(env.get("projects", [])) for env in data.get("environments", []))
            tools = len(data.get("tools", []))
            repos = len(data.get("content_repos", []))
            print(f"{GREEN}✓ Schema valid{NC}")
            print(f"  Version: {version}")
            print(f"  Projects: {projects}")
            print(f"  Tools: {tools}")
            print(f"  Content repos: {repos}")
            if check_paths_flag:
                print(f"  All paths exist on disk")
            if check_zones_flag:
                print(f"  All zones exist on disk")

    if errors:
        sys.exit(1)
    elif all_warnings and not errors:
        if not quiet:
            print(f"{YELLOW}Schema valid but warnings exist — check above.{NC}")
        sys.exit(0)
    else:
        if not quiet:
            print(f"\n{GREEN}✓ All checks passed.{NC}")
        sys.exit(0)


if __name__ == "__main__":
    main()
