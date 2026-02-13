# Phase 8 - Rollout and Cutover (Implemented)

Date: 2026-02-13  
Depends on: `docs/phase7_regression_shield.md`

## Cutover changes

1) Default enablement
- Updated `config.json`:
  - `npc_brain.infant_brain_v2_enabled: true`

2) Rollout coverage update
- Updated `tests/test_phase8_rollout.py` to explicitly run rollout snapshots with:
  - `npc_brain.infant_brain_v2_enabled = true`
  - `npc_brain.infant_brain_v2_debug_logging = false`

3) Rollout assertions
- Kept existing reproducibility/perf/history assertions.
- Added scaffold assertion:
  - `test_rollout_keeps_brain_scaffold_present`
  - validates NPC brain payloads include infant-state scaffolding under rollout conditions.

## Validation run

Executed:
- `python -m py_compile tests/test_phase8_rollout.py`
- `python -m unittest tests.test_phase8_rollout tests.test_phase7_infant_brain_regression_shield tests.test_phase6_infant_event_data_migration -v`

Result:
- All tests passed.

## Rollout status

- Infant brain v2 is now default-on via config.
- Deterministic seed reproducibility remains intact in rollout tests.
- Non-infant parity guardrails and infant-v2 isolation tests remain green.

## Known pre-existing failure (unchanged)

- `tests/test_phase5_npc_infant_event_autoresolve.py::test_auto_resolve_infant_npc_event_updates_target_npc`
- Fails with `resolved == 0` vs expected `>= 1`
- This issue predated phase-8 cutover and was not introduced by rollout changes.
