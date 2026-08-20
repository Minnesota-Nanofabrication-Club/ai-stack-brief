#!/usr/bin/env python3
"""Post one edition of the GopherFab Brief to a Discord channel via webhook.

Discord gets the member tier only — headline, per-layer item titles and deks, the
Foundations topic — with links back to the site for the deeper tier. See the
"Delivery surfaces" section of SPEC.md.

Standard library only: this runs in a bare CI container with no pip install step.

Usage:
    python3 scripts/post_discord.py --dry-run
    python3 scripts/post_discord.py --brief briefs/2026-08-20.json
    DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/... python3 scripts/post_discord.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# --- Discord API limits -----------------------------------------------------
# Verified 2026-08-20 against https://docs.discord.com/developers/resources/message
# ("Embed Limits") and the webhook execute endpoint docs.
MAX_CONTENT_CHARS = 2000       # message `content`
MAX_EMBEDS_PER_MESSAGE = 10    # embeds array length on webhook execute
MAX_EMBED_TITLE = 256
MAX_EMBED_DESCRIPTION = 4096
MAX_EMBED_FIELDS = 25
MAX_FIELD_NAME = 256
MAX_FIELD_VALUE = 1024
MAX_EMBED_FOOTER = 2048
# Combined cap across every embed's title, description, field names/values,
# footer text and author name in a single message.
MAX_EMBED_TOTAL_CHARS = 6000

# Webhook execute is roughly 30 requests / 60s per webhook, and 5 / 5s per channel.
# We post a handful of messages a day, so a fixed spacing is plenty.
POST_SPACING_SECONDS = 1.0
MAX_RETRIES_ON_429 = 5

DEFAULT_SITE_URL = "https://minnesota-nanofabrication-club.github.io/ai-stack-brief/"

REPO_ROOT = Path(__file__).resolve().parent.parent
BRIEFS_DIR = REPO_ROOT / "briefs"

# Layer order is bottom-of-cake to top, matching SPEC.md and the site.
LAYER_ORDER = ["energy", "chips", "infrastructure", "models", "applications"]
LAYER_META = {
    # The embed's left stripe. These sit between the site's light-theme accents
    # (site/style.css :root) and its dark-theme ones, so a layer is recognizably the
    # same color in Discord whichever theme the reader has set there.
    "energy":         {"name": "Energy",         "color": 0xB8842A},
    "chips":          {"name": "Chips",          "color": 0xB25060},
    "infrastructure": {"name": "Infrastructure", "color": 0x4B88AF},
    "models":         {"name": "Models",         "color": 0x7A6EC0},
    "applications":   {"name": "Applications",   "color": 0x43906E},
}
FOUNDATIONS_COLOR = 0x6E6259

CONFIDENCE_MARK = {"confirmed": "", "reported": " · reported", "rumored": " · rumored"}


class PostError(Exception):
    """Anything that should end the run with a readable message, not a traceback."""


# --- text handling ----------------------------------------------------------

_MENTION_PATTERNS = [
    (re.compile(r"@everyone", re.IGNORECASE), "@​everyone"),
    (re.compile(r"@here", re.IGNORECASE), "@​here"),
    (re.compile(r"<@"), "<​@"),   # user and role mentions
    (re.compile(r"<#"), "<​#"),   # channel mentions
]


def defang(text: str) -> str:
    """Neutralize anything in brief text that could ping the channel.

    allowed_mentions already suppresses pings server-side; this keeps the raw text
    from *looking* like a mass ping in the client, which is the part people react to.
    """
    for pattern, replacement in _MENTION_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def to_discord_markdown(text: str) -> str:
    """Convert the brief's restrained markdown subset to what Discord renders.

    Discord handles **bold**, *italic*, `code` and [text](url) inside embeds natively.
    Headings and images don't belong in a one-line dek, so they're flattened.
    """
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)  # headings
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)       # images -> alt text
    text = re.sub(r"[ \t]*\n[ \t]*", " ", text.strip())          # collapse to one flow
    text = re.sub(r"\s{2,}", " ", text)
    return defang(text)


def truncate(text: str, limit: int, more_url: str | None = None) -> str:
    """Cut at a word boundary, leaving room for the ellipsis and an optional link."""
    suffix = f"… [more]({more_url})" if more_url else "…"
    if len(text) <= limit:
        return text
    room = limit - len(suffix)
    if room <= 0:
        return text[:limit]
    cut = text[:room]
    space = cut.rfind(" ")
    if space > room * 0.6:
        cut = cut[:space]
    return cut.rstrip(" ,.;:—-") + suffix


def embed_char_count(embed: dict) -> int:
    """Characters that count toward Discord's 6000-per-message embed budget."""
    total = len(embed.get("title", "")) + len(embed.get("description", ""))
    total += len(embed.get("footer", {}).get("text", ""))
    total += len(embed.get("author", {}).get("name", ""))
    for field in embed.get("fields", []):
        total += len(field.get("name", "")) + len(field.get("value", ""))
    return total


# --- rendering --------------------------------------------------------------

def edition_url(site_url: str, date: str, anchor: str = "") -> str:
    base = site_url if site_url.endswith("/") else site_url + "/"
    return f"{base}#{date}" + (f"/{anchor}" if anchor else "")


def render_header(brief: dict, site_url: str) -> str:
    date = brief["date"]
    pretty = dt.date.fromisoformat(date).strftime("%A, %B %-d, %Y")
    headline = to_discord_markdown(brief.get("headline", ""))
    pulse_items = sum(len(l.get("items", [])) for l in brief["pulse"]["layers"])
    topic = brief["foundations"]["topic"]

    lines = [
        f"## GopherFab Brief — {pretty}",
        "",
        f"**{headline}**",
        "",
        f"{pulse_items} items across the stack, plus a deep dive on **{topic}**. "
        f"Full brief, with the technical tier and sources: {edition_url(site_url, date)}",
    ]
    return truncate("\n".join(lines), MAX_CONTENT_CHARS)


def render_item_field(item: dict, site_url: str, date: str) -> dict:
    title = truncate(to_discord_markdown(item["title"]), MAX_FIELD_NAME)
    title += CONFIDENCE_MARK.get(item.get("confidence", "confirmed"), "")

    dek = to_discord_markdown(item["dek"])
    source_line = ""
    sources = item.get("sources") or []
    if sources:
        src = sources[0]
        label = to_discord_markdown(src.get("publisher") or src.get("title") or "source")
        label = truncate(label, 60)
        source_line = f"\n[{label}]({src['url']})"
        if len(sources) > 1:
            source_line += f" +{len(sources) - 1} more"

    deep_link = f" · [go deeper]({edition_url(site_url, date, item['id'])})"
    room = MAX_FIELD_VALUE - len(source_line) - len(deep_link)
    value = truncate(dek, room) + source_line + deep_link
    return {"name": truncate(title, MAX_FIELD_NAME), "value": value, "inline": False}


def render_layer_embed(layer: dict, site_url: str, date: str) -> dict:
    meta = LAYER_META[layer["layer"]]
    items = layer["items"]
    fields = [render_item_field(i, site_url, date) for i in items[:MAX_EMBED_FIELDS]]
    return {
        "title": meta["name"],
        "color": meta["color"],
        "fields": fields,
    }


def render_foundations_embed(brief: dict, site_url: str) -> dict:
    f = brief["foundations"]
    date = brief["date"]
    url = edition_url(site_url, date, "foundations")

    parts = [f"*{to_discord_markdown(f['subtitle'])}*", "", to_discord_markdown(f["tldr"])]
    if f.get("try_this"):
        parts += ["", f"**Try this:** {to_discord_markdown(f['try_this'])}"]
    parts += ["", f"[Read the full explainer]({url})"]
    description = truncate("\n".join(parts), MAX_EMBED_DESCRIPTION, more_url=url)

    return {
        "title": truncate(f"Foundations — {f['topic']}", MAX_EMBED_TITLE),
        "url": url,
        "color": FOUNDATIONS_COLOR,
        "description": description,
        "footer": {"text": truncate(
            "Existing technology worth knowing, not news.", MAX_EMBED_FOOTER)},
    }


def build_payloads(brief: dict, site_url: str) -> list[dict]:
    """One header message, then embeds packed into messages within Discord's caps."""
    date = brief["date"]
    payloads: list[dict] = [{"content": render_header(brief, site_url)}]

    embeds: list[dict] = []
    by_slug = {l["layer"]: l for l in brief["pulse"]["layers"]}
    for slug in LAYER_ORDER:
        layer = by_slug.get(slug)
        if layer and layer.get("items"):
            embeds.append(render_layer_embed(layer, site_url, date))
    embeds.append(render_foundations_embed(brief, site_url))

    batch: list[dict] = []
    batch_chars = 0
    for embed in embeds:
        size = embed_char_count(embed)
        over_total = batch_chars + size > MAX_EMBED_TOTAL_CHARS
        over_count = len(batch) + 1 > MAX_EMBEDS_PER_MESSAGE
        if batch and (over_total or over_count):
            payloads.append({"embeds": batch})
            batch, batch_chars = [], 0
        batch.append(embed)
        batch_chars += size
    if batch:
        payloads.append({"embeds": batch})

    for payload in payloads:
        payload["allowed_mentions"] = {"parse": []}
    return payloads


# --- validation -------------------------------------------------------------

def check_payload(payload: dict, index: int) -> None:
    content = payload.get("content", "")
    if len(content) > MAX_CONTENT_CHARS:
        raise PostError(
            f"payload {index}: content is {len(content)} chars, over the "
            f"{MAX_CONTENT_CHARS} limit")

    embeds = payload.get("embeds", [])
    if len(embeds) > MAX_EMBEDS_PER_MESSAGE:
        raise PostError(
            f"payload {index}: {len(embeds)} embeds, over the "
            f"{MAX_EMBEDS_PER_MESSAGE} limit")

    total = 0
    for e_i, embed in enumerate(embeds):
        total += embed_char_count(embed)
        if len(embed.get("title", "")) > MAX_EMBED_TITLE:
            raise PostError(f"payload {index} embed {e_i}: title too long")
        if len(embed.get("description", "")) > MAX_EMBED_DESCRIPTION:
            raise PostError(f"payload {index} embed {e_i}: description too long")
        fields = embed.get("fields", [])
        if len(fields) > MAX_EMBED_FIELDS:
            raise PostError(f"payload {index} embed {e_i}: too many fields")
        for f_i, field in enumerate(fields):
            if len(field["name"]) > MAX_FIELD_NAME:
                raise PostError(f"payload {index} embed {e_i} field {f_i}: name too long")
            if len(field["value"]) > MAX_FIELD_VALUE:
                raise PostError(f"payload {index} embed {e_i} field {f_i}: value too long")
    if total > MAX_EMBED_TOTAL_CHARS:
        raise PostError(
            f"payload {index}: embeds total {total} chars, over the "
            f"{MAX_EMBED_TOTAL_CHARS} limit")


# --- posting ----------------------------------------------------------------

def post(webhook: str, payload: dict, index: int) -> None:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        webhook,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "gopherfab-brief (+https://github.com/Minnesota-Nanofabrication-Club/ai-stack-brief)",
        },
        method="POST",
    )

    for attempt in range(1, MAX_RETRIES_ON_429 + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if 200 <= response.status < 300:
                    return
                raise PostError(f"message {index}: Discord returned {response.status}")
        except urllib.error.HTTPError as err:
            if err.code == 429:
                retry_after = 1.0
                try:
                    retry_after = float(json.loads(err.read()).get("retry_after", 1.0))
                except (ValueError, json.JSONDecodeError):
                    header = err.headers.get("Retry-After")
                    if header:
                        retry_after = float(header)
                if attempt == MAX_RETRIES_ON_429:
                    raise PostError(
                        f"message {index}: still rate limited after "
                        f"{MAX_RETRIES_ON_429} attempts") from err
                print(f"  rate limited, waiting {retry_after:.1f}s", file=sys.stderr)
                time.sleep(retry_after + 0.25)
                continue
            if err.code == 404:
                raise PostError(
                    "Discord returned 404 — the webhook has been deleted or the URL is "
                    "wrong. Regenerate it in the channel's Integrations settings and "
                    "update the DISCORD_WEBHOOK_URL secret.") from err
            if err.code == 401:
                raise PostError("Discord returned 401 — the webhook token is invalid.") from err
            detail = ""
            try:
                detail = f" — {err.read().decode('utf-8', 'replace')[:400]}"
            except OSError:
                pass
            raise PostError(f"message {index}: Discord returned {err.code}{detail}") from err
        except urllib.error.URLError as err:
            raise PostError(f"message {index}: could not reach Discord — {err.reason}") from err


# --- entry point ------------------------------------------------------------

def resolve_brief(explicit: str | None, date: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise PostError(f"no brief at {path}")
        return path
    if date:
        path = BRIEFS_DIR / f"{date}.json"
        if not path.exists():
            raise PostError(f"no brief for {date} (looked for {path})")
        return path
    if not BRIEFS_DIR.exists():
        raise PostError(f"no briefs directory at {BRIEFS_DIR}")
    today = BRIEFS_DIR / f"{dt.date.today().isoformat()}.json"
    if today.exists():
        return today
    editions = sorted(p for p in BRIEFS_DIR.glob("*.json") if p.name != "index.json")
    if not editions:
        raise PostError("no editions in briefs/ — has the daily job run yet?")
    return editions[-1]


def load_brief(path: Path) -> dict:
    try:
        brief = json.loads(path.read_text())
    except json.JSONDecodeError as err:
        raise PostError(f"{path} is not valid JSON: {err}") from err
    for key in ("date", "headline", "pulse", "foundations"):
        if key not in brief:
            raise PostError(f"{path} is missing required field '{key}'")
    if "layers" not in brief.get("pulse", {}):
        raise PostError(f"{path} has no pulse.layers")
    for layer in brief["pulse"]["layers"]:
        if layer.get("layer") not in LAYER_META:
            raise PostError(f"{path} has unknown layer slug '{layer.get('layer')}'")
    return brief


def main() -> int:
    parser = argparse.ArgumentParser(description="Post a brief to Discord.")
    parser.add_argument("--brief", help="path to a brief JSON (default: today's, else latest)")
    parser.add_argument("--date", help="edition date YYYY-MM-DD, resolved inside briefs/")
    parser.add_argument("--webhook", help="webhook URL (default: $DISCORD_WEBHOOK_URL)")
    parser.add_argument("--site-url", default=DEFAULT_SITE_URL, help="base URL of the site")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the payloads that would be posted, and post nothing")
    args = parser.parse_args()

    try:
        path = resolve_brief(args.brief, args.date)
        brief = load_brief(path)
        payloads = build_payloads(brief, args.site_url)
        for i, payload in enumerate(payloads):
            check_payload(payload, i)

        if args.dry_run:
            print(f"# {len(payloads)} message(s) from {path}\n")
            for i, payload in enumerate(payloads):
                embeds = payload.get("embeds", [])
                chars = sum(embed_char_count(e) for e in embeds)
                print(f"--- message {i + 1}: {len(embeds)} embed(s), "
                      f"{chars} embed chars, {len(payload.get('content', ''))} content chars")
                print(json.dumps(payload, indent=2, ensure_ascii=False))
                print()
            return 0

        webhook = args.webhook or os.environ.get("DISCORD_WEBHOOK_URL")
        if not webhook:
            raise PostError(
                "no webhook configured. Set DISCORD_WEBHOOK_URL or pass --webhook. "
                "See docs/DISCORD.md.")
        if not webhook.startswith("https://"):
            raise PostError("the webhook URL must be an https:// URL")

        for i, payload in enumerate(payloads):
            post(webhook, payload, i)
            print(f"posted message {i + 1}/{len(payloads)}")
            if i < len(payloads) - 1:
                time.sleep(POST_SPACING_SECONDS)
        print(f"posted {path.name} to Discord")
        return 0

    except PostError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
