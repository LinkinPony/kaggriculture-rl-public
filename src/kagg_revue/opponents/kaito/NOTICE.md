# Kaito public-notebook attribution

## Kaito v48

This package is a behavior-preserving training-time optimization of Kaito
Fukami's public Kaggle notebook, “40/40 Early Floor | 39/46 Top-10 | v48 Fast
Routes”, released under the Apache License 2.0:

https://www.kaggle.com/code/kaitofukami/40-40-early-floor-39-46-top-10-v48-fast-routes

Frozen source `main.py` SHA-256:
`dadee25a9840313218384208c53b2c4752f82c3209cc654632e0b96c65e2664a`.

The notebook identifies the following public replay provenance. These are
behavioral citations and do not imply ownership of those participants' source
code:

- default route: ActiveMusyoku, Kaggriculture episode 96815867;
- first-YARN continuation: Kaileh57, episode 98720726;
- first-FARMERS_MARKET continuation: taiseiu, episode 98706979;
- BAKERY capital continuation: Cary Jin, episode 98316955.

Local modifications remove unused bundled modules, authenticate and load route
templates once, replace full-route deep copies with immutable shared templates,
and put mutable controller state in a fresh runtime per episode. The RL hot path
ports the active route, repair, market, clone-preemption, and terminal behavior
to C++ so it can read native engine state and step a batch without constructing
official observation dictionaries. A Python implementation remains the readable
reference. The original artifact remains the authority for behavior-equivalence
validation.

## Kaito v39

The `kaito.v39` package is a behavior-preserving training-time optimization of
Kaito Fukami's public Kaggle notebook, “103/126 Untouched Future Top-30 | v39
History Gate”, released under the Apache License 2.0:

https://www.kaggle.com/code/kaitofukami/103-126-untouched-future-top-30-v39-history-gate

Frozen source `main.py` SHA-256:
`c0298c82c2a2f9b41cd48657b63b16a9c6f07ea3ee02dc85062f807e54e8c54a`.

Local modifications authenticate and extract the four complete route tapes and
the nested public-state/history calibration memories into one compact immutable
asset. The active hierarchy, route repair, market reorder, preemption, market
maker, and history gate are reimplemented in C++ against the native engine;
mutable controller state remains episode-local. The original artifact is not
modified and remains the behavior authority.
