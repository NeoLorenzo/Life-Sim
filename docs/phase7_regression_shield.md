# Phase 7 - Regression Shield (Implemented)

Date: 2026-02-13  
Depends on: `docs/phase6_infant_event_data_migration.md`

## Implemented

Added regression-focused test suite:
- `tests/test_phase7_infant_brain_regression_shield.py`

Coverage added:

1) Infant-v2 isolation from legacy mapper
- Verifies infant v2 routing does not call `event_choice_to_features` for infant choices.

2) Non-infant parity under infant-v2 toggle
- Verifies non-infant event selection output is identical when toggling:
  - `npc_brain.infant_brain_v2_enabled = false`
  - `npc_brain.infant_brain_v2_enabled = true`

3) Infant-v2 deterministic choice behavior
- Verifies identical choice output for same seed + same event + same agent input.

## Validation run

Executed:
- `python -m py_compile tests/test_phase7_infant_brain_regression_shield.py`
- `python -m unittest tests.test_phase7_infant_brain_regression_shield tests.test_phase6_infant_event_data_migration tests.test_phase5_infant_state_dynamics tests.test_phase4_infant_brain_routing -v`

Result:
- All tests passed.

## Residual known issue

Unchanged pre-existing failing test (outside this suite):
- `tests/test_phase5_npc_infant_event_autoresolve.py::test_auto_resolve_infant_npc_event_updates_target_npc`
- Failure: expected resolved count `>= 1`, got `0`
- This failure was present before the infant-v2 regression-shield work.
