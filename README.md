# ai-stack-brief

**A daily 10-minute briefing on the AI hardware stack, written for the
Minnesota Nanofabrication Club (GopherFab) at the University of Minnesota.**

**Live site → <https://minnesota-nanofabrication-club.github.io/ai-stack-brief/>**

<!-- SCREENSHOT: replace this comment with a screenshot of the reading app on a
     phone, light and dark side by side. Save it as docs/screenshot.png and use:
     ![The reading app on a phone](docs/screenshot.png) -->

> _Screenshot goes here._

---

## What this is

Every morning a research agent reads the last week of the AI-infrastructure world,
writes one edition, and publishes it. An edition has two halves, and it is designed
so you can read the whole thing in ten minutes between classes.

**1. The Pulse (~5 min)** — what actually happened in the last ~7 days, organized
by Jensen Huang's five-layer AI cake:

| Layer | What lands here |
| --- | --- |
| **Energy** | Grid interconnects, PPAs, transformers, substations, cooling, water, siting |
| **Chips** | Process nodes, litho, etch/depo, metrology, packaging, HBM, fab capex, equipment, EDA |
| **Infrastructure** | Racks, networking and optics, storage, datacenter buildouts, clouds, supply chain |
| **Models** | Frontier and open-weight releases, training/inference research, evals, post-training |
| **Applications** | Deployed AI doing something real: science, medicine, robotics, chip design, coding |

`chips` is the home layer. It gets the most items and the deepest treatment. A layer
with nothing genuinely newsworthy that day is left out entirely rather than padded.

**2. Foundations (~5 min)** — one piece of *existing* technology explained properly.
Usually semiconductor process, fab, or packaging. Not news. The "cool tech I should
already know about" half. It rotates daily through a backlog of topics.

Everything is written twice, in one page: the top tier so a sophomore EE or matsci
student follows it with no background, and an expandable **go deeper** block on every
item with the dense numbers, the mechanism, the caveats, and the primary sources.

## How to read it

- Open <https://minnesota-nanofabrication-club.github.io/ai-stack-brief/>. It works on
  a phone; most people read it that way.
- Skim the headline and the deks. That is the five-minute pass.
- Expand **go deeper** on anything you actually care about.
- Every item carries a `confidence` marker — **confirmed**, **reported**, or
  **rumored**. Trust them; they are set deliberately.
- Every claim has sources. At least one of them is a primary or specialist-technical
  source: the paper, the filing, the transcript, the standard, the whitepaper, the
  teardown — not just somebody's write-up of a press release.
- Older editions are in the archive, driven by `briefs/index.json`.

## Where it gets delivered

The same JSON feeds two surfaces:

- **The website** (GitHub Pages) is canonical — both tiers, the archive, the deep dive.
- **The club Discord** gets a short version posted automatically after each edition
  publishes: the headline, then per-layer item titles with their one-line deks and a
  source link, then the Foundations topic, all linking back to the site. Setup for the
  webhook lives in **[docs/DISCORD.md](docs/DISCORD.md)**; the code is
  `scripts/post_discord.py` and `.github/workflows/discord.yml`. Discord is optional —
  if the webhook secret is not set, the site still publishes normally.

---

## The two halves of the repo

```
site/       the reading app        plain HTML/CSS/JS, no build step, no CDNs
briefs/     the content            one JSON per edition + a generated index
research/   the agent's brain      the prompts the daily run follows
scripts/    the tooling            validate, build the index, preview locally
docs/       operator docs          Discord webhook setup
SPEC.md     the contract           schema, layout, and rules — read this first
```

**`SPEC.md` is the contract.** Field names, directory layout, the five layer slugs,
the sizing rules, and the eight non-negotiables all live there. If you are about to
change how a brief is shaped, change `SPEC.md` first and everything else after.

---

## Run it locally

You need `git` and Python 3.9+. Nothing else — no npm, no pip, no build step.

```sh
git clone https://github.com/Minnesota-Nanofabrication-Club/ai-stack-brief.git
cd ai-stack-brief
python3 scripts/serve.py
```

Then open <http://localhost:8000/>.

`serve.py` composes the site exactly the way GitHub Pages will — `site/` at the root
with `briefs/` mounted at `/briefs/` — without copying anything into your working
tree, so `git status` stays clean.

```sh
python3 scripts/serve.py --port 8080     # if 8000 is taken
python3 scripts/serve.py --open          # open a browser too
python3 scripts/serve.py --host 0.0.0.0  # then open it on your phone over wifi
```

### The other two scripts

```sh
# Validate one edition, several, or the whole directory
python3 scripts/validate_brief.py briefs/2026-08-20.json
python3 scripts/validate_brief.py briefs/

# Treat warnings as errors — this is what the daily job runs before it commits
python3 scripts/validate_brief.py --strict briefs/2026-08-20.json

# Rebuild briefs/index.json from briefs/*.json
python3 scripts/build_index.py

# Fail (exit 1) if the committed index is stale — this is what CI runs
python3 scripts/build_index.py --check
```

The validator prints every problem it finds, not just the first, and each line names
the exact field path (`pulse.layers[1].items[0].sources[2].url`). **ERROR** means the
file violates `SPEC.md` and must not ship. **WARN** means it probably reads badly —
prose that has drifted far from the word targets, a `why_it_matters` that just
restates its `dek`, an item with no primary source, the same URL cited by two items.

`build_index.py` validates every brief before it will write the index, and refuses to
write an index that would advertise a broken edition. Its output is deterministic —
sorted keys, stable formatting — and it leaves `generated_at` alone when nothing else
changed, so a no-op rebuild produces an empty diff.

---

## How the daily job works

`.github/workflows/daily-brief.yml`, once a day:

1. **Fires at 12:00 UTC.** GitHub cron is UTC and never shifts for daylight saving,
   so that is **7:00 AM Central during CDT** (mid-March to early November) and
   **6:00 AM Central during CST** (early November to mid-March). GitHub also queues
   scheduled jobs under load, so treat it as "7am-ish".
2. **Runs Claude Code** (`anthropics/claude-code-action@v1`) with web search, pointed
   at `research/DAILY_BRIEF.md`. That file is the master prompt; the workflow only
   supplies the date, the news window, and the output path.
3. **Validates, hard.** `validate_brief.py --strict` on the new file. If the edition
   does not pass, the job fails and nothing is committed. A missing day is better than
   a broken one.
4. **Rebuilds `briefs/index.json`** and re-validates the whole archive.
5. **Commits and pushes** `briefs/YYYY-MM-DD.json` plus the index, then triggers the
   Pages deploy directly. (It has to call the deploy rather than rely on the push: a
   push made with the built-in `GITHUB_TOKEN` does not start another workflow.)
6. **If anything fails**, it opens a GitHub issue labelled `daily-brief-failure` — or
   comments on the existing open one — so the failure is visible instead of silent.
   The issue closes itself the next time a run succeeds. This exists because a sibling
   repo's sync job died quietly and nobody noticed for weeks.

### Running it by hand

**Actions → Daily brief → Run workflow.** The `date` input is optional; leave it blank
for today, or set it to `YYYY-MM-DD` to backfill a day that was missed. The workflow
has concurrency control, so a manual run and the cron cannot collide.

### What it costs

Two separate bills.

**GitHub Actions minutes.** Free on public repositories. On a private repo the daily
run is on the order of 10–30 minutes of a Linux runner per day.

**Anthropic API tokens.** This is the real cost. The workflow pins
`--model claude-opus-5` ($5 per million input tokens, $25 per million output). A
research run does a lot of web searching and fetching, and every turn resends the
growing context, so **budget roughly $5–15 per run — call it $150–450 a month** and
treat that as an estimate, not a quote.

**Check the real number after the first week** on the
[Anthropic Console usage page](https://console.anthropic.com/settings/usage) rather
than trusting the range above. Levers if it is too high, in the order worth trying:

- Lower `--max-turns` in `claude_args` (currently 150). Most of the cost is turns.
- Switch `--model` to `claude-sonnet-5` ($3 / $15 per million).
- Tighten `research/DAILY_BRIEF.md` so the agent searches less and decides sooner.
- Set a monthly spend limit in the Console so a runaway loop cannot surprise you.

---

## One-time setup (repo admin only)

**None of this can be done from the repository.** A human with admin rights has to
click through it in the GitHub web UI. Do all four steps before expecting the first
edition to appear.

### 1. Add the Anthropic API key — required

1. Get a key at <https://console.anthropic.com/settings/keys>. Make a key dedicated to
   this repo so you can revoke it without breaking anything else.
2. In this repo: **Settings → Secrets and variables → Actions → New repository secret**.
3. Name it exactly `ANTHROPIC_API_KEY`. Paste the key as the value. Save.

The name matters — `daily-brief.yml` reads `secrets.ANTHROPIC_API_KEY`. Without it the
Claude step fails on every run.

### 2. Add the Discord webhook — optional

1. Follow **[docs/DISCORD.md](docs/DISCORD.md)** to create the channel webhook.
2. Same place: **Settings → Secrets and variables → Actions → New repository secret**.
3. Name it exactly `DISCORD_WEBHOOK_URL`.

Skip this and everything else still works; the Discord post is just quietly skipped.

### 3. Turn on GitHub Pages — required

1. **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub Actions**. Not "Deploy
   from a branch" — the deploy workflow builds a composed tree (`site/` plus `briefs/`
   copied into `site/briefs/`) that does not exist as a branch anywhere.
3. Save. The first successful `Deploy Pages` run publishes to
   <https://minnesota-nanofabrication-club.github.io/ai-stack-brief/>.

If the repo is private, Pages needs a GitHub Team or Enterprise plan. On the free plan
the repo has to be public for the site to be reachable.

### 4. Check Actions permissions — required

**Settings → Actions → General**:

- **Actions permissions**: allow actions and reusable workflows. If the org restricts
  this to selected actions, `anthropics/claude-code-action`, `actions/checkout`,
  `actions/configure-pages`, `actions/upload-pages-artifact`, and
  `actions/deploy-pages` all need to be on the allowlist.
- **Workflow permissions**: **Read repository contents and packages permissions** is
  fine. Each workflow declares the extra scopes it needs at the top of its own file;
  you do not need to loosen the default. What you *do* need is the checkbox **"Allow
  GitHub Actions to create and approve pull requests"** left as-is (the job does not
  open PRs) and nothing blocking `contents: write`.
- If a **branch protection rule** or a **ruleset** covers `main`, add an exception for
  `github-actions[bot]`, or the daily commit will be rejected on push.

### 5. Sanity check

Trigger **Actions → Daily brief → Run workflow** and watch it. If it goes green and
the site updates, you are done. If it fails, the run log names the step, and an issue
labelled `daily-brief-failure` will be waiting for you.

> **Note on scheduled workflows.** GitHub disables cron schedules on a public
> repository after 60 days with no repository activity. This repo commits daily, so
> that clock never runs out — but if the job is broken for two months it will not
> restart itself. Fix the failure issue.

---

## Everyday tasks

### Add a Foundations topic to the backlog

The daily run picks tomorrow's Foundations topic off the top of
`research/FOUNDATIONS_BACKLOG.md`. To add one:

1. Open `research/FOUNDATIONS_BACKLOG.md`.
2. Add an entry in the same shape as the ones already there. It needs a **topic** (the
   human title, e.g. "Chemical mechanical planarization") and a kebab-case **slug**
   (e.g. `cmp`). The slug ends up in the published JSON as `foundations.slug`, so keep
   it short, lowercase, and hyphenated.
3. Put it where you want it in the queue — order in the file is the order it runs.
4. Open a pull request. CI will run the validator. Merge it.

Good candidates: something you can see or touch in the Nano Center, something with a
real mechanism to explain, something a sophomore has heard the name of but could not
draw. Bad candidates: news, roadmaps, and anything you would have to guess at.

### Correct a published brief

Editions are committed JSON files. Fix them like code — never by editing the live
site, which is regenerated on every deploy.

1. Branch, and edit `briefs/YYYY-MM-DD.json` directly.
2. Fix the content. If you are correcting a fact, also check that `confidence` is
   still honest and that the source you are citing actually says the new thing.
3. Validate before you push:

   ```sh
   python3 scripts/validate_brief.py --strict briefs/YYYY-MM-DD.json
   python3 scripts/build_index.py
   ```

   Run `build_index.py` whenever you change a `headline`, the item count, which layers
   appear, or `foundations.topic` / `foundations.slug` — all of those are mirrored into
   `briefs/index.json`. **Never hand-edit `briefs/index.json`**; CI checks it against
   what the script would generate and fails if they differ.
4. Open a pull request so someone else reads the correction. Merge. The Pages deploy
   runs automatically on push to `main` when `briefs/` changes.

If an edition is badly wrong rather than slightly wrong, correct it in place and say
so in the item — `SPEC.md` rule 1 is that a short honest edition beats a padded one,
and the same applies to a corrected one.

### Delete an edition

Delete the JSON file, run `python3 scripts/build_index.py`, commit both. The archive
and the site follow automatically.

---

## CI

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `daily-brief.yml` | 12:00 UTC daily, or by hand | Research, validate, commit, deploy |
| `pages.yml` | push to `main` touching `site/` or `briefs/`, or called | Compose `site/` + `briefs/` and deploy to Pages |
| `validate.yml` | every PR and push to `main` | Schema check on every brief + index freshness |
| `discord.yml` | after `Daily brief` completes | Post the edition to the club Discord |

`validate.yml` is the one that will fail your pull request. It runs the validator over
every brief and `build_index.py --check`, so a hand-edited or stale index is caught
before it reaches the site.

---

## Contributing

Read `SPEC.md`. Then, depending on what you are changing:

- **Content policy** (what counts as a source, what the quality bar is) —
  `research/SOURCES.md` and `research/QUALITY.md`.
- **What the daily agent does** — `research/DAILY_BRIEF.md`.
- **The reading app** — `site/`. No CDNs, no npm, no build step, system fonts only,
  dark and light both work, mobile first. Those are rules, not preferences.
- **The schema** — `SPEC.md` first, then `scripts/validate_brief.py`, then everything
  that reads the JSON.

Questions: ask in the club Discord.
