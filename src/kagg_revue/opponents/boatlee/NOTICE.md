# Boatlee v21 attribution

This package is a behavior-preserving training-time optimization of Boatlee's
public Kaggle notebook, “V21-R1 | Public-State Route Portfolio”, released under
the Apache License 2.0:

https://www.kaggle.com/code/boatlee/v21-r1-public-state-route-portfolio

Frozen source `main.py` SHA-256:
`c6f96a8521dc9aa369b6f27e5b36b9d481e5c1688f50c8ca215c3bb53f1f9eb8`.

The notebook describes its route hypotheses as derived from public Competition
replays and public notebooks. Those statements are behavioral citations and do
not imply ownership of the referenced participants' source code.

Local modifications offline-encode the Moon, Mutoy, and Munib route portfolios,
authenticate the compact asset once, put every mutable controller field in a
fresh episode session, and port the public-state router and active expert logic
to C++. The rollout hot path reads native engine state and advances the engine
without constructing observation dictionaries, decoding dynamic payloads, or
invoking Python. The frozen original artifact remains the authority for
behavior-equivalence validation.
