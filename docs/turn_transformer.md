# Turn-level recurrent policy

## Objectives and Scope

Actor generates farmers, hands, and ordered market requests directly each turn. The complete causal history is stored for retrievability; a separate continuous strategy workspace preserves the actor's fixed-shaped state across turns. The rule engine remains responsible for legality and official transitions, and the model does not introduce planning proxies.

```text
actor-visible observation + previous turn action
                    |
                    v
             scene resampler
              |           |
              |           +---- raw scene memory -----------------+
              v                                               decoder
       cached causal history ----> persistent GRU strategy memory --+
                                                              |
                                      legality compiler ------+
                                                              v
                                               farmer -> hands -> market
```

## Invariance of Correctness

- The Actor and Critic can only access information visible at submission. The own-unit inventory order comes from the actual lexicographical order in the observation; the corresponding field for opponents is always zero.
- The current action ABI retains only explicitly specified quantity actions. The default `PICKUP`/`PLACE` request specification is now represented as the same action plus `quantity=1`, and the DEFAULT policy row no longer exists.
- Unit capacity is the shared shape between artifact and runtime, not the official rule limit. Once capacity is reached, `HIRE` must be masked; for each `HIRE` already selected within the same market prefix, the projected unit count is updated first.
- Causal history KV and strategy state are isolated by seat/environment and are only reset at episode boundaries or step breaks. Padding does not advance persistent state; training re-computation, eager inference, and CUDA Graph all use the same GRU parameters and identical causal observation order.
- The strategy first uses fixed learned slot queries to extract observations from history tokens and scene latents of each turn; during training, extraction across all turns is fully parallelized, followed by a single fused scan via cuDNN GRU along the episode dimension. The GRU hidden state is a persistent state across turns; the tokens available for the decoder/critic in the current turn are derived from the hidden state via slot self-attention and MLP. Slots have no discrete IDs, codebook, hand-written semantics, or independent PPO likelihood.
- The decoder retains the original scene/history cross-attention and applies an independent strategy cross-residual at each layer; the strategy output projection starts from zero and cannot alter legality. The critic's strategy residual also starts from zero and applies a stop-gradient to the strategy input.
- Promotion eligibility is based solely on shared seed, paired seat, complete official rules, and formal time budget under W/L/T outcomes; distillation KL,
  slot coverage and training throughput are used only for migration and runtime diagnostics.

## Current Interfaces and Migration

Native releases `turn-policy-actions-v2`, `actor-observation-v2`, and GPU policy state v3. The action vocabulary is divided into two segments: unit/market. The unit observation extends the original field with an item-wise inventory-order rank. The Actor's capacity and the decision capacity for one turn are jointly determined by the migration artifact and the resolved environment, and cannot be individually overridden at runtime.

The initial migration entry point for vocabulary/capacity remains `python -m kagg_revue.rl.strategy_migration`. The switch from serial workspace to persistent GRU uses `python -m kagg_revue.rl.memory_migration`, with configuration parsed by [`configs/memory_migration_config.yaml`](../configs/memory_migration_config.yaml). The latter authenticates the update-boundary checkpoint along with the initial actor, reuses the shapes unchanged scene/history, workspace observation/readout, decoder, and critic weights, as well as existing optimizer moments; only initializes the newly added GRU parameters, without distillation, and retains the update and distributed random states. Exact copy counts and artifact hashes are based solely on the generated `migration-report.json`.

Early vocabulary/capacity migration marginalized the DEFAULT probability quality and latent-skill conditional behavior of the old actor; it does not belong to this memory architecture switch. The Persistent GRU branch directly continues PPO from the completed warm-up strategy checkpoint, without replaying teacher data or re-executing critic warm-up.

New compact data must use dataset v4 and be bound with action codec, observation encoder, unit shape, and derived-fact ABI. Old shards lack inventory order and additional unit slots and cannot be padded and reclassified as new data. Chunked BC currently rejects recurrent strategy; the stateful training of the main strategy comes from complete sequence semantic distillation and complete episode PPO.

Each RL rollout report records the actual coverage of new unit slots, decision positions, and inventory-order fields.
No coverage indicates that the complete rule-based RL has not yet reached that state, and thus the teacher cannot truncate the output to generate labels.

## Verification and Open Decision-making

Return validation coverage of native/official observation encoding consistency, explicit quantity action codec, same turn HIRE capacity, CPU/CUDA economic replay, sequence/eager/CUDA history and strategy recurrence, decoder logits parity, padding state freeze, as well as critic's gradient isolation from actor state.

The number of strategy slots and subsequent optimization settings are recorded in the resolved migration/run log. Throughput, power consumption, and GPU memory can only be confirmed in the training implementation; the challenger has deployment significance only after a complete closed-loop competition proves that it has no regression and improves the direct outcome.
A failed challenger does not alter the current submission incumbent.
