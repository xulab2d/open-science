# tMoTe2 Deck Patterns

Purpose:
- Fast internal guide to how Xu Lab tMoTe2 project decks are structured, what they tend to emphasize, and what kinds of observations are treated as meaningful.

Primary source families:
- `/Volumes/Xu Lab/tMoTe2_Measuring/*/*.pptx`
- especially current-relevance anchor decks:
  - `CWB_Yifan_D93_Run2_attodry522`
  - `Shuai-MT43-DR911`
  - `WJL_Zengde_B79_Attodry911`
  - `Zengde_WJL_C7_Attodry911`
  - `Zengde_Weijie_A5_AAtA_dot_oldattodry`
  - `courtney_christiano_D88_*`

## Chunk 1: What these decks usually contain

Recurring first-slide content:
- sample or device name
- who fabricated it
- who measured it
- date or temperature
- stacking or twist-angle description when known

Recurring setup content:
- fabrication stack
- gate geometry and dielectric thicknesses
- gate-voltage limits
- contact or leakage checks

Interpretation:
- these decks are not polished papers; they are lab-working summaries that mix device facts, quick conclusions, and next-step logic
- they are high-value for recovering naming conventions, calibration assumptions, and what experimenters thought was worth following up

## Chunk 2: Recurring summary style

The decks typically move in this order:
1. sample/fabrication/context
2. gate or contact sanity checks
3. spatial maps or spot-finding
4. doping or dual-gate maps
5. selected linecuts / integrated windows / follow-up scans
6. short interpretation bullets and next actions

Useful consequence:
- when summarizing a new project, mirror this progression rather than jumping directly into abstract analysis

## Chunk 3: What is often treated as interesting

In tMoTe2 optical decks, people repeatedly call out:
- whether gates are actually working
- whether a spot is bilayer, monolayer, twisted interface, edge, or spacer region
- whether integer or fractional features are visible
- whether a feature sharpens, shifts, splits, disappears, or becomes asymmetric with `n` or `D`
- whether a dual-gate pattern resembles a familiar phase diagram shape
- whether a feature is likely from one interface/layer versus another
- whether a regime suggests tunneling, interlayer coupling, or an interface-specific signal

Examples from anchor decks:
- B45: “strong correlated states,” filling-factor assignment uncertainty, stronger PL when holes are pushed toward one interface
- C5: “fractional features visible,” “many fractions below -1/2,” estimate of true `D = 0`
- C7: a gate-spacing threshold interpreted as likely tunneling onset
- A5 dot: persistence or loss of dot features before/after dual-gate scans
- MT43: usable contacts, map-based density calibration, inferred twist angle from transport maps

## Chunk 4: Common observables and figure logic

Frequent optical observables:
- dual-gate PL maps
- doping dependence at fixed `D`
- integrated intensity in an energy window
- tracked trion/exciton peak positions
- spot-resolved spatial maps

Frequent transport / magnetic observables:
- dual-gate maps of resistance-related channels
- contact-resistance and leakage diagnostics
- field sweeps and hysteresis maps
- `n-D` maps after gate-coordinate conversion

Important practical rule:
- the decks often treat linecuts and integrated windows as meaningful only after the spot identity and gating quality have been established

## Chunk 5: Recurrent reasoning patterns

Patterns worth remembering:
- first decide what part of the stack is being measured
- then ask whether the gates are controlling the intended interface
- only then interpret fine structure as correlation physics

Frequent caveats:
- weak or missing features can be due to temperature, bad contacts, cracks, degraded spots, poor gate coupling, or being on the sample edge
- asymmetric behavior across `D` is often interpreted layer/interface-selectively rather than as generic noise
- “normal” bilayer behavior is used as a local control against more exotic twisted or dot-like behavior

## Chunk 6: What these decks are good for in future requests

Use tMoTe2 decks to recover:
- sample identity and owners
- gate thicknesses and allowed voltage ranges
- which observables the project trusted
- what the experimenter already thought was strange, promising, or ambiguous
- how the lab phrases a worthwhile next step

Do not overtrust them for:
- final calibrations
- polished figure choices
- publication-grade terminology

## Chunk 7: Immediate retrieval heuristics

If a user asks about:
- current moiré/tMoTe2 project context: check these decks before raw data
- preferred plot style for a project: inspect the project deck
- whether a feature is “interesting”: compare with the deck’s own callouts and next-step logic
- naming or ownership: sample deck first, then project root

Known issue:
- at least one D88 PPTX appears partially corrupted during automated extraction, so that family may need manual fallback if automated text extraction fails.
