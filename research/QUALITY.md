# Quality bar

`SPEC.md` defines the schema and the sizing. This file defines what *good* looks like
inside those fields, using worked before/after examples. Read it before writing, and run
the per-item checklist at the bottom before you commit.

> **The examples below are illustrative craft demonstrations, not facts.** Some are built
> on real public knowledge, some are invented to show a shape. **Never copy a number, a
> quote, or a URL out of this file into a brief.** Everything in a real edition comes from
> a document you fetched today.

---

## The one-paragraph version

An item earns its slot when a reader who skips it is worse informed about something that
will still matter in six months. Write the consequence, not the announcement. Write the
mechanism, not the adjective. Put a number on it, with a unit, from a document you
actually opened. Give the reader the standing context before you give them the event, so
that someone who has never met this subfield can use the item at all. If you cannot say who
disagrees or what would falsify the claim, you probably do not understand it well enough to
publish it yet.

---

## Example 1 — a padded item, and its rewrite

### Before (cut this)

```json
{
  "id": "chips-startup-raises",
  "title": "AI chip startup raises $200M Series C",
  "dek": "A Silicon Valley AI chip startup has announced a $200 million Series C funding round led by a major venture firm.",
  "why_it_matters": "The round shows continued strong investor appetite for AI chip startups and validates the company's technology in a competitive market.",
  "deeper_md": "The round brings total funding to $410M. The company was founded in 2021 by former engineers from a major chipmaker. It plans to use the funds to accelerate product development, expand its engineering team, and scale go-to-market operations. The Series C was led by a major venture firm with participation from existing investors.",
  "confidence": "confirmed"
}
```

What is wrong with it:

- The `dek` is the headline with more words. It adds nothing.
- `why_it_matters` says "investor appetite" and "validates," which are true of every
  funding round ever announced and therefore predict nothing.
- `deeper_md` is the press release's boilerplate paragraph. "Accelerate product
  development, expand the team, scale go-to-market" is what every company says.
- No number in the whole item is load-bearing except the headline dollar figure, and the
  dollar figure does not change what gets built.

Per the finance rule in `DAILY_BRIEF.md` §4: **a financial document is a source, never a
subject.** A round, a valuation, an acquisition, or a quarter's results is never the thing
the item is about. **Default action: kill it.**

The mechanical version of that rule, and the one to actually run on a draft:

> **Strike every dollar figure from the item. If nothing technical is left standing, cut
> the item.**

Do it literally on the "before" block above. Delete `$200 million`, `$410M`, and `Series
C`, and what remains is "a company exists and intends to develop products." There is no
machine, no physics, and no code on the page. That is the whole test, and it takes ten
seconds.

Note what the test does *not* say. It does not say avoid filings — filings are T1 evidence
and the brief leans on them heavily. A 10-Q purchase-obligations note, a take-or-pay wafer
commitment, or a capacity reservation is a statement about what will physically be built,
usually the earliest one available. Cite it, and write the item about the thing being built.
Consider an item sourced entirely from an earnings call, whose subject is that cleanroom
floor space — not tool lead time — is what caps how fast equipment capacity can grow. Strike
the capex figure and the constraint is still standing. That item passes.

### After (only if what the money buys is a physical commitment)

```json
{
  "id": "chips-analog-inmem-tapeout-funding",
  "title": "Analog in-memory startup funds a 12-inch tapeout after two shuttle runs",
  "dek": "A startup building chips that do matrix multiplication inside the memory array itself — instead of shuttling numbers to a separate compute unit — raised enough to pay for a full production mask set, the first hard commitment in a field that has mostly lived on multi-project shuttle wafers.",
  "why_it_matters": "Analog in-memory compute has had promising research silicon for a decade and almost no production silicon, because a full mask set at an advanced node costs more than most of these companies had raised in total. Paying for one is the step that turns a paper result into something a customer can buy, and it puts a date on when the accuracy-versus-efficiency claims get tested by someone other than the authors.",
  "confidence": "reported"
}
```

The rewrite passes because **the subject is the mask set, not the round.** A mask set is a
specific, expensive, irreversible physical commitment, and it is the thing that changed; the
financing is one sourced clause inside the sentence, doing the work a source does. Run the
strike test on it: there is no dollar figure in the item at all, and everything still
stands. That is the shape the finance rule permits — the round is never the subject, but a
named physical capability the money buys can be. Notice too that `dek` expands "in-memory
compute" inline, in the sentence, without a parenthetical lecture, and that `confidence` is
`reported`, not `confirmed`, because a funding announcement without a filing is a company
telling you about itself.

Be honest about how rare this is. The overwhelming majority of rounds do not clear this bar,
and "but the money buys capability X" is exactly the rationalization a padded item reaches
for. If you cannot name the physical thing, with a specificity a reader could later check,
the answer is the default: kill it.

---

## Example 2 — `why_it_matters` that restates the `dek`

### Before

```
dek:            "TSMC said its 2 nm process entered volume production at Fab 20 in
                 Hsinchu, with a second site in Kaohsiung ramping later this year."
why_it_matters: "This marks an important milestone for TSMC's 2 nm technology and
                 demonstrates the company's continued leadership in advanced process
                 nodes as it expands capacity across multiple sites."
```

That is the `dek` again with "important milestone" and "continued leadership" bolted on.
`SPEC.md` rule 3 says cut the item. But usually the right fix is not to cut — it is that
the writer stopped at the announcement and never asked *so what*.

### After

```
why_it_matters: "Volume production at two sites at once is the part that is new: the
                 previous node ramped from one site for three quarters, which is what
                 rationed early supply and set prices. Two ramping fabs is the first
                 signal that wafer allocation for 2 nm will be decided by customer
                 commitments rather than by capacity, which changes who can get it."
```

The test: **cover the `dek` with your hand and read `why_it_matters` alone.** If it still
carries information — a consequence, a constraint, a thing that becomes possible or
impossible — it passes. If it only makes sense as an echo, rewrite it.

Three reliable ways to find the consequence when you cannot see one:

1. **Who is now constrained?** Whose plan gets harder or cheaper because of this?
2. **What was the previous number?** Almost nothing is interesting in isolation and almost
   everything is interesting as a delta.
3. **What does this make measurable?** A date, a spec, or a filing turns an argument into
   something that can be checked later.

If none of the three produces an answer, the item is not an item.

---

## Example 3 — `deeper_md` as a longer restatement vs. `deeper_md` that adds mechanism

The `deeper_md` block is the reason the club's technical core reads this at all. It is
**not** a summary written again at greater length. It should contain things the member
tier deliberately left out: numbers with units, the physical or economic mechanism, the
named caveat, and the name of whoever disputes it.

### Before

```markdown
The new packaging technology allows more chips to be connected together with higher
bandwidth. This is important for AI accelerators, which need to move large amounts of
data between compute and memory. The company says the technology offers significant
improvements over the previous generation and will enter production next year.
Analysts have described the announcement as significant for the advanced packaging
market, which has been supply constrained.
```

Everything in that paragraph is either in the `dek` already or is unfalsifiable. "Higher
bandwidth," "significant improvements," "supply constrained" — no numbers, no mechanism,
no source of disagreement. It is 60 words of nothing.

### After

```markdown
The claimed step is bump pitch: 25 µm microbumps to 6 µm hybrid-bonded pads, roughly
17× the interconnect density per unit area (density scales as pitch⁻²). That is the
mechanism behind the bandwidth number — the interface gets wider, not faster, so the
energy per bit falls with the shorter link rather than rising with frequency; the
paper reports 0.05 pJ/bit versus 0.25 pJ/bit for the microbump baseline (Table 3).

Two caveats the presentation does not lead with. First, hybrid bonding needs surface
flatness on the order of a nanometer over the whole bonding area, which pushes the
requirement back onto CMP and onto particle control — one 0.5 µm particle voids the
bond over a region far larger than itself. Second, the yield figure quoted is
bond-level, not stack-level; for a 4-high stack the compounded number is what matters
and it was not given.

Two independent packaging analysts have argued the pitch number is a research vehicle
rather than a production spec, pointing out that the demonstrated die size was 4 mm²
against production reticles of 800 mm²+, where warpage across the die dominates.
```

Length is similar. Information density is not. Note what it does:

- **Numbers carry units and a source location** ("Table 3"), so a reader can check.
- **The mechanism is stated**, not gestured at: wider interface, shorter link, lower
  energy per bit — and *why* pitch⁻² gives 17×.
- **The caveats are specific and physical**, and they connect back to a process step
  (CMP, particle control) the audience can picture.
- **The dispute is named as a position**, with the reason behind it, not as "some
  analysts are skeptical."

If you cannot write a `deeper_md` like the "after" version, you did not read a primary
source. Go read one. That is the fix, not better adjectives.

---

## Example 4 — written from the press release vs. written from the paper

**This is the single most important example in this file.** Trade press exists to tell you
that something happened. It is almost never sufficient to tell you *what* happened. The
rule in `DAILY_BRIEF.md` is: use the aggregator to find the story, then go get the
document and write from that.

Same event, two versions.

### Before — written from the press release and a trade write-up

```
title:  "Memory maker announces next-generation HBM with higher bandwidth"
dek:    "A leading memory manufacturer announced its next-generation high-bandwidth
         memory, which the company says delivers significantly improved bandwidth and
         power efficiency for AI accelerators."
deeper: "The company said the new product represents a major advance and will begin
         mass production in the second half of next year, pending customer
         qualification. The announcement was made at an industry conference. Analysts
         expect strong demand given AI datacenter buildouts."
sources: [ company newsroom post, trade site summary of the company newsroom post ]
confidence: "confirmed"
```

Notice the two sources are one source. The trade site summarized the newsroom post. That
is a single-source item wearing a disguise, and `SOURCES.md` says to treat it as one.

### After — written from the conference paper and the standard

```
title:  "HBM base die moves to a logic process, and the thermal budget moves with it"
dek:    "The next generation of high-bandwidth memory — the stacks of DRAM sitting
         beside an AI accelerator — puts its bottom control die on a logic process
         instead of a DRAM process, which lets the memory vendor put customer logic
         inside the memory stack and makes the stack meaningfully harder to cool."
why:    "This is the point where memory stops being a commodity part bought on price
         per gigabyte. If the base die carries customer-specific logic, the stack has
         to be co-designed with the accelerator, qualification stops being fungible
         between vendors, and switching suppliers late in a program stops being
         possible. It also moves a heat source underneath the DRAM, which is the layer
         with the tightest temperature limit in the package."
deeper: "The published spec puts the interface at 2,048 bits per stack at a per-pin
         rate of 8 Gb/s, so about 2 TB/s per stack against roughly 1.2 TB/s for the
         prior generation — the gain is interface width, not pin speed, which is why
         it needs the finer TSV pitch rather than a faster I/O circuit.

         The thermal problem is the interesting part. DRAM retention is exponential in
         temperature; refresh interval roughly halves every 10 °C, so a hotter stack
         spends more of its bandwidth on refresh and less on the accelerator. Putting
         an active logic die at the bottom of the stack adds heat below eight DRAM
         dies whose thermal path runs *up* through the stack, and the paper's own
         measurements (Fig. 7) show the top die running warmest.

         Caveat: the bandwidth number is a peak interface figure at nominal voltage.
         Sustained bandwidth under a realistic access pattern was not reported, and
         the two prior generations both landed below their headline number in
         independent measurement."
sources: [ JEDEC standard page, conference paper PDF, vendor technical brief,
           independent measurement writeup ]
confidence: "reported"
```

What changed, and why it is worth the extra twenty minutes of fetching:

| | Press-release version | Document version |
| --- | --- | --- |
| Numbers | "significantly improved" | 2,048 bits, 8 Gb/s, ~2 TB/s vs ~1.2 TB/s, with the source of the gain identified |
| Mechanism | none | width not frequency → finer TSV pitch → base die on logic process → heat under the DRAM |
| Caveat | none | peak vs sustained, and the prior track record on that gap |
| What a reader learns | that a company made an announcement | why memory vendors and accelerator vendors are now locked together, and one physical reason it is hard |
| Falsifiable? | no | yes — sustained bandwidth can be measured later |
| Sources | one, restated twice | four, three of them primary or technical |

The title also changed. "Company announces product" is a press-release title. "The base
die moves to a logic process, and the thermal budget moves with it" is a *finding*.

Note the honest `confidence` downgrade: a specification and a conference paper describe
what is intended and what was measured on test silicon, which is `reported`, not
`confirmed` production behavior.

---

## Example 5 — a Foundations section that reads like an encyclopedia vs. one that teaches

### Before

```markdown
## Chemical mechanical planarization

Chemical mechanical planarization (CMP) is a process used in semiconductor
manufacturing to planarize wafer surfaces. It was developed by IBM in the 1980s and
became widely adopted in the 1990s. The process uses a combination of chemical and
mechanical forces. A rotating polishing pad and a chemical slurry are applied to the
wafer surface. CMP is used for both dielectric and metal planarization, including
shallow trench isolation, interlayer dielectric, and copper damascene processes. Key
process parameters include down force, platen speed, and slurry chemistry. Common
defects include dishing, erosion, and scratches.
```

Accurate. Complete. Teaches nothing. It is a list of true nouns. A reader finishes it
able to recognize the words and unable to predict anything.

### After

```markdown
## Why flatness is the whole game

Here is the constraint everything else follows from. A modern exposure tool focuses
light into a layer of resist with a depth of focus measured in tens of nanometers —
call it 100 nm to be generous. Anything on the wafer surface taller than that budget
is out of focus, and out of focus means the pattern does not print.

Now count what a single metal layer adds. You etch trenches, fill them with copper,
and the copper piles up over the dense regions and sags over the empty ones. The
resulting topography is easily 500 nm — five times the entire focus budget — and you
have ten more layers to build on top of it. Without planarization you can print two
or three layers and then you are finished, because layer four has nothing flat to
land on.

That is why CMP exists, and it explains the thing that surprises people first: the
process deliberately scratches the wafer. You press the wafer face-down onto a
rotating polyurethane pad and flood the interface with a slurry of nanometer-scale
abrasive particles in a reactive chemistry. The chemistry softens the top few atomic
layers into something mechanically weak; the abrasive wipes that weakened layer away.
Neither half works alone — chemistry alone etches everywhere including the low spots,
abrasive alone gouges. It is planarizing rather than merely thinning because the high
spots carry more of the contact pressure, so they are removed faster. Removal rate
tracks pressure times velocity, which is Preston's equation, and it is the reason CMP
engineers spend their lives on pad conditioning and pressure uniformity.
```

The difference is not tone and it is not length. It is that the "after" version:

1. **Starts from a constraint the reader can feel** (100 nm focus budget vs 500 nm of
   copper topography) rather than from a definition.
2. **Makes one number do the argumentative work.** 5× the focus budget, ten layers to go.
3. **Explains the counterintuitive thing** — why grinding the wafer makes it flatter —
   instead of listing that both chemical and mechanical forces are involved.
4. **Introduces jargon after the idea it names**, never before. Preston's equation arrives
   as a name for something the reader just understood, not as a term to be defined.
5. **Ends pointing somewhere** — pad conditioning, pressure uniformity — which is where
   the next section starts.

A Foundations section is a piece of teaching with a beginning, a load-bearing middle, and
a handoff. If your section would survive having its sentences shuffled, it is a list, not
an explanation. Rewrite it.

**The `try_this` test.** `try_this` must be something a MNF member could actually
do, see, or read *this week* with the access they have. Good: measure the contrast curve
of the resist on the shelf and plot dose-to-clear; hold a CMP pad from the teaching lab
and look at the grooves; read section 3 of a specific named paper; pull one company's
10-K and find the capex line. Bad: "learn more about CMP"; "consider the implications";
anything that requires a tool the club does not have or a paywall it cannot pass.

---

## Example 6 — `background_md` that gives footing vs. a news summary in disguise

`background_md` is required on every Pulse item, and it is the field that decides whether a
reader who has never met this subfield can use the rest of the item at all. Two to four
sentences, 50–110 words, and it answers exactly three questions: **what is this area, what
problem does it exist to solve, and why would anyone care?**

There is one test, and almost every bad `background_md` fails it:

> **Delete the news. Would this paragraph still be true next year?**

Background is the standing context the news sits in. It is not a second summary of the
event — the `dek` already did that, and spending the reader's one paragraph of footing on a
restatement leaves them exactly as lost as before.

Take a monolithic-3D research item as the worked case.

### Before (this is a news summary with the wrong field name on it)

```markdown
In recent years, monolithic 3D integration has attracted significant interest as a
promising path to continued scaling. Researchers have now demonstrated a process that
grows a second layer of transistors directly on top of an existing device layer, rather
than bonding two finished wafers together. The work represents an important step toward
practical 3D chips and could eventually change how processors are built.
```

Why it fails, in order of severity:

1. **It does not survive the delete-the-news test.** Every sentence is about the
   demonstration. Remove the demonstration and the paragraph is empty. That is the
   definition of a news summary, and it is the failure this field exists to prevent.
2. **It repeats the `dek`.** The reader is told twice that someone grew transistors on top
   of transistors, and told nothing about why that is hard.
3. **There is no mechanism and no constraint.** "Promising," "important step," "could
   eventually" — nothing here can be wrong, so nothing here is information.
4. **It opens with "In recent years."** Throat-clearing that delays the first real sentence
   by a full clause. Banned; see below.
5. **A reader who did not know what the back end of a chip is still does not.** The
   paragraph assumed the very knowledge it was supposed to supply.

### After

```markdown
Chips are normally built as a single layer of transistors with copper wiring stacked
above them. Monolithic 3D means growing a *second* layer of transistors on top of that
wiring instead of bonding two finished wafers together, which would buy density without
needing finer lithography. The obstacle is heat: everything above the first layer has to
be built below roughly 400 °C or the copper and insulating material already in place
degrade. That thermal ceiling is why the field keeps looking at oxide semiconductors
deposited at low temperature rather than conventional silicon.
```

Every sentence of that is still true next year. It is the world, not the event. Note what
it does:

- **It starts from the object, not from a trend.** First sentence: how chips are normally
  built. The reader now has somewhere to stand.
- **It names the alternative it is being compared against** — wafer bonding — because a
  reader cannot evaluate "instead of" without knowing what the instead is.
- **It states one hard constraint with a number**: roughly 400 °C, and *why* (copper and
  the insulator degrade). A standing number is worth ten adjectives, and this one does not
  expire.
- **It ends pointing at the consequence** — low-temperature oxide semiconductors — which is
  exactly where the item's `deeper_md` will pick up.
- **No analogy.** Nobody is told to think of it like a layer cake. Mechanism, then stop.

The same shape works outside semiconductors, which matters now that `computing` is a layer.
For an item about a new register-allocation algorithm:

```markdown
A compiler's last serious decision is which of a program's values live in the processor's
few dozen registers and which get written out to memory, because a register access costs
about a cycle and a memory access costs tens to hundreds. Choosing well is equivalent to
coloring a graph, which is NP-complete, so every production compiler runs a heuristic and
accepts that it will sometimes spill a value it should have kept. Register allocation has
therefore stayed an open problem for fifty years: the theory is settled and the practice
is still tuning.
```

Same test, same result: delete the news and it stands. Same rules — a constraint the reader
can feel (one cycle versus hundreds), a named mechanism (graph coloring, NP-complete), no
analogy, no throat-clearing.

### Three other shapes that fail

- **The definition.** "Monolithic 3D integration is a technique for building multiple
  layers of transistors in a single fabrication flow." True, 20 words, teaches nothing.
  That is a glossary entry, not footing.
- **The analogy dodge.** "Think of it like building a second storey on a house instead of
  buying a second house." The reader now has a picture and still cannot tell you what goes
  wrong. An analogy after the mechanism is a gift; an analogy instead of it is a dodge.
- **The stakes essay.** "As AI workloads grow, the demand for compute has never been
  higher, and the industry is under pressure to find new ways to scale." This is true of
  every item in the brief and therefore belongs in none of them.

---

## Example 7 — a per-item `glossary`

Required on every Pulse item: **2–4 entries**, each `{ "term": …, "definition": … }`, one
sentence each, ≤ 40 words. Same worked item as Example 6.

### Before

```json
"glossary": [
  { "term": "BEOL", "definition": "Back end of line." },
  { "term": "Monolithic 3D", "definition": "A monolithic 3D integration approach." },
  { "term": "IGZO", "definition": "Indium gallium zinc oxide, a material used in the semiconductor industry." }
]
```

Three entries, and not one of them is a definition:

- **"BEOL — back end of line"** expands an acronym and stops. The reader can now pronounce
  it. **Expanding an acronym is not a definition.** If your entry is complete once the
  letters are spelled out, you have not written one.
- **"Monolithic 3D — a monolithic 3D integration approach"** defines a term with itself.
- **"IGZO — a material used in the semiconductor industry"** is true of roughly everything
  and predicts nothing. Say what it *is* and what it *does*.
- And the list skips every symbol and unit in the item, which is where a newcomer actually
  gets stuck.

### After

```json
"glossary": [
  { "term": "BEOL (back end of line)", "definition": "The copper wiring stack built above the transistors; copper and the low-k insulator around it degrade with heat, so everything added after it must be processed below roughly 400 °C." },
  { "term": "Thermal budget", "definition": "The cumulative time-at-temperature a wafer can absorb before already-built structures are damaged — here about 400 °C for anything above the first transistor layer." },
  { "term": "IGZO", "definition": "An amorphous indium–gallium–zinc-oxide semiconductor that can be deposited below 400 °C and leaks extremely little when off, which is why it is the usual candidate for a transistor built up in the wiring stack." },
  { "term": "mV/dec (subthreshold swing)", "definition": "The gate voltage a transistor needs to change its current tenfold; room temperature puts a floor near 60 mV/decade, so it is the number that says whether a new channel material is competitive." }
]
```

What changed:

| | Before | After |
| --- | --- | --- |
| BEOL | the letters spelled out | what it physically is, and the constraint it imposes |
| Coverage | three words | two words, one concept, **one unit** |
| Circularity | "monolithic 3D is a monolithic 3D approach" | dropped — `background_md` already teaches it |
| Usefulness | reader can pronounce the terms | reader can parse `deeper_md` |

Two habits worth naming. **Cover symbols and units, not only words** — `V_th`, `mV/dec`,
`WNS/TNS`, `pJ/bit`, `GT/s`, `k₁`, `σ` are exactly what stops a reader cold, and exactly
what a glossary written on autopilot skips, because they do not look like vocabulary. And
**define only what the item actually uses**: if `deeper_md` never says "damascene,"
damascene does not belong here, however central it is to the subfield.

Fewer than two entries means you did not read your own prose adversarially. More than four
means the item is trying to teach too much at once — cut it back, or move the teaching into
`background_md`, which is the field built for it.

---

## Per-item checklist

Run this on every Pulse item before it goes in the file. An item that fails any of the
first six gets fixed or cut — there is no third option.

1. **Primary source present.** At least one source is a paper, filing, standard, patent,
   transcript, proceeding, dataset, or vendor technical document — not a press release
   and not an aggregator. I fetched it myself.
2. **Every URL fetched.** I opened every URL in `sources`. None came from memory or from
   a link in another article that I did not click.
3. **Every number traceable.** Every figure in `dek`, `why_it_matters`, and `deeper_md`
   appears in one of the cited documents, with the unit the document used. No number is
   converted, rounded, or combined without saying so.
4. **`why_it_matters` survives hand-over-`dek`.** Read alone, it carries a consequence.
5. **`dek` stands alone.** It will appear in Discord with no headline, no layer heading,
   and no other item beside it. It names the actor and the thing, expands its own jargon,
   and reads correctly cold on a phone screen.
6. **It survives the strike test.** Delete every dollar figure in the item. Something
   technical — a machine, a physical constraint, a piece of code — is still standing. A
   round, a valuation, a transaction, or a quarter's results is never the subject.
7. **Sources are independent.** Two outlets summarizing the same press release count as
   one source. If everything traces to one origin, `confidence` is at most `reported`.
8. **`confidence` is honest.** `confirmed` = a primary document says it or two independent
   originals agree. `reported` = a credible outlet with sourcing, or a company describing
   itself. `rumored` = supply-chain chatter, unnamed sources, a single social post.
9. **`background_md` is background.** Present, 50–110 words, and it survives the
   delete-the-news test: remove the event and it is still true next year. It explains a
   mechanism rather than reaching for an analogy, it does not repeat the `dek`, and it does
   not open with "In recent years."
10. **`glossary` has 2–4 real definitions**, covering the symbols and units the item uses as
    well as the words. No entry is an acronym spelled out. No duplicate `term`.
11. **`deeper_md` adds a mechanism, a number, and a caveat** — not a longer paragraph.
12. **The title is a finding, not an announcement.** Prefer "X moves to Y, and Z follows"
    over "Company announces X." Under 80 characters.
13. **`fab_angle` is omitted unless it is real.** A forced one is worse than none.
14. **Not already covered.** Not in the last 7 editions, unless it is explicitly framed as
    an update with what changed.
15. **One story, one item, one layer.** Not the same event split across two layers. It is
    filed under the layer that owns the thing that changed — analog and process work in
    `silicon`, architecture and systems *research* in `computing`, shipping products in
    `chips` — and the other half of a spanning story is a sentence in `deeper_md`.
16. **Banned constructions absent.** See below.

---

## Banned constructions

These are banned because each one is a place where a writer reached for emphasis instead
of information. If you want the reader to feel that something is significant, give them
the fact that made *you* feel it.

**Hype adjectives and nouns.** game-changer, game-changing, revolutionary, groundbreaking,
seismic, watershed, unprecedented, massive, huge, staggering, eye-watering, blistering,
blazing-fast, breakneck, monster, beast, insane, wild, jaw-dropping, mind-blowing,
next-level, cutting-edge, state-of-the-art (as praise rather than as a benchmark
comparison), best-in-class, world-class, industry-leading, paradigm shift, holy grail,
silver bullet, secret sauce, arms race, gold rush, Moore's Law is dead (as a standalone
claim), the death of X, the end of X.

**Empty openers and filler transitions.** "In the world of X…", "In today's fast-moving
X…", "It's no secret that…", "As we all know…", "Let's dive in", "Buckle up", "Here's the
kicker", "But here's the thing", "That said" (used as a beat rather than a contrast),
"Needless to say", "At the end of the day", "It remains to be seen", "Only time will
tell", "The implications are profound", "This could be huge."

**Hedging that conveys nothing.** "may or may not", "could potentially", "is expected to
possibly", "some analysts believe" (name them or cut it), "reports suggest" (which
report?), "it is understood that", "sources say" (whose?), "is poised to", "is set to
revolutionize", "signals a shift", "underscores the importance of", "highlights the
growing trend of." Real hedging names the uncertainty: *what* is unknown, *who* would
know, and *when* it gets resolved.

**Faux urgency.** "breaking", "just in", "you need to know", "everyone is talking about",
"the race is on", "the clock is ticking", "make no mistake", "this changes everything."
The brief runs daily and covers a seven-day window. Nothing in it is breaking.

**Announcement scaffolding.** "announced today", "unveiled", "took the wraps off",
"showcased", "is proud to", "marks a milestone", "represents a significant step forward",
"demonstrates the company's commitment to." These are press-release verbs. If you find one
in your draft, you are probably writing from a press release — which is the actual problem
the phrase is warning you about.

**Background-paragraph tells.** `background_md` invites a register that reads like a
literature review, and every phrase in it is a way of not saying anything: "In recent
years", "Over the past decade", "As AI workloads grow", "With the slowing of Moore's Law",
"has attracted significant interest", "has emerged as a promising approach", "is an active
area of research", "has long been a challenge", "researchers have long sought", "is one of
the most promising candidates", "represents an important step toward", "could eventually
enable", "is expected to play a key role". Also banned here specifically: **"Think of it
like…", "is essentially just…", "imagine a…"** — the analogy dodge, which does more damage
in `background_md` than anywhere else, because this is the paragraph the reader was relying
on for the mechanism. Start with the object or the constraint, in the first six words.

**Glossary tells.** An entry that consists only of the expanded acronym ("BEOL — back end
of line"). An entry that defines a term with itself ("monolithic 3D — a monolithic 3D
approach"). And the three filler openers that guarantee a non-definition: "**refers to**",
"**is a type of**", "**is a technique used in**". If the entry would still be true with a
different term in front of it, it is not a definition.

**Two specific bans worth calling out.** Never write that a company is "leading" or
"leapfrogging" unless you cite the measurement and the metric. And never write "up to" a
number without also writing what it was measured at — "up to 4× faster" with no workload
named is a marketing claim, and repeating it uncritically makes the brief an amplifier.

---

## Word-count discipline

`SPEC.md` targets ~1,100 words of Pulse prose (`dek` + `why_it_matters` across all items)
and ~1,100 words of Foundations. With 7–13 items, that is roughly 100–150 words per item
for the member tier. Practical guides:

- `dek`: one sentence, 25–45 words. It may be long, but it must be one idea.
- `why_it_matters`: one or two sentences, 30–70 words.
- `background_md`: two to four sentences, 50–110 words; anything outside 45–120 is a
  warning. Under 45 you have written a definition rather than footing; over 120 you have
  started writing `deeper_md` a second time.
- `glossary`: 2–4 entries, one sentence each, ≤ 40 words.
- `deeper_md`: 80–200 words per `SPEC.md`. Under 80 usually means you did not read a
  primary source; over 200 usually means you are narrating the paper instead of extracting
  from it.
- Foundations `sections`: at least three, 100–180 words of `body_md` each. Four to six
  sections is the usual shape for ~1,100 words.
- Foundations `glossary`: at least four entries — a longer piece earns a longer list than
  the 2–4 a Pulse item carries. Define terms that appear in the piece, in the sense
  the piece used them. Definitions are one or two sentences and are allowed to be
  opinionated about what matters.

If you are over budget, cut the weakest item entirely rather than trimming every item into
uselessness. If you are under budget, do not inflate — see the short-week rule in
`DAILY_BRIEF.md`.
