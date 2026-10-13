# Grounded v2 Features and Action Interface

2026-09-08. Achieve grounded action semantics per single turn using an independent feature version.
`grounded-production-context-v2`. The buffer from original `grounded-unit-support-v1` is still supported.

## Observation Layout

10×10, 32 slot units: 10,108 items from the old entity part, 1,800 items from the new context, 1,408 items from the end-unit support information, totaling **13,316** FP16 values.
The offsets for land within the old entity, friendly units, global data, opponent units, goods, and daily history remain unchanged.

Add context arranged in the following order:

| Section | Shape | Content |
| --- | --- | --- |
| Land | 2×100×8 | Current harvestable status, time to first yield, time to maximum yield, remaining lifespan, watering/fed requirements, continuous drought/starvation risk, animal maintenance, current market value of output |
| Goods | 9×8 | Own carried quantity, warehouse stock, total sum, land output, current market value of inventory and output, number of harvestable land plots, carried quantity ratio, corresponding crop seed count |
| Global | 2×8 | Production land plots, harvestable land plots, watering needed, feeding needed, water/food shortage risk, care required, land approaching lifespan, proportion of land not yet producing first yield |
| Public History | 4×28 | Price changes over nine categories in Turn 1/4/12/24, nine market stock changes, changes in both parties' cash, workers, and land, coverage rate, scale, intraday, and global time |

Private opponent information is not included in the context. The encoder additionally incorporates the existing 44-bit operation support and two "private inventory known / operation support known" flags into the unit input; the opponent's two flags are set to zero. The historical buffer retains at least 25 observations, and explicitly records the ratio when coverage is insufficient. Tokens with no available historical data at the beginning of the game are not used as attention keys.

The land first performs shared lightweight spatial convolutions, then combines with global, both parties' units, goods, stores, and four historical tokens to pass through a Transformer, resulting in a total of 286 tokens. The Actor and Critic use independent parameters.
The BC's `ContractSession::EncodeReplay`, deployed `ContractSession::Observe`, and trained `Batch::Observe/ObserveSelfPlay` all call the same `EncodeContext`.

## Conditional Actions

Units select a position pointer between PASS and the current grounded candidate plots, then output 44 types of operations along with exact quantities.
Position, operation, and quantity are sequentially passed to the shared condition module. The market holds at most ten orders, with each order first selecting an operation before selecting a quantity, and inheriting the prior unit selection and market request. Only clearly typed reads learn valid categories; when adapting to native ABI, padding is completed to a uniform vocabulary width without adding parameters for filler categories.

Externally there are still 276 fields: 32 units, each with two groups of four fields, plus ten groups of market operations/quantities.
The second unit's task slot and release field are statically padded; fields missing due to absent units or after halting do not contribute to loss.
Critic's typed symbol embeddings are partitioned by field semantics; the exclusive prefix scan only reads actions prior to the current selection.

## Engineering Evidence

- [Two complete game replays](../outputs/analysis/grounded-v2-20260908/replay-roundtrip.json):
  New features, action reconstruction, and full state consistency, totaling 2,880 observations.
- [Compiled backward verification](../outputs/analysis/grounded-v2-20260908/compiled-gradient.json):
  BF16 compilation loss is bounded, and all Actor parameters have finite gradients.
- [Dual-GPU BC checkpoint](../outputs/analysis/grounded-v2-20260908/bc-stop.json):
  Exact sample progress, optimizer, and RNG states from both workers are preserved.
- [Complete official image](../outputs/analysis/grounded-v2-20260908/native-mirror/report.json):
  Four matches, 5,752 decision features are consistent across the training core, script batches, deployment interface, and official interpreter.
- [Sampling and prefix semantics](../outputs/analysis/grounded-v2-20260908/semantic-checks.json):
  144 real-state eager CPU and TorchScript samplings are identical; prefix value does not read current or subsequent actions.
- [CPU deployment verification](../outputs/analysis/grounded-v2-20260908/cpu-qualification.json):
  The same 76.45 MB compressed package completes two official matches under Python 3.11/3.12, with identical runtime trajectories;
  maximum cold-start action latency is 2.177 seconds, subsequent actions take 0.323 seconds. Randomly initialized weights are used here; formal training results must still undergo re-verification of exact weights and deployment package.

These checks verify the execution and interfaces, and do not constitute conclusions regarding the model's game strength. The final training identity and acceptance results are available at
[Current Mainline](CURRENT_MAINLINE.md).
