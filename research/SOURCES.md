# Source policy

What counts as a source for this brief, what each source is good for, how it is biased,
and how to actually search it. Organized by the five layers in `SPEC.md`, with `chips`
given the most depth because it is the home layer.

**The governing principle, from `DAILY_BRIEF.md` §2:** trade press is used to *find* a
story. The item is written from the underlying document. Every published item carries at
least one Tier 1 or Tier 2 source that the agent fetched during that run.

---

## 1. The tier system

| Tier | What it is | How it may be used |
| --- | --- | --- |
| **T1 — Primary** | The thing itself. SEC/TWSE/DART/EDINET filings, earnings transcripts, peer-reviewed papers and preprints, conference proceedings and slide decks, standards documents, patents, regulatory dockets and Federal Register notices, government datasets, first-party technical whitepapers and model cards, court filings. | Always citable. Preferred basis for every claim. A number in the brief should come from here whenever one exists. |
| **T2 — Specialist technical** | People who read T1 for a living and add analysis: SemiAnalysis, Fabricated Knowledge, TechInsights teardowns, Yole, Objective Analysis, Chips and Cheese, The Next Platform, Interconnects, Epoch AI, LBNL/EPRI/IEA analysis, Dell'Oro. Also specialist trade press with real reporting: SemiEngineering, Digitimes, TheElec, Utility Dive, RTO Insider, Data Center Frontier. | Citable. Satisfies the "at least one T1/T2 source" rule. Still check what T1 document they are reading, and go read it too if the claim is load-bearing. |
| **T3 — General and business press** | Reuters, Bloomberg, WSJ, FT, Nikkei Asia, The Information, Ars Technica, Tom's Hardware, TechCrunch, The Register. | Citable as corroboration and for the fact that something was reported. **Never the only source for a technical claim or a number.** |
| **T4 — Aggregators and social** | Hacker News, Reddit, X/Twitter threads, YouTube commentary, Substack roundups with no original reporting, press-release wires (PR Newswire, Business Wire), LinkedIn posts, forum leaks. | **Discovery only.** Use to find leads. Not a citation. |

**The T4 rule.** An item whose evidence rests only on T4 sources is either killed or
published with `confidence: "rumored"` and prose that says plainly that it is a rumor,
who is claiming it, and what document would settle it. It never gets a `confirmed` or
`reported` value, and it never gets a number stated as fact.

**Two outlets are one source if they share an origin.** Two write-ups of the same press
release, or two summaries of the same Digitimes report, count once. Before marking
anything `confirmed` on the strength of "multiple outlets," trace each back to its origin.

---

## 2. Blocklist — never the sole basis for a claim

These are not "low quality" sources to be used carefully. They are sources that may not
carry a claim on their own, ever, regardless of how plausible the claim looks:

- **Anonymous or pseudonymous social accounts.** Leaker accounts, "industry insider"
  handles, anonymous Discord/Telegram screenshots, accounts whose track record you cannot
  check. A named analyst posting under their own name with a stated method is different —
  that is T2.
- **SEO content farms and scraped-rewrite sites.** Sites whose articles are rewrites of
  other articles with no reporting, no byline, or a fake byline. Tell-tales: no author
  page, no corrections policy, article text that paraphrases a single upstream piece
  paragraph by paragraph, "As of [year], …" boilerplate.
- **AI-generated aggregator pages.** Auto-summarized "news" sites, LLM-written roundups,
  and answer-engine snippets. If a page has no identifiable human author or organization
  standing behind it, it is not a source. Never cite a search-result summary; cite the
  page it summarized, after fetching it.
- **Stock-promotion and financial-content-marketing sites.** Anything whose business model
  is generating trading interest — penny-stock newsletters, "top 5 AI stocks" pages,
  sponsored "research" from investor-relations marketing firms. Also: sell-side price
  targets repeated without the underlying analysis.
- **Press-release wires as evidence of anything but the release.** A wire item proves the
  company said something. It does not corroborate the content. Two wires carrying the same
  release are one source.
- **Pages you could not fetch.** If it did not load, it is not a source. See `SPEC.md`
  rule 2.
- **Your own memory.** Model priors are not a source. If you did not fetch it today, it
  does not go in the file.

Special caution, not a ban: **vendor benchmark claims** and **analyst "channel checks"**
are usable but must be attributed in the prose to the party making them, with the method
named or its absence noted.

---

## 3. Paywalls, bot blocks, and how to actually fetch things

### Paywall policy

Do not pay, do not attempt to bypass, do not use pirated copies. When the source you want
is paywalled:

"Do not bypass" includes technical accidents in your favour: a misconfigured RSS feed that
emits full paid articles, a print-view URL, an AMP page, a cache, or a reader-mode trick is
still bypassing the paywall. If the publisher meant you to read it for free, it would not
be behind a paywall.

1. **Find the open equivalent.** Almost every paywalled technical claim has one: the arXiv
   preprint, the author's copy on a lab page, the conference slide deck, the company's own
   press page, the filing the article was written from.
2. **Cite the open one and use the paywalled one as corroboration** — but only if you
   actually read enough of it to know what it says. Never cite a paywalled article on the
   strength of its headline and first paragraph.
3. **If nothing open exists**, say so in `deeper_md` ("the figure comes from a subscription
   report and could not be independently checked") and set `confidence` accordingly.

Frequently paywalled here: The Information (hard), Stratechery (freemium), Digitimes
(hard, headline visible), RTO Insider (hard), E&E News/Politico Pro (hard), IEEE Xplore
(most papers — see §4 for the open route), Yole and TrendForce reports (hard; their press
releases are free), most sell-side research (unavailable, do not cite secondhand).

### Bot blocks are not death

A large fraction of good sources return 403/404/429 to automated fetchers while being
perfectly alive in a browser. **Do not conclude a source is dead from a failed fetch, and
do not silently drop it from the run.** Confirmed bot-blocking as of 2026-08-20:
`sec.gov`, `fda.gov`, `openai.com`, `x.ai`, `science.org`, `cell.com`, `bls.gov`,
`defense.gov`, `jedec.org`, `semi.org`, `opencompute.org`, `ferc.gov`, `nrc.gov`,
`emp.lbl.gov`, `tsmc.com`, `investor.nvidia.com`, `cadence.com`, `umc.com`, `mrs.org`,
`imaps.org`, `yolegroup.com`, `semianalysis.com`, `pcisig.com`, `gridstatus.io`,
`arstechnica.com`, `venturebeat.com` (rate limit), `eetimes.com` (HTTP/2 reset),
`date-conference.com` and `fuse.wikichip.org` (connection reset), and — for the energy and
infrastructure layers — **the entirety of `ferc.gov` and `nrc.gov`**, plus
`latitudemedia.com`, `gridstatus.io`, `ir.aboutamazon.com`, `investor.atmeta.com`,
`investor.oracle.com`, `datacentermap.com` (429), and Gartner and Omdia.

**The two fetchers fail on different sites — always try both.** Serve WebFetch but 403
curl: `investor.tsmc.com`, `investors.micron.com`. Serve curl but 403 or time out
WebFetch: `semiconductors.org`, `newsroom.lamresearch.com`, `investors.gf.com`,
`ir.appliedmaterials.com`, `semiengineering.com`. SEC serves neither without a
contact-email User-Agent. `umc.com`, `opencompute.org`, and `yolegroup.com` served
nothing to anything.

Order of attack when a fetch fails:

1. **Retry with `curl` and a browser User-Agent** via bash. This works on many of the
   above. It is how the EDGAR full-text API was verified for this file:
   ```bash
   curl -s -A "GopherFab ai-stack-brief <contact email>" \
     "https://efts.sec.gov/LATEST/search-index?q=%22CoWoS%22&forms=8-K&startdt=2026-08-01&enddt=2026-08-20"
   ```
   SEC specifically requires a User-Agent that identifies you with a contact address.
2. **Use the machine-readable endpoint instead of the HTML page.** See the table in §3.1
   below — several of the most important sources in this file are only reliably reachable
   that way.
3. **Find the same document somewhere open** — the preprint, the mirror, the regulator's
   copy, the company's own PDF.
4. **If all of that fails, the URL does not go in the brief.** Note it in the run notes so
   the source list can be fixed.

### 3.1 Machine-readable endpoints, all verified 2026-08-20

Prefer these over scraping the HTML. They are faster, more reliable, and dated.

**Keyless:**

| What | Endpoint |
| --- | --- |
| SEC EDGAR full-text search | `https://efts.sec.gov/LATEST/search-index?q=…&forms=…&startdt=…&enddt=…` (needs a UA naming you + a contact email) |
| SEC company submissions | `https://data.sec.gov/submissions/CIK##########.json` (same UA rule) |
| Federal Register (all agencies, incl. FERC and BIS filters) | `https://www.federalregister.gov/api/v1/documents.json?conditions[agencies][]=…` |
| arXiv | `https://export.arxiv.org/api/query?search_query=cat:cs.AR&…` (attribution required) |
| Nature | `https://www.nature.com/nature.rss` |
| bioRxiv | `https://connect.biorxiv.org/biorxiv_xml.php?subject=all` |
| ClinicalTrials.gov | `https://clinicaltrials.gov/api/v2/studies` |
| NSF awards | `https://api.nsf.gov/services/v1/awards.json?keyword=…` |
| HKEX filings | `https://www1.hkexnews.hk/search/titleSearchServlet.do?lang=E` |
| EIA "Today in Energy" | `https://www.eia.gov/rss/todayinenergy.xml` |
| DOE news | `https://www.energy.gov/rss/energygov/2193718` |

**Free key required:** EIA API v2 (`api.eia.gov/v2/`, register at
`eia.gov/opendata/register.php`) · regulations.gov v4 (`api.regulations.gov/v4/`, via
api.data.gov) · Grid Status (`api.gridstatus.io/v1/`, 500k rows/month free).

**Useful RSS:** Utility Dive `/feeds/news/` · RTO Insider `/feed/` (full text) · Heatmap
`/feeds/feed.rss` · Canary `/rss.rss` · POWER `/feed/` · Latitude `/feed/` · DCD `/rss/` ·
The Next Platform `/feed/` · Dell'Oro `/feed/` · The Register `/headlines.atom` · Fierce
`/rss/xml` · **SemiAnalysis `newsletter.semianalysis.com/feed`** (not the WordPress one).

**Check every feed's newest item date before trusting it.** Known liars: `jedec.org/rss.xml`
(2020), `semianalysis.com/feed/` (2025), Data Center Frontier `/rss` (404 — the real one is
a `__rss/website-scheduled-content.xml?input=…` query-string URL).

### JavaScript-rendered pages

Some pages return 200 with no content to a fetcher because the data loads client-side.
Known: Census BTOS, DARPA news, NSF award search UI, and most eval leaderboards (Arena,
SWE-bench, ARC). For these, prefer the API, the underlying CSV/JSON, or the organization's
blog post announcing the numbers — and if you can only see the page chrome, you have not
read the page.

### Verification legend used below

`✅` fetched successfully on 2026-08-20 · `⚠️` bot-blocked or JS-only to an automated
fetcher but believed live (see above) · `❗` could not be verified — check before relying
on it.

---

## 4. Cross-cutting primary sources

These serve every layer. Learn to search them; they are where the brief's credibility
comes from.

### SEC EDGAR — the single highest-value tool here

| Resource | URL | Notes |
| --- | --- | --- |
| Full-text search (UI) | `https://www.sec.gov/edgar/search/` ⚠️ | Searches the text of filings since 2001. |
| Full-text search (API) | `https://efts.sec.gov/LATEST/search-index?q=…&forms=…&startdt=…&enddt=…` ✅ | Returns JSON. Requires a descriptive `User-Agent` with a contact address. This is the workhorse. |
| Company browse | `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=…&type=10-Q` ✅ | Per-company filing history. |
| Submissions JSON | `https://data.sec.gov/submissions/CIK{cik}.json` ✅ | Every filing a company has made, structured. |
| **XBRL company concept** | `https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json` ✅ | **Structured financials, free, no key.** The right way to pull capex. |

**Use the XBRL API for capex, not the IR pages.** It is keyless, structured, and immune
to the Cloudflare blocking that hits half the investor-relations sites. Verified
2026-08-20 with `PaymentsToAcquirePropertyPlantAndEquipment`: Microsoft (CIK 0000789019)
$115.9B FY26; Alphabet (0001652044) $80.6B; Meta (0001326801) $49.1B; Oracle
(0001341439) $55.7B FY26; CoreWeave (0001769628) $14.1B.

⚠️ **The tag is not consistent across filers, and the failure is silent.** Amazon
(0001018724) and Nvidia (0001045810) report capex under
**`PaymentsToAcquireProductiveAssets`** instead. Querying the wrong tag does not error —
it returns a stale figure that looks valid. Amazon silently returned a **2017** number.
So: **try both tags, and always check the period end date on the value you use.** These
figures are cash-flow capex and **exclude finance leases**, which are increasingly
material for Microsoft, Meta, and Oracle — a datacenter item resting on capex alone can
understate real commitment badly.

**How to search it well.** Search for *phrases that only appear in filings*, not for
company names: `"purchase commitments"`, `"wafer supply agreement"`, `"capacity
reservation"`, `"take-or-pay"`, `"CoWoS"`, `"advanced packaging"`, `"power purchase
agreement"`, `"interconnection agreement"`. Restrict `forms=8-K` for events and `10-Q` for
quarterly detail. An 8-K filed the same week is a `confirmed`-grade source and usually
predates the trade coverage.

Read: the cash-flow statement for capex, the notes for purchase obligations and capacity
commitments, and **the diff in risk factors versus last quarter** — a newly added risk
factor is one of the most reliable early signals available for free.

### Non-US filings

| Jurisdiction | URL | Notes |
| --- | --- | --- |
| Taiwan (TSMC, UMC, ASE, Foxconn) | **English: `https://emops.twse.com.tw/server-java/t58query`** ✅ | MOPS. **`mops.twse.com.tw/mops/web/index` is dead** — the Chinese site is now a hash-routed SPA (`/mops/#/web/home`) that returns an empty shell to fetchers. The English `emops` host is server-rendered and fetchable. Taiwanese law requires **monthly revenue filed by the 10th** — a genuinely leading indicator. Look under Operating Statements. |
| Korea (Samsung, SK hynix) | `https://dart.fss.or.kr/` ✅ · English: `https://englishdart.fss.or.kr/` ✅ | DART. English is a subset of the Korean filings, which are fuller and earlier. Samsung's provisional earnings guidance ("잠정실적") lands here about a week after quarter end. |
| Japan (TEL, Advantest, Screen, Disco, Kioxia) | `https://disclosure2.edinet-fsa.go.jp/` ✅ · weekly list `/week0010.aspx` ✅ | EDINET. **Japanese only — no working English interface.** The API (`api.edinet-fsa.go.jp/api/v2/documents.json`) is live but returns 401 without a free registered key. The companies' own English IR decks are usually the faster route. |
| Hong Kong (SMIC, Hua Hong) | `https://www.hkexnews.hk/index.htm` ✅ · search `https://www1.hkexnews.hk/search/titlesearch.xhtml` ✅ · **JSON `https://www1.hkexnews.hk/search/titleSearchServlet.do`** ✅ (supports `lang=E`) | SMIC's HKEX filings carry capacity and utilization detail its press releases omit, and are often independent of its STAR Market disclosures. |

### Regulatory and legal

| Resource | URL | Good for / bias |
| --- | --- | --- |
| Federal Register | `https://www.federalregister.gov/` · API `https://www.federalregister.gov/api/v1/documents.json` ✅ | The authoritative text of every US rule, including export controls. The API is free, keyless, and searchable by agency and date. Always cite the notice, never the summary of it. |
| Regulations.gov | `https://www.regulations.gov/` | Dockets and public comments. Industry comment letters on a proposed rule are an underused source of real technical detail. |
| BIS (export controls) | `https://www.bis.gov/` ✅ — **`bis.doc.gov` is dead, not redirecting: no TLS handshake at all** | Entity List changes, license requirements. **Do not use `bis.gov/regulations/federal-register-notices`** — it loads but renders "Showing 0 Federal Register Notices." Use the Federal Register API with the agency filter instead: `https://www.federalregister.gov/api/v1/documents.json?per_page=20&order=newest&conditions[agencies][]=industry-and-security-bureau` ✅ (clean JSON, keyless). The press release is a summary; the notice is the rule. |
| CourtListener / RECAP | `https://www.courtlistener.com/` ✅ | Free docket access. Complaints and filed exhibits beat coverage of them. |
| USPTO | `https://www.uspto.gov/patents/search` · data at `https://data.uspto.gov` | Patents publish 18 months after filing, so they describe the past, not the roadmap. Good for "how does this actually work," bad for "what ships next." |

### The conference calendar

`DAILY_BRIEF.md` §1 requires a calendar pass at the start of every run. Check whether one
of these is running this week — conference weeks produce a burst of high-quality primary
material, and the technical program is public even when the papers are not.

Dates below were read off the official sites on 2026-08-20. Re-check them; conference
sites roll over to the next edition and quietly delete the last one.

| Venue | URL | Next / most recent | Layer |
| --- | --- | --- | --- |
| **Hot Chips** | `https://hotchips.org/` ✅ | **2026: Aug 23–25, Stanford Memorial Auditorium** — imminent. Archives index at `/archives/`; slides and talks historically posted free | chips + infrastructure |
| SPIE Photomask + EUV (BACUS) | `https://spie.org/conferences-and-exhibitions/photomask-technology-and-extreme-ultraviolet-lithography` ✅ | **2026: Sept 8–11, Monterey.** Exhibition Sept 9–10 free with registration | chips (masks, EUV) |
| imec ITF Taiwan | `https://www.imecitf.com/` ✅ | **2026: Aug 31, Taipei** | chips |
| 3DIC | `https://3dic-conf.org/` ✅ (**not** an ieee.org path) | 2026: Oct 1–2, Georgia Tech, Atlanta | chips (packaging) |
| ITC (International Test Conference) | `https://www.itctestweek.org/` ✅ | 2026: Oct 11–16, San Antonio | chips (test) |
| OCP Global Summit | `https://www.opencompute.org/` ⚠️ | 2026: Oct 12–15, San Jose ❗ (third-party sources agree; **never confirmed on OCP's own site**, which is fully bot-blocked) | infrastructure, energy |
| SEMICON West | `semiconwest.org` ⚠️ | **2026: Oct 13–15, Moscone, SF — the last San Francisco edition.** Then **2027: Mar 30–Apr 1, Phoenix** (permanent move *and* a fall→spring shift) | chips |
| AVS International Symposium | `https://www.avs.org/` → `http://www.avs72.avs.org/` ✅ | 2026: Oct 24–29, Pittsburgh. **Free Abstract Book and Technical Program PDFs** — one of the most open on this list | chips (surfaces, thin films) |
| MICRO | `https://www.microarch.org/micro59/` ✅ | 2026: Oct 31–Nov 4, Athens | chips (architecture) |
| SC (Supercomputing) | `https://supercomputing.org/` | November | infrastructure |
| MRS Fall | `mrs.org` ⚠️ (confirmed via `engagemrs.org`) | 2026: Nov 29–Dec 4, Boston | chips (materials) |
| NeurIPS | `https://neurips.cc/` ✅ | 2026: Dec 6–12, Sydney (+ Atlanta and Paris satellites Dec 9–13) | models |
| **IEDM** | `http://ieee-iedm.org/` ✅ | **2026: Dec 12–16, Hilton SF Union Square** (72nd). Tutorials Dec 12, short courses Dec 13 — titles and abstracts free, slides attendee-only | chips (devices, process) |
| **ISSCC** | `https://www.isscc.org/` ✅ | 2027: Feb 14–18, SF Marriott Marquis. **Best free archive here:** `/past-conferences` has advance programs, Trends documents, and 2026 plenary videos | chips (circuits) |
| **SPIE Advanced Lithography + Patterning** | `https://spie.org/conferences-and-exhibitions/advanced-lithography-and-patterning` ✅ | 2027: Feb 21–25, San Jose | chips (litho) — **the most relevant conference in the world to GopherFab's stepper** |
| IRPS | `https://irps.org/` ✅ | 2027: Mar 21–25, San Diego | chips (reliability) |
| ISPD | `https://ispd.cc/` ✅ | 2027: Mar 31–Apr 2, Taipei; abstracts due Sept 21 2026 | chips (physical design, ML-for-EDA contests) |
| Photomask Japan | `https://smartconf.jp/content/pmj2026/info` ✅ | 2026: Apr 8–10, PACIFICO Yokohama (the homepage confusingly also advertises Apr 7–9 2027 — cite `/info`) | chips (masks) |
| CICC | `https://www.ieee-cicc.org/` ✅ | 2027: Apr 18–21, San Diego | chips (circuits) |
| DATE | `date-conference.com` ❗ (connection reset on every attempt) | 2026: Apr 20–22, Verona (secondary sources only) | chips (EDA) |
| ASMC | `https://www.semi.org/en/connect/events/advanced-semiconductor-manufacturing-conference-asmc` ⚠️ | 2026: May 11–14, Albany NY ❗ | chips (manufacturing) |
| ECTC | `https://www.ectc.net/` ✅ | 2027: June 1–4, Gaylord Rockies, Denver | chips (packaging) |
| **IITC** | `https://iitc-conference.org/` ✅ — **`iitc-ieee.org` does not exist** | 2026: June 1–4, San Jose | chips (interconnect) |
| VLSI Symposium | `https://www.vlsisymposium.org/` ✅ | 2026: June 14–18, Honolulu | chips (technology + circuits) |
| ISCA | `https://www.iscaconf.org/isca2026/` ✅ | 2026: June 27–Jul 1, Raleigh | chips (architecture) |
| DAC | `https://www.dac.com/` ✅ | 2027: July 11–14, San Jose (2026 was Jul 26–29, Long Beach). Free program portal and PDF | chips (EDA) |
| ESSERC | `https://www.esserc.org/` ✅ — **ESSCIRC and ESSDERC have merged and renamed;** `esscirc-essderc.org` is obsolete | 2026: Sept 7–10, Palma de Mallorca; 2027: Sept 6–9, Helsinki | chips |
| OFC | `https://www.ofcconference.org/` ✅ | March | infrastructure (optics) |
| ICML / ICLR / ACL / CVPR | `icml.cc` · `iclr.cc` · `2026.aclweb.org` · `cvpr.thecvf.com` ✅ | 2026 editions have all happened; `iclr.cc` now serves ICLR 2027 (Apr 26–30) | models |
| SEMICON Taiwan / Korea | via `https://www.semi.org/` ⚠️ | Taiwan ~early Sept (Taipei), Korea ~February (Seoul) ❗ | chips |
| IMAPS | `imaps.org` ❗ (403 on every path) | unverified | chips (packaging) |

### Getting conference papers without IEEE Xplore access

Most IEDM/ISSCC/VLSI/ECTC/IRPS/IITC papers live behind IEEE Xplore
(`https://ieeexplore.ieee.org/` ✅; per-conference archives via
`/xpl/conhome/<id>/all-proceedings`). SPIE papers are at
`https://www.spiedigitallibrary.org/conference-proceedings-of-spie` ✅. Both are
paywalled for most content. The open routes, in order of preference:

1. **The advance program / technical program PDF** on the conference's own site — free,
   and it carries paper titles, authors, affiliations, and often a short abstract. This
   alone is frequently enough to write an accurate item about *what was disclosed*.
2. **The presenting company's or lab's own press page and slide deck.** imec
   (`https://www.imec-int.com/en` ✅), CEA-Leti, TSMC, Intel, Samsung, and the equipment
   vendors routinely post the deck.
3. **The authors' preprint or institutional repository copy.**
4. **University library access**, which UMN students have — worth saying in `try_this`
   when the underlying paper is a good read.
5. **Trade coverage of the talk** (SemiEngineering and EE Times send people to these) —
   T2, and honest to cite as "as reported from the session."

Never cite a paper you have only seen the title of. Cite the program listing as a program
listing.

---

## 5. Chips — the home layer

### 5.1 Primary: company IR and technical disclosure

Monthly and quarterly numbers from these companies are the closest thing this brief has to
ground truth about what is physically being built.

Deep links here were verified individually on 2026-08-20 — several of the obvious guesses
are 404s, so use the exact paths.

| Company | Where | What it is good for |
| --- | --- | --- |
| **TSMC** | **`https://investor.tsmc.com/english/monthly-revenue/2026`** ✅ (year is a path segment) · quarterly `/english/quarterly-results/2026/q2` · calendar `/english/financial-calendar` | **Monthly revenue, published around the 10th** — the single most useful recurring datapoint in the layer, and unaudited by its own note. Quarterly call gives node mix, capex guidance, and advanced-packaging capacity language. **`www.tsmc.com/english/monthly-revenue` is a 404 — the host must be `investor.tsmc.com`. curl gets 403; WebFetch works.** Bias: management is deliberately vague about customers and about CoWoS capacity. |
| **ASML** | `https://www.asml.com/en/investors` ✅ | **Quarterly net bookings are the most-watched leading indicator for wafer-fab equipment.** Also EUV and immersion unit shipments and the China mix. The quarterly CFO video interview is unusually candid. Bias: bookings are lumpy and ASML says so — do not annualize a quarter. |
| **Applied Materials** | **`https://ir.appliedmaterials.com/news-releases`** ✅ | Depo, etch, implant, and CMP demand by segment — the best read on the trailing-edge vs leading-edge capex split. `appliedmaterials.com/us/en/investor-relations.html` 403s; use the `ir.` subdomain. October fiscal year end, so Q3 lands mid-August. |
| **Lam Research** | **`https://newsroom.lamresearch.com/press-releases`** ✅ | Etch and deposition with a strong NAND/DRAM signal. Lam's commentary on 3D NAND layer counts is a genuine technical source. `investor.lamresearch.com/news-events/press-releases` is a 404. |
| **KLA** | **`https://ir.kla.com/news-events/press-releases`** ✅ | Process control and inspection — a leading indicator, because metrology is bought before a ramp. |
| **Tokyo Electron** | `https://www.tel.com/ir/` ✅ · library `https://www.tel.com/ir/library/` ✅ | Coater/developer (track) and etch. Good English materials. `/ir/library/results/` is a 404; use `/report/`, `/consolidated-financial-statements/`, and the Fact Book at `/fb/`. March fiscal year end, so "FY2027 Q1" means Apr–Jun 2026. |
| **Nvidia** | **Use EDGAR (NVDA), not the IR site** | `investor.nvidia.com` renders as a JS shell with no financial data to a fetcher, and 403s curl. The 8-K and 10-Q carry the numbers. **The purchase-obligations note in the 10-Q is more informative than the keynote.** Fiscal year ends late January. |
| **AMD** | `https://ir.amd.com/news-events/press-releases` ✅ | Calendar-aligned quarters. |
| **Intel** | **`https://www.intc.com/news-events/press-releases`** ✅ (`investor.intel.com` did not resolve) | Foundry segment reporting, node status (18A/14A), capex, and government-stake and foundry-customer announcements. Bias: Intel's node naming and "on track" language needs independent corroboration every time. |
| **Micron** | `https://investors.micron.com/` ✅ | DRAM/NAND bit growth, HBM sold-out language, capex. **Fiscal year ends late August/early September, so its full-year report lands in late September, offset from everyone else** — which makes it the first read on a new memory cycle. |
| **SK hynix** | **`https://news.skhynix.com/en/category/ir/`** ✅ · DART for filings | HBM share and qualification status. **There is no working dedicated English IR portal** — `skhynix.com/ir/…` 404s. Use the newsroom IR category plus DART English. |
| **Samsung** | **`https://www.samsung.com/global/ir/financial-information/earnings-release/`** ✅ (archive to 2011) · DART | Foundry + memory. Provisional earnings guidance lands on DART about a week after quarter end, before the full release. |
| **UMC** | ❗ **fully Cloudflare-blocked** — all `umc.com` paths 403 to both fetchers. **Substitute: MOPS English (ticker 2303) or UMC's 6-K on EDGAR.** | Mature-node utilization — the best read on the non-AI part of the industry. Same ~10th-of-the-month revenue cadence as TSMC. |
| **GlobalFoundries** | **`https://investors.gf.com/investor-relations/news-events/press-releases`** ✅ (`gf.com/investors` and `investors.gf.com/press-releases` are both 404s) | Specialty and trailing-edge. |
| **SMIC** | **`https://www.smics.com/en/site/company_financialSummary`** ✅ — quarterly back to 2004, downloadable Excel | China capacity and utilization. Pair with HKEXnews for the formal PDFs. Bias: disclosure is thin and strategically timed. |
| Rapidus | `https://www.rapidus.inc/en/` ✅ · news `/en/news_topics/` | 2 nm GAA effort; pilot line running at Chitose, Hokkaido, with mass production targeted 2027. No financials — private consortium. Bias: heavily government-backed and publicity-forward; treat every milestone as `reported`. |
| Cerebras | EDGAR: CBRS ✅ | Now a public filer — its 8-Ks are a primary source on AI-accelerator deployments. |

### 5.2 Primary: standards, consortia, and roadmaps

| Body | URL | Good for / bias |
| --- | --- | --- |
| **JEDEC** | `https://www.jedec.org/` ⚠️ · press `/news/pressreleases` | The authoritative memory standards — HBM, DDR, LPDDR, GDDR. **Free download with free registration**, no membership or payment. State of play as of 2026-08-20: **HBM4 is published** (JESD270-4, Apr 2025; now **JESD270-4A v1.1, Dec 2025** — 2048-bit, up to 8 Gb/s, ~2 TB/s per stack, 32 channels × 2 pseudo-channels), with a companion bump-matrix standard JESD271-4; **SPHBM4** (reduced-pin HBM4 for organic substrates) announced Jul 2026; **no HBM4E standard exists** — that name is currently vendor marketing on the HBM4 platform. **Distinguish "spec published" from "spec balloted" from "member announced intent"** — vendors blur these constantly, and HBM4E is the live example. |
| ⚠️ **JEDEC RSS — blacklisted** | `https://www.jedec.org/rss.xml` | **Returns HTTP 200 with a newest item from July 2020.** A dead feed that looks alive. Never poll it; it is exactly the kind of thing that would silently freeze a daily brief. |
| **SEMI** | `https://www.semi.org/` ⚠️ · standards `/en/standards` · billings `/en/products-services/market-data/equipment/billings-report` | Equipment and materials standards (paid, via SEMIViews) plus market data. **Cadence trap: SEMI discontinued the monthly North America billings press release in February 2022** (Book-to-Bill ended in 2017). Only quarterly global billings releases remain, roughly 6–8 weeks after quarter end, and those are free. The site is bot-blocked; SEMI mirrors its releases to PR Newswire, which fetches fine. Bias: a supplier trade association — the market data is credible, the policy items are lobbying. |
| **IRDS** | `https://irds.ieee.org/editions` ✅ | The ITRS successor roadmap. **Genuinely free — direct PDFs open without a login** (verified). ⚠️ **The newest downloadable edition is 2024**; the page shows unlinked placeholder headings for a 2025 Update and a 2026 Edition, and the homepage copy is stale. Excellent Foundations material. Bias: consensus roadmaps are conservative and chronically slip. |
| **UCIe** | `https://www.uciexpress.org/` ✅ · `/specifications` | Die-to-die interconnect. **Current: UCIe 3.0, released Aug 2025** — 32 GT/s up to 48/64 GT/s, runtime recalibration, extended sideband, manageability. Free but form-gated (name, email, company, country, citizenship; up to 7 business days), and the licence is **evaluation-only with no right to implement**. Ignore the stale "COMING SOON UCIe 1.0" fragment still on the homepage. Bias: consortium messaging overstates ecosystem readiness relative to shipping silicon. |
| **CXL Consortium** | `https://www.computeexpresslink.org/` ✅ · specs `/cxl-specification/` · **blog `https://computeexpresslink.org/blog/`** (`/newsroom` is a 404) | **Current: CXL 4.0, released Feb 2026** — 64→128 GT/s, bundled ports, enhanced memory RAS. Free with registration. Bias: a persistent gap between spec version and deployed hardware that the blog will not flag for you. |
| **PCI-SIG** | `https://pcisig.com/specifications` ⚠️ · `/newsroom` | **PCIe 7.0 final (Jun 2025, 128 GT/s); PCIe 8.0 in draft** — 256 GT/s, ~1 TB/s bidirectional at x16, PAM4 plus FLIT, new connector under evaluation, Draft 0.5 to members May 2026, ratification targeted 2028. **Strictest gate on this list:** the spec index (titles and dates) is public, but every actual spec and ECN is members-only. The public ECN list is still useful for tracking velocity. |
| **Ultra Ethernet Consortium** | **`https://ultraethernet.org/specification/`** ✅ (redirects to `/specification-history/`) | **Current: UEC 1.0.3, July 2026** (1.0 shipped Jun 2025). **No form, no registration, no membership — direct PDF download.** The most open source on this page. ⚠️ **Poll the specification page, not the blog** — the blog is stale (Dec 2025). Bias: explicit pro-Ethernet, anti-InfiniBand advocacy for AI fabrics. |
| **OIF** | `https://www.oiforum.com/` ✅ · press `/press-room/` · **`/technical-work/implementation-agreements-ias/`** ✅ | **One of the highest-signal consortium sources here.** Implementation Agreement PDFs are publicly listed and directly downloadable free, 2000–2026, with obsolete versions marked — CEI SerDes (6G through 224G+), CMIS (5.4 released Jun 2026), FlexE, 400G/800G coherent, co-packaging modules. Multi-vendor interop demos are concrete rather than aspirational. |
| **imec** | `https://www.imec-int.com/en` ✅ · ITF `https://www.imecitf.com/` ✅ | Research roadmaps for CFET, high-NA, backside power, 2D materials, spin qubits. Free press material and slides, excellent technical depth. Bias: funded by the whole industry, so everything is "promising" and every timeline is a research timeline. **Separate imec's research press releases from ITF keynotes** — ITF is a promotional roadshow validating the roadmaps of the same firms that fund imec. |
| **CEA-Leti** | `https://www.leti-cea.com/cea-tech/leti/english/Pages/Welcome.aspx` ✅ · French `https://www.cea.fr/cea-tech/leti` ✅ | FD-SOI, 3D and hybrid bonding, imaging, quantum, FeRAM. Free. The French page sometimes carries items earlier and has RSS. Bias: national-lab PR, EU-industrial-policy aligned, milestones often years from production. |
| **Fraunhofer** | **`https://www.mikroelektronik.fraunhofer.de/en.html`** ✅ (prefer this over the general newsroom) | European pilot lines, Research Fab Microelectronics Germany capacity, packaging and photonics. Weak on leading-edge logic. |
| **SRC** | `https://www.src.org/newsroom/` ✅ | US pre-competitive research consortium. **The MAPT Roadmap (v2.0, Oct 2025) is the US industry counterpart to IRDS.** Listings are public; full research outputs are member-gated. Bias: industry plus DoD/NSF funded — read MAPT as "what industry wants government to fund," not as a neutral forecast. |
| 🚨 **NSTC — read the note** | **`https://www.nist.gov/chips/research-development-programs/national-semiconductor-technology-center`** ✅ — **`natcast.org` now hard-redirects here** | **Natcast, the nonprofit that operated the NSTC, was terminated.** Commerce voided the operating agreement in August 2025 (declaring it void *ab initio*), transferred NSTC control to NIST, and Natcast laid off most staff in September 2025; NIST has run the program directly since, with an NSTC charter dated March 2026. **The NIST page does not mention Natcast at all and reads as though nothing happened** — so pair it with trade press before writing anything about NSTC continuity, and note that the $825M Albany EUV Accelerator's funding status was a casualty. Directly relevant to a university nanofab club's access to US facilities. |
| **WSTS** | **`https://www.wsts.org/76/Recent-News-Release`** ✅ | **Historical Blue Book billings are free with no login**; the forecast dataset is members-only, but the forecast press releases are free. Forecasts twice yearly (spring ~May/June, autumn ~Nov/Dec, timed to SEMICON events). |
| **SIA** | **`https://www.semiconductors.org/news-events/latest-news/`** ✅ · `/category/press-releases/` | Monthly global semiconductor sales, free and punctual — **published in the first week of the month, reporting the month two months prior.** ⚠️ **SIA's monthly figures are the WSTS three-month-moving-average data**, so the two overlap; SIA is the faster free English front end. `/latest-news/press-releases/` is a 404. WebFetch 403s this domain; curl works. Bias: a US industry lobby — the sales data is a dataset, the policy commentary is advocacy. |

### 5.3 Specialist trade press (T2)

| Source | URL | Good for / bias |
| --- | --- | --- |
| **Semiconductor Engineering** | `https://semiengineering.com/` ✅ (curl; 403s WebFetch) | **The best free technical trade publication for this layer.** Long, engineer-written pieces on process, packaging, test, EDA, power, and reliability, usually with named sources from the tool vendors. Free, no registration. **Its "Chip Industry Week In Review" is the single best weekly roundup available — start the chips sweep there.** Bias: heavily vendor-sourced; the experts quoted are selling something, and the topic mix follows its EDA and IP sponsors' interests. Superb Foundations raw material. |
| EE Times | `https://www.eetimes.com/` ⚠️ (homepage resets/times out to fetchers; recent 2026 articles confirmed via index) | Broad electronics industry news plus analyst columns; sends people to the conferences. Mostly free, some registration-gated. Bias: AspenCore-owned with heavy event and vendor coverage, and thinner than its 2010s reputation after layoffs. |
| Digitimes | `https://www.digitimes.com/news/` ✅ | Taiwan supply chain: capacity bookings, order cuts, foundry allocation. Frequently first and frequently wrong. **Hard paywall** beyond headlines and summaries. Bias: single-sourced supply-chain checks presented with more confidence than they deserve. Treat as `rumored` unless corroborated. |
| TheElec | `https://www.thelec.net/` ✅ (Korean: `thelec.kr`) | Korean supply chain — Samsung and SK hynix equipment orders, HBM lines, packaging investments. Often has real detail nobody else does, days early. Free. English versions are sometimes machine-translated; the Korean originals are fuller. Same single-source caution as Digitimes. |
| BusinessKorea | `https://www.businesskorea.co.kr/` ✅ | English Korean business daily with decent semiconductor coverage. Free headlines. Bias: pro-chaebol, promotional, light verification. |
| Economic Daily News (Taiwan) | `https://money.udn.com/money/index` ✅ | Chinese-language Taiwan supply chain — **frequently the true origin of stories that Digitimes and Tom's Hardware relay a day later.** Freemium. |
| CommonWealth | `https://english.cw.com.tw/` ✅ | Long-form Taiwanese industrial analysis with more depth than the daily press. Paywall status unclear ❗. Bias: Taiwan national-interest framing. |
| Nikkei Asia (Tech/Semiconductors) | `https://asia.nikkei.com/Business/Tech/Semiconductors` ✅ | Japan and pan-Asian supply chain with real reporting standards and executive access. **Paywalled.** Bias: Japanese establishment perspective. |
| Nikkei xTech | `https://xtech.nikkei.com/` ✅ | Japanese-language engineering trade press; teardowns, materials, and equipment detail. Freemium, Japanese only. |
| AnySilicon | `https://anysilicon.com/` ✅ | Useful **free calculators** — die-per-wafer, ASIC cost — plus an ASIC/IP vendor directory. Free. Bias: a lead-generation business; its "news" is lightly rewritten PR, so treat articles as T4 and the calculators as tools, not sources. |
| SemiWiki | `https://semiwiki.com/` ✅ | EDA/IP-centric blogs and forum discussion; the forum threads sometimes surface real engineers. Free. Bias: it is a vendor-sponsored blog platform — most posts are content marketing. Treat posts as T3 and forum threads as T4. |
| 3D InCites | `https://www.3dincites.com/` ✅ | Advanced packaging and heterogeneous integration community coverage, including ECTC and IMAPS reporting. Free. Bias: small, enthusiastic, packaging-industry-adjacent. |
| Chip Scale Review | `https://chipscalereview.com/` ✅ | Packaging and test technical articles, free PDFs. Vendor-authored but genuinely technical. |
| Semiconductor Digest | `https://www.semiconductor-digest.com/` ✅ (note the hyphen) | **The successor to Solid State Technology**, whose archives it hosts; the standalone magazine is dead. Free. Essentially a lightly edited press-release wire — high completeness, low analysis. |
| Compound Semiconductor | `https://compoundsemiconductor.net/` ✅ | GaN, SiC, InP, photonics, III-V epitaxy. News free, magazine gated. The right source for the non-silicon parts of the layer. |
| Bits&Chips | **`https://bits-chips.com/`** ✅ (**`bits-chips.nl` now redirects here**) | Dutch high-tech ecosystem — ASML, ASM, Besi, NXP, and the Eindhoven supply chain — in English. Partly free, partly membership. The best window into the lithography supply chain outside ASML's own IR. Bias: regional ecosystem booster. |
| IEEE Spectrum (semiconductors) | `https://spectrum.ieee.org/topic/semiconductors/` ✅ | Well-edited explanatory journalism. Free. Good Foundations source; rarely breaks news. |
| The Register | `https://www.theregister.com/on_prem/hpc/` ✅ | Skeptical, technically literate, and willing to say a claim is nonsense. Free. Bias: contrarian by house style. |
| Tom's Hardware | `https://www.tomshardware.com/` ✅ | Fast aggregation of Asian trade press into English, with useful context. Free. Bias: aggregation — always chase the source it cites, which is usually Digitimes, TheElec, or a Korean paper. Treat as T3. |
| ServeTheHome | `https://www.servethehome.com/` ✅ | Hands-on server, accelerator, and networking hardware coverage with real photos of real systems. Free. |
| ~~AnandTech~~ | `anandtech.com` → 301 → `forums.anandtech.com` ✅ | **DEAD — confirmed.** Ceased publication 30 Aug 2024 after 27 years; the site was pulled offline 1 Aug 2025 and the domain now hard-redirects to the (still live) forums. **Do not cite it as a current source.** Its archive remains excellent Foundations background — cite via the Wayback Machine. |
| WikiChip / WikiChip Fuse | `en.wikichip.org` · `fuse.wikichip.org` ❗ | **Could not be verified** — six attempts across protocols and paths all returned connection resets or 422. Independent reporting has described Fuse as largely dormant for some time. **Do not auto-ingest and do not assume it is live.** The wiki's microarchitecture reference pages remain useful in a browser. |

### 5.4 Specialist analysts (T2)

| Source | URL | Good for / bias |
| --- | --- | --- |
| **SemiAnalysis** (Dylan Patel) | `https://semianalysis.com/` ⚠️ (bot-blocked; ~180k+ subscribers confirmed via proxy) | Datacenter, accelerator, and fab economics with real modeling. **Freemium plus an expensive institutional tier.** Bias: confident, directional calls that move stocks; occasionally wrong in ways it rarely revisits; **it sells data to investors, so read the incentive.** Cite free posts only; never repeat a paywalled number you have not read. |
| **Fabricated Knowledge** (Doug O'Laughlin) | `https://www.fabricatedknowledge.com/` ✅ | Semiconductor cycle, capex, and memory analysis. Substack freemium. Bias: buy-side investment lens — these are theses, not neutral reporting. |
| **TechInsights** | `https://www.techinsights.com/` ⚠️ · blog `/resources/blogs` | **Die teardowns and reverse engineering** — the only public source that will tell you what is physically inside a shipping chip, including independent process-node verification. **The definitive arbiter of "did they really ship on N3."** Blog and the "Behind the Headlines" newsletter are free; teardowns, cost models, and databases are a very expensive subscription. **It absorbed IC Knowledge** — Scotten Jones's wafer-cost models are now sold as "Semiconductor Manufacturing Economics," and `icknowledge.com` redirects here. Bias: public posts are teasers for paid reports. |
| Objective Analysis (Jim Handy) | `https://objective-analysis.com/` ✅ | The memory-market specialist — DRAM, NAND, and emerging-memory economics. Free blog and podcasts, paid reports. Bias: independent, contrarian on memory hype, and **unusually willing to score its own past forecasts**, which is rare enough to be worth trusting. |
| Chips and Cheese | `https://chipsandcheese.com/` ✅ (`/archive` for dates) | Independent **microbenchmark-driven** CPU and GPU microarchitecture analysis — real measurements on real silicon, and the closest surviving successor to AnandTech's deep dives. Substack freemium. Bias: combative toward vendor marketing claims, which is largely the point; small sample sizes. |
| The Next Platform | `https://www.nextplatform.com/` ✅ | Systems, HPC, and AI infrastructure with unusually deep architectural and TCO analysis. Free with newsletter signup. Bias: strong opinions on vendor strategy; enterprise/HPC lens. |
| Yole Group | `https://www.yolegroup.com/` ❗ **fully bot-blocked** — every path 403 to two fetchers and two proxies | Market and technology analysis for packaging, imaging, power, MEMS, photonics. Reports paid; press releases normally free. **Could not be verified at all on 2026-08-20** — treat any Yole number reaching you secondhand with care. Bias: a consultancy — TAM forecasts are directionally useful, the precision is marketing. |
| TrendForce | `https://www.trendforce.com/` ✅ | The most-quoted source for DRAM and NAND contract and spot pricing. Free insights and press releases; DataTrack and pricing databases paid. Bias: press releases are teasers, and the widely recirculated price forecasts get revised often and quietly. |
| Counterpoint Research | `https://www.counterpointresearch.com/` ✅ | Handset silicon and, increasingly, AI compute share estimates. Freemium. Bias: figures are **modeled, not reported**, and vendors dispute them regularly — always attribute. |
| Dell'Oro Group | `https://www.delloro.com/` ✅ | Networking, datacenter capex, and optics market share. Free press releases, paid reports. |
| The Chip Letter | `https://thechipletter.substack.com/` ✅ (**`thechipletter.com` does not resolve**) | Computing and semiconductor **history**, written well. Substack freemium. Excellent Foundations source; near-zero news value. |
| Asianometry (Jon Y) | `https://www.asianometry.com/` ✅ + YouTube `@Asianometry` ❗ (YouTube not fetch-verifiable) | Historical and structural explainers on semiconductors and East Asian industrial history. Free, weekly. Excellent Foundations background; not a news source, and chase the sources it cites. |
| SemiVision | `https://substack.com/@semivision` ✅ (**`semivision.com.tw` does not exist**) | Silicon photonics, co-packaged optics, and advanced packaging supply chain, Taiwan-sourced. Substack paid tiers. Bias: **pseudonymous, rumor-heavy, no editorial layer — corroborate everything.** Effectively T4 on its own. |
| High Yield | YouTube `@HighYield` ❗ | Die-shot and architecture video analysis, by reputation. **Could not be verified** — YouTube is not fetchable by these tools. |
| Sell-side research (Bernstein, Morgan Stanley, etc.) | no public URL — **institutional only** | Reaches you only secondhand through press citations. **These analysts' firms have banking relationships with the companies they rate.** Cite as "per a Bernstein note reported by X," never as a primary source, and never as a number of record. |

### 5.5 Where to look for `chips` items other people miss

- **TSMC and UMC monthly revenue** (MOPS, ~10th of the month) versus their own quarterly
  guidance. A monthly number that misses guidance is a story before anyone writes it up.
- **The equipment vendors' quarterly segment splits** — they reveal ramp timing before the
  foundries do. ASML's net bookings in particular.
- **New or changed risk factors** in 10-Qs across the equipment vendors, diffed
  quarter-over-quarter.
- **Conference technical programs**, posted weeks before the conference and free.
- **JEDEC, UCIe, CXL, UEC, and OIF publication announcements**, which set what becomes
  buildable — and the gap between a published spec and shipping silicon.
- **imec press releases** (as distinct from ITF keynotes), which is where CFET, high-NA,
  and backside-power timelines actually get stated.
- **NSTC/NIST program announcements**, which affect US university fab access directly —
  and which need trade-press corroboration given the Natcast termination.
- **arXiv `cs.AR`** — `https://arxiv.org/list/cs.AR/recent` ✅ — low volume, high signal
  for accelerator and chip-design work.
- **The OIF implementation-agreement list**, which is free, dated, and tells you what the
  optics industry has actually agreed to build.

---

## 6. Energy

### Primary

| Source | URL | Good for / bias |
| --- | --- | --- |
| **FERC** | eLibrary `https://elibrary.ferc.gov/eLibrary/search` ✅ · **`ferc.gov` itself is 403 to every automated method** ⚠️ | Every filing in every federal electricity docket: interconnection agreements, tariff changes, co-location disputes, large-load proceedings. **This is where datacenter power fights are actually litigated, months before they are reported.** Two practical problems: eLibrary is a JavaScript SPA that returns no text to a fetcher, and **there is no public FERC API** (`api.ferc.gov` does not exist). **Workaround: the Federal Register API with the FERC agency filter** — `https://www.federalregister.gov/api/v1/documents.json?conditions[agencies][]=federal-energy-regulatory-commission` ✅, keyless JSON, current to today. |
| **EIA** | Electric Power Monthly `https://www.eia.gov/electricity/monthly/` ✅ · Form 860 `/electricity/data/eia860/` ✅ · Form 923 `/electricity/data/eia923/` ✅ · STEO `/outlooks/steo/` ✅ · Grid Monitor `/electricity/gridmonitor/dashboard/electric_overview/US48/US48` ✅ · **API v2 `https://api.eia.gov/v2/` — live, free key required** (register at `eia.gov/opendata/register.php`) · browser `https://www.eia.gov/opendata/browser/` ✅ · **RSS `https://www.eia.gov/rss/todayinenergy.xml`** ✅ | Generation, capacity, retirements, and prices by plant and by month — the authoritative US dataset. **Roughly a two-month lag** (as of 2026-08-20 the Electric Power Monthly carried May 2026 data). Bias: minimal on the data; the STEO forecast has historically under-forecast datacenter load. |
| **NERC** | **`https://www.nerc.com/our-work/assessments/long-term-reliability-assessments`** ✅ · summer `/summer-reliability-assessments` · winter `/winter-reliability-assessments` | The reliability community's own view of whether load growth is outrunning supply. Free. **The 2025 LTRA is the current edition; the next is due December 2026.** Serves curl but 403s WebFetch. Bias: institutionally conservative, which is the point. |
| **PJM** | `https://www.pjm.com/planning` ✅ · serial queue `https://www.pjm.com/planning/service-requests/serial-service-request-status` ✅ · cycle status `/planning/m/cycle-service-request-status` · load forecast `/planning/resource-adequacy-planning/load-forecast-dev-process` ✅ | The RTO where datacenter load growth is most acute. Deep links move — enter at `/planning`. |
| **MISO** | `https://www.misoenergy.org/planning/transmission-planning/` ✅ (MTEP) · **queue `https://www.misoenergy.org/planning/generator-interconnection/GI_Queue/`** ✅ | Minnesota's RTO — **the club's own grid**, which makes it the right first stop for any energy item with a local angle. Dashboards and maps, plus the DPP cycle documents. |
| **ERCOT** | planning `https://www.ercot.com/gridinfo/planning` ✅ · **large load `https://www.ercot.com/services/rq/large-load-integration`** ✅ · resource adequacy `/gridinfo/resource` ✅ (GIS report, CDR, MORA) | The most permissive large-load interconnection regime in the US, and therefore where the most aggressive datacenter siting happens. ⚠️ **ERCOT publishes the large-load *process* but no public MW-by-project queue report** — do not cite an "ERCOT large load queue" number without finding the actual document. |
| CAISO / SPP / ISO-NE / NYISO | `https://www.caiso.com/generation-transmission/generation/generator-interconnection` ✅ · `https://www.spp.org/engineering/generator-interconnection/` ✅ · `https://www.iso-ne.com/system-planning/interconnection-service/interconnection-request-queue` ✅ (PDF + XLSX) · `https://www.nyiso.com/interconnections` ✅ (XLSX) | The other queues. Several publish the queue as a spreadsheet, which is a primary dataset you can actually check a claim against. |
| LBNL "Queued Up" | `https://emp.lbl.gov/queues` ❗ 403 to every method · **mirror ✅ `https://eta-publications.lbl.gov/publications/queued-characteristics-power-plants`** (append `-0`, `-1` for the 2021/2022/2023 editions) | The standard annual synthesis of every US interconnection queue, and what most journalists are quoting. The mirror carries **free PDF and XLSX** data files. ⚠️ The mirror stops at 2023 — the 2024/2025 editions live only behind the blocked canonical page, so confirm the edition year before citing. Useful framing from the abstract: only **~24%** of 2000–2015 queue projects were ever built, and median wait rose from ~1.9 to ~3.5 years, so a queue megawatt is not a delivered megawatt. |
| **NRC** | **ADAMS `https://adams-search.nrc.gov/`** ✅ (**the old `adams.nrc.gov` is NXDOMAIN**) · `nrc.gov` itself is 403 to every method ⚠️ | Reactor and SMR licensing dockets. **The gap between "announced an SMR partnership" and "submitted a construction permit application" is enormous, and ADAMS is how you tell which one happened.** ADAMS is an SPA, so plan on a browser. |
| **DOE** | `https://www.energy.gov/` ✅ · **Office of Electricity `https://www.energy.gov/oe/office-electricity`** ✅ (**`energy.gov/gdo/*` is a 404 — the Grid Deployment Office is gone**) · **Office of Energy Dominance Financing `https://www.energy.gov/EDF`** ✅ (**the former Loan Programs Office**) · RSS `https://www.energy.gov/rss/energygov/2193718` ✅ | Grid grants, transmission, and the best source for GW-scale nuclear and grid debt financing. Bias: heavy current-administration framing — separate the announcement from the appropriation. |
| **IEA** | *Electricity 2026* `https://www.iea.org/reports/electricity-2026` ✅ (Feb 2026) · ***Key Questions on Energy and AI* `https://www.iea.org/reports/key-questions-on-energy-and-ai`** ✅ (Apr 2026) · *Energy and AI* `/reports/energy-and-ai` ✅ (2025) | Global electricity and datacenter-demand analysis, free under CC BY. **The single most-cited and most-misquoted set of datacenter demand numbers in circulation** — the ranges are wide and are routinely repeated without their error bars. If you cite one, cite the range. |
| EPRI | `https://www.epri.com/` ✅ (JS-heavy) · **DCFlex `https://dcflex.epri.com/`** ✅ | Utility-funded applied research. DCFlex is the load-flexibility demonstration program and is mostly public — the right source for "can datacenters actually curtail." Bias: utility-industry framing. |
| Uptime Institute | `https://uptimeinstitute.com/` ✅ · Global Data Center Survey 2026 (16th annual) | PUE, outage causes, cooling adoption. **Executive summary free with a form; the full report is paid.** Bias: a self-selected survey of operators. |
| ASHRAE TC 9.9 | committee page via `https://tpc.ashrae.org/` ✅ · **`https://datacom.ashrae.org` ✅ — about $33/yr** | The thermal guidelines the whole industry designs to. The Datacom book series has been replaced by the online "Datacom Encyclopedia." |
| **State PUCs** | **Directory of all 50: `https://www.puc.pa.gov/about-the-puc/national-list-of-utility-commissions/`** ✅ (better than NARUC's, which is member-gated) · Texas `https://interchange.puc.texas.gov/` ✅ (incomplete TLS chain — curl works, WebFetch fails) · Virginia `https://scc.virginia.gov/docketsearch` ✅ · Georgia `https://psc.ga.gov/facts-advanced-search/` ✅ · Ohio `https://dis.puc.state.oh.us/` ⚠️ | **Where datacenter rate classes, special tariffs, and co-location arrangements are actually decided.** There is no national portal and no common schema — every commission is a different platform, most have WAFs, almost none have RSS. Practical method: let Utility Dive or RTO Insider tell you *which* docket, then pull the docket yourself. |
| **Utility IR** | Sempra `https://www.sempra.com/investors` ✅ · Dominion `investors.dominionenergy.com` ✅ · AEP `www.aep.com/investors` ✅ · Entergy `investors.entergy.com` ✅ · Oncor `oncor.com/content/oncorwww/us/en/home/investors.html` ✅ · **Southern `investor.southerncompany.com`** · Xcel `investors.xcelenergy.com` · Talen `ir.talenenergy.com` · **Vistra `investor.vistracorp.com`** · **Constellation `investors.constellationenergy.com`** · NRG `investors.nrg.com` | **Utility earnings calls now contain more concrete datacenter-load information than most technology reporting.** Search transcripts for "data center" and "large load." Sempra/Oncor has been the richest on ERCOT large-load request volumes — and since ERCOT publishes no queue report, that IR disclosure *is* the primary source for those numbers. ⚠️ **The singular/plural of the `investor(s).` subdomain is inconsistent and the wrong one is NXDOMAIN** — the exact hosts above were verified. Bias: utilities have an incentive to make load growth sound large and certain, because rate base follows it. |

### Trade press and analysts

| Source | URL | Good for / bias |
| --- | --- | --- |
| Utility Dive | `https://www.utilitydive.com/` ✅ · feed `/feeds/news/` | Free, fast, competent coverage of utility regulation and datacenter interconnection. The default T2 read for this layer. Bias: trade-press framing sympathetic to utilities. |
| **RTO Insider** | `https://www.rtoinsider.com/` ✅ · feed `/feed/` | The most detailed gavel-to-gavel coverage of RTO/ISO and NERC proceedings that exists. **Subscription; headlines free.** Use it to find the docket, then read the docket on eLibrary for free — that is the intended workflow. ⚠️ **Its RSS feed appears to emit full article text in `content:encoded`, past the paywall. Do not use it that way.** Reading paid content through a misconfigured feed is bypassing a paywall, which §3 forbids. Use the feed for headlines and dates only. |
| Latitude Media | `https://www.latitudemedia.com/` ⚠️ **(403 to WebFetch; fine via curl with a browser UA)** · feed `/feed/` | **The most datacenter-power-focused outlet there is.** Free, plus gated reports. |
| Heatmap News | `https://heatmap.news/` ✅ · feed `/feeds/feed.rss` | Energy transition and local siting fights, including datacenter opposition — the best source on the politics of where these things get built. ~$10/mo. Bias: climate-forward but empirical, and open about it. |
| Canary Media | `https://www.canarymedia.com/` ✅ · feed `/rss.rss` | Clean energy, nonprofit-funded, free. Bias: explicit clean-energy advocacy. |
| POWER Magazine | `https://www.powermag.com/` ✅ · feed `/feed/` | Generation engineering — turbines, plant retrofits, thermal cycles. **The most genuinely engineering-focused of the energy trade press, which suits this audience.** Free tier plus a paid tier. Bias: thermal-friendly, and it runs vendor content. |
| T&D World | `https://www.tdworld.com/` ✅ | Transmission and distribution hardware — transformers, switchgear, conductors. Free plus a gated Insider tier. Bias: utility-friendly. |
| Data Center Dynamics | `https://www.datacenterdynamics.com/en/` ✅ · **energy channel `/en/the-energy-sustainability-channel/`** (the old `/en/power-cooling/` is a 404) · feed `/rss/` | Global datacenter buildouts, power deals, cooling. Free. Bias: prints announcements with light scrutiny — always chase the underlying filing. |
| Data Center Frontier | `https://www.datacenterfrontier.com/` ✅ | US-focused and more analytical than DCD. Free. ⚠️ `/rss` is a 404; the real feed is the `__rss/website-scheduled-content.xml?input=…` query-string URL. |
| Grid Status | site `gridstatus.io` ⚠️ **403 to all clients** · **API `https://api.gridstatus.io/v1/` responds; `/v1/datasets` needs a free key** (500k rows/month free tier) | Live and historical ISO load, price, and fuel-mix data — **the fastest way to check a load or price claim yourself instead of repeating it.** There is also an open-source `gridstatus` Python library. |
| Construction Physics | `https://www.construction-physics.com/` ✅ · feed `/feed` | Brian Potter on why building physical things costs what it costs — transformers, transmission, nuclear. Substack freemium. **Superb Foundations material for the energy layer.** Bias: abundance/buildability-leaning. |
| Volts | `https://www.volts.wtf/` ✅ | Long interviews with people who actually run the system. Freemium. Bias: openly progressive and deeply informed — both parts are true. |
| Doomberg | **`https://newsletter.doomberg.com/`** ✅ (**moved off Substack**) | Contrarian energy-realist takes. **Expensive** (~$400/yr). Useful only as a counterweight; do not cite it as a factual source. |
| Semafor Energy | `https://www.semafor.com/vertical/energy` ✅ (**the Net Zero vertical was retired**) | Geopolitics, capital, and energy. Free. |
| Princeton ZERO Lab | **`https://zero.lab.princeton.edu/`** ✅ (**`zero.princeton.edu` is NXDOMAIN**) | Jesse Jenkins's modeling group. ⚠️ Site news is stale to 2025; the live output is the *Shift Key* podcast. |

---

## 7. Infrastructure

### Primary

**Hyperscaler and neocloud filings.** Capex lands in the **cash-flow statement of the
10-Q**, not the press release, and the finance-lease line is where a lot of datacenter
commitment hides. Verified IR pages: Microsoft `https://www.microsoft.com/en-us/investor/`
✅, Alphabet `https://abc.xyz/investor/` ✅, Amazon
`https://ir.aboutamazon.com/quarterly-results/default.aspx` ⚠️, Meta
`https://investor.atmeta.com` ⚠️, Oracle `https://investor.oracle.com/financials/default.aspx`
⚠️ (the `/quarterly-reports/` path is a 404), CoreWeave `https://investors.coreweave.com`,
Nebius `https://nebius.com/investor-hub` (the `group.nebius.com` path is dead). **The
fastest cross-cut is EDGAR full-text search across all of them at once** for phrases like
`"data center"`, `"finance leases"`, and `"purchase obligations"`. `data.sec.gov/submissions/CIK##########.json`
is also keyless with a proper User-Agent.

**Vendor IR — the supply chain sees the buildout a quarter before the clouds report it.**
Broadcom, Marvell, Arista (`/Financial-Information/default.aspx` — the
`/Financials/Quarterly-Results/` path is a 404), Ciena, Coherent
(`https://www.coherent.com/company/investor-relations` — `investors.coherent.com` is dead),
Lumentum (`investor.lumentum.com`), Vertiv, Super Micro, Credo, **Astera Labs
(`https://ir.asteralabs.com`)**, **Celestica (`https://celestica.gcs-web.com`)**, Fabrinet
(`investor.fabrinet.com`), Amphenol. ⚠️ **The `investor.` vs `investors.` vs `ir.` prefix is
inconsistent across these companies and the wrong guess is usually NXDOMAIN** — verify
before use rather than constructing the hostname.

**Nvidia.** Newsroom `https://nvidianews.nvidia.com` ✅ is more useful than the IR site,
which renders as an empty JS shell; use EDGAR for the numbers. GTC keynote replays are
free and are genuine technical disclosures.

**Specifications and consortia** — spec *publication* is the event; announcements of
intent are not. Ultra Ethernet (free ungated PDF, v1.0.3 as of Jul 2026), CXL 4.0, UALink,
PCI-SIG (members-only specs), OIF implementation agreements (free).

**OCP** `https://www.opencompute.org/` ⚠️ — rack, power, cooling, and optics specifications
contributed by the people actually deploying them, free. **Note the URL shape:** projects
live under `/community/` as well as `/projects/` (`/community/rack-and-power` works,
`/projects/cooling-environments` works). The site 403s WebFetch entirely; `curl --compressed`
with a browser UA gets through. The October Global Summit is a dense primary-source week.

**Conferences.** Hot Chips (`hotchips.org` ✅ — 2026: Aug 23–25, Stanford; architecture
disclosures with slides), Hot Interconnects (`hoti.org` ✅ — 2026: Aug 19–21, virtual),
SC (`https://sc26.supercomputing.org/` ✅ — 2026: Nov 15–20, Chicago), OFC
(`https://www.ofcconference.org/` ✅ — 2027: Mar 7–11, LA), ECOC (`https://www.ecoc2026.org/`
✅ — 2026: Sept 20–24, Málaga), **Nvidia GTC** (`nvidia.com/gtc/` ✅ — Berlin Oct 20–22 2026,
Washington DC Nov 30–Dec 3 2026, San Jose Mar 15–18 2027; **keynote replays are free**).

**Benchmarks.** MLPerf `https://mlcommons.org/benchmarks/` ✅ — the only audited public
hardware performance numbers; **Training v6.0 is the current round**, and note that the
inference-datacenter landing page still renders a stale "V3.1" title, so check the results
post rather than the page header. Results are vendor-submitted with tuned configurations —
read the submission details, not the summary chart. Top500 `https://www.top500.org/` ✅ —
67th list published June 2026; LINPACK is a poor proxy for AI work, and the list's value is
knowing what got built and where.

### Trade press and analysts

The Next Platform `https://www.nextplatform.com/` ✅ (feed `/feed/`), ServeTheHome ✅,
Blocks & Files `https://blocksandfiles.com/` ✅ (storage), Data Center Frontier ✅, Data
Center Dynamics ✅, Light Reading ✅, Fierce Network ✅ (feed at `/rss/xml`; `/feed` is a
404), The Register ✅ (**`/data_centre/` now redirects to `/tag/datacenter`, and there is
no per-tag feed — use `/headlines.atom`**), Dell'Oro ✅ (free press releases), Synergy
Research ✅ (free press releases, no feed), TeleGeography ⚠️ (subscription; but
`submarinecablemap.com` is free), CBRE and JLL datacenter market reports ✅ (free, and the
vacancy and pipeline numbers are real data — note the reporting lag, which runs half a
year), SemiAnalysis ⚠️ (**the WordPress feed at `semianalysis.com/feed/` has been stale
since 2025 — the live one is `newsletter.semianalysis.com/feed`**).

**Site-level data and permitting.** Baxtel ✅ and Cloudscene ✅ are free to browse
(Data Center Map is behind a bot wall and unusable). For a specific project, the real
primary source is **county or municipal records**: find the jurisdiction's permit portal —
almost always Tyler EnerGov, Tyler Munis, Accela, or CitizenServe on an off-domain host —
and note that **rezoning detail usually lives in the Granicus or CivicClerk board agenda
packet, not the permit portal**. This is slow, and it is also where the genuinely
un-covered stories are.

---

## 8. Models

### Primary

| Source | URL | Notes |
| --- | --- | --- |
| arXiv listings | `https://arxiv.org/list/cs.LG/recent` · `cs.CL` · **`cs.AR`** ✅ | `cs.AR` (hardware architecture) is the highest-signal, lowest-volume category for this brief. `cs.LG`/`cs.CL` are firehoses — use them with a specific query, not as a feed. |
| arXiv API | `https://export.arxiv.org/api/query` ✅ | Free, keyless, attribution required. The reliable way to search by category and date. |
| Hugging Face papers | `https://huggingface.co/papers` ✅ | Community-upvoted daily triage of arXiv. Good discovery, popularity-biased — upvotes track demo appeal, not rigor. |
| Hugging Face models | `https://huggingface.co/models?sort=trending` ✅ | The config and model card give parameter count, context length, architecture, and license directly. This is a primary source; the launch blog post is not. |
| OpenReview | `https://openreview.net/` ✅ | Reviews and scores for ICLR/NeurIPS/ICML submissions, often months before publication. Reading the reviewers' objections is the fastest way to find the caveat for a `deeper_md`. Public API available. |
| Lab technical reports and model cards | Anthropic `https://www.anthropic.com/news` ✅ · Google DeepMind `https://deepmind.google/discover/blog/` ✅ · Microsoft Research `https://www.microsoft.com/en-us/research/blog/` ✅ · AI2 `https://allenai.org/blog` ✅ · Meta `https://ai.meta.com/blog/` ✅ · Mistral `https://mistral.ai/news` ✅ · DeepSeek `https://api-docs.deepseek.com/news/` ✅ · NVIDIA research `https://research.nvidia.com/publications` ✅ · EleutherAI `https://blog.eleuther.ai` ✅ · OpenAI `https://openai.com/news/` ⚠️ · xAI `https://x.ai/news` ⚠️ · Qwen `https://qwen.ai` ⚠️ (the old `qwenlm.github.io` blog is frozen at Sept 2025) · Moonshot `https://moonshot.cn` ⚠️ (Chinese only) · Z.ai/GLM ❗ (`z.ai/blog` 404s; correct path not established) | **Distinguish the technical report from the launch post.** System cards, model cards, and evaluation appendices are T1. The launch blog's benchmark bar chart is marketing. AI2/OLMo is the most reproducible (data + weights + code); DeepSeek and Qwen publish genuinely detailed reports; Cohere's blog is nearly all marketing. |

### Evaluation and safety organizations

| Source | URL | Notes |
| --- | --- | --- |
| UK AI Security Institute | `https://www.aisi.gov.uk/` ✅ | **Renamed from AI *Safety* Institute.** Best independent government evaluation work. UK-policy framing. |
| CAISI (NIST) | `https://www.nist.gov/caisi` ✅ | **The former US AI Safety Institute, renamed** Center for AI Standards and Innovation. Publishes adversary-model evaluations. Explicit US-competitiveness framing — read the framing separately from the measurements. |
| METR | `https://metr.org/` ✅ | Autonomy and task-horizon evaluations. Depends on lab-granted access, which is a real conflict; discloses it. |
| Epoch AI | `https://epoch.ai/` ✅ (**not** `epochai.org`, which redirects) | The best quantitative trend data in the field, plus FrontierMath. Bias: extrapolation-friendly; note the OpenAI funding relationship on FrontierMath, which Epoch discloses. |
| Apollo Research | `https://www.apolloresearch.ai/` ✅ | Deception/scheming evaluations. Low cadence; now a PBC, so note the commercial interest. |
| Redwood Research | `https://www.redwoodresearch.org/` ✅ | AI control agenda. Strong prior — cite the experiments, not the framing. |

### Benchmarks and leaderboards

Treat every leaderboard as T2 at best, and read `QUALITY.md`'s rule: a score with no
method is not a fact.

| Board | URL | Status |
| --- | --- | --- |
| Arena | `https://arena.ai/leaderboard` ✅ | **Renamed** — `lmarena.ai` redirects here (Chatbot Arena → LMArena → Arena, Jan 2026). Human preference; style and verbosity bias. Tables render client-side. |
| Artificial Analysis | `https://artificialanalysis.ai/` ✅ | Best cross-cut of price, latency, and capability. Vendor-adjacent commercially. |
| SWE-bench | `https://swebench.com/` ✅ | The de facto coding benchmark. Contamination and scaffold differences make cross-model comparison fragile. |
| Terminal-Bench | `https://www.tbench.ai/leaderboard` ✅ | Best current agentic-terminal evaluation; reports cost alongside score. Scaffold-dependent. |
| ARC Prize | `https://arcprize.org/` ✅ | ARC-AGI-1/2/3; the 2026 prize is running. Narrow domain by design, and the framing carries an anti-scaling thesis. |
| FrontierMath | `https://epoch.ai/frontiermath/tiers-1-4` ✅ | Held-out hard mathematics. |
| OpenRouter rankings | `https://openrouter.ai/rankings` ✅ | Real token-usage share — an adoption signal, explicitly not a quality signal. Sample is OpenRouter's users. |
| MLPerf | `https://mlcommons.org/benchmarks/inference-datacenter/` ✅ | Audited hardware numbers. |
| **Stale — do not treat as current** | Aider polyglot leaderboard (`aider.chat/docs/leaderboards/`, entries stop ~Aug 2025) · HLE site (`agi.safe.ai`, last updated Apr 2025) · GPQA Diamond (effectively saturated) | Use Artificial Analysis for current scores on these instead. |

### Commentary (T2/T3)

Interconnects `https://interconnects.ai` ✅ (open-weights and post-training; author is at
AI2), Ahead of AI `https://magazine.sebastianraschka.com` ✅ (the best architecture
explainers; largely free), Simon Willison `https://simonwillison.net` ✅ (fastest hands-on
testing; low skepticism about risk), The Batch `https://www.deeplearning.ai/the-batch/` ✅,
Zvi Mowshowitz `https://thezvi.substack.com` ✅ (exhaustive, strong doom prior), Import AI
`https://jack-clark.net` ⚠️ (excellent paper summaries; **author is an Anthropic
co-founder — a direct conflict on anything Anthropic-related**), AI as Normal Technology
`https://www.normaltech.ai/` ✅ (**renamed from AI Snake Oil**; the standing skeptical
counterweight), Transformer `https://www.transformernews.ai/` ✅ (policy), The Information
⚠️ (**hard paywall**, best original business scoops), Stratechery ⚠️ (paywalled).

---

## 9. Applications

| Source | URL | Notes |
| --- | --- | --- |
| Nature | `https://www.nature.com/nature.rss` ✅ — **use the RSS; the HTML index redirects to auth** | News free, research mostly paywalled. Highest prestige, and an embargo cycle that inflates novelty. |
| Science / Cell | `science.org` ⚠️ · `cell.com` ⚠️ | Bot-blocked to fetchers; use the publisher's press release plus the DOI. |
| bioRxiv / medRxiv | `https://connect.biorxiv.org/biorxiv_xml.php?subject=all` ✅ · `medrxiv.org` ✅ | Now operated by **openRxiv**. Not peer reviewed — say so every time you cite one. |
| FDA AI-enabled devices | `https://www.fda.gov/medical-devices/software-medical-device-samd/artificial-intelligence-enabled-medical-devices` ⚠️ | **Retitled** from "AI/ML-Enabled" to "AI-Enabled." The only hard ground truth on deployed medical AI: ~1,451 devices authorized through end-2025, ~76% radiology, list last updated 2026-03-04. Explicitly non-exhaustive and keyword-derived, and clearance is not evidence of efficacy. |
| ClinicalTrials.gov | `https://clinicaltrials.gov/api/v2/studies` ✅ | Free JSON API, no key. Registration is not a result. |
| NSF awards | `https://api.nsf.gov/services/v1/awards.json?keyword=…` ✅ | Use the API; the web UI renders blank to fetchers. Earliest signal on academic direction. |
| USPTO | `https://www.uspto.gov/patents/search` ✅ · `https://data.uspto.gov` | 18-month publication lag. |
| DARPA / DoD contracts | `https://www.darpa.mil/news` ⚠️ (JS) · `https://www.defense.gov/News/Contracts/` ⚠️ | Contract announcements carry dollar figures and vendor names — the only hard numbers in defense AI. |
| Synopsys news | `https://news.synopsys.com/` ✅ | Best-verified EDA/AI-in-chip-design source. Entirely vendor marketing — claims are unaudited; pair with DAC/ISPD papers. |
| Cadence / Siemens EDA | `cadence.com` ⚠️ · Siemens EDA ❗ (not verified) | Same caveat. |
| Waymo safety hub | `https://waymo.com/safety/impact/` ✅ | 220.6M rider-only miles through March 2026, broken out by metro. Self-reported and self-selected operating domain, but it is the best public autonomy dataset. |
| Physical Intelligence | `https://www.pi.website/blog` ✅ (**moved** from physicalintelligence.company) | The most technically substantive robotics lab blog. |
| Figure | `https://www.figure.ai/news` ✅ | Demo videos with no metrics. Treat claims as `reported` at best. |
| Census BTOS | `https://www.census.gov/hfp/btos/` ⚠️ (JS) — press releases at `census.gov/newsroom/press-releases/2026/btos-<month>-<day>.html` | **The only nationally representative firm-level AI-adoption series.** Self-reported and definition-sensitive. |
| Ramp Economics Lab | `https://ramp.com/data` ✅ (**`ramp.com/ai-index` is now a 404**) | Fastest corporate AI-spend signal. Sample is Ramp cardholders — startup/SMB-skewed, card-spend proxy only. Always state the sample when citing it. |
| Stanford HAI AI Index | `https://hai.stanford.edu/ai-index` ✅ (**moved** from aiindex.stanford.edu) | Annual compendium, published each April. Comprehensive and always half a year stale. |
| Anthropic Economic Index | `https://www.anthropic.com/economic-index` ✅ | Real task-level usage data, Claude-only and vendor-authored. |

---

## 10. Maintaining this file

This list decays. Sources shut down, rename, move behind paywalls, and start blocking
fetchers. Everything above was checked on **2026-08-20**; the `✅`/`⚠️`/`❗` marks are that
day's result, not a permanent property.

`DAILY_BRIEF.md` §10 requires the daily agent to report any source here that was dead,
moved, or newly paywalled during its run. When that happens:

1. Fix the URL in this file in the same commit as the brief, and update the mark.
2. If a source is genuinely gone, **move it to a struck-through line with a note** rather
   than deleting it — knowing that AnandTech is dead is more useful than its absence.
3. If a source has been quietly wrong more than once, write that down next to it. The bias
   notes in this file are the accumulated memory of the project and they are worth more
   than the URLs.

### Dead or moved as of 2026-08-20 — do not restore these

`anandtech.com` (dead; redirects to forums) · `bis.doc.gov` (dead, no TLS at all →
`bis.gov`) · `natcast.org` (organization terminated → NIST NSTC page) ·
`icknowledge.com` (acquired → TechInsights) · `esscirc-essderc.org` (merged → `esserc.org`)
· `ieee-iitc.org` (never existed → `iitc-conference.org`) · `semivision.com.tw` (DNS
failure → Substack) · `bits-chips.nl` (→ `.com`) · `semiconductordigest.com` (→
hyphenated) · `lmarena.ai` (→ `arena.ai`) · `aisnakeoil.com` (→ `normaltech.ai`) ·
`aiindex.stanford.edu` (→ `hai.stanford.edu/ai-index`) · `epochai.org` (→ `epoch.ai`) ·
`physicalintelligence.company` (→ `pi.website`) · `ramp.com/ai-index` (404 → `ramp.com/data`)
· `qwenlm.github.io/blog` (frozen Sept 2025 → `qwen.ai`) · `mops.twse.com.tw/mops/web/index`
· `www.tsmc.com/english/monthly-revenue` · `semiconductors.org/latest-news/press-releases/`
· `gf.com/investors` · `investor.lamresearch.com/news-events/press-releases` ·
`appliedmaterials.com/us/en/investor-relations.html` · `tel.com/ir/library/results/` ·
`skhynix.com/ir/…` · `computeexpresslink.org/newsroom` · `semi.org/asmc` · `adams.nrc.gov` (NXDOMAIN →
`adams-search.nrc.gov`) · `energy.gov/gdo/*` (Grid Deployment Office → Office of
Electricity) · DOE Loan Programs Office (→ Office of Energy Dominance Financing,
`energy.gov/EDF`) · `zero.princeton.edu` (NXDOMAIN → `zero.lab.princeton.edu`) ·
`datacenterdynamics.com/en/power-cooling/` (→ the energy & sustainability channel) ·
Doomberg on Substack (→ `newsletter.doomberg.com`) · Semafor Net Zero (→ `/vertical/energy`)
· `oracle.com` `/financials/quarterly-reports/` · Arista `/Financials/Quarterly-Results/` ·
`investors.coherent.com`, `investors.asteralabs.com`, `investors.celestica.com` and several
other `investors.*` subdomains (NXDOMAIN) · `lola.loudoun.gov` (NXDOMAIN) — **but the
Loudoun County land-application portal itself is live at `https://www.loudoun.gov/lola` ✅**,
which is the one worth having: Loudoun is Data Center Alley, and its permit filings are
where a buildout shows up before it is announced. Maricopa and Prince William Accela
paths tried on 2026-08-20 all 404.

### Feeds that lie

- **`jedec.org/rss.xml`** — returns HTTP 200 with a newest item from **July 2020**.
  Blacklisted. A 200 is not freshness; check the newest item's date on any feed before
  trusting it.
- **Aider polyglot leaderboard** and **`agi.safe.ai` (HLE)** — both render fine and both
  stopped being updated in 2025.
- **`bis.gov/regulations/federal-register-notices`** — loads and reports zero notices.

### Known gaps to be resolved by a human

The current Z.ai/GLM blog URL · Siemens EDA's newsroom URL · whether WikiChip Fuse
(`fuse.wikichip.org`) and EE Times (`eetimes.com`) are alive or gone · NRC ADAMS' current
search endpoint · OCP's own site and its 2026 Summit dates (fully bot-blocked) · Yole
Group (fully bot-blocked) · IMAPS and IMAPSource access terms · SPIE Advanced Lithography
**2026** dates (the site has rolled over to 2027) · ISPD 2026 dates · DATE 2026 · MRS
Spring 2026/2027 · SEMICON Taiwan and Korea dates · whether an HBM4E JEDEC standard exists
(absence of evidence only — JEDEC's document search is not crawlable) · **LBNL "Queued Up"
current edition** (`emp.lbl.gov` 403s every method) · FERC Form 714 and any FERC RSS ·
PCI-SIG (host refuses the fetcher entirely) · whether ERCOT publishes any public large-load
MW queue report · Eaton and Schneider IR · state datacenter tax-incentive disclosures.
