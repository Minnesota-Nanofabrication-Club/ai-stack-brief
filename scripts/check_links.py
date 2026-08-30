#!/usr/bin/env python3
"""Fetch every URL an edition cites and report the ones that are not there.

`validate_brief.py` is deliberately offline: it checks the *shape* of a URL —
absolute, http(s), plausible host, not `example.com` — and never opens a socket.
That makes it fast, hermetic, and safe to run on every push. It also means a
citation the model invented out of whole cloth sails through it clean, because
`https://arxiv.org/abs/2608.09508` is a perfectly well-formed URL whether or not
that paper exists.

This script is the other half. It is the only automated check standing between a
plausible-looking hallucinated source and a published edition, so it runs in the
daily job right after the agent writes the file, and the agent is told to run it
on itself before it finishes.

Classification, and the reasoning behind it:

  2xx, 3xx              OK.        The document is there.
  404, 410              ERROR.     The document is not there. On a URL the agent
                                   claims to have fetched during this run, that is
                                   the signature of a fabricated citation.
  DNS does not resolve  ERROR.     An invented hostname.
  401, 402, 403, 429    WARN.      Paywalled, or the host blocks automated
                                   fetchers. `research/SOURCES.md` documents a
                                   standing list of these (IEEE, some vendor IR
                                   pages, Cloudflare-fronted trade press). The
                                   URL is unverifiable from CI, not disproven.
  other 4xx / 5xx       WARN.      Server-side trouble, usually transient.
  timeout, conn reset   WARN.      Ditto. Do not fail a build on flaky egress.

So the hard failure is reserved for the two cases that actually mean "this does
not exist." Everything ambiguous degrades to a warning, and `--strict` promotes
warnings if you want the paranoid reading.

Usage:
    python3 scripts/check_links.py briefs/2026-08-30.json
    python3 scripts/check_links.py --strict briefs/2026-08-30.json
    python3 scripts/check_links.py briefs/          # whole archive

Exit status: 0 clean, 1 problems found, 2 bad invocation.

Stdlib only, like everything else in this repo.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Many excellent primary sources refuse a bare urllib User-Agent while serving a
# browser perfectly happily. `research/SOURCES.md` calls this out as the single
# most common reason a good URL looks dead. Present as a browser so that a WARN
# means "genuinely unreachable" rather than "we announced ourselves as a bot."
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)

# Per-host User-Agent overrides.
#
# SEC EDGAR rejects generic browser agents: its access policy requires the
# requester to declare a contact, and it wants an *email address*, in the shape
# "Organisation Name contact@domain". A URL is not accepted. Until someone puts a
# real club contact address here, EDGAR will keep answering 403 or hanging up,
# which lands as an "unverifiable" WARN rather than a failure — filings do not
# block a publish, they just do not get machine-verified.
#
# To turn EDGAR verification on, replace the value below with e.g.
#     "Minnesota Nanofabrication Club contact@yourdomain.org"
# SEC also rate-limits to 10 requests/second; --workers 8 is already under that,
# but a burst of EDGAR URLs in one edition can still trip a disconnect.
HOST_USER_AGENTS = {
    "sec.gov": (
        "MNF AI Stack Brief link checker "
        "(+https://github.com/Minnesota-Nanofabrication-Club/ai-stack-brief)"
    ),
}

DEFAULT_TIMEOUT = 20.0
DEFAULT_WORKERS = 8

# Not there. The whole point of this script.
FATAL_STATUS = {404, 410}

# Unverifiable from CI, not disproven. Paywall, bot wall, or rate limit.
BLOCKED_STATUS = {401, 402, 403, 429}


class Result:
    """One URL, and what happened when we asked for it."""

    def __init__(self, url: str, where: str):
        self.url = url
        self.where = where
        self.level = "ok"          # ok | warn | error
        self.detail = ""

    def mark(self, level: str, detail: str) -> "Result":
        self.level = level
        self.detail = detail
        return self


def collect_paths(raw: list[str]) -> tuple[list[str], list[str]]:
    """Expand directories to the briefs inside them. Mirrors validate_brief.py."""
    paths: list[str] = []
    problems: list[str] = []
    for item in raw:
        p = Path(item)
        if p.is_dir():
            found = sorted(
                str(f) for f in p.glob("*.json") if f.name != "index.json"
            )
            if not found:
                problems.append(f"{item} contains no brief JSON files")
            paths.extend(found)
        elif p.is_file():
            paths.append(str(p))
        else:
            problems.append(f"{item} does not exist")
    return paths, problems


def collect_urls(doc: dict) -> list[tuple[str, str]]:
    """Every cited URL in an edition, paired with a JSON-ish path for the report."""
    out: list[tuple[str, str]] = []

    def take(sources, where: str) -> None:
        if not isinstance(sources, list):
            return
        for i, src in enumerate(sources):
            if isinstance(src, dict) and isinstance(src.get("url"), str):
                out.append((src["url"], f"{where}[{i}].url"))

    pulse = doc.get("pulse") or {}
    for li, layer in enumerate(pulse.get("layers") or []):
        if not isinstance(layer, dict):
            continue
        slug = layer.get("layer", li)
        for ii, item in enumerate(layer.get("items") or []):
            if not isinstance(item, dict):
                continue
            ident = item.get("id", ii)
            take(item.get("sources"), f"pulse.{slug}.{ident}.sources")

    foundations = doc.get("foundations") or {}
    if isinstance(foundations, dict):
        take(foundations.get("sources"), "foundations.sources")

    return out


def probe(url: str, where: str, timeout: float) -> Result:
    """HEAD the URL, falling back to GET where HEAD is not honoured."""
    res = Result(url, where)

    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    agent = USER_AGENT
    for suffix, override in HOST_USER_AGENTS.items():
        if host == suffix or host.endswith("." + suffix):
            agent = override
            break

    def request(method: str):
        req = urllib.request.Request(url, method=method)
        req.add_header("User-Agent", agent)
        req.add_header("Accept", "*/*")
        return urllib.request.urlopen(req, timeout=timeout)

    for method in ("HEAD", "GET"):
        try:
            with request(method) as resp:
                code = getattr(resp, "status", 200) or 200
                return res.mark("ok", f"{code}")
        except urllib.error.HTTPError as exc:
            code = exc.code
            # A fair number of servers reject HEAD outright but serve GET fine.
            # Retry once before believing the status.
            if method == "HEAD" and code in (400, 403, 405, 406, 501):
                continue
            if code in FATAL_STATUS:
                return res.mark("error", f"HTTP {code} — this URL does not exist")
            if code in BLOCKED_STATUS:
                return res.mark(
                    "warn", f"HTTP {code} — paywalled or bot-blocked; unverifiable here"
                )
            return res.mark("warn", f"HTTP {code}")
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            text = str(reason)
            # An invented hostname is as damning as a 404.
            if "Name or service not known" in text or "nodename nor servname" in text:
                return res.mark("error", f"host does not resolve — {text}")
            if method == "HEAD":
                continue
            return res.mark("warn", f"unreachable — {text}")
        except Exception as exc:  # noqa: BLE001 — never let one URL kill the run
            if method == "HEAD":
                continue
            return res.mark("warn", f"{type(exc).__name__}: {exc}")

    return res.mark("warn", "no response to HEAD or GET")


def check_file(path: str, timeout: float, workers: int) -> tuple[list[Result], str | None]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return [], f"{path}: {exc}"

    pairs = collect_urls(doc)
    if not pairs:
        return [], None

    # Deduplicate: the same paper is often cited by two items, and there is no
    # reason to ask the server twice or to report it twice.
    seen: dict[str, str] = {}
    for url, where in pairs:
        seen.setdefault(url, where)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(
            pool.map(lambda kv: probe(kv[0], kv[1], timeout), sorted(seen.items()))
        )
    return results, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_links.py",
        description="Fetch every URL an edition cites and flag the ones that are not there.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        metavar="PATH",
        help="brief JSON file(s), or a directory of them (index.json is skipped)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings (paywalls, bot walls, timeouts) as errors too",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"per-request timeout in seconds (default {DEFAULT_TIMEOUT:g})",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"parallel requests (default {DEFAULT_WORKERS})",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="only print URLs that have problems",
    )
    args = parser.parse_args(argv)

    paths, problems = collect_paths(args.paths)
    for problem in problems:
        print(f"ERROR  {problem}", file=sys.stderr)
    if not paths:
        if not problems:
            print("ERROR  nothing to check", file=sys.stderr)
        return 2

    n_err = n_warn = n_ok = 0
    failing_files = 0

    for path in paths:
        results, load_error = check_file(path, args.timeout, args.workers)
        if load_error:
            print(f"ERROR  {load_error}", file=sys.stderr)
            problems.append(load_error)
            continue

        errs = [r for r in results if r.level == "error"]
        warns = [r for r in results if r.level == "warn"]
        n_err += len(errs)
        n_warn += len(warns)
        n_ok += len(results) - len(errs) - len(warns)

        bad = bool(errs) or (args.strict and warns)
        if bad:
            failing_files += 1

        if not errs and not warns:
            if not args.quiet:
                print(f"OK    {path}  —  {len(results)} URL(s) all reachable")
            continue

        status = "FAIL" if bad else "PASS"
        print(
            f"{status}  {path}  —  {len(errs)} unreachable, "
            f"{len(warns)} unverifiable, {len(results)} checked"
        )
        for r in errs:
            print(f"  ERROR  {r.where}: {r.detail}")
            print(f"         {r.url}")
        for r in warns:
            label = "ERROR" if args.strict else "WARN "
            print(f"  {label}  {r.where}: {r.detail}" + (" [strict]" if args.strict else ""))
            print(f"         {r.url}")

    print()
    print(
        f"{len(paths)} file(s) checked — {n_err} unreachable, "
        f"{n_warn} unverifiable, {n_ok} OK, {failing_files} file(s) failing"
    )
    if n_err:
        print(
            "\nAn unreachable URL on a source the agent claims to have fetched during "
            "the run is the signature of a fabricated citation. Do not publish it: "
            "find the real source or drop the item."
        )

    if problems:
        return 2
    return 1 if failing_files else 0


if __name__ == "__main__":
    sys.exit(main())
