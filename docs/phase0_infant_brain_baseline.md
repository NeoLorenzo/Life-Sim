# Phase 0 Baseline - Infant Brain Redesign

Date: 2026-02-13
Scope: Baseline capture and design freeze only (no behavior changes).

## 1) Frozen current infant decision path

- Event selection entrypoint: `life_sim/simulation/events.py:260` (`_choose_indices_with_brain`)
- Infant NPC monthly auto-resolve wrapper: `life_sim/simulation/events.py:417` (`auto_resolve_npc_infant_events`)
- Infant month-cursor resolve path: `life_sim/simulation/events.py:521` (`resolve_infant_event_for_agent_at_month`)
- Infant replay loop: `life_sim/simulation/events.py:574` (`replay_infant_events_for_agent`)

## 2) Frozen legacy conversion points to replace in redesign

- Feature mapper: `life_sim/simulation/brain.py:81` (`event_choice_to_features`)
- Artificial temperament conversion:
  - `life_sim/simulation/brain.py:103` -> `features["delta_happiness"] += avg / 10.0`
  - `life_sim/simulation/brain.py:104` -> `features["novelty"] += abs(avg) / 12.0`

## 3) Non-goals for redesign (locked)

- Do not change non-infant decision behavior (`age_months >= 36`).
- Do not change adult/child utility features used by `NPCBrain` outside infant flow.
- Do not alter RNG seed contract used by `make_decision_rng`.

## 4) Determinism acceptance criteria (Phase 0 definition)

- Same world seed + agent UID + month step + domain + decision key must produce identical infant choice outcomes.
- Infant backfill replay must remain deterministic for same seed across runs.
- Legacy/adult path outputs must remain unchanged while infant redesign is behind a feature flag.

## 5) Baseline test execution evidence

Attempted command:

```powershell
pytest -q tests/test_phase5_npc_infant_event_autoresolve.py tests/test_infant_backfill_event_replay.py
```

Result:

- `pytest` not on PATH.

Fallback attempted:

```powershell
python -m pytest -q tests/test_phase5_npc_infant_event_autoresolve.py tests/test_infant_backfill_event_replay.py
```

Result:

- `No module named pytest`.

Executed baseline via unittest:

```powershell
python -m unittest tests.test_phase5_npc_infant_event_autoresolve tests.test_infant_backfill_event_replay -v
```

Result summary:

- Total: 5 tests
- Passed: 4
- Failed: 1
- Failure:
  - `tests/test_phase5_npc_infant_event_autoresolve.py:49`
  - `AssertionError: 0 not greater than or equal to 1`

Passing tests:

- `test_auto_resolve_is_deterministic_for_same_seed`
- `test_npc_backfill_infant_replay_is_deterministic`
- `test_npc_backfill_replay_disabled_keeps_event_history_empty`
- `test_npc_backfill_replays_infant_events_when_enabled`

## 6) Phase 0 exit status

- Baseline path references captured: complete
- Legacy conversion points captured: complete
- Non-goals and determinism criteria documented: complete
- Current baseline tests recorded: complete (with one existing failing test in auto-resolve suite)
