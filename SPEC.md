# ai-stack-brief — project spec (shared contract)

**Read this before writing any file in this repo.** Every part of the system — the
reading app, the research prompts, the CI job, the daily content — agrees on the data
contract defined here. Do not invent alternative field names or directory layouts.

## What this is

A daily briefing app for the **Minnesota Nanofabrication Club (MNF)** at the
University of Minnesota. It publishes one edition per day in two halves:

1. **The Pulse** — what actually happened in the last ~7 days, organized by the seven
   layers below, bottom to top: Energy → Silicon → Chips → Computing → Infrastructure
   → Models → Applications. This is the "what's going on in the world" half.
2. **Foundations** (~5 min) — one piece of *existing* technology, usually semiconductor
   process / fab / packaging, explained properly. Not news. The "cool tech I should
   already know about" half. Rotates daily through a backlog.

**How long it takes to read.** About **10 minutes** if the territory is already
familiar — the Pulse's news prose and the Foundations member tier come to roughly
1,100 words each. Nearer **15 minutes** if you also read every item's `background_md`,
and longer again if you open the deeper blocks. That is the intended shape, not a
failure to hit a target: a reader who already knows what a threshold voltage is skips
the background and is done in ten, and a reader who does not gets the footing instead
of bouncing off. Do not compress the backgrounds to defend a ten-minute number.

This is not a news aggregator. The point is that a curious engineer **learns something
technical** from every edition. An item that tells you a thing happened but leaves you
no better able to explain how it works has failed, however newsworthy it was.

The audience is **two-tier in one page**: every item is written so a sophomore EE or
matsci student understands it, and every item carries an expandable "go deeper" block
with the dense numbers and primary sources for the club's technical core.

## The seven layers (fixed vocabulary)

Use these exact slugs in data files. Do not add, rename, or reorder layers.

The taxonomy started as Jensen Huang's five-layer AI cake and outgrew it. The cake has
nowhere to put computer science that is not an AI model, and nowhere to put device,
process and analog/RF work that is not about AI accelerators — which is most of what
this club actually does. Two layers were added, `silicon` under `chips` and `computing`
above it. The whole value of the vocabulary is that **a story has exactly one obvious
home**, so keep the scope lines crisp.

Listed bottom to top. This is also the publication order.

| slug | name | scope |
| --- | --- | --- |
| `energy` | Energy | Generation, grid interconnection, power delivery, cooling and thermal. What it takes to feed and cool the rest of the stack. |
| `silicon` | Silicon | How devices and circuits are physically made and how they physically work: device physics, materials, transistors, lithography, deposition, etch, CMP, doping, metrology, yield and test, packaging, MEMS, and analog / RF / mixed-signal circuit design. AI involvement is irrelevant here — this layer is about the physics and the process. |
| `chips` | Chips | The digital products built out of silicon and the industry that makes them: accelerators, memory, interconnect and I/O, chip roadmaps and shipments, digital EDA, foundry capacity and tooling. |
| `computing` | Computing | Computer science that is not an AI model: programming languages, compilers, operating systems, distributed systems, databases, storage, security and cryptography, formal methods, algorithms and complexity, and computer-architecture *research*. If it is a chip product it belongs in `chips`; if it is an idea about how to compute it belongs here. |
| `infrastructure` | Infrastructure | Datacenters, network fabrics, cluster design, cloud capacity, and the buildouts that host large-scale compute. |
| `models` | Models | AI/ML research proper: architectures, training methods, inference techniques, evaluation and interpretability. |
| `applications` | Applications | Technology deployed in the world doing something — AI or otherwise. |

**Boundary cases, decided once so they are not re-argued daily:**

- An analog amplifier design technique → `silicon`, not `chips`.
- A new HBM stack generation → `chips`.
- A hybrid-bonding pitch record → `silicon` (it is a process result).
- A new register-allocation algorithm → `computing`.
- A RISC-V microarchitecture research paper → `computing`.
- A shipping RISC-V product → `chips`.
- A transformer variant → `models`.
- An ML-for-EDA placement paper → `chips` (digital EDA), unless the contribution is
  chiefly an ML method, in which case `models`.

**Layer bias for this club:** `silicon` and `chips` are the home layers. Together they
get the most items and the deepest treatment. A day with three good silicon/chips items
and one item elsewhere is a better edition than five thin items spread evenly.

## Repository layout

```
ai-stack-brief/
├─ SPEC.md                     # this file — the contract
├─ README.md                   # what it is, how to run it, how to set it up
├─ site/                       # the reading app (static, no build step, no CDNs)
│  ├─ index.html
│  ├─ style.css
│  └─ app.js
├─ briefs/                     # one JSON per edition + a generated index
│  ├─ index.json               # generated by scripts/build_index.py — never hand-edit
│  └─ YYYY-MM-DD.json
├─ research/                   # the instructions the daily agents follow
│  ├─ DAILY_BRIEF.md           # master prompt for the daily run
│  ├─ SOURCES.md               # source policy: what counts, what doesn't
│  ├─ QUALITY.md               # the quality bar + worked good/bad examples
│  └─ FOUNDATIONS_BACKLOG.md   # rotating queue of evergreen deep-dive topics
├─ scripts/
│  ├─ build_index.py           # regenerates briefs/index.json from briefs/*.json
│  ├─ validate_brief.py        # validates one brief JSON against the schema below
│  ├─ post_discord.py          # renders a brief into the club Discord channel
│  └─ serve.py                 # local preview server (site/ + briefs/ mounted together)
├─ docs/
│  └─ DISCORD.md               # webhook setup for a club admin
└─ .github/workflows/
   ├─ daily-brief.yml          # cron: run the research agent, commit the new brief
   ├─ discord.yml              # post the new edition to Discord — this is the publication
   └─ validate.yml             # PR check: schema + index freshness
```

## Delivery surface

**Discord is the publication.** There is one surface, and it carries the edition whole:
every item's `background_md`, `glossary` with definitions, `dek`, `why_it_matters`,
`deeper_md`, `fab_angle` and full source list, plus all of `foundations`. Nothing is
held back for somewhere else, because there is no somewhere else — an edition is read
in the channel or it is not read.

This is a deliberate change. The brief was previously published to GitHub Pages with
Discord carrying a teaser that linked to it; Pages has been removed, and
`scripts/post_discord.py` now sequences a complete edition across as many messages as it
takes rather than packing a summary into embed fields.

Consequences for writers, and they are the whole reason this section exists:

- **A `dek` must still stand on its own.** It is read on a phone, in a chat client,
  with the previous item scrolled off the top.
- **Reading order is linear and cannot be skipped around.** There are no anchors and no
  collapsible blocks. `background_md` arrives before the news whether or not the reader
  wanted it, so it has to earn its place in two or three sentences.
- **`deeper_md` cannot hide behind a disclosure triangle.** Everyone sees it. Write it
  so that a reader who stops halfway has still gained something.

**The site is not deleted.** `site/` still renders an edition properly and is served
locally by `python3 scripts/serve.py`, which mounts `site/` at the root and `briefs/`
at `/briefs/`. The app therefore fetches **`./briefs/index.json`** and
**`./briefs/YYYY-MM-DD.json`** — relative, same-origin, no CORS. Restoring
`.github/workflows/pages.yml` is all it would take to publish it again.

## Data contract

### `briefs/YYYY-MM-DD.json`

```jsonc
{
  "date": "2026-08-20",                    // ISO date, America/Chicago, == filename
  "generated_at": "2026-08-20T11:04:00Z",  // ISO 8601 UTC
  "window": "2026-08-13..2026-08-20",      // news window the Pulse covers
  "headline": "One sentence naming the single most consequential thing this week.",
  "pulse": {
    "read_time_min": 8,
    "layers": [
      {
        "layer": "chips",                  // one of the seven slugs above
        "items": [
          {
            "id": "chips-tsmc-a14-risk",   // kebab-case, unique within the edition
            "title": "Short declarative headline, <= 80 chars",
            "dek": "One sentence a sophomore understands, jargon expanded inline.",
            "why_it_matters": "1-2 sentences. Consequence, not restatement.",
            "background_md": "Markdown. The standing context the news sits in: what this area is, what problem it exists to solve, why anyone cares. 50-110 words.",
            "deeper_md": "Markdown. The dense tier: numbers, mechanism, caveats, who disputes it. 80-200 words.",
            "glossary": [ { "term": "V_th", "definition": "..." } ],   // 2-4 entries
            "fab_angle": "Optional. What this means for people who run/build fabs. Omit if forced.",
            "confidence": "confirmed",     // confirmed | reported | rumored
            "sources": [
              { "title": "...", "url": "https://...", "publisher": "...", "date": "2026-08-18" }
            ]
          }
        ]
      }
    ]
  },
  "foundations": {
    "read_time_min": 5,
    "topic": "Chemical mechanical planarization",
    "slug": "cmp",                          // kebab-case, matches FOUNDATIONS_BACKLOG entry
    "subtitle": "How you make a wafer flat enough to print on, by deliberately scratching it.",
    "tldr": "2-3 sentences. The whole idea, no jargon.",
    "sections": [
      {
        "heading": "Why flatness is the whole game",
        "body_md": "Member-tier explanation. 100-180 words.",
        "deeper_md": "Optional dense tier for this section. Numbers, equations, failure modes."
      }
    ],
    "glossary": [ { "term": "Dishing", "definition": "..." } ],
    "try_this": "Something a MNF member could actually do, see, or read this week.",
    "sources": [ { "title": "...", "url": "https://...", "publisher": "...", "date": "2019" } ]
  }
}
```

**Required fields.** Top level: `date`, `generated_at`, `window`, `headline`, `pulse`,
`foundations`. `pulse`: `read_time_min`, `layers`. Item: `id`, `title`, `dek`,
`why_it_matters`, `background_md`, `deeper_md`, `glossary` (2-4), `confidence`,
`sources` (>= 1). Foundations: `read_time_min`, `topic`, `slug`, `subtitle`, `tldr`,
`sections` (>= 3), `glossary` (>= 4), `try_this`, `sources` (>= 3). A section requires
`heading` and `body_md`; `deeper_md` is optional.

### `background_md` — the footing, on every item

Two to four sentences that give a reader who has never heard of this subfield enough to
understand the rest of the item. It answers: what is this area, what problem does it
exist to solve, and why would anyone care?

- **It is not a summary of the news.** It is the standing context the news sits in. If
  you deleted the news, this paragraph would still be true next year.
- Explain the **mechanism**, not an analogy. An analogy in place of a mechanism is a
  dodge — the same rule `QUALITY.md` already applies to `deeper_md`.
- Assume no prior exposure to the subfield. Do assume general engineering literacy: a
  reader who knows what a transistor and a compiler are.
- Do not repeat the `dek`. `background_md` is the world; `dek` is the event.
- Target **50-110 words**. A validator warns outside 45-120.

### `glossary` — 2-4 terms, on every item

Same shape as `foundations.glossary`: objects with `term` and `definition`.

- 2-4 entries. Fewer than two means you did not look hard enough at your own prose;
  more than four means the item is trying to teach too much at once.
- Cover the terms **this item actually uses** and that a newcomer would stumble on —
  including symbols and units (`V_th`, `mV/dec`, `WNS/TNS`), not only words.
- One sentence each, <= 40 words. Mechanism, not restatement: "BEOL — the copper wiring
  stack built above the transistors, which limits everything built later to about
  400 °C" is good; "BEOL — back end of line" is useless.
- No duplicate `term` within an item.
- Expanding an acronym is not a definition on its own. Say what it *is*.

**Inline expansion in the `dek` stays.** These two fields are additive, not a place to
offload the work. The `dek` must still expand jargon inline on first use — the reader
should not have to look down at the glossary to parse a one-sentence summary. In
Discord the glossary is several messages away and cannot be jumped to.

**Source dates.** A source `date` is the publication date at whatever granularity the
source actually has: `YYYY-MM-DD` for news and papers, `YYYY-MM` or a bare `YYYY` for an
undated technical reference or a classic paper. All three forms are valid; a validator
must accept them.

**Source order is editorial.** `sources[0]` is the strongest primary document for the
item, not the first thing you found. It is the one a reader skimming will follow, so a
mis-ordered list sends the club to a press release instead of the filing.

**Layer order.** The `layers` array runs in canonical bottom-to-top order — energy,
silicon, chips, computing, infrastructure, models, applications — with absent layers
simply skipped.

**Word targets have a tolerance.** "Near 1,100 words" means within roughly ±25%. A
validator warns outside that band and never errors on it; an unusually rich or quiet
week legitimately moves the number. Where a target is stated as a range rather than a
number — `background_md`'s 50-110, `deeper_md`'s 80-200 — the validator's warning
threshold sits outside the range, not at its edges, because writing to hit a word count
is how you get padding.

### Choosing `confidence`

| value | when |
| --- | --- |
| `confirmed` | Rests on a primary document (filing, paper, transcript, standard, executed order), or is triangulated across independent outlets that are not all repeating one wire story. |
| `reported` | One credible outlet, or a single-group preprint with no replication. True as far as anyone outside can tell, but not corroborated. |
| `rumored` | Supply-chain chatter, unnamed sources, or a claim whose only support is an interested party. Publishable, but say who benefits from believing it. |

Vendor-reported numbers stay vendor-reported no matter how confident the vendor sounds.

**Continuity across editions.** When a later edition returns to a story it already
covered, the item id takes an `-update` suffix (`chips-amat-cleanroom-constraint-update`)
and the prose says explicitly what changed since the brief last said otherwise.

**Sizing per edition.** 7-13 Pulse items total across the seven layers. **At least one
item across `silicon` and `chips` combined** — either one satisfies it, and in a normal
edition the two together carry the largest share. Seven layers need more room than five
did, which is why the ceiling moved from 11 to 13; padding is still worse than a short
edition, and a layer with nothing genuinely newsworthy is **omitted entirely**, never
filled. Below seven items an edition is incomplete rather than quiet: find a seventh
story worth writing up.

**Word budgets are separate and never pooled.** Each is measured on its own, because
folding a new field into an existing budget turns a useful warning into one that fires
every day and gets ignored:

| budget | what it counts | target |
| --- | --- | --- |
| Pulse news | `dek` + `why_it_matters` across all items | ~1,100 words, ±25% |
| Pulse background | `background_md` across all items | ~80 words × item count; flagged outside 50-110 × item count |
| Foundations member tier | `tldr` + every section `body_md` | ~1,100 words, ±25% |

Everything else — `deeper_md` on items and sections, both glossaries, `fab_angle`,
`subtitle`, `try_this` — sits on top and is uncounted. The background budget scales with
item count because, unlike the news budget, it is not a fixed amount of reading spread
across however many stories there are: every item owes its own paragraph, so a
seven-item edition owes about half what a thirteen-item one does. Its band is the
per-item range multiplied out, so an edition whose every background is inside its own
50-110 target can never trip it; what it catches is systematic drift, eleven backgrounds
that are each "only" 118 words and collectively 1,300.

**`read_time_min` is an estimate of the member tier as written, not a fixed number.**
Compute it at roughly 220 words per minute over everything a member-tier reader reads in
that half, backgrounds included, and round up. For the Pulse that is
`(1,100 + 80 × item_count) / 220`, so a typical edition lands at **7-9**, not the 5 it
was before every item carried a background. Foundations stays at 5. Publishing a 5 when
the half takes nine minutes is the same category of error as an unsourced number: it is
a claim about the product that is not true.

### `briefs/index.json` (generated)

```jsonc
{
  "generated_at": "2026-08-20T11:04:12Z",
  "latest": "2026-08-20",
  "editions": [
    {
      "date": "2026-08-20",
      "headline": "...",
      "foundations_topic": "Chemical mechanical planarization",
      "foundations_slug": "cmp",
      "item_count": 9,
      "layers": ["energy", "chips", "infrastructure", "models", "applications"]
    }
  ]
}
```

`editions` is sorted newest-first.

## Non-negotiable rules

1. **Never invent a fact, a number, or a source.** Every claim in a brief traces to a URL
   in its `sources`. If a number is disputed or unconfirmed, say so and set `confidence`
   accordingly. A short honest edition beats a padded one.
2. **No dead links, and no unread ones.** Every URL must be one the research agent
   actually fetched during that run.
3. **Cite the primary technical source, not the coverage of it.** Trade press is for
   *finding* a story; the item is written from the underlying document — the arXiv or
   IEEE paper, the conference proceeding, the SEC filing, the earnings transcript, the
   patent, the standards document, the vendor whitepaper, the teardown. Every item
   carries **at least one primary or specialist-technical source**. An item resting only
   on press releases and aggregators is upgraded or cut. The reader's stated goal is to
   learn the technical substance, so the citation list is part of the product, not
   decoration.
4. **No filler.** "X announced Y" with no consequence is not an item. If `why_it_matters`
   restates `dek`, cut the item.
5. **No external runtime dependencies in `site/`.** No CDNs, no npm, no build step. Plain
   HTML/CSS/JS that opens from a file server. System font stack only.
6. **Dark and light both work.** Follow `prefers-color-scheme`, plus a manual toggle that
   persists in `localStorage`.
7. **Mobile first.** Most members will read this on a phone between classes.
8. **The club's own work is context, not content.** Per the club's Drive, which is the
   source of truth for what MNF is doing: the program is to *"design, fabricate, and
   demonstrate a custom integrated circuit (IC) through a vertically integrated
   fabrication workflow"* — building the fab (maskless lithography stepper, sputterer,
   tube furnace, spinner, etcher, probe station) **and** designing the IC that runs
   through it. Both halves are the club's work, so `fab_angle` and `try_this` may
   connect to either the process side or the design side. The brief is still about the
   world, not the club.
9. **A financial document is a source, never a subject.** Filings, earnings calls, capex
   disclosures and procurement records are excellent primary evidence — rule 3 actively
   wants them, and the best item in the archive so far is a cleanroom floor-space
   constraint read out of an earnings call. But the item must be *about* a physical or
   engineering constraint, and it must lead with the mechanism. If the most interesting
   sentence you can write is about money rather than about the machine, the physics, or
   the code, it is not an item.

   Never an item, regardless of how well sourced:
   - a share price move, a market cap, a valuation, or an index
   - a funding round, an IPO, or an analyst price target
   - an acquisition or merger reported as a transaction
   - quarterly results reported as results — beats, misses, guidance
   - anything whose consequence is a number on a balance sheet rather than a change in
     what can be built

   **The test:** strike every dollar figure from the item. If nothing technical is left
   standing, cut the item.

   This is judgement, not something a validator can check, so it is on the writer. It
   is also not retroactive — editions already published stay exactly as they were
   published; the rule applies from the day it was written down.
