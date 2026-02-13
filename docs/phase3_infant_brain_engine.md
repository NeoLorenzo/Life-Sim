# Phase 3 - Infant Brain Engine (Implemented)

Date: 2026-02-13  
Depends on: `docs/phase2_data_contracts.md`

## Implemented in this phase

1) New infant appraisal and state contracts in `life_sim/simulation/brain.py`
- `CANONICAL_INFANT_APPRAISAL_KEYS`
- `DEFAULT_INFANT_PARAMS`
- `DEFAULT_INFANT_STATE`
- `DEFAULT_INFANT_BRAIN_WEIGHTS`
- `DEFAULT_INFANT_BRAIN_PENALTIES`

2) New deterministic mapping/extraction helpers in `life_sim/simulation/brain.py`
- `temperament_to_infant_params(temperament)`
- `choice_to_infant_appraisal(choice)`
- Deterministic fallback path for missing `effects.infant_appraisal`

3) New infant decision engine in `life_sim/simulation/brain.py`
- `InfantBrain` class with:
  - utility scoring based on comfort/cost/fit
  - energy and safety penalties
  - softmax probability distribution
  - deterministic RNG-compatible sampling
  - trace payload for debug/testing

## What is intentionally not changed yet

- Event routing still uses legacy `NPCBrain` path in `EventManager`.
- Feature flags are not consumed by selection routing yet.
- No changes to `events.json` content in this phase.

## Tests added and status

Added:
- `tests/test_phase3_infant_brain_core.py`

Validated:
- `python -m unittest tests.test_phase3_infant_brain_core tests.test_phase1_npc_brain_core -v`
- Result: all tests passed.

## Phase 3 checklist

- [x] Infant appraisal schema codified in code.
- [x] Temperament to infant-params mapping implemented.
- [x] Deterministic appraisal fallback implemented.
- [x] Infant utility engine implemented.
- [x] Deterministic choice behavior validated.
- [x] Legacy NPC brain core tests still pass.
