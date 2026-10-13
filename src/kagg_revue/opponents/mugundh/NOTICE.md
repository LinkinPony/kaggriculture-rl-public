# Mugundh v21 attribution

This package is a behavior-preserving training-time optimization of Mugundh
J B's public Kaggle notebook, “V21 | Multi-Route Agent | Sell Divergence
Guarder”, released under the Apache License 2.0:

https://www.kaggle.com/code/mugundhjb/v21-multi-route-agent-sell-divergence-guarder

Frozen source `main.py` SHA-256:
`e2f9107e9e537b77b9e908744114a43cece81a6316e33a69ff8aa02618b4c0f1`.

The notebook describes its route tapes as a behavioral reconstruction from
public traces. Those statements are behavioral citations and do not imply
ownership of the traced participants' source code.

Local modifications offline-encode the route and counter tapes, authenticate
the compact portfolio once, put every mutable controller field in a fresh
episode session, and port the active route selection, legacy-layout fallback,
weed repair, market ranking, sell preemption/debt, R5/MD counters, room guards,
terminal liquidation, and sell-divergence guard to C++. The native rollout
reads engine state and advances the engine without constructing observation
dictionaries or invoking the notebook. The frozen original artifact remains
the authority for behavior-equivalence validation.
