#!/usr/bin/env python3
"""Post one edition of the MNF Brief to a Discord channel via webhook.

Discord is the delivery surface for this project. GitHub Pages is off; `site/` is
still in the repo and still readable locally with `python3 scripts/serve.py`, but it
has no public URL, so a member cannot click through to anything. **Whatever this
script does not post is unread.** That single fact decides the whole design below.

So an edition goes out complete: for every Pulse item its background, dek, why it
matters, fab angle, technical tier, glossary *with the definitions*, confidence and
full source list; then all of Foundations — tl;dr, every section with its deeper
tier, the glossary, try this, and the sources. On the 2026-08-20 edition that is
about 69,000 characters of brief against a 6,000-character-per-message budget, so
the edition is a sequence of messages, not one clever message.

Three consequences worth stating up front, because they look like mistakes:

1. **No embed fields.** A field value caps at 1024 characters and a single
   `deeper_md` runs to ~1,230, so fields cannot carry this content at all. Text goes
   in message `content` (2,000) and embed `description` (4,096) instead.
2. **Nothing is ever truncated.** Long prose is *split* at paragraph, then sentence,
   then word boundaries, never mid-word, and `check_coverage` re-reads the finished
   payloads and refuses to post if any field of the brief failed to appear in them.
   A hard Discord limit that genuinely cannot be routed around is logged loudly to
   stderr; it is never absorbed silently.
3. **Threading is best-effort, and the limit is Discord's, not ours.** See the
   THREADING note below.

Standard library only: this runs in a bare CI container with no pip install step.

Usage:
    python3 scripts/post_discord.py --dry-run
    python3 scripts/post_discord.py --brief briefs/2026-08-20.json
    DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/... python3 scripts/post_discord.py
    python3 scripts/post_discord.py --thread          # forum/media channels only
    python3 scripts/post_discord.py --thread-id 1234  # post into an existing thread

THREADING, and what a plain incoming webhook can actually do
------------------------------------------------------------
This repo holds one credential, `DISCORD_WEBHOOK_URL`. There is no bot token, and a
webhook is not a bot: it can execute into a channel and nothing else. Given that:

* **Forum or media channel — a real thread, no bot needed.** Webhook execute accepts
  `thread_name` in the body, which opens a new forum post and puts the message in
  it. Adding `?wait=true` makes Discord return the created message, whose
  `channel_id` *is* the new thread; every later message is then posted with
  `?thread_id=<that id>`. That is what `--thread` does, and it is the setup worth
  having: one forum post per edition, roughly twenty messages inside it, and a
  channel that lists editions by date instead of an endless scroll.
* **Existing thread, any channel type.** `?thread_id=` posts into a thread that
  already exists, so if someone (or another automation) makes the thread, `--thread-id`
  fills it. Threads in a text channel auto-archive, so this is a manual-run tool
  rather than something the daily workflow can rely on.
* **Ordinary text channel, creating the thread ourselves — not possible.** Starting a
  thread on a message is `POST /channels/{channel_id}/messages/{message_id}/threads`,
  which needs a bot token with CREATE_PUBLIC_THREADS; `thread_name` on webhook
  execute is rejected outside forum/media channels. This script does not pretend
  otherwise: it fails with an explanation rather than inventing an endpoint.

The fallback — plain ordered messages in the channel — is the default and is fine.
Every item leads with a coloured embed carrying the layer name and the item title,
so the sequence reads as a brief even without a thread wrapped round it.
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
import urllib.parse
import urllib.request
from pathlib import Path
from typing import NamedTuple

# --- Discord API limits -----------------------------------------------------
# Verified 2026-08-20 against https://docs.discord.com/developers/resources/message
# ("Embed Limits") and the webhook execute endpoint docs.
MAX_CONTENT_CHARS = 2000       # message `content`
MAX_EMBEDS_PER_MESSAGE = 10    # embeds array length on webhook execute
MAX_EMBED_TITLE = 256
MAX_EMBED_DESCRIPTION = 4096
MAX_EMBED_AUTHOR = 256
MAX_EMBED_FOOTER = 2048
MAX_EMBED_FIELDS = 25          # unused by this renderer; check_payload still guards it
MAX_FIELD_NAME = 256
MAX_FIELD_VALUE = 1024
MAX_THREAD_NAME = 100
# Combined cap across every embed's title, description, field names/values,
# footer text and author name in a single message.
MAX_EMBED_TOTAL_CHARS = 6000

# Our own chunk size, not Discord's, and it is set for readability because it turns
# out not to buy anything else. The intuition is that smaller chunks pack the 6,000
# characters of a message more tightly and so need fewer messages; measured on the
# 2026-08-20 edition (74k characters delivered) that is worth almost nothing —
# 1,500 and 2,000 give 16 messages, everything from 2,500 to 4,000 gives 17 — because
# the count is driven by total volume, not by packing waste. What the chunk size does
# change is how often an item is cut in half: 1,500 produces 71 embeds, 4,000
# produces 36. So take the largest value that still leaves headroom under the 4,096
# description cap for the fence-balancing case in split_markdown.
CHUNK_CHARS = 4000

# Webhook execute is roughly 30 requests / 60s per webhook, and 5 / 5s per channel.
# A full edition is now ~15 messages rather than 3, which puts us close enough to the
# per-channel bucket that exactly 1.0s was tempting fate; 1.25s keeps a 20-message
# edition comfortably under both buckets and still delivers in under half a minute.
POST_SPACING_SECONDS = 1.25
MAX_RETRIES_ON_429 = 5

REPO_ROOT = Path(__file__).resolve().parent.parent
BRIEFS_DIR = REPO_ROOT / "briefs"

# Layer order is bottom-of-cake to top, matching SPEC.md and site/app.js. Seven, not
# five: `silicon` (the physics and the process) and `computing` (computer science
# that is not an AI model) were added because the club's work does not fit inside
# "AI". Keep this list and site/app.js's LAYERS in the same order — the Discord post
# and the local site should read the same way down the stack.
LAYER_ORDER = [
    "energy",
    "silicon",
    "chips",
    "computing",
    "infrastructure",
    "models",
    "applications",
]
LAYER_META = {
    # `color` is the embed's left stripe. These sit between the site's light-theme
    # accents (site/style.css :root) and its dark-theme ones, so a layer is
    # recognizably the same colour in Discord whichever theme the reader has set
    # there. The two new ones follow the same construction: silicon is the midpoint
    # of #456d14/#99c464 (moss), computing of #7e1e7c/#cf6fcb (plum). Those hues were
    # picked to sit in the palette's only wide gaps, so no stripe is within ~45° of
    # another.
    #
    # `scope` is the same line the site prints under each layer heading. It is worth
    # the ~80 characters a day: Discord readers no longer have a page to consult, and
    # the scope line is what tells someone why a story about an amplifier is filed
    # under Silicon rather than Chips.
    "energy": {
        "name": "Energy", "color": 0xB8842A,
        "scope": "Generation, grid, power delivery, cooling",
    },
    "silicon": {
        "name": "Silicon", "color": 0x6F983C,
        "scope": "Device physics, materials, litho, process, packaging, analog and RF",
    },
    "chips": {
        "name": "Chips", "color": 0xB25060,
        "scope": "Accelerators, memory, interconnect, digital EDA, foundry capacity",
    },
    "computing": {
        "name": "Computing", "color": 0xA646A3,
        "scope": "Languages, compilers, systems, databases, security, architecture research",
    },
    "infrastructure": {
        "name": "Infrastructure", "color": 0x4B88AF,
        "scope": "Racks, optics, datacenters, clouds, supply chain",
    },
    "models": {
        "name": "Models", "color": 0x7A6EC0,
        "scope": "Releases, training, architectures, evals",
    },
    "applications": {
        "name": "Applications", "color": 0x43906E,
        "scope": "Technology deployed in the world, doing something",
    },
}
FOUNDATIONS_COLOR = 0x6E6259

# Spelled out rather than implied. The site can afford a coloured chip with a
# tooltip; here the reader gets one line of text and no hover, so "confirmed" says
# so explicitly instead of being signalled by the absence of a marker.
CONFIDENCE_NOTE = {
    "confirmed": "Confirmed — on the record from a primary source.",
    "reported": "Reported — credible reporting, not primary-confirmed.",
    "rumored": "Rumored — single-sourced or unconfirmed. Treat as weak.",
}


class PostError(Exception):
    """Anything that should end the run with a readable message, not a traceback."""


class Block(NamedTuple):
    """One logical unit of the edition, before it is cut to fit Discord.

    A block is written as though length were no object — an item's whole body, a
    Foundations section with its deeper tier — and `blocks_to_embeds` is the only
    place that worries about limits. Keeping the two apart is what makes it possible
    to promise that nothing is dropped: the renderer never has to decide what to cut,
    because it never cuts.
    """
    body: str
    color: int
    title: str = ""     # embed title, first chunk only
    author: str = ""    # embed author line, first chunk only (the layer name)
    label: str = ""     # short name repeated on continuation chunks
    footer: str = ""    # embed footer, last chunk only (the confidence note)


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


def to_discord_inline(text: str) -> str:
    """Flatten to a single line. For titles and other one-line metadata only.

    Discord handles **bold**, *italic*, `code` and [text](url) natively. Headings and
    images don't belong in an embed title, so they're stripped.
    """
    text = re.sub(r"^#{1,6}\s*", "", str(text), flags=re.MULTILINE)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[ \t]*\n[ \t]*", " ", text.strip())
    text = re.sub(r"\s{2,}", " ", text)
    return defang(text)


def to_discord_block(text: str) -> str:
    """Convert a markdown *body* to what Discord renders, keeping its shape.

    The old one-line flattener was right when Discord only ever carried a dek. It is
    wrong now: `deeper_md` and the Foundations sections are multi-paragraph prose with
    bullet lists, and collapsing their newlines would run the whole thing into one
    grey wall. So paragraphs, list markers and line breaks survive; only the things
    Discord cannot render are touched.

    Headings become `###` — Discord does render `#` in embeds, but at a size that
    shouts louder than the item's own title and breaks the visual hierarchy of the
    post. Images become their alt text, since an embed description cannot show one.
    """
    text = str(text).replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)        # images -> alt text
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "### ", text, flags=re.MULTILINE)
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)      # trailing spaces
    text = re.sub(r"\n{3,}", "\n\n", text)                       # collapse blank runs
    return defang(text.strip())


def truncate(text: str, limit: int) -> str:
    """Cut at a word boundary. **Metadata only** — never call this on brief prose.

    Titles, author lines, footers and thread names have hard caps that no amount of
    splitting can route around, and they are labels rather than content. Everything
    that carries meaning goes through split_markdown instead, which preserves all of
    it. If a title ever does get cut, render_item_block puts the full text back into
    the body so the words still reach the reader.
    """
    if len(text) <= limit:
        return text
    room = limit - 1
    cut = text[:room]
    space = cut.rfind(" ")
    if space > room * 0.6:
        cut = cut[:space]
    return cut.rstrip(" ,.;:—-") + "…"


_SENTENCE_BREAK = re.compile(r"(?<=[.!?…])\s+")


def _paragraphs(text: str) -> list[str]:
    """Blank-line-separated paragraphs, with fenced code blocks kept whole.

    Splitting inside a ``` fence would leave one chunk with an unclosed fence and the
    next starting mid-code, which Discord renders as garbage. Tracking fence parity
    while walking the paragraphs costs ten lines and keeps any code block that fits in
    an embed intact. A fence too long to fit at all is still split — see the warning
    in split_markdown — because the alternative is not posting it.
    """
    out: list[str] = []
    pending: list[str] = []
    in_fence = False
    for para in re.split(r"\n\s*\n", text):
        pending.append(para)
        if para.count("```") % 2:
            in_fence = not in_fence
        if not in_fence:
            out.append("\n\n".join(pending))
            pending = []
    if pending:
        out.append("\n\n".join(pending))
    return [p for p in out if p.strip()]


def _pack(pieces: list[str], joiner: str, limit: int) -> list[str]:
    """Greedily join pieces in order, never exceeding the limit. Order is preserved,
    so the result is deterministic: the same brief always splits the same way."""
    out: list[str] = []
    current = ""
    for piece in pieces:
        candidate = piece if not current else current + joiner + piece
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                out.append(current)
            current = piece
    if current:
        out.append(current)
    return out


def split_markdown(text: str, limit: int, where: str) -> list[str]:
    """Cut prose into chunks of at most `limit` characters, losing nothing.

    Four levels, each tried only when the one above leaves something too long:
    paragraphs, then lines (so a list is broken between bullets), then sentences,
    then words. A single word longer than the whole limit is the one case with no
    honest answer — that gets hard-cut and shouted about on stderr, because it means
    the brief contains a 3,000-character "word" and somebody should look at it.

    `where` is a human-readable location used only in that warning.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= limit:
        return [text]

    # Aim for equal chunks rather than greedy-full ones. A 4,700-character item split
    # at a 4,000 limit reads as a wall followed by a 700-character orphan; split at
    # 2,350 it reads as two halves. The target is only an aim — if packing to it
    # happens to need an extra chunk (a paragraph longer than the target), fall back
    # to the real limit rather than paying a whole extra message for tidiness.
    balanced = -(-len(text) // limit)                # ceil: chunks we cannot avoid
    target = max(-(-len(text) // balanced), 1)
    chunks = _pack(_paragraphs(text), "\n\n", target)
    if len(chunks) > balanced or any(len(c) > limit for c in chunks):
        chunks = _pack(_paragraphs(text), "\n\n", limit)

    for joiner, splitter in (("\n", lambda s: s.split("\n")),
                             (" ", lambda s: _SENTENCE_BREAK.split(s)),
                             (" ", lambda s: s.split(" "))):
        if all(len(c) <= limit for c in chunks):
            break
        rebuilt: list[str] = []
        for chunk in chunks:
            if len(chunk) <= limit:
                rebuilt.append(chunk)
            else:
                rebuilt.extend(_pack(splitter(chunk), joiner, limit))
        chunks = rebuilt

    # A fenced block bigger than one embed is the one case _paragraphs cannot keep
    # whole, and the result is a chunk with an unclosed ```. Balancing it by injecting
    # a closing fence would be prettier, but the injected characters would land in the
    # middle of a field and check_coverage — which relies on each field arriving
    # contiguous — would then report a phantom loss. Nothing is dropped either way, so
    # this warns and leaves the text alone rather than trading a real guarantee for a
    # cosmetic one. It needs a >4,000-character code block in a brief to fire at all.
    for chunk in chunks:
        if chunk.count("```") % 2:
            print(f"warning: {where}: a fenced code block is longer than the "
                  f"{limit}-character embed limit and had to be split across embeds, so "
                  f"one of them will render with an unclosed fence. Shorten the block.",
                  file=sys.stderr)
            break

    final: list[str] = []
    for chunk in chunks:
        while len(chunk) > limit:
            print(f"warning: {where}: {len(chunk)} characters with no word break inside "
                  f"the {limit}-character embed limit — splitting mid-token. Check the "
                  f"brief for an unbroken URL or table.", file=sys.stderr)
            final.append(chunk[:limit])
            chunk = chunk[limit:]
        if chunk:
            final.append(chunk)
    return final


# --- rendering --------------------------------------------------------------

def edition_url(site_url: str, date: str, anchor: str = "") -> str:
    base = site_url if site_url.endswith("/") else site_url + "/"
    return f"{base}#{date}" + (f"/{anchor}" if anchor else "")


def render_sources(sources: list, label: str = "Sources") -> str:
    """A numbered source list. Markdown links, so Discord suppresses the link
    previews that a bare URL would unfurl into — twenty unfurled previews would be
    longer than the brief."""
    lines = []
    for source in sources or []:
        if not isinstance(source, dict):
            continue
        title = to_discord_inline(source.get("title") or source.get("url") or "Untitled source")
        url = source.get("url")
        entry = f"[{title}]({url})" if url else title
        trail = ", ".join(x for x in (source.get("publisher"), source.get("date")) if x)
        if trail:
            entry += f" — {to_discord_inline(trail)}"
        lines.append(entry)
    if not lines:
        return ""
    numbered = "\n".join(f"{i}. {line}" for i, line in enumerate(lines, 1))
    return f"**{label}**\n{numbered}"


def render_glossary(entries: list, label: str = "Terms") -> str:
    """Terms *with* their definitions. The definitions are the reason the field
    exists — a bare list of jargon would tell a reader they are out of their depth
    without doing anything about it, and there is no longer a site to look them up
    on."""
    lines = []
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        term = to_discord_inline(entry.get("term") or "").strip()
        definition = to_discord_inline(entry.get("definition") or "").strip()
        if not term and not definition:
            continue
        if term and definition:
            lines.append(f"**{term}** — {definition}")
        else:
            # Half an entry is malformed input, but half an entry delivered is still
            # better than a line reading "**** something" or a silently dropped term.
            lines.append(f"**{term}**" if term else definition)
    return f"**{label}**\n" + "\n".join(lines) if lines else ""


def render_header(brief: dict, site_url: str | None, threaded: bool) -> list[str]:
    """The opening message. Returns a list of content chunks — normally one.

    It is a list rather than a string because a header long enough to overflow 2,000
    characters must split, not truncate: the headline is the one line most likely to
    be read at all, and quietly clipping it would be the worst possible place to lose
    words.
    """
    date = brief["date"]
    pretty = dt.date.fromisoformat(date).strftime("%A, %B %-d, %Y")
    headline = to_discord_inline(brief.get("headline", ""))
    layers = brief["pulse"]["layers"]
    pulse_items = sum(len(l.get("items", [])) for l in layers)
    named = [LAYER_META[l["layer"]]["name"] for l in layers if l.get("items")]
    topic = to_discord_inline(brief["foundations"]["topic"])

    minutes = 0
    for section in (brief.get("pulse"), brief.get("foundations")):
        try:
            minutes += int(section.get("read_time_min") or 0)
        except (TypeError, ValueError):
            pass

    lines = [f"## MNF Brief — {pretty}", ""]
    if brief.get("window"):
        lines += [f"News window {to_discord_inline(brief['window'])}", ""]
    lines += [f"**{headline}**", ""]

    tail = f"{pulse_items} items — {', '.join(named)} — plus a deep dive on **{topic}**."
    if minutes:
        tail += f" About {minutes} minutes to read."
    lines.append(tail)
    lines.append(
        "The complete edition follows in this thread: every item in full, then Foundations."
        if threaded else
        "The complete edition follows below: every item in full, then Foundations.")
    if site_url:
        lines += ["", f"Also readable at {edition_url(site_url, date)}"]

    return split_markdown("\n".join(lines), MAX_CONTENT_CHARS, "header")


def render_item_block(item: dict, slug: str) -> Block:
    """One Pulse item, whole. Same order the site renders it in, so a member who
    reads both surfaces is never re-learning the layout: background first (it is the
    footing for everything after it), then the news, then why it matters, then the
    fab angle, the technical tier, the terms, and the sources."""
    meta = LAYER_META[slug]
    title = to_discord_inline(item.get("title") or "Untitled")

    parts: list[str] = []
    # A title over 256 characters cannot go in the embed title. Rather than lose the
    # tail of it, the full text is repeated as the first line of the body.
    if len(title) > MAX_EMBED_TITLE:
        parts.append(f"**{title}**")
    if item.get("background_md"):
        parts.append("**Before the news**\n" + to_discord_block(item["background_md"]))
    if item.get("dek"):
        parts.append(to_discord_block(item["dek"]))
    if item.get("why_it_matters"):
        parts.append("**Why it matters**\n" + to_discord_block(item["why_it_matters"]))
    if item.get("fab_angle"):
        parts.append("**Fab angle**\n" + to_discord_block(item["fab_angle"]))
    if item.get("deeper_md"):
        parts.append("**Go deeper**\n" + to_discord_block(item["deeper_md"]))
    glossary = render_glossary(item.get("glossary"))
    if glossary:
        parts.append(glossary)
    sources = render_sources(item.get("sources"))
    if sources:
        parts.append(sources)

    confidence = str(item.get("confidence") or "").lower()
    note = CONFIDENCE_NOTE.get(confidence, CONFIDENCE_NOTE["reported"])

    return Block(
        body="\n\n".join(parts),
        color=meta["color"],
        title=truncate(title, MAX_EMBED_TITLE),
        author=meta["name"],
        label=title,
        footer=truncate(note, MAX_EMBED_FOOTER),
    )


def render_pulse_blocks(brief: dict) -> list[Block]:
    blocks: list[Block] = []
    by_slug = {l["layer"]: l for l in brief["pulse"]["layers"]}
    for slug in LAYER_ORDER:
        layer = by_slug.get(slug)
        if not layer or not layer.get("items"):
            continue          # a layer with nothing today is omitted, never padded
        meta = LAYER_META[slug]
        blocks.append(Block(
            body=f"*{meta['scope']}*",
            color=meta["color"],
            title=meta["name"].upper(),
        ))
        for item in layer["items"]:
            blocks.append(render_item_block(item, slug))
    return blocks


def render_foundations_blocks(brief: dict) -> list[Block]:
    f = brief["foundations"]
    blocks: list[Block] = []

    opening = []
    if f.get("subtitle"):
        opening.append(f"*{to_discord_inline(f['subtitle'])}*")
    if f.get("tldr"):
        opening.append("**The whole idea**\n" + to_discord_block(f["tldr"]))
    opening.append("*Existing technology worth knowing, not news.*")
    blocks.append(Block(
        body="\n\n".join(opening),
        color=FOUNDATIONS_COLOR,
        title=truncate(f"Foundations — {to_discord_inline(f['topic'])}", MAX_EMBED_TITLE),
        author="Part two",
        label=to_discord_inline(f["topic"]),
    ))

    for i, section in enumerate(f.get("sections") or [], 1):
        parts = []
        if section.get("body_md"):
            parts.append(to_discord_block(section["body_md"]))
        if section.get("deeper_md"):
            parts.append("**Go deeper**\n" + to_discord_block(section["deeper_md"]))
        heading = to_discord_inline(section.get("heading") or f"Section {i}")
        blocks.append(Block(
            body="\n\n".join(parts),
            color=FOUNDATIONS_COLOR,
            title=truncate(f"{i}. {heading}", MAX_EMBED_TITLE),
            label=heading,
        ))

    glossary = render_glossary(f.get("glossary"), label="Glossary")
    if glossary:
        blocks.append(Block(body=glossary, color=FOUNDATIONS_COLOR,
                            title="Glossary", label="Glossary"))
    if f.get("try_this"):
        blocks.append(Block(body=to_discord_block(f["try_this"]), color=FOUNDATIONS_COLOR,
                            title="Try this", label="Try this"))
    sources = render_sources(f.get("sources"), label="Foundations sources")
    if sources:
        blocks.append(Block(body=sources, color=FOUNDATIONS_COLOR,
                            title="Foundations sources", label="Foundations sources"))
    return blocks


def blocks_to_embeds(blocks: list[Block]) -> list[dict]:
    """Cut each block to fit an embed description, in order.

    A block that needs more than one embed keeps its title on the first and gets an
    author line naming the item on every continuation, because chunks of one item can
    land in different messages a second apart and an untitled wall of text arriving
    on its own is disorienting.
    """
    embeds: list[dict] = []
    for block in blocks:
        chunks = split_markdown(block.body, CHUNK_CHARS, block.label or block.title or "block")
        if not chunks:
            chunks = [""]
        for i, chunk in enumerate(chunks):
            embed: dict = {"color": block.color}
            if chunk:
                embed["description"] = chunk
            if i == 0:
                if block.title:
                    embed["title"] = block.title
                if block.author:
                    embed["author"] = {"name": truncate(block.author, MAX_EMBED_AUTHOR)}
            elif block.label:
                embed["author"] = {"name": truncate(block.label + " (continued)", MAX_EMBED_AUTHOR)}
            if block.footer and i == len(chunks) - 1:
                embed["footer"] = {"text": block.footer}
            embeds.append(embed)
    return embeds


def embed_char_count(embed: dict) -> int:
    """Characters that count toward Discord's 6000-per-message embed budget."""
    total = len(embed.get("title", "")) + len(embed.get("description", ""))
    total += len(embed.get("footer", {}).get("text", ""))
    total += len(embed.get("author", {}).get("name", ""))
    for field in embed.get("fields", []):
        total += len(field.get("name", "")) + len(field.get("value", ""))
    return total


def build_payloads(brief: dict, site_url: str | None = None,
                   threaded: bool = False) -> list[dict]:
    """The header message, then every block packed into messages within the caps."""
    payloads: list[dict] = [{"content": chunk}
                            for chunk in render_header(brief, site_url, threaded)]

    embeds = blocks_to_embeds(render_pulse_blocks(brief) + render_foundations_blocks(brief))

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
    if len(payload.get("thread_name", "")) > MAX_THREAD_NAME:
        raise PostError(f"payload {index}: thread_name over {MAX_THREAD_NAME} chars")

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
        if len(embed.get("author", {}).get("name", "")) > MAX_EMBED_AUTHOR:
            raise PostError(f"payload {index} embed {e_i}: author name too long")
        if len(embed.get("footer", {}).get("text", "")) > MAX_EMBED_FOOTER:
            raise PostError(f"payload {index} embed {e_i}: footer too long")
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


def _squash(text: str) -> str:
    """Whitespace-free form, for comparing rendered text against its source.

    Splitting replaces a paragraph break with a message boundary, so the delivered
    text differs from the source by exactly the whitespace at the seams. Removing all
    whitespace from both sides makes the comparison indifferent to where the cuts
    fell while still catching a genuinely missing sentence.
    """
    return re.sub(r"\s+", "", text)


def check_coverage(brief: dict, payloads: list[dict]) -> None:
    """Refuse to post an edition that is not all there.

    This is the enforcement half of "never silently drop content". Every field the
    reader is owed is rendered exactly as the payload builder would render it, then
    looked for in the flattened text of the finished payloads. If a future edit to
    the packing, splitting or truncation logic starts eating prose, the run fails
    with the SPEC-style location of what went missing instead of posting a brief with
    a hole in it. It costs a few milliseconds and it is the only reason the promise
    in the module docstring is worth anything.
    """
    # Everything that will actually reach a reader, in one string. Message and embed
    # boundaries are deliberately erased: a paragraph split across two messages is
    # still delivered, and the whole point of the check is to find text that reaches
    # nobody at all.
    delivered = _squash("".join(
        [p.get("content", "") for p in payloads] +
        [e.get("title", "") + e.get("description", "") +
         e.get("author", {}).get("name", "") + e.get("footer", {}).get("text", "")
         for p in payloads for e in p.get("embeds", [])]
    ))

    missing: list[str] = []

    def want(text: str, where: str) -> None:
        needle = _squash(text)
        if needle and needle not in delivered:
            missing.append(where)

    want(to_discord_inline(brief.get("headline", "")), "headline")

    by_slug = {l["layer"]: l for l in brief["pulse"]["layers"]}
    for slug in LAYER_ORDER:
        layer = by_slug.get(slug)
        if not layer or not layer.get("items"):
            continue
        li = brief["pulse"]["layers"].index(layer)
        for ii, item in enumerate(layer["items"]):
            at = f"pulse.layers[{li}].items[{ii}]"
            want(to_discord_inline(item.get("title", "")), f"{at}.title")
            for field in ("background_md", "dek", "why_it_matters", "fab_angle", "deeper_md"):
                if item.get(field):
                    want(to_discord_block(item[field]), f"{at}.{field}")
            for gi, entry in enumerate(item.get("glossary") or []):
                if isinstance(entry, dict):
                    want(to_discord_inline(entry.get("term", "")), f"{at}.glossary[{gi}].term")
                    want(to_discord_inline(entry.get("definition", "")),
                         f"{at}.glossary[{gi}].definition")
            for si, source in enumerate(item.get("sources") or []):
                if isinstance(source, dict):
                    want(to_discord_inline(source.get("title", "")), f"{at}.sources[{si}].title")
                    want(source.get("url", ""), f"{at}.sources[{si}].url")
            want(CONFIDENCE_NOTE.get(str(item.get("confidence", "")).lower(),
                                     CONFIDENCE_NOTE["reported"]), f"{at}.confidence")

    f = brief["foundations"]
    for field in ("topic", "subtitle"):
        if f.get(field):
            want(to_discord_inline(f[field]), f"foundations.{field}")
    for field in ("tldr", "try_this"):
        if f.get(field):
            want(to_discord_block(f[field]), f"foundations.{field}")
    for si, section in enumerate(f.get("sections") or []):
        at = f"foundations.sections[{si}]"
        if section.get("heading"):
            want(to_discord_inline(section["heading"]), f"{at}.heading")
        for field in ("body_md", "deeper_md"):
            if section.get(field):
                want(to_discord_block(section[field]), f"{at}.{field}")
    for gi, entry in enumerate(f.get("glossary") or []):
        if isinstance(entry, dict):
            want(to_discord_inline(entry.get("term", "")), f"foundations.glossary[{gi}].term")
            want(to_discord_inline(entry.get("definition", "")),
                 f"foundations.glossary[{gi}].definition")
    for si, source in enumerate(f.get("sources") or []):
        if isinstance(source, dict):
            want(to_discord_inline(source.get("title", "")), f"foundations.sources[{si}].title")
            want(source.get("url", ""), f"foundations.sources[{si}].url")

    if missing:
        listed = "\n  ".join(missing[:20])
        more = f"\n  …and {len(missing) - 20} more" if len(missing) > 20 else ""
        raise PostError(
            f"{len(missing)} field(s) of the brief did not survive into the payloads. "
            f"Discord is the only delivery surface, so this is a bug in the renderer, "
            f"not something to post around:\n  {listed}{more}")


# --- posting ----------------------------------------------------------------

def webhook_with(webhook: str, params: dict) -> str:
    """Add query parameters without clobbering any the URL already carries."""
    parts = urllib.parse.urlsplit(webhook)
    query = dict(urllib.parse.parse_qsl(parts.query))
    query.update({k: v for k, v in params.items() if v})
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))


def post(webhook: str, payload: dict, index: int, want_json: bool = False) -> dict | None:
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
                    if not want_json:
                        return None
                    try:
                        return json.loads(response.read().decode("utf-8"))
                    except (ValueError, json.JSONDecodeError) as err:
                        raise PostError(
                            f"message {index}: Discord accepted the post but returned no "
                            f"readable message object, so the thread id is unknown") from err
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
            if err.code == 400 and "thread_name" in payload:
                raise PostError(
                    "Discord rejected the thread. `thread_name` on a webhook only works in a "
                    "forum or media channel; in an ordinary text channel, starting a thread "
                    "needs a bot token, which this repo does not have. Either move the "
                    "webhook to a forum channel, pass --thread-id for a thread that already "
                    f"exists, or drop --thread and post a plain sequence.{detail}") from err
            raise PostError(f"message {index}: Discord returned {err.code}{detail}") from err
        except urllib.error.URLError as err:
            raise PostError(f"message {index}: could not reach Discord — {err.reason}") from err
    return None


def deliver(webhook: str, payloads: list[dict], thread_name: str | None,
            thread_id: str | None) -> None:
    """Post every message in order, keeping them together in a thread if we can."""
    for i, payload in enumerate(payloads):
        body = dict(payload)
        params: dict[str, str] = {}
        if i == 0 and thread_name:
            # Creating the thread and posting the header are the same request; ?wait=true
            # is what makes Discord hand back the message, and with it the id of the
            # thread every following message has to be addressed to.
            body["thread_name"] = thread_name
            params["wait"] = "true"
        elif thread_id:
            params["thread_id"] = thread_id

        created = post(webhook_with(webhook, params), body, i, want_json=bool(params.get("wait")))

        if i == 0 and thread_name:
            thread_id = str((created or {}).get("channel_id") or "")
            if not thread_id:
                raise PostError(
                    "the thread was created but Discord did not return its channel id, so "
                    "the rest of the edition has nowhere to go. Re-run with --thread-id "
                    "pointing at the thread that was just created, or without --thread.")
            print(f"created thread {thread_id}")

        print(f"posted message {i + 1}/{len(payloads)}")
        if i < len(payloads) - 1:
            time.sleep(POST_SPACING_SECONDS)


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
    parser = argparse.ArgumentParser(description="Post a brief to Discord, in full.")
    parser.add_argument("--brief", help="path to a brief JSON (default: today's, else latest)")
    parser.add_argument("--date", help="edition date YYYY-MM-DD, resolved inside briefs/")
    parser.add_argument("--webhook", help="webhook URL (default: $DISCORD_WEBHOOK_URL)")
    # No default any more. Pages is off and the site has no public URL, so a default
    # would print a link that 404s on every item, every day. Pass it only if you have
    # actually published the site somewhere.
    parser.add_argument("--site-url", default=None,
                        help="optional: a URL where the site is published, linked from the header")
    parser.add_argument("--thread", action="store_true",
                        help="open a forum thread for this edition (forum/media channels only)")
    parser.add_argument("--thread-name",
                        help="name for the thread created by --thread (default: the date)")
    parser.add_argument("--thread-id",
                        help="post into an existing thread by id, in any channel type")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the payloads that would be posted, and post nothing")
    args = parser.parse_args()

    try:
        if (args.thread or args.thread_name) and args.thread_id:
            raise PostError("--thread/--thread-name create a new thread and --thread-id "
                            "posts into an existing one; pick one")

        path = resolve_brief(args.brief, args.date)
        brief = load_brief(path)

        thread_name = None
        if args.thread or args.thread_name:
            default_name = f"MNF Brief — {dt.date.fromisoformat(brief['date']).strftime('%B %-d, %Y')}"
            thread_name = truncate(to_discord_inline(args.thread_name or default_name),
                                   MAX_THREAD_NAME)

        payloads = build_payloads(brief, args.site_url,
                                  threaded=bool(thread_name or args.thread_id))
        for i, payload in enumerate(payloads):
            check_payload(payload, i)
        check_coverage(brief, payloads)

        if args.dry_run:
            sizes = []
            for i, payload in enumerate(payloads):
                embeds = payload.get("embeds", [])
                sizes.append((sum(embed_char_count(e) for e in embeds),
                              len(payload.get("content", "")), len(embeds)))
            print(f"# {len(payloads)} message(s) from {path}")
            if thread_name:
                print(f"# thread: creating \"{thread_name}\" on message 1 (?wait=true), "
                      f"then ?thread_id=<new id> on the rest")
            elif args.thread_id:
                print(f"# thread: posting every message with ?thread_id={args.thread_id}")
            else:
                print("# thread: none — a plain ordered sequence in the channel")
            worst = max(sizes, key=lambda s: s[0] + s[1])
            print(f"# largest message: {worst[0]} embed chars (limit {MAX_EMBED_TOTAL_CHARS}), "
                  f"{worst[1]} content chars (limit {MAX_CONTENT_CHARS})")
            print(f"# total delivered: {sum(s[0] + s[1] for s in sizes)} chars, "
                  f"{sum(s[2] for s in sizes)} embeds")
            print("# coverage: every field of every item and all of Foundations verified "
                  "present\n")
            for i, payload in enumerate(payloads):
                print(f"--- message {i + 1}: {sizes[i][2]} embed(s), "
                      f"{sizes[i][0]} embed chars, {sizes[i][1]} content chars")
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

        deliver(webhook, payloads, thread_name, args.thread_id)
        print(f"posted {path.name} to Discord in {len(payloads)} messages")
        return 0

    except PostError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
