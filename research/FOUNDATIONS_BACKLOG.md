# Foundations backlog — the rotating queue

The Foundations half of each edition (see `SPEC.md`) explains **one piece of existing
technology**, properly. Not news. This file is the queue it draws from.

Every row has a **slug** (kebab-case, goes straight into `foundations.slug` in the brief
JSON), a **topic** (goes into `foundations.topic`), a **one-line angle** — the reason the
topic is worth 1,100 words rather than a Wikipedia link — and a **difficulty** tag.

- `intro` — a first-year student with high-school chemistry and physics can follow it.
- `core` — assumes a semiconductor devices or process course, or one summer in a fab.
- `advanced` — assumes the reader already knows the `core` version and wants the physics,
  the failure modes, and the numbers.

**★ = especially relevant to MNF's maskless lithography stepper.** These are the
topics where the club is going to hit the physics personally: optics and resolution,
resist processing, stage positioning and overlay, DMD behavior, and the metrology needed
to know whether a print worked. Roughly one Foundations edition in four should be a ★
topic. Do not make it more than that — the brief is about the world, not the club.

---

## Rotation rule

1. **Default: take the highest row in the table that has not run in the last 90 days.**
   Read the last 90 editions in `briefs/` (or all of them, if fewer exist) and collect
   every `foundations.slug`. Skip any slug in that set. Tables are read top-to-bottom,
   section by section, in the order they appear in this file.
2. **Mix the difficulty.** Look at the last 7 editions' Foundations difficulty tags. Do
   not run three `advanced` topics in a row, and do not run five `intro` topics in a row.
   If the default pick would violate that, take the next eligible row that does not.
3. **Mix the section.** Do not run two topics from the same `##` section on consecutive
   days. Skip down to the next eligible row in a different section.
4. **Override for relevance.** If a Pulse item in today's edition makes a specific
   Foundations topic unusually useful — a high-NA EUV shipment makes `high-na-euv` the
   obvious companion piece, an HBM5 spec vote makes `hbm-stack-architecture` the obvious
   companion piece — take that topic instead of the queue pick, *provided* it has not run
   in the last 90 days. Say so in one clause of the `subtitle` or the `tldr` so the reader
   sees the connection. Use this override at most twice a week; if every Foundations piece
   chases the news, the section stops being evergreen and becomes a second Pulse.
5. **Never override into a repeat.** If the relevant topic ran 40 days ago, do not rerun
   it. Link the earlier edition from the Pulse item's `deeper_md` instead and take the
   normal queue pick.
6. **Keep the queue fed.** Count the rows that have never run. If that count drops below
   30, append at least three new rows to the appropriate sections before writing today's
   edition — the same run that consumes a topic replenishes the queue. New rows must be
   evergreen technology, not news framed as background.
7. **Retiring a topic is allowed.** If a row turns out to be too thin for 1,100 honest
   words, or duplicates another row, delete it and note the deletion in the commit
   message. Do not silently leave dead rows to be picked again next quarter.

---

## Lithography and patterning

| slug | topic | angle | level | ★ |
| --- | --- | --- | --- | --- |
| `photolithography-basics` | Photolithography, end to end | The whole loop — coat, expose, develop, etch, strip — and why every other process step exists to serve it | intro | ★ |
| `resolution-limits-k1-na` | Resolution, NA, and the k₁ factor | Rayleigh's equation is three symbols that set the entire economics of the industry; what each one costs to improve | intro | ★ |
| `contact-proximity-projection` | Contact, proximity, and projection printing | Three ways to get a pattern onto resist, and why the cheap ones damage the mask | intro | ★ |
| `stepper-vs-scanner` | Steppers and scanners | Why the industry moved from stepping a whole field to scanning a slit, and what that bought in field size and distortion | intro | ★ |
| `depth-of-focus` | Depth of focus and why wafers must be flat | The DOF budget is tens of nanometers; every upstream process step is fighting for a slice of it | core | ★ |
| `photoresist-chemistry` | Photoresist chemistry | Novolac/DNQ vs chemically amplified resists — the acid-catalyzed cascade that made deep-UV possible and made resist storage a headache | core | ★ |
| `contrast-curve-dose-to-clear` | Contrast curves and dose-to-clear | The one characterization every new resist needs, how to measure it on a bench, and what γ actually predicts | intro | ★ |
| `resist-track-and-bake` | The coat/develop track | Spin curves, soft bake, post-exposure bake, puddle develop — the unglamorous steps that dominate CD uniformity | intro | ★ |
| `overlay-and-alignment` | Overlay and alignment | Printing layer 12 on top of layer 11 to a few nanometers: alignment marks, grid models, and where the error budget goes | core | ★ |
| `wafer-stage-nanopositioning` | Wafer stages and nanopositioning | Interferometers, encoders, air bearings, and moving a 30 kg stage at 1 g while holding sub-nanometer position | advanced | ★ |
| `illumination-and-pupil-shaping` | Illumination engineering | Annular, dipole, quadrupole, and freeform pupils — reshaping the source to buy resolution for one specific pattern | advanced | ★ |
| `opc-and-resolution-enhancement` | OPC, phase-shift masks, and inverse lithography | The mask stops looking like the circuit; how much compute now sits between GDS and glass | core | |
| `immersion-193i` | 193 nm immersion lithography | A puddle of water as a lens element — and the twenty years of workhorse patterning that followed | core | |
| `multipatterning-sadp-saqp` | Multipatterning: LELE, SADP, SAQP | Making pitches the exposure tool cannot resolve, by using spacers as the real mask | core | |
| `euv-source-physics` | The EUV source | Tin droplets shot at 50 kHz, hit twice by a CO₂ laser, converting a few percent of the light — the least-efficient step in the industry | advanced | |
| `euv-optics-and-multilayers` | EUV optics and Bragg multilayers | Nothing transmits at 13.5 nm, so everything reflects — Mo/Si stacks, vacuum, and the photon budget | advanced | |
| `high-na-euv` | High-NA EUV | 0.55 NA buys resolution and costs half the field; the anamorphic optics and the stitching problem that follows | advanced | |
| `euv-stochastics-and-ler` | Stochastics, shot noise, and line-edge roughness | At 13.5 nm each photon carries 92 eV, so there are fewer of them — and Poisson statistics become a yield problem | advanced | |
| `photomask-manufacturing` | How a photomask is made | E-beam writing onto quartz, defect repair, and why a mask set costs as much as a house | core | |
| `pellicles` | Pellicles | A membrane held above the mask so particles land out of focus; why EUV made this nearly impossible | advanced | |
| `maskless-lithography` | Maskless lithography | DMD, LCD, and laser-direct-write systems: throughput vs flexibility, and where the maskless approach genuinely wins | core | ★ |
| `dmd-micromirror-devices` | Digital micromirror devices | A million hinged aluminum mirrors switching in microseconds, and the diffraction physics of using them as a photomask | core | ★ |
| `electron-beam-lithography` | Electron-beam lithography | Nanometer resolution with no mask, at a throughput that makes it a research tool — plus proximity-effect correction | core | ★ |
| `nanoimprint-lithography` | Nanoimprint lithography | Stamping resist instead of exposing it: the defectivity and template-wear problems that keep it out of logic | core | |
| `directed-self-assembly` | Directed self-assembly | Block copolymers that phase-separate into lines and holes, guided by a coarse pre-pattern | advanced | |
| `mask-cost-and-mpw-shuttles` | Mask cost and multi-project wafers | Why shuttle runs exist, what a tapeout actually costs at 130 nm vs 3 nm, and how students get real silicon | intro | ★ |

## Deposition

| slug | topic | angle | level | ★ |
| --- | --- | --- | --- | --- |
| `thermal-oxidation` | Thermal oxidation and Deal–Grove | The one process that made silicon win over germanium, and a model simple enough to solve by hand | intro | ★ |
| `spin-coating-physics` | Spin coating | Thickness goes as ω^(−1/2): the fluid mechanics behind the most-used step in a teaching cleanroom | intro | ★ |
| `pvd-sputtering` | Sputtering and evaporation | Knocking atoms off a target with plasma, step coverage, and why PVD lost the via but kept the barrier | core | ★ |
| `cvd-lpcvd-pecvd` | CVD: LPCVD, PECVD, and the pressure trade | Conformality, temperature budget, and why plasma lets you deposit nitride below 400 °C | core | ★ |
| `atomic-layer-deposition` | Atomic layer deposition | Self-limiting surface chemistry, one monolayer per cycle — the only way to line a 60:1 aspect-ratio hole | core | |
| `epitaxy-and-strain` | Epitaxy and strained silicon | Growing crystal on crystal, and using lattice mismatch on purpose to speed up carriers | advanced | |
| `damascene-electroplating` | Copper electroplating and damascene | Superfilling additives that make copper grow bottom-up inside a trench, discovered mostly by accident | core | |
| `precursor-supply-chain` | Precursors, gases, and the specialty chemical supply chain | Where TMA, WF₆, and neon actually come from, and what a single-source precursor does to a ramp | core | |

## Etch

| slug | topic | angle | level | ★ |
| --- | --- | --- | --- | --- |
| `wet-etching-and-anisotropy` | Wet etching and crystallographic anisotropy | KOH etches (100) 400× faster than (111), which is how you get a perfect V-groove with a beaker | intro | ★ |
| `plasma-fundamentals` | Plasma fundamentals for process engineers | Sheaths, self-bias, ion energy distributions — the physics shared by etch, PECVD, and sputtering | core | ★ |
| `reactive-ion-etching` | Reactive ion etching | Chemical plus physical etching, sidewall passivation, and how directionality is actually achieved | core | ★ |
| `deep-rie-bosch` | Deep RIE and the Bosch process | Alternating etch and passivation to cut through a wafer, and the scallops it leaves behind | core | ★ |
| `atomic-layer-etching` | Atomic layer etching | Etch's answer to ALD: separating modification from removal to take off one layer at a time | advanced | |
| `etch-selectivity-and-loading` | Selectivity, loading, and ARDE | Why a dense array etches slower than an isolated feature, and how process engineers compensate | core | |
| `high-aspect-ratio-etch` | High-aspect-ratio etch for 3D NAND | Punching a 10 µm hole through 200+ alternating layers, straight, at production throughput | advanced | |

## Planarization, cleaning, and contamination

| slug | topic | angle | level | ★ |
| --- | --- | --- | --- | --- |
| `cmp` | Chemical mechanical planarization | Making a wafer flat enough to print on by deliberately scratching it — chemistry plus abrasion plus Preston's equation | core | |
| `cmp-dishing-and-dummy-fill` | Dishing, erosion, and dummy fill | Why layout rules force you to add metal shapes that do nothing electrically | advanced | |
| `rca-clean` | The RCA clean | SC-1, SC-2, and HF-last: the 1965 recipe that still starts most process flows | intro | ★ |
| `cleanroom-contamination-control` | Cleanrooms and contamination control | ISO classes, laminar flow, gowning, and where the particles actually come from (you) | intro | ★ |
| `metallic-contamination-and-lifetime` | Metallic contamination and minority-carrier lifetime | Parts per trillion of copper will kill a device; how gettering rescues the wafer | advanced | |
| `ultrapure-water-and-chemicals` | Ultrapure water and process chemicals | 18.2 MΩ·cm water is a manufactured product; what a fab's chemical plant looks like | intro | ★ |
| `esd-and-wafer-handling` | ESD, handling, and mechanical yield loss | The damage that has nothing to do with physics of devices and everything to do with tweezers | intro | ★ |

## Doping, anneal, and thermal budget

| slug | topic | angle | level | ★ |
| --- | --- | --- | --- | --- |
| `ion-implantation` | Ion implantation | A particle accelerator as a production tool: dose, energy, channeling, and the damage you have to repair | core | |
| `diffusion-and-thermal-budget` | Diffusion and the thermal budget | Every hot step moves every dopant you already placed; the budget is spent in order | core | |
| `rta-and-laser-anneal` | Rapid thermal and laser annealing | Milliseconds and microseconds of heat: activating dopants without letting them move | core | |
| `junction-abruptness` | Junction engineering and abruptness | Why the ideal source/drain junction is a step function and physics refuses to give you one | advanced | |

## Metrology and inspection

| slug | topic | angle | level | ★ |
| --- | --- | --- | --- | --- |
| `four-point-probe` | Four-point probe and sheet resistance | The cheapest useful measurement in a fab, the geometry correction factor, and what it tells you about a film | intro | ★ |
| `ellipsometry` | Ellipsometry and reflectometry | Measuring a 5 nm film with light much longer than 5 nm, by watching polarization instead of intensity | core | ★ |
| `profilometry-and-afm` | Stylus profilometry and AFM | Two ways to measure a step height, and the artifacts each one invents | intro | ★ |
| `cd-sem` | CD-SEM | Measuring linewidth with electrons without shrinking the resist while you look at it | core | ★ |
| `scatterometry-ocd` | Scatterometry and optical CD | Fitting a diffraction spectrum to a model of the profile — inference, not imaging | advanced | |
| `defect-inspection` | Defect inspection: brightfield, darkfield, die-to-die | Finding a 20 nm particle on a 300 mm wafer in minutes, and the false-count problem | core | |
| `ebeam-inspection-and-voltage-contrast` | E-beam inspection and voltage contrast | Seeing an open via as a brightness difference, because charge tells you what light cannot | advanced | |
| `fib-tem-failure-analysis` | FIB, TEM, and physical failure analysis | Cutting a lamella out of one transistor to find out why the chip failed | core | |
| `wafer-flatness-bow-warp` | Flatness, bow, warp, and film stress | Stoney's equation, why a stressed film curls a wafer, and how that lands back on lithography | core | ★ |
| `in-line-vs-offline-metrology` | In-line vs offline metrology and APC | Feeding a measurement back into the next lot's recipe — run-to-run control in practice | core | |

## Yield, reliability, and test

| slug | topic | angle | level | ★ |
| --- | --- | --- | --- | --- |
| `yield-models` | Yield models: Poisson, Murphy, negative binomial | Why the simplest defect model is too pessimistic, and how a fab estimates D₀ | core | |
| `spc-in-fabs` | Statistical process control on a real line | Control charts, Cpk, out-of-control action plans, and why the chart is only as good as the sampling plan | core | ★ |
| `wafer-sort-and-final-test` | Wafer sort, probe cards, and final test | Touching thousands of pads with needles, and why test time is a real fraction of die cost | core | |
| `design-for-test-scan` | Design for test: scan chains, ATPG, BIST | Adding hardware whose only job is to make the chip testable, and what it costs in area | core | |
| `known-good-die` | Known-good die and the chiplet test problem | Stacking four dies means multiplying four yields; testing before bonding is the whole ballgame | advanced | |
| `reliability-mechanisms` | Electromigration, TDDB, NBTI, hot carriers | The four ways a working chip dies slowly, and the acceleration models used to promise ten years | advanced | |
| `burn-in-and-bathtub` | Burn-in and the bathtub curve | Paying to fail the weak parts early, and why the economics of burn-in changed with automotive AI | core | |
| `latchup-and-esd-protection` | Latchup and on-chip ESD protection | The parasitic thyristor hiding in every CMOS well, and the diodes added to keep it asleep | core | |

## Devices and device physics

| slug | topic | angle | level | ★ |
| --- | --- | --- | --- | --- |
| `mosfet-fundamentals` | The MOSFET, honestly | Inversion, threshold voltage, and the square-law model — plus where that model stops being true | intro | ★ |
| `subthreshold-slope-60mv` | Subthreshold swing and the 60 mV/decade limit | The thermodynamic floor that ended voltage scaling and set the power wall | core | |
| `short-channel-effects` | Short-channel effects | DIBL, punchthrough, and V_T roll-off: what goes wrong when the gate loses control | core | |
| `dennard-scaling-and-its-end` | Dennard scaling and why it ended | The rule that made every node better for free, and the leakage that broke it | intro | |
| `high-k-metal-gate` | High-k / metal gate | Replacing SiO₂ after 40 years, and why the gate had to stop being polysilicon at the same time | core | |
| `finfet` | FinFET | Wrapping the gate on three sides, the fin-quantization problem, and what it did to layout | core | |
| `gate-all-around-nanosheet` | Gate-all-around nanosheets | Sheets released by etching SiGe out from under silicon; the width knob FinFET never had | core | |
| `cfet-stacked-devices` | CFET and stacked transistors | Putting the pFET on top of the nFET to buy area without buying resolution | advanced | |
| `strain-engineering` | Strain engineering | Bending the lattice to make carriers faster: eSiGe, stress liners, and mobility limits | advanced | |
| `sram-bitcell-scaling` | The 6T SRAM cell and why it stopped shrinking | Read/write margins, the butterfly curve, and the reason cache is eating die area | core | |
| `dram-cell-and-capacitor` | DRAM: 1T1C, capacitor scaling, refresh | Storing charge in a hole with a 60:1 aspect ratio, and why DRAM scaling is harder than logic | core | |
| `3d-nand` | 3D NAND | Going vertical instead of smaller: string stacking, charge-trap cells, and layer counts as a roadmap | core | |
| `emerging-memory` | MRAM, ReRAM, PCM | Three non-volatile technologies that keep almost winning, and the metric each one actually beats | core | |
| `ferroelectric-hfo2` | Ferroelectric hafnium oxide | A 2011 accident that made ferroelectrics CMOS-compatible, and the memory and logic ideas it unlocked | advanced | |
| `oxide-semiconductors-igzo` | IGZO and oxide-channel transistors | Ultra-low leakage transistors you can build in the back end of the line, at low temperature | advanced | |
| `wide-bandgap-gan-sic` | GaN and SiC power devices | Why bandgap sets breakdown field, and how that shrinks a power converter | core | |
| `power-mosfet-igbt` | Power MOSFETs, IGBTs, and the on-resistance trade | Vertical device structures and the silicon limit line every datasheet is chasing | core | |
| `cmos-image-sensors` | CMOS image sensors | Backside illumination, stacked sensor + logic, and pixel-level hybrid bonding shipped by the billion | core | |
| `soi-and-fdsoi` | SOI and FD-SOI | The other way to control a short channel — buried oxide, back-gate biasing, and the RF niche it owns | core | |

## Interconnect and advanced packaging

| slug | topic | angle | level | ★ |
| --- | --- | --- | --- | --- |
| `beol-rc-delay` | BEOL interconnect and RC delay | Transistors got faster, wires did not; how the back end became the bottleneck | core | |
| `low-k-dielectrics` | Low-k and airgap dielectrics | Trading mechanical strength for capacitance, and what that does to packaging | advanced | |
| `interconnect-resistivity-crisis` | The resistivity crisis: ruthenium, molybdenum, and barrier-less wires | Copper's electron mean free path is 39 nm, so sub-20 nm wires stop obeying bulk resistivity | advanced | |
| `backside-power-delivery` | Backside power delivery | Moving the power rails to the other side of the wafer, and the nano-TSVs that get them there | advanced | |
| `through-silicon-vias` | Through-silicon vias | Via-first, via-middle, via-last, and the keep-out zone stress imposes on nearby transistors | core | |
| `hybrid-bonding` | Hybrid bonding | Copper-to-copper direct bonding at sub-micron pitch — flatness requirements that make CMP the hero again | advanced | |
| `interposers-and-cowos` | Interposers, CoWoS, and 2.5D | Why the industry built a silicon circuit board, and why its capacity became a global bottleneck | core | |
| `hbm-stack-architecture` | HBM stack architecture | 1024+ bit interfaces, TSV-stacked DRAM, base die logic, and the thermal problem of a hot stack on a hot die | core | |
| `fan-out-wafer-level-packaging` | Fan-out wafer-level packaging | Reconstituting known-good dies into a new "wafer" of mold compound, and the die-shift problem | core | |
| `microbumps-and-pitch-scaling` | Microbumps, pillars, and pitch scaling | From 130 µm solder balls to 9 µm pillars to no bumps at all | core | |
| `substrates-abf-and-glass` | Package substrates: ABF buildup and glass cores | The unglamorous laminate that limited AI accelerator supply, and why glass is being tried | core | |
| `warpage-and-underfill` | Warpage, underfill, and thermomechanical stress | Silicon and organic substrates expand at different rates; everything else follows from that | advanced | |
| `thermal-interface-and-die-attach` | Thermal interface materials and die attach | Getting 1 kW out of a package, one thermal resistance at a time | core | |
| `chiplets-and-ucie` | Chiplets and UCIe | Splitting a die to dodge reticle limits and yield, and the standard trying to make dies interoperable | core | |
| `co-packaged-optics` | Co-packaged optics | Moving the optical engine onto the switch package because copper reach ran out | advanced | |
| `silicon-photonics` | Silicon photonics | Waveguides, ring modulators, and germanium detectors built in a CMOS fab | core | |

## MEMS, analog, and mixed-signal

| slug | topic | angle | level | ★ |
| --- | --- | --- | --- | --- |
| `mems-fabrication` | MEMS fabrication: surface vs bulk micromachining | Sacrificial layers, release etch, stiction — the moving parts a cleanroom can build | core | ★ |
| `piezo-nanopositioning` | Piezoelectric actuators and flexure stages | Sub-nanometer motion with no bearings, plus hysteresis and creep you have to control around | core | ★ |
| `analog-basics-bandgap` | Bandgap references and analog first principles | Getting a voltage that does not care about temperature, out of two transistors run differently | core | |
| `adc-architectures` | ADC architectures | SAR, sigma-delta, pipeline, flash — the speed/resolution/power triangle in one page | core | |
| `pll-and-clock-distribution` | PLLs and clock distribution | Making one clean clock and getting it everywhere with less than a picosecond of skew | core | |
| `serdes-and-signal-integrity` | SerDes and signal integrity | 224 Gb/s down a piece of copper: equalization, FEC, and the eye diagram | advanced | |
| `on-chip-power-delivery` | On-chip power delivery and IR drop | Integrated voltage regulators, decoupling capacitance, and the di/dt problem at 1000 A | advanced | |

## Fab operations and economics

| slug | topic | angle | level | ★ |
| --- | --- | --- | --- | --- |
| `czochralski-wafer-manufacturing` | From sand to wafer | Siemens process, Czochralski pulling, slicing, lapping, and epi — before any fab touches it | core | ★ |
| `cleanroom-hvac-and-vibration` | The building is the tool | HVAC, air changes, vibration isolation, and why fab construction costs what it costs | intro | ★ |
| `cycle-time-and-wip` | Cycle time, WIP, and Little's law | Why a 40-day cycle time is a competitive weapon, and how queueing theory runs a fab | core | ★ |
| `cost-per-wafer-and-per-transistor` | Cost per wafer vs cost per transistor | The two curves diverged around 28 nm; almost every strategic decision since follows from that | intro | |
| `fab-capex-and-depreciation` | Fab capex, depreciation, and utilization | Why a fab must run flat out, and how depreciation schedules shape pricing | intro | |
| `wafer-size-transitions` | 150, 200, 300, and the 450 mm that never happened | The economics of a wafer-size transition, and why the industry stopped | intro | ★ |
| `foundry-vs-idm-vs-fabless` | Foundry, IDM, and fabless | Three business models, the PDK as the interface, and where the margin actually sits | intro | |
| `pdks-and-open-source-pdks` | PDKs, and what an open-source PDK contains | Device models, DRC rules, and standard cells — what you actually get with SKY130 or IHP SG13G2 | core | ★ |
| `tapeout-and-mpw-programs` | Tapeout: what actually gets sent | GDSII/OASIS, sign-off decks, and the shuttle programs that put student designs on real silicon | intro | ★ |

## Chip design and EDA

| slug | topic | angle | level | ★ |
| --- | --- | --- | --- | --- |
| `rtl-to-gdsii` | RTL to GDSII | The whole digital flow in one map: synthesis, floorplan, place, CTS, route, sign-off | core | ★ |
| `static-timing-analysis` | Static timing analysis | Setup, hold, and why the slowest path is found without simulating a single vector | core | |
| `place-and-route` | Placement and routing | Wirelength, congestion, and the optimization problem underneath every physical design tool | core | |
| `standard-cells-and-track-height` | Standard cells and track height | What a 6-track library means, and how cell architecture sets density more than the node number | core | |
| `verification-formal-and-uvm` | Verification: simulation, UVM, and formal | Why verification is most of the engineering effort, and what formal proves that testing cannot | core | |
| `ml-for-eda` | Machine learning in EDA | Where learned methods actually beat classical optimizers, and where the published comparisons are contested | advanced | |

## Energy

| slug | topic | angle | level | ★ |
| --- | --- | --- | --- | --- |
| `grid-interconnection-queues` | Interconnection queues | Why a datacenter or a solar farm waits years for a grid connection, and what a study cluster is | intro | |
| `transformers-and-substations` | Large power transformers and substations | A three-year lead time on a piece of iron and copper is now a constraint on AI buildout | core | |
| `datacenter-power-architecture` | From substation to socket | Medium-voltage distribution, UPS topologies, 48 V racks, and the 800 VDC proposals | core | |
| `power-electronics-efficiency` | Converters, efficiency, and where watts go | Every conversion stage costs a few percent; the arithmetic of stacking five of them | core | |
| `liquid-cooling` | Liquid cooling: cold plates, CDUs, immersion | Air runs out around 50 kW a rack; what replaces it and what it costs in plumbing | core | |
| `datacenter-thermodynamics` | The thermodynamics of a datacenter | Approach temperature, chillers vs free cooling, and why PUE hides more than it reveals | core | |
| `water-use-and-cooling-tradeoffs` | Water, WUE, and the evaporative trade | Trading kilowatts for liters, and how siting decisions get made on that curve | intro | |
| `nuclear-and-smrs` | Nuclear power and SMRs for datacenters | What is actually licensable this decade versus what is a press release | core | |
| `behind-the-meter-generation` | Behind-the-meter generation | Gas turbines, fuel cells, and bridge power — the physics and the permitting | core | |
| `demand-response-and-curtailment` | Flexible load and curtailment | Treating a training cluster as a dispatchable resource, and whether operators will actually do it | core | |
| `grid-frequency-and-inertia` | Frequency, inertia, and why big loads are scary | What a 500 MW load step does to a grid, and the ride-through standards that follow | advanced | |

## Systems, networking, and inference

| slug | topic | angle | level | ★ |
| --- | --- | --- | --- | --- |
| `transformer-inference-mechanics` | What actually happens during inference | Prefill vs decode, why one is compute-bound and the other memory-bound, and what that does to a serving stack | core | |
| `kv-cache-and-batching` | KV cache, batching, and continuous batching | The memory that grows with every token, and the scheduling tricks that pay for it | core | |
| `roofline-and-arithmetic-intensity` | The roofline model | One plot that tells you whether you are compute-bound or bandwidth-bound, and how to use it on a real kernel | core | ★ |
| `quantization` | Quantization: INT8, FP8, FP4, and the rest | What a number format actually costs in silicon area, and where accuracy goes when you shrink it | core | |
| `mixture-of-experts` | Mixture of experts | Buying parameters without buying FLOPs, and the routing and all-to-all traffic that follows | core | |
| `speculative-decoding` | Speculative decoding | Guessing several tokens with a small model and checking them with a big one, for free latency | advanced | |
| `attention-and-memory-bandwidth` | Attention, FlashAttention, and the memory wall | Why the winning kernel optimization was about data movement, not arithmetic | advanced | |
| `distributed-training-parallelism` | Data, tensor, pipeline, and expert parallelism | Four ways to split a model across chips, and the communication bill for each | advanced | |
| `collective-communications` | All-reduce and collective communication | Ring vs tree algorithms, and why network topology shows up in training throughput | core | |
| `network-topologies-fat-tree-vs-torus` | Fat trees, dragonfly, and torus | How you wire 100,000 accelerators, and what each topology costs in optics | advanced | |
| `optical-transceivers` | Optical transceivers and DSP | 800G and 1.6T modules, the power per bit, and why linear-drive optics is being tried | core | |
| `rdma-and-lossless-fabrics` | RDMA, RoCE, and lossless Ethernet | Moving data without the CPU, and the congestion-control problem that comes with it | advanced | |
| `systolic-arrays-and-tpus` | Systolic arrays | A 1978 idea that turned out to be the right shape for matrix multiply, and how TPUs use it | core | |
| `gpu-microarchitecture` | Inside a GPU | SMs, warps, tensor cores, and the memory hierarchy that determines whether your kernel is fast | core | |
| `hbm-bandwidth-vs-capacity` | The bandwidth/capacity trade in AI memory | Why accelerators are memory-starved, and what HBM, LPDDR, and CXL each solve | core | |
| `storage-for-ai-checkpointing` | Storage and checkpointing at cluster scale | Writing a multi-terabyte checkpoint without stalling 10,000 GPUs | core | |
| `reliability-at-cluster-scale` | Failures at cluster scale | MTBF arithmetic when you have 100,000 of something, and what silent data corruption does to a training run | core | |

## Applications and measurement

| slug | topic | angle | level | ★ |
| --- | --- | --- | --- | --- |
| `benchmarks-and-contamination` | How to read an AI benchmark | Contamination, saturation, harness differences, and the error bars nobody prints | core | |
| `ai-for-science-evaluation` | Evaluating "AI for science" claims | The difference between a prediction, a validated prediction, and a discovery | core | |
| `robot-learning-data-problem` | The data problem in robotics | Why robots have no internet-scale dataset, and the teleoperation and sim approaches to faking one | core | |
| `autonomy-safety-statistics` | Reading autonomous-vehicle safety statistics | Miles per intervention, exposure matching, and the reporting rules that shape the numbers | core | |
| `ai-adoption-measurement` | Measuring AI adoption | Survey instruments, token counts, and revenue: three ways to count, three different answers | intro | |
