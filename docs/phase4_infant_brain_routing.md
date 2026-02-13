# Phase 4 - Infant Brain Routing (Implemented)

Date: 2026-02-13  
Depends on: `docs/phase3_infant_brain_engine.md`

## Implemented

Updated `life_sim/simulation/events.py` routing in `_choose_indices_with_brain(...)`:

- Added infant-v2 activation gate:
  - `npc_brain.infant_brain_v2_enabled` must be `true`
  - agent age cursor must be `<= 35` months
  - event must be infant event (`_is_infant_event`)
  - agent must have temperament data

- Added infant context builder:
  - merges derived temperament params (`temperament_to_infant_params`) with scaffolded brain params
  - loads infant state from `agent.brain["infant_state"]` with clamped defaults
  - loads infant-v2 weights/penalties from config

- Added infant-v2 choice path:
  - uses `choice_to_infant_appraisal(...)`
  - scores/selects via `InfantBrain`
  - preserves deterministic RNG contract via existing `make_decision_rng(...)`
  - supports single-select and generic multi-select
  - optional debug logging controlled by `infant_brain_v2_debug_logging`

- Preserved non-infant path:
  - existing `NPCBrain` routing remains unchanged for non-infant events
  - IGCSE special-case path is unchanged

## Tests added

- `tests/test_phase4_infant_brain_routing.py`
  - verifies infant events route away from `NPCBrain` when v2 is enabled
  - verifies non-infant events do not route through `InfantBrain`

## Validation run

- `python -m py_compile life_sim/simulation/events.py tests/test_phase4_infant_brain_routing.py`
- `python -m unittest tests.test_phase4_infant_brain_routing tests.test_phase3_infant_brain_core -v`
- Result: all tests passed.
