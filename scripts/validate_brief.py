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

LAYER_SLUGS = ["energy", "chips", "infrastructure", "models", "applications"]
CONFIDENCE_VALUES = ["confirmed", "reported", "rumored"]

REQUIRED_TOP = ["date", "generated_at", "window", "headline", "pulse", "foundations"]
REQUIRED_ITEM = [
    "id",
    "title",
    "dek",
    "why_it_matters",
    "deeper_md",
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
MIN_ITEMS = 5
MAX_ITEMS = 11
MIN_SECTIONS = 3
MIN_GLOSSARY = 4
MIN_FOUNDATIONS_SOURCES = 3

# Soft targets from SPEC.md (warnings only).
SPEC_MIN_ITEMS = 7  # SPEC says 7-11; 5 and 6 are tolerated but flagged
TITLE_MAX_CHARS = 80
PULSE_PROSE_TARGET = 1100  # dek + why_it_matters across all items
FOUNDATIONS_PROSE_TARGET = 1100  # member tier only: tldr + section body_md
PROSE_TOLERANCE = 0.25  # SPEC: "within roughly +/-25%"
DEEPER_MD_RANGE = (80, 200)  # words
SECTION_BODY_RANGE = (100, 180)  # words
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


def check_item(rep: Report, item, where: str, edition_date: str | None,
               seen_urls: dict) -> dict:
    """Validate one Pulse item. Returns collected stats for edition-level checks."""
    stats = {"id": None, "prose_words": 0}

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
    for field in ("dek", "why_it_matters", "deeper_md"):
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
        rep.error("pulse.layers", "is empty; an edition needs at least the chips layer")
        return

    seen_slugs: dict[str, int] = {}
    seen_ids: dict[str, list[str]] = {}
    total_items = 0
    total_prose = 0
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
            stats = check_item(
                rep, item, f"{lwhere}.items[{ii}]", edition_date, seen_urls
            )
            total_prose += stats["prose_words"]
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

    # chips must be present
    if "chips" not in seen_slugs:
        rep.error(
            "pulse.layers",
            "no item in the `chips` layer; SPEC requires at least one "
            "(chips is this club's home layer)",
        )

    # item count
    if total_items < MIN_ITEMS:
        rep.error(
            "pulse",
            f"{total_items} Pulse items; minimum is {MIN_ITEMS}",
        )
    elif total_items > MAX_ITEMS:
        rep.error(
            "pulse",
            f"{total_items} Pulse items; maximum is {MAX_ITEMS}",
        )
    elif total_items < SPEC_MIN_ITEMS:
        rep.warn(
            "pulse",
            f"{total_items} Pulse items; SPEC's stated target is "
            f"{SPEC_MIN_ITEMS}-{MAX_ITEMS} (a short honest edition is allowed, "
            "but check nothing was dropped by accident)",
        )

    # canonical layer order
    canonical = [s for s in LAYER_SLUGS if s in present_order]
    if present_order and present_order != canonical:
        rep.warn(
            "pulse.layers",
            f"layers are ordered {present_order}; SPEC fixes the cake order as "
            f"{canonical} (energy -> chips -> infrastructure -> models -> applications)",
        )

    # total prose budget
    _check_word_budget(
        rep, "pulse", total_prose, PULSE_PROSE_TARGET,
        "dek + why_it_matters across all items (excludes deeper_md)",
    )


def _check_word_budget(rep: Report, where: str, actual: int, target: int,
                       what: str) -> None:
    if actual == 0:
        return
    lo = int(target * (1 - PROSE_TOLERANCE))
    hi = int(target * (1 + PROSE_TOLERANCE))
    if actual < lo:
        rep.warn(
            where,
            f"{what} is {actual} words; SPEC targets ~{target} "
            f"(flagged below {lo}). The 5-minute read claim gets thin.",
        )
    elif actual > hi:
        rep.warn(
            where,
            f"{what} is {actual} words; SPEC targets ~{target} "
            f"(flagged above {hi}). This will not read in 5 minutes.",
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

    # glossary
    glossary = f.get("glossary")
    if "glossary" in f:
        if not isinstance(glossary, list):
            rep.error("foundations.glossary", f"must be an array, got {typename(glossary)}")
        else:
            if len(glossary) < MIN_GLOSSARY:
                rep.error(
                    "foundations.glossary",
                    f"{len(glossary)} entr(y/ies); SPEC requires at least {MIN_GLOSSARY}",
                )
            terms_seen: dict[str, int] = {}
            for i, entry in enumerate(glossary):
                gwhere = f"foundations.glossary[{i}]"
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
                            f"(already at foundations.glossary[{terms_seen[key]}])",
                        )
                    else:
                        terms_seen[key] = i

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
