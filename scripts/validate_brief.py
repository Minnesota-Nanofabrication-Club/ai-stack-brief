#!/usr/bin/env python3
"""Validate ai-stack-brief edition JSON against the contract in SPEC.md.

Standard library only. No pip installs, no network.

Usage:
    python3 scripts/validate_brief.py briefs/2026-08-20.json
    python3 scripts/validate_brief.py briefs/                # every *.json except index.json
    python3 scripts/validate_brief.py --strict briefs/2026-08-20.json

Exit codes:
    0  no hard errors (warnings may have been printed)
    1  at least one hard error (or, with --strict, at least one warning)
    2  bad invocation / unreadable input

Design notes for whoever is reading this because CI just failed:
  * Every problem found is printed. The validator never stops at the first one.
  * Each line is prefixed ERROR or WARN and carries a path like
    `pulse.layers[1].items[0].sources[2].url` so you can go straight to the field.
  * Source `date` may be YYYY-MM-DD, YYYY-MM, or a bare YYYY. All three are
    valid per SPEC ("Source dates") -- Foundations legitimately cites classic
    papers and undated vendor references alongside dated news.
  * Word budgets are deliberately plural and never pooled. The member tier
    (`dek` + `why_it_matters`) is budgeted separately from `background_md`,
    which is budgeted separately from `deeper_md` and the glossaries. Folding
    an added field into an existing budget is how a useful warning turns into
    one that fires on every edition and gets ignored.
  * ERROR means the file violates SPEC.md and must not ship.
  * WARN means it probably reads badly (too long, too short, restated dek,
    the same link cited twice). Fix them if you can; --strict makes them fatal.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import unicodedata
from datetime import date as date_cls
from datetime import datetime
from urllib.parse import urlsplit

# --------------------------------------------------------------------------
# Contract constants — these mirror SPEC.md. Change SPEC.md first.
# --------------------------------------------------------------------------

# The taxonomy is no longer Jensen Huang's five-layer AI cake. It grew two layers
# because the old one had nowhere to put half of what this club actually does:
# `silicon` for device physics, process, packaging and analog/RF (work that is not
# about AI at all), and `computing` for computer science that is not an AI model
# (compilers, OSes, distributed systems, architecture research). The list order IS
# the canonical bottom-to-top publication order — build_index.py imports this name
# and uses it to order the per-edition layer list, and check_pulse() below uses it
# to flag an edition whose layers are out of order. Reorder this list and you
# reorder the product, so don't, unless SPEC.md changed first.
LAYER_SLUGS = [
    "energy",
    "silicon",
    "chips",
    "computing",
    "infrastructure",
    "models",
    "applications",
]

# The two home layers. SPEC used to require "at least one item in `chips`"; with
# `silicon` split out of it, a perfectly good fab/process edition could suddenly
# have zero `chips` items and fail a rule it was never meant to fail. The rule is
# therefore about the pair, not either slug on its own.
HOME_LAYER_SLUGS = ("silicon", "chips")

CONFIDENCE_VALUES = ["confirmed", "reported", "rumored"]

REQUIRED_TOP = ["date", "generated_at", "window", "headline", "pulse", "foundations"]
# `background_md` and `glossary` are required on every item, not optional extras.
# The reasoning is in SPEC: the reader this product is for is a curious engineer
# who does not already know the subfield, and without standing context and a term
# list they hit `deeper_md` cold. An item that cannot carry two sentences of
# background and two defined terms is an item nobody understood well enough to
# publish, so a missing field is an error rather than a warning.
REQUIRED_ITEM = [
    "id",
    "title",
    "dek",
    "why_it_matters",
    "background_md",
    "deeper_md",
    "glossary",
    "confidence",
    "sources",
]
REQUIRED_PULSE = ["read_time_min", "layers"]
REQUIRED_FOUNDATIONS = [
    "read_time_min",
    "topic",
    "slug",
    "subtitle",
    "tldr",
    "sections",
    "glossary",
    "try_this",
    "sources",
]
REQUIRED_SOURCE = ["title", "url", "publisher", "date"]

# Hard bounds (fatal).
#
# The item range used to be a hard 5-11 with a warning below SPEC's stated floor
# of 7. That soft band is gone: SPEC's floor and the validator's floor are now the
# same number, because with seven layers to cover, six items is not a quiet week,
# it is an incomplete run. Padding is still the worse sin -- the fix for a
# six-item day is to find a seventh story worth writing up, never to inflate a
# layer that had nothing. If a genuinely dead week ever justifies fewer, that is a
# conscious edit to SPEC.md and to this constant, not something CI waves through.
MIN_ITEMS = 7
MAX_ITEMS = 13
MIN_SECTIONS = 3
MIN_GLOSSARY = 4
MIN_FOUNDATIONS_SOURCES = 3
# Per-item glossary bounds. Fewer than two entries means nobody reread their own
# prose looking for jargon; more than four means the item is trying to teach a
# whole subfield in one sitting and should have been narrowed or split.
MIN_ITEM_GLOSSARY = 2
MAX_ITEM_GLOSSARY = 4

# Soft targets from SPEC.md (warnings only).
TITLE_MAX_CHARS = 80
PULSE_PROSE_TARGET = 1100  # dek + why_it_matters across all items
FOUNDATIONS_PROSE_TARGET = 1100  # member tier only: tldr + section body_md
PROSE_TOLERANCE = 0.25  # SPEC: "within roughly +/-25%"
DEEPER_MD_RANGE = (80, 200)  # words
SECTION_BODY_RANGE = (100, 180)  # words
BACKGROUND_MD_RANGE = (50, 110)  # words -- SPEC's stated target for background_md
# The warn band is deliberately wider than the target. Two sentences of real
# mechanism sometimes land at 47 words and sometimes at 115, and flagging that
# would train writers to pad or truncate to hit a number, which is exactly the
# behaviour this product does not want. Outside 45-120 it is no longer a
# paragraph of standing context -- it is a stub, or it is a second deeper_md.
BACKGROUND_MD_WARN_RANGE = (45, 120)
# A definition longer than this has stopped defining and started explaining;
# that material belongs in `deeper_md`, where the reader chose to opt in.
GLOSSARY_DEF_MAX_WORDS = 40
DEK_SIMILARITY_LIMIT = 0.72  # difflib ratio above this == restatement
DEK_MIN_WORDS = 10  # SPEC "Delivery surfaces": a dek must stand alone in Discord
DEK_MAX_WORDS = 60

# SPEC non-negotiable rule 3: every item carries at least one primary or
# specialist-technical source. A validator cannot read a page, so this is a
# domain heuristic that produces a WARNING, never a hard error. Two lists:
# things that are clearly primary/specialist, and things that are clearly
# coverage. An item whose sources are all coverage gets flagged.
#
# Add domains here when the heuristic is wrong — it is meant to be edited.
PRIMARY_SOURCE_HINTS = (
    # papers, standards, filings, government
    "arxiv.org", "biorxiv.org", "openreview.net", "doi.org", "ieee.org",
    "acm.org", "nature.com", "science.org", "aip.org", "iop.org", "aps.org",
    "electrochem.org", "ecsdl.org", "spie.org", "osti.gov", "nist.gov",
    "sec.gov", "uspto.gov", "patents.google.com", "federalregister.gov",
    "ferc.gov", "eia.gov", "energy.gov", "nrel.gov", "europa.eu", "bis.doc.gov",
    "jedec.org", "semi.org", "opencompute.org", "ietf.org", "pcisig.com",
    "unipro.org", "khronos.org", "mlcommons.org",
    # grid operators, reliability bodies and utility regulators — the energy layer's
    # primary documents live here (queue reports, planning studies, tariffs, IRPs)
    "pjm.com", "misoenergy.org", "ercot.com", "caiso.com", "iso-ne.com",
    "nyiso.com", "spp.org", "nerc.com", "epri.com", "iea.org",
    # specialist technical press and analysis
    "semianalysis.com", "semiengineering.com", "semiwiki.com", "techinsights.com",
    "chipsandcheese.com", "spectrum.ieee.org", "eetimes.com", "3dincites.com",
    "angstronomics.com", "morethanmoore.substack.com", "irds.ieee.org",
    # primary corporate/technical publications (whitepapers, tech blogs, decks)
    "asml.com", "tsmc.com", "intel.com", "samsung.com", "skhynix.com",
    "micron.com", "nvidia.com", "amd.com", "arm.com", "appliedmaterials.com",
    "lamresearch.com", "kla.com", "tel.com", "zeiss.com", "imec-int.com",
    "synopsys.com", "cadence.com", "siemens.com", "globalfoundries.com",
    "rapidus.inc", "huggingface.co", "github.com", "openai.com",
    "georgiapower.com", "southerncompany.com", "xcelenergy.com", "gevernova.com",
    "siemens-energy.com", "entegris.com", "dupont.com", "screen.co.jp",
    "anthropic.com", "deepmind.google", "ai.meta.com", "research.google",
)

COVERAGE_ONLY_HINTS = (
    "prnewswire.com", "businesswire.com", "globenewswire.com", "newswire.ca",
    "reddit.com", "news.ycombinator.com", "x.com", "twitter.com",
    "seekingalpha.com", "benzinga.com", "finance.yahoo.com", "msn.com",
    "medium.com", "substack.com",
)

KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
WINDOW_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})$")
SOURCE_DATE_RE = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’/.\-]*")
MD_STRIP_RE = re.compile(r"[`*_>#\[\]()!]|https?://\S+")


# --------------------------------------------------------------------------
# Problem collection
# --------------------------------------------------------------------------


class Report:
    """Accumulates errors and warnings for a single file."""

    def __init__(self, path: str):
        self.path = path
        self.errors: list[tuple[str, str]] = []
        self.warnings: list[tuple[str, str]] = []

    def error(self, where: str, message: str) -> None:
        self.errors.append((where, message))

    def warn(self, where: str, message: str) -> None:
        self.warnings.append((where, message))

    @property
    def ok(self) -> bool:
        return not self.errors

    def render(self, strict: bool) -> str:
        lines = []
        n_err, n_warn = len(self.errors), len(self.warnings)
        if not n_err and not n_warn:
            lines.append(f"OK    {self.path}")
            return "\n".join(lines)

        status = "FAIL" if (n_err or (strict and n_warn)) else "PASS"
        summary = f"{n_err} error(s), {n_warn} warning(s)"
        lines.append(f"{status}  {self.path}  —  {summary}")
        for where, message in self.errors:
            lines.append(f"  ERROR  {where}: {message}")
        for where, message in self.warnings:
            label = "ERROR" if strict else "WARN "
            lines.append(f"  {label}  {where}: {message}" + (" [strict]" if strict else ""))
        return "\n".join(lines)


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------


def words(text: str) -> list[str]:
    """Word tokens of markdown-ish prose, with markup and URLs removed."""
    if not isinstance(text, str):
        return []
    cleaned = MD_STRIP_RE.sub(" ", text)
    return WORD_RE.findall(cleaned)


def word_count(text: str) -> int:
    return len(words(text))


def normalize_for_similarity(text: str) -> str:
    """Lowercase, strip accents/punctuation, collapse whitespace."""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def similarity(a: str, b: str) -> float:
    """Blend of sequence similarity and content-word overlap.

    difflib alone misses "same sentence, reordered clauses"; a bag-of-words
    Jaccard alone misses "same sentence, one word swapped". Take the max so
    either kind of restatement trips the check.
    """
    na, nb = normalize_for_similarity(a), normalize_for_similarity(b)
    if not na or not nb:
        return 0.0
    seq = difflib.SequenceMatcher(None, na, nb).ratio()

    stop = {
        "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "is",
        "are", "was", "were", "it", "its", "that", "this", "with", "by", "as",
        "at", "from", "be", "been", "will", "has", "have", "had", "but", "not",
    }
    sa = {w for w in na.split() if w not in stop}
    sb = {w for w in nb.split() if w not in stop}
    if not sa or not sb:
        return seq
    jaccard = len(sa & sb) / len(sa | sb)
    # Containment: a why_it_matters that is the dek plus three words.
    containment = len(sa & sb) / min(len(sa), len(sb))
    return max(seq, jaccard, containment * 0.95)


def is_nonempty_str(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


def typename(value) -> str:
    return type(value).__name__


def check_iso_date(value: str) -> bool:
    try:
        date_cls.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


def check_url(value) -> str | None:
    """Return None if the URL is fine, else a human explanation."""
    if not isinstance(value, str):
        return f"must be a string, got {typename(value)}"
    if value.strip() == "":
        return "is empty"
    if value != value.strip():
        return "has leading/trailing whitespace"
    if re.search(r"\s", value):
        return "contains whitespace"
    parts = urlsplit(value)
    if parts.scheme not in ("http", "https"):
        return f"must be an absolute http(s) URL (scheme is {parts.scheme!r} in {value!r})"
    if not parts.netloc:
        return f"has no host: {value!r}"
    host = parts.netloc.split("@")[-1].split(":")[0]
    if "." not in host or host.startswith(".") or host.endswith("."):
        return f"host {host!r} does not look like a domain"
    if re.search(r"[^A-Za-z0-9.\-]", host):
        return f"host {host!r} contains invalid characters"
    if "example.com" in host or host in ("localhost",):
        return f"looks like a placeholder host ({host!r}) — sources must be real, fetched URLs"
    return None


# --------------------------------------------------------------------------
# Field-level checks
# --------------------------------------------------------------------------


def host_of(url) -> str:
    if not isinstance(url, str):
        return ""
    host = urlsplit(url).netloc.split("@")[-1].split(":")[0].lower()
    return host[4:] if host.startswith("www.") else host


def _host_matches(host: str, hints: tuple) -> bool:
    return any(host == h or host.endswith("." + h) for h in hints)


def looks_primary(url) -> bool:
    host = host_of(url)
    if not host:
        return False
    # Any government host is primary by construction: an executive order, a docket
    # filing, a licensing document, or an agency dataset is the document itself.
    if host.endswith(".gov") or host.endswith(".mil"):
        return True
    # University and academic-institute hosts: preprints, lab pages, course notes
    # and technical reports live here, and Foundations leans on them heavily.
    if host.endswith(".edu") or host.endswith(".ac.uk") or host.endswith(".edu.tw"):
        return True
    return _host_matches(host, PRIMARY_SOURCE_HINTS)


def looks_coverage_only(url) -> bool:
    host = host_of(url)
    return bool(host) and _host_matches(host, COVERAGE_ONLY_HINTS)


def check_source(rep: Report, src, where: str, seen_urls: dict) -> None:
    if not isinstance(src, dict):
        rep.error(where, f"must be an object, got {typename(src)}")
        return

    for field in REQUIRED_SOURCE:
        if field not in src:
            rep.error(f"{where}.{field}", "required field is missing")
        elif not is_nonempty_str(src[field]):
            rep.error(
                f"{where}.{field}",
                f"must be a non-empty string, got {typename(src[field])}"
                if not isinstance(src[field], str)
                else "is empty",
            )

    url = src.get("url")
    if isinstance(url, str) and url.strip():
        problem = check_url(url)
        if problem:
            rep.error(f"{where}.url", problem)
        else:
            seen_urls.setdefault(url, []).append(where)

    sdate = src.get("date")
    if isinstance(sdate, str) and sdate.strip():
        if not SOURCE_DATE_RE.match(sdate.strip()):
            rep.error(
                f"{where}.date",
                f"{sdate!r} must be YYYY, YYYY-MM, or YYYY-MM-DD",
            )
        elif len(sdate.strip()) == 10 and not check_iso_date(sdate.strip()):
            rep.error(f"{where}.date", f"{sdate!r} is not a real calendar date")


def check_glossary(rep: Report, glossary, where: str, min_entries: int,
                   max_entries: int | None = None,
                   definition_max_words: int | None = None,
                   count_note: str = "") -> None:
    """Validate a `[{term, definition}, ...]` array.

    There are two glossaries in the schema now — the long-standing Foundations one
    and the new per-item one — and they are the same shape, so they get the same
    code. The two callers differ only in their bounds, which is exactly the kind of
    difference a parameter is for; duplicating forty lines so that one copy could
    say "at least 4" and the other "2-4" would guarantee the two drift apart the
    first time somebody fixes a message in one of them.

    The split between ERROR and WARN follows the rest of this file. Structure is an
    error: not an array, wrong number of entries, a missing or empty `term` or
    `definition`, the same term defined twice in one list. Those either break the
    renderer or mean the writer did not do the work. Length is a warning, because
    a 42-word definition is a style problem and a human should decide.

    `definition_max_words` is deliberately left None for Foundations. Its glossary
    is the reference appendix to a 1,100-word deep dive, where a definition that
    carries an equation or a failure mode is doing its job; several existing ones
    legitimately run past 40 words. The per-item glossary is inline footing for a
    reader who is mid-paragraph, and there the cap is real.
    """
    if not isinstance(glossary, list):
        rep.error(where, f"must be an array, got {typename(glossary)}")
        return

    n = len(glossary)
    if n < min_entries or (max_entries is not None and n > max_entries):
        expected = (
            f"at least {min_entries}"
            if max_entries is None
            else f"{min_entries}-{max_entries}"
        )
        message = f"{n} entr(y/ies); SPEC requires {expected}"
        if count_note:
            message += ". " + count_note
        rep.error(where, message)

    terms_seen: dict[str, int] = {}
    for i, entry in enumerate(glossary):
        gwhere = f"{where}[{i}]"
        if not isinstance(entry, dict):
            rep.error(gwhere, f"must be an object, got {typename(entry)}")
            continue
        for field in ("term", "definition"):
            if field not in entry:
                rep.error(f"{gwhere}.{field}", "required field is missing")
            elif not is_nonempty_str(entry[field]):
                rep.error(f"{gwhere}.{field}", "must be a non-empty string")
        term = entry.get("term")
        if isinstance(term, str) and term.strip():
            key = term.strip().lower()
            if key in terms_seen:
                rep.error(
                    f"{gwhere}.term",
                    f"duplicate glossary term {term!r} "
                    f"(already at {where}[{terms_seen[key]}])",
                )
            else:
                terms_seen[key] = i
        definition = entry.get("definition")
        if definition_max_words and isinstance(definition, str):
            dn = word_count(definition)
            if dn > definition_max_words:
                rep.warn(
                    f"{gwhere}.definition",
                    f"{dn} words; SPEC asks for one sentence, <= {definition_max_words}. "
                    "If it needs more than that, the explanation belongs in `deeper_md`.",
                )


def check_item(rep: Report, item, where: str, edition_date: str | None,
               seen_urls: dict) -> dict:
    """Validate one Pulse item. Returns collected stats for edition-level checks."""
    # `prose_words` and `background_words` are kept apart on purpose; see the two
    # budget calls in check_pulse() for why they must never be added together.
    stats = {"id": None, "prose_words": 0, "background_words": 0}

    if not isinstance(item, dict):
        rep.error(where, f"must be an object, got {typename(item)}")
        return stats

    for field in REQUIRED_ITEM:
        if field not in item:
            rep.error(f"{where}.{field}", "required field is missing")

    # id
    item_id = item.get("id")
    if "id" in item:
        if not isinstance(item_id, str):
            rep.error(f"{where}.id", f"must be a string, got {typename(item_id)}")
        elif not item_id:
            rep.error(f"{where}.id", "is empty")
        elif not KEBAB_RE.match(item_id):
            rep.error(
                f"{where}.id",
                f"{item_id!r} is not kebab-case "
                "(lowercase letters/digits joined by single hyphens, e.g. 'chips-tsmc-a14-risk')",
            )
        else:
            stats["id"] = item_id

    # title
    title = item.get("title")
    if "title" in item:
        if not is_nonempty_str(title):
            rep.error(f"{where}.title", "must be a non-empty string")
        elif len(title) > TITLE_MAX_CHARS:
            rep.warn(
                f"{where}.title",
                f"{len(title)} chars; SPEC targets <= {TITLE_MAX_CHARS}",
            )

    # prose fields
    for field in ("dek", "why_it_matters", "background_md", "deeper_md"):
        if field in item and not is_nonempty_str(item[field]):
            rep.error(f"{where}.{field}", "must be a non-empty string")

    if "fab_angle" in item and item["fab_angle"] is not None:
        if not is_nonempty_str(item["fab_angle"]):
            rep.error(
                f"{where}.fab_angle",
                "if present must be a non-empty string — omit the key instead of leaving it blank",
            )

    dek = item.get("dek") if isinstance(item.get("dek"), str) else ""
    wim = item.get("why_it_matters") if isinstance(item.get("why_it_matters"), str) else ""
    stats["prose_words"] = word_count(dek) + word_count(wim)

    # near-duplicate dek / why_it_matters (SPEC rule 4)
    if dek and wim:
        ratio = similarity(dek, wim)
        if ratio >= DEK_SIMILARITY_LIMIT:
            rep.warn(
                f"{where}.why_it_matters",
                f"reads as a restatement of `dek` (similarity {ratio:.2f} >= "
                f"{DEK_SIMILARITY_LIMIT:.2f}). SPEC rule 4: why_it_matters must give the "
                "consequence, not repeat the news. Rewrite it or cut the item.",
            )

    # The dek also ships to Discord with no headline above it and no layer
    # context around it, so it has to stand on its own (SPEC, Delivery surfaces).
    if dek:
        n = word_count(dek)
        if n < DEK_MIN_WORDS:
            rep.warn(
                f"{where}.dek",
                f"{n} words — too short to stand alone. In Discord this line appears with "
                "no title or layer around it; it must make sense by itself.",
            )
        elif n > DEK_MAX_WORDS:
            rep.warn(
                f"{where}.dek",
                f"{n} words; SPEC asks for one sentence a sophomore understands.",
            )

    if "deeper_md" in item and isinstance(item.get("deeper_md"), str):
        n = word_count(item["deeper_md"])
        lo, hi = DEEPER_MD_RANGE
        if n and not (lo * 0.7 <= n <= hi * 1.3):
            rep.warn(
                f"{where}.deeper_md",
                f"{n} words; SPEC targets {lo}-{hi}",
            )

    # background_md — the standing context the news sits in. There is no machine
    # check for the thing that actually matters here (is it mechanism or is it an
    # analogy? does it duplicate the dek?), so length is the only proxy available,
    # and it is a decent one: under ~45 words nobody has explained what a field is
    # and why it exists, and over ~120 words the writer has drifted into writing a
    # second `deeper_md` in the slot reserved for footing.
    if isinstance(item.get("background_md"), str):
        n = word_count(item["background_md"])
        stats["background_words"] = n
        lo, hi = BACKGROUND_MD_RANGE
        warn_lo, warn_hi = BACKGROUND_MD_WARN_RANGE
        if n and n < warn_lo:
            rep.warn(
                f"{where}.background_md",
                f"{n} words; SPEC targets {lo}-{hi}. Too short to give a reader who has "
                "never heard of this subfield any footing — say what the area is, what "
                "problem it exists to solve, and what the obstacle is.",
            )
        elif n > warn_hi:
            rep.warn(
                f"{where}.background_md",
                f"{n} words; SPEC targets {lo}-{hi}. This is drifting into a second "
                "`deeper_md`. background_md is the standing context, not the analysis — "
                "move the numbers and the caveats down into deeper_md.",
            )

    # per-item glossary
    if "glossary" in item:
        check_glossary(
            rep,
            item.get("glossary"),
            f"{where}.glossary",
            MIN_ITEM_GLOSSARY,
            max_entries=MAX_ITEM_GLOSSARY,
            definition_max_words=GLOSSARY_DEF_MAX_WORDS,
            count_note=(
                "Cover the terms this item actually uses and a newcomer would stumble "
                "on, symbols and units included."
            ),
        )

    # confidence
    if "confidence" in item:
        conf = item.get("confidence")
        if conf not in CONFIDENCE_VALUES:
            rep.error(
                f"{where}.confidence",
                f"{conf!r} is not allowed; must be one of "
                + ", ".join(repr(c) for c in CONFIDENCE_VALUES),
            )

    # sources
    if "sources" in item:
        sources = item.get("sources")
        if not isinstance(sources, list):
            rep.error(f"{where}.sources", f"must be an array, got {typename(sources)}")
        elif len(sources) < 1:
            rep.error(
                f"{where}.sources",
                "every item needs at least 1 source (SPEC rule 1: no unsourced claims)",
            )
        else:
            for i, src in enumerate(sources):
                check_source(rep, src, f"{where}.sources[{i}]", seen_urls)
            if edition_date:
                _warn_future_sources(rep, sources, f"{where}.sources", edition_date)
            _warn_no_primary_source(rep, sources, f"{where}.sources")

    return stats


def _warn_no_primary_source(rep: Report, sources: list, where: str) -> None:
    """SPEC rule 3 — heuristic, so a warning rather than an error."""
    urls = [s.get("url") for s in sources if isinstance(s, dict)]
    urls = [u for u in urls if isinstance(u, str) and u.strip()]
    if not urls:
        return
    if any(looks_primary(u) for u in urls):
        # SPEC: sources[0] is the strongest primary document, not the first thing
        # found. post_discord.py links sources[0] and nothing else, so a misordered
        # list sends the club to a press release instead of the filing.
        if not looks_primary(urls[0]):
            primary = next(u for u in urls if looks_primary(u))
            rep.warn(
                f"{where}[0]",
                "the first source is not the primary document, but "
                f"{host_of(primary)} in the same list is. Discord links only "
                "sources[0] — reorder so the primary document leads.",
            )
        return

    hosts = sorted({host_of(u) for u in urls if host_of(u)})
    if not hosts:
        return  # the URLs are broken; the URL errors already say so
    all_coverage = all(looks_coverage_only(u) for u in urls)
    detail = (
        "every source is a newswire/aggregator/social host"
        if all_coverage
        else "no source is on the known primary/specialist list"
    )
    rep.warn(
        where,
        f"SPEC rule 3: {detail} ({', '.join(hosts)}). Every item needs at least one "
        "primary or specialist-technical source — the arXiv/IEEE paper, the SEC filing, "
        "the earnings transcript, the patent, the standard, the vendor whitepaper, the "
        "teardown. Add one, or cut the item. (Heuristic by domain: if this source really "
        "is primary, add its host to PRIMARY_SOURCE_HINTS in scripts/validate_brief.py.)",
    )


def _warn_future_sources(rep: Report, sources: list, where: str, edition_date: str) -> None:
    try:
        edition = date_cls.fromisoformat(edition_date)
    except ValueError:
        return
    for i, src in enumerate(sources):
        if not isinstance(src, dict):
            continue
        raw = src.get("date")
        if not (isinstance(raw, str) and len(raw.strip()) == 10):
            continue
        try:
            sdate = date_cls.fromisoformat(raw.strip())
        except ValueError:
            continue
        if sdate > edition:
            rep.error(
                f"{where}[{i}].date",
                f"{raw} is after the edition date {edition_date}",
            )


def check_pulse(rep: Report, brief: dict, edition_date: str | None,
                seen_urls: dict) -> None:
    pulse = brief.get("pulse")
    if not isinstance(pulse, dict):
        if "pulse" in brief:
            rep.error("pulse", f"must be an object, got {typename(pulse)}")
        return

    for field in REQUIRED_PULSE:
        if field not in pulse:
            rep.error(f"pulse.{field}", "required field is missing")

    rt = pulse.get("read_time_min")
    if "read_time_min" not in pulse:
        pass  # already reported above
    elif not isinstance(rt, int) or isinstance(rt, bool) or rt <= 0:
        rep.error("pulse.read_time_min", f"must be a positive integer, got {rt!r}")

    layers = pulse.get("layers")
    if "layers" not in pulse:
        return  # already reported by the REQUIRED_PULSE loop above
    if not isinstance(layers, list):
        rep.error("pulse.layers", f"must be an array, got {typename(layers)}")
        return
    if not layers:
        rep.error(
            "pulse.layers",
            "is empty; an edition needs at least one item across the home layers "
            "(`silicon` / `chips`)",
        )
        return

    seen_slugs: dict[str, int] = {}
    seen_ids: dict[str, list[str]] = {}
    total_items = 0
    total_prose = 0
    total_background = 0
    home_items = 0
    present_order: list[str] = []

    for li, layer in enumerate(layers):
        lwhere = f"pulse.layers[{li}]"
        if not isinstance(layer, dict):
            rep.error(lwhere, f"must be an object, got {typename(layer)}")
            continue

        slug = layer.get("layer")
        if "layer" not in layer:
            rep.error(f"{lwhere}.layer", "required field is missing")
        elif not isinstance(slug, str):
            rep.error(f"{lwhere}.layer", f"must be a string, got {typename(slug)}")
        elif slug not in LAYER_SLUGS:
            rep.error(
                f"{lwhere}.layer",
                f"{slug!r} is not a valid layer slug; must be one of "
                + ", ".join(LAYER_SLUGS),
            )
        elif slug in seen_slugs:
            rep.error(
                f"{lwhere}.layer",
                f"duplicate layer {slug!r} (already at pulse.layers[{seen_slugs[slug]}]); "
                "merge the items into a single layer block",
            )
        else:
            seen_slugs[slug] = li
            present_order.append(slug)

        items = layer.get("items")
        if "items" not in layer:
            rep.error(f"{lwhere}.items", "required field is missing")
            continue
        if not isinstance(items, list):
            rep.error(f"{lwhere}.items", f"must be an array, got {typename(items)}")
            continue
        if not items:
            rep.error(
                f"{lwhere}.items",
                "is empty; SPEC says a layer with nothing newsworthy is omitted entirely, "
                "not included empty",
            )
            continue

        for ii, item in enumerate(items):
            total_items += 1
            if slug in HOME_LAYER_SLUGS:
                home_items += 1
            stats = check_item(
                rep, item, f"{lwhere}.items[{ii}]", edition_date, seen_urls
            )
            total_prose += stats["prose_words"]
            total_background += stats["background_words"]
            if stats["id"]:
                seen_ids.setdefault(stats["id"], []).append(f"{lwhere}.items[{ii}]")

    # duplicate ids across the whole edition
    for item_id, locations in sorted(seen_ids.items()):
        if len(locations) > 1:
            rep.error(
                "pulse",
                f"item id {item_id!r} is used {len(locations)} times "
                f"({', '.join(locations)}); ids must be unique within an edition",
            )

    # a home-layer item must be present
    #
    # Counting items rather than testing for the slug matters: a layer block can
    # exist with an empty `items` array (already an error above), and "the chips
    # key was there" is not the property SPEC cares about. What it cares about is
    # that the edition actually says something about how silicon gets made or what
    # got built out of it.
    if home_items < 1:
        rep.error(
            "pulse.layers",
            "no item in `silicon` or `chips`; SPEC requires at least one across the "
            "two (they are this club's home layers, and in a normal edition they "
            "should carry the largest share of it)",
        )

    # item count
    if total_items < MIN_ITEMS:
        rep.error(
            "pulse",
            f"{total_items} Pulse items; minimum is {MIN_ITEMS}. Find another story "
            "worth writing up — do not pad a layer that had nothing.",
        )
    elif total_items > MAX_ITEMS:
        rep.error(
            "pulse",
            f"{total_items} Pulse items; maximum is {MAX_ITEMS}",
        )

    # canonical layer order
    canonical = [s for s in LAYER_SLUGS if s in present_order]
    if present_order and present_order != canonical:
        rep.warn(
            "pulse.layers",
            f"layers are ordered {present_order}; SPEC fixes the bottom-to-top order as "
            f"{canonical} (out of the full sequence "
            + " -> ".join(LAYER_SLUGS)
            + ")",
        )

    # Two budgets, kept apart on purpose.
    #
    # The ~1,100-word member-tier budget was written when `dek` + `why_it_matters`
    # were the only member-tier prose on an item. If `background_md` were folded
    # into that number, every edition from now on would blow the ceiling by roughly
    # the word count of the backgrounds and the warning would become noise nobody
    # reads -- the same reason `deeper_md` and the Foundations glossary have always
    # been counted separately. So the news budget stays exactly what it was, and
    # background gets its own.
    _check_word_budget(
        rep, "pulse", total_prose, PULSE_PROSE_TARGET,
        "dek + why_it_matters across all items (excludes background_md, deeper_md)",
    )

    # The background budget scales with the item count, because unlike the news
    # budget it is not a fixed amount of reading spread over however many stories
    # there are -- every item carries its own paragraph, so seven items owe about
    # half what thirteen do. The band is the per-item target range multiplied out,
    # which has a useful property: an edition where every single background sits
    # inside its own 50-110 target can never trip this. What it does catch is the
    # systematic drift the per-item check tolerates -- eleven backgrounds that are
    # each "only" 118 words are individually fine and collectively 1,300 words of
    # context nobody signed up to read.
    if total_items > 0:
        bg_lo, bg_hi = BACKGROUND_MD_RANGE
        _check_word_budget(
            rep, "pulse", total_background,
            (bg_lo + bg_hi) // 2 * total_items,
            f"background_md across all {total_items} items",
            band=(bg_lo * total_items, bg_hi * total_items),
            low_note=(
                f"That averages under {bg_lo} words an item — the backgrounds are "
                "stubs, and a newcomer still has no footing."
            ),
            high_note=(
                f"That averages over {bg_hi} words an item. Background is meant to be "
                "the footing, not the article; push detail into deeper_md."
            ),
        )


def _check_word_budget(rep: Report, where: str, actual: int, target: int,
                       what: str, band: tuple[int, int] | None = None,
                       low_note: str = "The 5-minute read claim gets thin.",
                       high_note: str = "This will not read in 5 minutes.") -> None:
    """Warn when a running word total leaves its band.

    `band` overrides the default +/-25% tolerance. It exists for budgets whose
    acceptable range is already stated elsewhere in SPEC as a per-unit target --
    multiplying that range out is both more honest and more forgiving than
    re-deriving a percentage around its midpoint, which would flag editions whose
    every individual item was in range.

    The notes default to the read-time sentences the two ~1,100-word member-tier
    budgets have always printed, so those messages are unchanged; a budget that is
    not about the five-minute claim passes its own.
    """
    if actual == 0:
        return
    if band is not None:
        lo, hi = band
    else:
        lo = int(target * (1 - PROSE_TOLERANCE))
        hi = int(target * (1 + PROSE_TOLERANCE))
    if actual < lo:
        rep.warn(
            where,
            f"{what} is {actual} words; SPEC targets ~{target} "
            f"(flagged below {lo}). {low_note}",
        )
    elif actual > hi:
        rep.warn(
            where,
            f"{what} is {actual} words; SPEC targets ~{target} "
            f"(flagged above {hi}). {high_note}",
        )


def check_foundations(rep: Report, brief: dict, seen_urls: dict) -> None:
    f = brief.get("foundations")
    if not isinstance(f, dict):
        if "foundations" in brief:
            rep.error("foundations", f"must be an object, got {typename(f)}")
        return

    for field in REQUIRED_FOUNDATIONS:
        if field not in f:
            rep.error(f"foundations.{field}", "required field is missing")

    rt = f.get("read_time_min")
    if "read_time_min" not in f:
        pass  # already reported by the REQUIRED_FOUNDATIONS loop above
    elif not isinstance(rt, int) or isinstance(rt, bool) or rt <= 0:
        rep.error("foundations.read_time_min", f"must be a positive integer, got {rt!r}")

    for field in ("topic", "subtitle", "tldr", "try_this"):
        if field in f and not is_nonempty_str(f[field]):
            rep.error(f"foundations.{field}", "must be a non-empty string")

    slug = f.get("slug")
    if "slug" in f:
        if not isinstance(slug, str) or not slug:
            rep.error("foundations.slug", "must be a non-empty string")
        elif not KEBAB_RE.match(slug):
            rep.error(
                "foundations.slug",
                f"{slug!r} is not kebab-case (must match the FOUNDATIONS_BACKLOG entry, e.g. 'cmp')",
            )

    # SPEC "Sizing per edition": the ~1,100-word Foundations target counts the
    # MEMBER TIER ONLY -- `tldr` plus every section `body_md`. `deeper_md`,
    # `glossary`, `subtitle`, and `try_this` sit on top and are not counted.
    prose_words = 0
    if isinstance(f.get("tldr"), str):
        prose_words += word_count(f["tldr"])

    # sections
    sections = f.get("sections")
    if "sections" in f:
        if not isinstance(sections, list):
            rep.error("foundations.sections", f"must be an array, got {typename(sections)}")
        else:
            if len(sections) < MIN_SECTIONS:
                rep.error(
                    "foundations.sections",
                    f"{len(sections)} section(s); SPEC requires at least {MIN_SECTIONS}",
                )
            headings_seen: dict[str, int] = {}
            for i, sec in enumerate(sections):
                swhere = f"foundations.sections[{i}]"
                if not isinstance(sec, dict):
                    rep.error(swhere, f"must be an object, got {typename(sec)}")
                    continue
                for field in ("heading", "body_md"):
                    if field not in sec:
                        rep.error(f"{swhere}.{field}", "required field is missing")
                    elif not is_nonempty_str(sec[field]):
                        rep.error(f"{swhere}.{field}", "must be a non-empty string")
                if "deeper_md" in sec and sec["deeper_md"] is not None:
                    if not is_nonempty_str(sec["deeper_md"]):
                        rep.error(
                            f"{swhere}.deeper_md",
                            "if present must be a non-empty string — omit the key instead",
                        )
                heading = sec.get("heading")
                if isinstance(heading, str) and heading.strip():
                    key = heading.strip().lower()
                    if key in headings_seen:
                        rep.warn(
                            f"{swhere}.heading",
                            f"duplicates the heading at foundations.sections[{headings_seen[key]}]",
                        )
                    else:
                        headings_seen[key] = i
                body = sec.get("body_md")
                if isinstance(body, str):
                    n = word_count(body)
                    prose_words += n
                    lo, hi = SECTION_BODY_RANGE
                    if n and not (lo * 0.7 <= n <= hi * 1.3):
                        rep.warn(f"{swhere}.body_md", f"{n} words; SPEC targets {lo}-{hi}")

    # glossary — same shape and same code as the per-item glossaries; see
    # check_glossary() for why Foundations does not get the definition length cap.
    if "glossary" in f:
        check_glossary(rep, f.get("glossary"), "foundations.glossary", MIN_GLOSSARY)

    # sources
    sources = f.get("sources")
    if "sources" in f:
        if not isinstance(sources, list):
            rep.error("foundations.sources", f"must be an array, got {typename(sources)}")
        else:
            if len(sources) < MIN_FOUNDATIONS_SOURCES:
                rep.error(
                    "foundations.sources",
                    f"{len(sources)} source(s); SPEC requires at least {MIN_FOUNDATIONS_SOURCES}",
                )
            for i, src in enumerate(sources):
                check_source(rep, src, f"foundations.sources[{i}]", seen_urls)

    _check_word_budget(
        rep, "foundations", prose_words, FOUNDATIONS_PROSE_TARGET,
        "member tier (tldr + section body_md; excludes deeper_md, glossary, try_this)",
    )


def check_top_level(rep: Report, brief: dict, filename: str) -> str | None:
    """Returns the validated edition date string, or None."""
    for field in REQUIRED_TOP:
        if field not in brief:
            rep.error(field, "required top-level field is missing")

    edition_date = None
    raw_date = brief.get("date")
    if "date" in brief:
        if not isinstance(raw_date, str):
            rep.error("date", f"must be a string, got {typename(raw_date)}")
        elif not re.match(r"^\d{4}-\d{2}-\d{2}$", raw_date):
            rep.error("date", f"{raw_date!r} must be an ISO date formatted YYYY-MM-DD")
        elif not check_iso_date(raw_date):
            rep.error("date", f"{raw_date!r} is not a real calendar date")
        else:
            edition_date = raw_date
            stem = os.path.splitext(os.path.basename(filename))[0]
            if stem != raw_date:
                rep.error(
                    "date",
                    f"{raw_date!r} does not match the filename stem {stem!r}; "
                    f"the file must be named {raw_date}.json",
                )

    gen = brief.get("generated_at")
    if "generated_at" in brief:
        if not isinstance(gen, str) or not gen.strip():
            rep.error("generated_at", "must be a non-empty ISO 8601 UTC string")
        else:
            parsed = _parse_utc(gen)
            if parsed is None:
                rep.error(
                    "generated_at",
                    f"{gen!r} is not ISO 8601 UTC; expected e.g. '2026-08-20T11:04:00Z'",
                )
            elif not (gen.endswith("Z") or gen.endswith("+00:00")):
                rep.error(
                    "generated_at",
                    f"{gen!r} must be UTC (end with 'Z'), not a local offset",
                )
            elif edition_date:
                gen_day = parsed.date()
                ed = date_cls.fromisoformat(edition_date)
                if abs((gen_day - ed).days) > 1:
                    rep.warn(
                        "generated_at",
                        f"{gen} is {abs((gen_day - ed).days)} days from the edition date "
                        f"{edition_date}",
                    )

    win = brief.get("window")
    if "window" in brief:
        if not isinstance(win, str) or not win.strip():
            rep.error("window", "must be a non-empty string")
        else:
            m = WINDOW_RE.match(win.strip())
            if not m:
                rep.error(
                    "window",
                    f"{win!r} must look like 'YYYY-MM-DD..YYYY-MM-DD'",
                )
            else:
                start_s, end_s = m.group(1), m.group(2)
                if not check_iso_date(start_s) or not check_iso_date(end_s):
                    rep.error("window", f"{win!r} contains a date that is not real")
                else:
                    start, end = date_cls.fromisoformat(start_s), date_cls.fromisoformat(end_s)
                    if start > end:
                        rep.error("window", f"{win!r} starts after it ends")
                    if edition_date and end_s != edition_date:
                        rep.warn(
                            "window",
                            f"window ends {end_s} but the edition date is {edition_date}; "
                            "SPEC's example ends the window on the edition date",
                        )
                    if edition_date and (end - start).days > 14:
                        rep.warn(
                            "window",
                            f"{(end - start).days}-day window; the Pulse covers ~7 days",
                        )

    headline = brief.get("headline")
    if "headline" in brief:
        if not is_nonempty_str(headline):
            rep.error("headline", "must be a non-empty string")
        else:
            n = word_count(headline)
            if n > 45:
                rep.warn("headline", f"{n} words; SPEC asks for one sentence")

    known = set(REQUIRED_TOP)
    for key in brief:
        if key not in known:
            rep.warn(key, "is not a field in the SPEC schema; it will be ignored by the app")

    return edition_date


def win_present(brief):
    # tiny helper kept so the `window` guard above reads defensively even if
    # `brief` is not a dict-like with membership semantics we expect.
    return brief if isinstance(brief, dict) else {}


def _parse_utc(value: str):
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def check_cross_item_sources(rep: Report, seen_urls: dict) -> None:
    for url, locations in sorted(seen_urls.items()):
        item_locs = [loc for loc in locations if loc.startswith("pulse.")]
        if len(locations) > 1:
            # Same URL twice inside one item's source list is an error;
            # across different items it is a warning (two items may
            # legitimately lean on one long article, but usually it means
            # the same story got split in two).
            containers = {loc.rsplit(".sources[", 1)[0] for loc in locations}
            if len(containers) < len(locations):
                rep.error(
                    "sources",
                    f"{url} is listed twice in the same sources array "
                    f"({', '.join(locations)})",
                )
            if len(containers) > 1 and len(item_locs) > 1:
                rep.warn(
                    "sources",
                    f"{url} is cited by more than one item ({', '.join(sorted(containers))}); "
                    "check these are not the same story written twice",
                )


# --------------------------------------------------------------------------
# File-level driver
# --------------------------------------------------------------------------


def validate_file(path: str) -> Report:
    rep = Report(path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        rep.error("<file>", f"cannot read: {exc}")
        return rep

    if not raw.strip():
        rep.error("<file>", "is empty")
        return rep

    try:
        brief = json.loads(raw)
    except json.JSONDecodeError as exc:
        rep.error(
            "<file>",
            f"is not valid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}",
        )
        return rep

    if not isinstance(brief, dict):
        rep.error("<file>", f"top level must be a JSON object, got {typename(brief)}")
        return rep

    if not raw.endswith("\n"):
        rep.warn("<file>", "does not end with a newline")

    seen_urls: dict[str, list[str]] = {}
    edition_date = check_top_level(rep, brief, path)
    check_pulse(rep, brief, edition_date, seen_urls)
    check_foundations(rep, brief, seen_urls)
    check_cross_item_sources(rep, seen_urls)
    return rep


def collect_paths(inputs: list[str]) -> tuple[list[str], list[str]]:
    """Expand files/dirs into a sorted list of brief paths. Returns (paths, problems)."""
    paths: list[str] = []
    problems: list[str] = []
    for raw in inputs:
        if os.path.isdir(raw):
            found = sorted(
                os.path.join(raw, name)
                for name in os.listdir(raw)
                if name.endswith(".json") and name != "index.json"
            )
            if not found:
                problems.append(f"{raw}: directory contains no brief JSON files")
            paths.extend(found)
        elif os.path.isfile(raw):
            paths.append(raw)
        else:
            problems.append(f"{raw}: no such file or directory")
    # de-dupe, keep order
    seen = set()
    unique = []
    for p in paths:
        rp = os.path.abspath(p)
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    return unique, problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_brief.py",
        description="Validate ai-stack-brief edition JSON against SPEC.md.",
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
        help="treat warnings as errors (used by the daily job before it commits)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="only print files that have problems",
    )
    args = parser.parse_args(argv)

    paths, problems = collect_paths(args.paths)
    for problem in problems:
        print(f"ERROR  {problem}", file=sys.stderr)
    if not paths:
        if not problems:
            print("ERROR  nothing to validate", file=sys.stderr)
        return 2

    reports = [validate_file(p) for p in paths]

    failed = 0
    total_errors = total_warnings = 0
    for rep in reports:
        total_errors += len(rep.errors)
        total_warnings += len(rep.warnings)
        bad = bool(rep.errors) or (args.strict and rep.warnings)
        if bad:
            failed += 1
        if bad or not args.quiet:
            print(rep.render(args.strict))

    print()
    verb = "errors" if not args.strict else "errors (warnings promoted by --strict)"
    print(
        f"{len(reports)} file(s) checked — {total_errors} {verb}, "
        f"{total_warnings} warning(s), {failed} file(s) failing"
    )
    if problems:
        return 2
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
