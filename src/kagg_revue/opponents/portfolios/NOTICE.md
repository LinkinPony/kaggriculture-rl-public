# Public notebook attribution

The September 16 active population consists of the following native adaptations.
The frozen source identities and Rayk's companion file are recorded in
`data/external/kaggriculture-public-native-20260916/manifest.json` and `catalog.py`.
Original source, embedded attribution notices, notebooks and acquisition metadata
remain under `data/external/kaggriculture-notebook-survey-20260914/` and
`data/external/kaggriculture-notebook-survey-20260914-refresh/`, with Ahmed V45
under `data/external/kaggriculture-notebook-survey-20260916/`.

- [Ahmed V45](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v45-first-turn-wheat-round-trip),
  by ahmedberatozer: `ahmed_v45`.
- [MetaCounter R1](https://www.kaggle.com/code/alperen5252525/kaggriculture-metacounter-r1-scored-agent),
  by alperen5252525: `metacounter_r1`.
- [Shop Router 0913](https://www.kaggle.com/code/yhay81/shop-router-0913),
  by yhay81: `shop_router_0913`.
- [Rank Your Agent](https://www.kaggle.com/code/raykkretzschmar/kaggriculture-rank-your-agent),
  by raykkretzschmar, extracted V38 low-pressure entry point: `rayk_v38_low_pressure`.
- [Farming Score V4](https://www.kaggle.com/code/lynnsakurai/farming-score-v4-a-better-shop),
  by lynnsakurai, September 14 retrieval: `farming_v4_0914`.

Local changes compile the frozen source's functions and control flow into C++
translation units, share identical functions and immutable route data, and execute
with native containers directly from the engine. No Python interpreter or per-turn
Python callback runs in the trainer. The compiler rejects unsupported syntax.
Source ordering, controller state and copy behavior are retained and independently
qualified; source wall-clock planning diagnostics are excluded from equality checks.
V45 uses the reviewed V43 container-copy adapter normalization; all seven adapter
definitions are authenticated before removal. Its reservation-horizon `try/finally`
is compiled with cleanup on both return and exception, retaining exception precedence.
The Apache 2.0 text is retained in `LICENSE`. Upstream notices credit, among others,
thomastschinkel, yhay81, tetsutani, aurax7, prvsiyan, lucifer19,
Dmitrii Gluzdov and Kaggle's kaggle-environments contributors. These upstream
credits and references to public replay data do not imply ownership of other
competitors' source code.

The following versions are retired from new training configurations and the
trusted registry. Ahmed V41/V42 and the September 12 Farming V4 snapshot require their
archived runtime for reproduction; their original sources and route assets remain preserved.
Earlier hand-written native ports also remain available through legacy modules.

Native adaptations of the following public Kaggle notebooks, with the Apache 2.0 license text retained in `LICENSE`. Frozen original notebooks and source files remain under `data/external/kaggriculture-notebook-survey-20260908/`.

- [router_95](https://www.kaggle.com/code/thomastschinkel/kaggriculture-95-5-win-rate-via-replay-routing)
  Frozen `main.py` SHA-256: `8241246765098c50223d897739cb32076b71a303284d2e5e1c5f0fb495bb5a97`.
- [farming_v4](https://www.kaggle.com/code/lynnsakurai/farming-score-v4-a-better-shop)
  Frozen `main.py` SHA-256: `1590394cf30c8989a3e1cfdb027d89b5ccd97c2fb4cdc14959a15555b2b2361a`.
- [kaito_v58](https://www.kaggle.com/code/kaitofukami/238-238-known-streams-v58-minimax-closed-loop)
  Frozen `main.py` SHA-256: `b041058ec187a8d0a01edc0eab8de068b53deca3e6c1973faf74ace6916ddcb9`.
- [boatlee_v29](https://www.kaggle.com/code/boatlee/v29-r1-adaptive-market-hysteresis)
  Frozen `main.py` SHA-256: `c4a6964cec3c1c99207c32bb1fd91e53c3ec01e6890da5734331cbeab1cc1267`.
  Retired from the active training factory and trusted registry; retained for historical reproduction.
- [shop_router_0908](https://www.kaggle.com/code/yhay81/shop-router-0908)
  Frozen `main.py` SHA-256: `66585d1a5dbfe11c946a3c400278592f860342bc4a8f5e5f87f2a9293348984b`.
  Original notebook, submission archive and four source/data files are preserved in
  `data/external/kaggriculture-shop-router-0908-20260908/`, with all file hashes in
  `provenance.json`. Companion identities are also bound in `catalog.py`.

Local modifications statically extract the action tapes and Thomas routing trees, share immutable decoded assets, and translate runtime routing, repair, market budgeting and market-flow state to C++. Kaito v58 advances ten independent controllers eagerly instead of replaying their warm-up prefixes at construction; the resulting controller states are copied when a training batch forks. No Python notebook code executes in the training loop.

The Shop Router adaptation loads four tapes and the two frozen decisions from JSON,
then evaluates the exact public shop-count and egg-inventory predicates in C++ at
steps 144 and 648. It preserves repeated-call decisions, episode reset and cloned
session state. Unsupported routing model shapes are rejected during extraction.

The original authors' embedded references to public replays and other strategies remain in the frozen original notebooks; these references do not imply authorship of other competitors' source code. Existing Kaito v48 support helpers are reused where the frozen v58 source has the same behavior.

- [shop_router_0909](https://www.kaggle.com/code/yhay81/shop-router-0909), by yhay81.
  Frozen main.py SHA-256: `d6d74997dc5b483db63d8e39cafa1afeec0f366824e75107e109123f111e866b`.
  Source notebook, 13 action tapes and Apache 2.0 license are preserved under
  `data/external/kaggriculture-shop-router-0909-20260909/`.
  This separate C++ adaptation preserves ordered-shop routing, worker-local daily
  action queues, advanced-sale debt, final liquidation and repeated-call resets.
  The original source credits aurax7 Reactive Router for sale timing and shed projection.
