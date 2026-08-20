#!/usr/bin/env python3
"""Regenerate briefs/index.json from briefs/*.json.

Standard library only. No pip installs, no network.

Usage:
    python3 scripts/build_index.py             # rewrite briefs/index.json
    python3 scripts/build_index.py --check     # CI: fail if the index is stale
    python3 scripts/build_index.py --briefs-dir path/to/briefs

Exit codes:
    0  index written, or (with --check) index is up to date
    1  a brief failed validation, or (with --check) the index is stale
    2  bad invocation / unreadable input

Rules this enforces:
  * Every brief is validated (validate_brief.py, hard errors only) before it can
    be listed. If any brief is invalid the index is NOT written — a broken
    edition must never be advertised to the app.
  * Output is deterministic: sorted keys, 2-space indent, LF, trailing newline.
    `generated_at` is only refreshed when the edition list actually changed, so
    a no-op rebuild produces a zero-line diff.
  * `editions` is sorted newest-first, as SPEC.md requires.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validate_brief import LAYER_SLUGS, validate_file  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BRIEFS_DIR = os.path.join(REPO_ROOT, "briefs")
INDEX_NAME = "index.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def brief_paths(briefs_dir: str) -> list[str]:
    return sorted(
        os.path.join(briefs_dir, name)
        for name in os.listdir(briefs_dir)
        if name.endswith(".json") and name != INDEX_NAME
    )


def edition_entry(brief: dict) -> dict:
    """Build one `editions` row exactly per the SPEC schema."""
    foundations = brief.get("foundations") or {}
    layers_present = []
    item_count = 0
    for layer in (brief.get("pulse") or {}).get("layers") or []:
        slug = layer.get("layer")
        if slug in LAYER_SLUGS and slug not in layers_present:
            layers_present.append(slug)
        item_count += len(layer.get("items") or [])

    return {
        "date": brief["date"],
        "headline": brief["headline"],
        "foundations_topic": foundations.get("topic", ""),
        "foundations_slug": foundations.get("slug", ""),
        "item_count": item_count,
        # canonical cake order, not file order
        "layers": [s for s in LAYER_SLUGS if s in layers_present],
    }


def build(briefs_dir: str) -> tuple[dict | None, list[str]]:
    """Return (index_without_generated_at, problem_messages)."""
    problems: list[str] = []
    if not os.path.isdir(briefs_dir):
        return None, [f"{briefs_dir}: no such directory"]

    paths = brief_paths(briefs_dir)
    editions = []
    for path in paths:
        report = validate_file(path)
        if not report.ok:
            problems.append(report.render(strict=False))
            continue
        with open(path, "r", encoding="utf-8") as fh:
            brief = json.load(fh)
        editions.append(edition_entry(brief))

    if problems:
        return None, problems

    editions.sort(key=lambda e: e["date"], reverse=True)

    seen = {}
    for e in editions:
        if e["date"] in seen:
            problems.append(
                f"duplicate edition date {e['date']} — two files claim the same day"
            )
        seen[e["date"]] = True
    if problems:
        return None, problems

    return {
        "latest": editions[0]["date"] if editions else None,
        "editions": editions,
    }, []


def render(index: dict) -> str:
    return json.dumps(index, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def read_existing(index_path: str) -> dict | None:
    try:
        with open(index_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="build_index.py",
        description="Regenerate briefs/index.json from briefs/*.json.",
    )
    parser.add_argument(
        "--briefs-dir",
        default=DEFAULT_BRIEFS_DIR,
        help="directory holding the edition JSON files (default: <repo>/briefs)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit 1 if the on-disk index differs from the generated one",
    )
    args = parser.parse_args(argv)

    briefs_dir = os.path.abspath(args.briefs_dir)
    index_path = os.path.join(briefs_dir, INDEX_NAME)

    core, problems = build(briefs_dir)
    if core is None:
        print(
            "Refusing to build the index — these briefs do not validate:\n",
            file=sys.stderr,
        )
        for problem in problems:
            print(problem, file=sys.stderr)
        print(
            "\nFix the briefs above (python3 scripts/validate_brief.py briefs/) "
            "and run this again. The index was not written.",
            file=sys.stderr,
        )
        return 1 if os.path.isdir(briefs_dir) else 2

    existing = read_existing(index_path)

    # Keep `generated_at` stable when nothing else changed, so rebuilding the
    # index in CI does not produce a one-line churn diff every single run.
    generated_at = utc_now_iso()
    if existing is not None:
        existing_core = {
            "latest": existing.get("latest"),
            "editions": existing.get("editions"),
        }
        if existing_core == core and isinstance(existing.get("generated_at"), str):
            generated_at = existing["generated_at"]

    index = dict(core)
    index["generated_at"] = generated_at
    payload = render(index)

    if args.check:
        try:
            with open(index_path, "r", encoding="utf-8") as fh:
                on_disk = fh.read()
        except FileNotFoundError:
            print(
                f"STALE  {index_path} does not exist.\n"
                "       Run: python3 scripts/build_index.py",
                file=sys.stderr,
            )
            return 1
        except OSError as exc:
            print(f"ERROR  cannot read {index_path}: {exc}", file=sys.stderr)
            return 2

        if on_disk == payload:
            print(f"OK     {index_path} is up to date ({len(core['editions'])} edition(s))")
            return 0

        print(f"STALE  {index_path} does not match the generated index.", file=sys.stderr)
        print("       Run: python3 scripts/build_index.py — and commit the result.", file=sys.stderr)
        print("       Diff (on-disk -> generated):", file=sys.stderr)
        import difflib

        diff = difflib.unified_diff(
            on_disk.splitlines(keepends=True),
            payload.splitlines(keepends=True),
            fromfile="briefs/index.json (on disk)",
            tofile="briefs/index.json (generated)",
        )
        for line in diff:
            sys.stderr.write("       " + line if line.endswith("\n") else "       " + line + "\n")
        return 1

    if existing is not None and read_raw(index_path) == payload:
        print(f"OK     {index_path} already current ({len(core['editions'])} edition(s))")
        return 0

    tmp_path = index_path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload)
        os.replace(tmp_path, index_path)
    except OSError as exc:
        print(f"ERROR  cannot write {index_path}: {exc}", file=sys.stderr)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return 2

    latest = core["latest"] or "(none)"
    print(
        f"WROTE  {index_path} — {len(core['editions'])} edition(s), latest {latest}"
    )
    return 0


def read_raw(path: str) -> str | None:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


if __name__ == "__main__":
    sys.exit(main())
