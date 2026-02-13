# Phase 2 - Config and Data Contracts (Implemented)

Date: 2026-02-13  
Depends on: `docs/phase1_infant_domain_spec.md`

## Scope completed

This phase adds non-breaking scaffolding only:
- New config toggles and constants container for infant brain v2.
- Brain profile contract fields for infant v2 metadata, params, and state.
- Backward-compatible normalization for agents that load older brain payloads.

No selection logic was switched to infant v2 in this phase.

## Changes applied

1) `config.json`
- Added `npc_brain.infant_brain_v2_enabled` (default `false`)
- Added `npc_brain.infant_brain_v2_debug_logging` (default `false`)
- Added `npc_brain.infant_brain_v2` object:
  - `version`
  - `weights` (`comfort`, `cost`, `fit`)
  - `penalties` thresholds and magnitudes from Phase 1 spec

2) `life_sim/simulation/sim_state.py`
- Extended `_build_brain_profile(...)` to include:
  - `infant_brain_version`
  - `infant_brain_v2_enabled`
  - `infant_params` defaults
  - `infant_state` defaults
- Values are deterministic/static scaffolding and do not alter event choice routing.

3) `life_sim/simulation/agent.py`
- Added `_ensure_brain_contract(...)` to normalize missing keys for backward compatibility.
- Called normalization in `Agent.__init__` right after brain payload creation/copy.
- Ensures older brain payloads gain the new infant-v2 scaffold fields safely.

## Backward compatibility guarantees

- Existing callers can pass old brain dicts; missing keys are auto-filled.
- Existing phase tests that assert base brain shape remain valid.
- Existing runtime path still uses legacy `NPCBrain` event scoring for infants.

## Phase 2 checklist

- [x] Add config flag `infant_brain_v2_enabled`.
- [x] Add config flag `infant_brain_v2_debug_logging`.
- [x] Add config bucket for infant-v2 constants.
- [x] Add brain profile metadata version key for infant v2.
- [x] Add default infant params scaffold.
- [x] Add default infant state scaffold.
- [x] Add backward-compatible key normalization for older agent brain payloads.
- [x] Keep runtime behavior unchanged (no routing change in event decision path).
