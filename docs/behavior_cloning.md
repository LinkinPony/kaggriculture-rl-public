# Kaggle replay behavior cloning

## Objectives and Scope

BC only modifies the actor's initial distribution before the fresh terminal-W/D/L RL. It does not treat replay similarity, NLL, action accuracy, or terminal cash as evidence of strength, nor does it generate structured initial templates. Promotion to production remains determined solely by complete official rules, shared seed, paired seats, and formal time budget under closed-loop games.

The current minimum pipeline is:

```text
Kaggle ZIP for the latest complete UTC day
        |
        |  Stream short prefixes; select episodes by actual token-prefix coverage
        v
Episode-start opening segments from complete DONE replays
        |
        |  observation/action ABI + compact economic state
        v
dataset-v5 NPZ shards
        |
        |  Actor-only initialization; fresh optimizer; contiguous prefix unroll
        v
BC actor after the specified epoch count -> fresh terminal-W/D/L RL
```

## Invariance of Correctness

- The date window must come from the most recent complete UTC day in the downloaded index; incomplete data from the same day cannot be falsely treated as a complete day. The index, daily package, manifest within the daily package, selection, compact shard, and actor artifact all record verifiable identities.
- The original episode remains as a Kaggle ZIP under `data/external/`. The scanner only decompresses and reads the required opening bytes; training only reads the compact shard and does not generate daily JSON directories.
- Training alignment is fixed to `steps[t].observation -> steps[t+1].action`. The replay source must be a complete `DONE` game; both seats are preserved and included in the same split.
- Opening selection uses only the token sequence derived from current codec applied to recorded actions. The number of actions, terminal score, agent name, and pre-specified target actions are not involved in selection; `BUILD_COOP` does not receive additional weighting.
- The selector covers experience clusters across multiple prefix lengths and limits the repetition of identical full-prefixes for dual seats. Configuration only specifies the maximum data budget; the actual available sample count is determined by deduplication results and cannot be padded with full repetitions of replay to meet batch size requirements.
- Compact data uses the same deployed observation encoder, action codec, and native actor-safe economic state. dataset-v5 validates the economic-state ABI, byte count per shard, and SHA-256.
- The persistent GRU training sequence must start from the 0th turn of the episode, and one unroll covers the entire stored opening segment; it is prohibited to reset the strategy state mid-segment and continue computing loss.
- BC is initialized from an authenticated actor-only artifact. The architecture, vocabulary, encoder, facts, and economic ABI must match field-by-field; no critic, optimizer, or RNG from the source RL system may be imported.
- If the task requires exactly a specified number of training epochs, the published artifact must select the final epoch and cannot be rolled back to a lower number of training epochs based on validation performance. BC reports still explicitly lack promotion authority.

## Entry and Current Implementation

Data entry is `kagg-revue-bc-data prepare`, configuration see [`configs/bc_data.yaml`](../configs/bc_data.yaml). Scanning reads bounded by ZIP member, multi-process transformation processes only the episode-start segments specified in the selection list; the selection list is released together with the dataset. Training entry is:

```bash
kagg-revue train model=persistent_gru experiment=opening_diverse_bc
```

Model and task configurations are respectively available at
[`configs/model/persistent_gru.yaml`](../configs/model/persistent_gru.yaml) and
[`configs/experiment/opening_diverse_bc.yaml`](../configs/experiment/opening_diverse_bc.yaml).
Long-running tasks must be executed within a named tmux session, and the resolved configuration, data identity, checkpoint, training report, and opening distribution diagnosis are written to `outputs/`.

## 2026-08-28 Evidence Snapshot

This input covers three complete UTC days from 2026-08-25 to 2026-08-27, scanning a total of 2,071 episodes, with 0 rejections during scanning and conversion. Based on resolved selection, 94 episodes are obtained; these cover all 1/2/4/8 turn experience prefixes from the source set and limit identical dual-seat 8-turn prefixes to at most two episodes. The dataset ID is `8a5662699ca07dd1d317aab15b6ebc0d4f0221aa8fdfb789bdb952b916a74a0`, with the authoritative clearing unit located at `data/external/kaggriculture-episodes-2026-08-25_2026-08-28/compact-opening-diverse-v1/`.

The sole initialization source refers to the complete update 2495 actor snapshot specified for the run; the checkpoint SHA-256 is
`fd22e8682cd4bb2f99a31c6ec238354f299bdf0cf8300c214475c4c2aa299bcf`, and the snapshot SHA-256 is
`24aedf7e048ebd57806c72e860d7377f3fdc4f47588195ff83f8622b681ab832`. BC uses a fresh optimizer to complete exactly 2 epochs, resulting in a final actor SHA-256 of
`cfd2cc43f33b023db2c087a604953cce844a1548e5df5c9c113aae3a102873f7`. In the initial decision diagnosis, the PASS probability of the source actor is 99.965%, and the experience distribution after BC is BUILD_PASTURE at 52.585%, PASS at 46.406%, and BUILD_COOP at 0.023%; this result only demonstrates an expected perturbation in the opening distribution, not an improvement in strength.

## Open Decision-making

Subset budget, prefix length, learning rate, and batch size are determined only in the resolved config and the generated report. If a closed-loop is performed subsequently and evidence shows that BC perturbation is too strong or too weak, only one attributable setting should be changed in the next iteration; templates, branches, projections, candidate advancement, or additional rollout noise should not be reintroduced on the RL hot path.
