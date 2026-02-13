# Phase 1 Spec - Infant Domain Model (No Runtime Changes)

Date: 2026-02-13  
Depends on: `docs/phase0_infant_brain_baseline.md`

## 1) Goal and scope

This phase defines the infant decision domain contract only. It does not change runtime behavior.

In scope:
- Infant appraisal dimensions for event choices.
- Infant internal state schema.
- Temperament to infant-drive mapping formulas.
- Infant scoring equation specification.
- `events.json` extension shape and deterministic fallback rules.

Out of scope:
- Wiring into `EventManager` selection path.
- New brain class implementation.
- Any config flag or runtime migration logic.

## 2) Canonical infant appraisal dimensions

Each infant event choice should be represented by this normalized appraisal vector:

- `comfort_value` in `[0.0, 1.0]`
- `energy_cost` in `[0.0, 1.0]`
- `safety_risk` in `[0.0, 1.0]`
- `novelty_load` in `[0.0, 1.0]`
- `familiarity` in `[0.0, 1.0]`
- `social_soothing` in `[0.0, 1.0]`

Interpretation:
- Higher `comfort_value` and `social_soothing` are approach signals.
- Higher `energy_cost` and `safety_risk` are avoidance signals.
- `novelty_load` is not globally good/bad; it is filtered by infant novelty tolerance.
- `familiarity` is generally reassuring and buffers novelty overload.

## 3) Infant internal state schema

Additive state contract (for future wiring under `agent.brain["infant_state"]`):

- `energy_level` in `[0.0, 1.0]` (higher means more available activation)
- `satiety_level` in `[0.0, 1.0]` (higher means less hunger discomfort)
- `security_level` in `[0.0, 1.0]` (higher means safer baseline)
- `stimulation_load` in `[0.0, 1.0]` (higher means currently overloaded)
- `last_event_novelty` in `[0.0, 1.0]` (memory term for carryover novelty)

Default initialization (spec only):
- `energy_level = 0.65`
- `satiety_level = 0.60`
- `security_level = 0.70`
- `stimulation_load = 0.25`
- `last_event_novelty = 0.20`

## 4) Temperament to infant-drive mapping

Source temperament traits are from `life_sim/constants.py`:
- `Activity`
- `Regularity`
- `Approach_Withdrawal`
- `Adaptability`
- `Threshold`
- `Intensity`
- `Mood`
- `Distractibility`
- `Persistence`

Normalize each trait to centered range:

`z(trait) = clamp((trait - 50.0) / 50.0, -1.0, 1.0)`

Derived infant parameters (all clamped to `[0.0, 1.0]`):

- `novelty_tolerance = clamp01(0.50 + 0.28*z(Approach_Withdrawal) + 0.20*z(Adaptability) + 0.12*z(Activity) - 0.15*z(Threshold))`
- `threat_sensitivity = clamp01(0.50 - 0.24*z(Threshold) - 0.18*z(Mood) + 0.16*z(Intensity) - 0.10*z(Adaptability))`
- `energy_budget = clamp01(0.50 + 0.30*z(Activity) + 0.20*z(Persistence) + 0.15*z(Regularity) - 0.12*z(Distractibility))`
- `self_regulation = clamp01(0.50 + 0.22*z(Regularity) + 0.20*z(Persistence) + 0.16*z(Adaptability) - 0.18*z(Intensity) - 0.14*z(Distractibility))`
- `comfort_bias = clamp01(0.50 + 0.25*z(Mood) + 0.15*z(Regularity) + 0.10*z(Threshold) - 0.10*z(Intensity))`

Rationale:
- `Approach_Withdrawal`, `Adaptability`, and `Activity` should raise novelty tolerance.
- Lower `Threshold` should increase sensitivity; higher `Intensity` should increase reactivity.
- `Regularity` and `Persistence` support regulated, sustained responding.

## 5) Infant scoring equation (spec for implementation phase)

Given appraisal vector `a` and infant state `s`, compute intermediate terms:

- `need_comfort = 1.0 - (0.5*s.satiety_level + 0.5*s.security_level)`
- `effective_energy_margin = s.energy_level - a.energy_cost`
- `novelty_mismatch = abs(a.novelty_load - novelty_tolerance)`
- `overload_pressure = clamp01(0.6*s.stimulation_load + 0.4*s.last_event_novelty + a.novelty_load - self_regulation)`

Utility components:

- `comfort_term = (a.comfort_value * (0.55 + 0.45*comfort_bias)) + (a.social_soothing * (0.35 + 0.65*need_comfort)) + (a.familiarity * (0.20 + 0.30*threat_sensitivity))`
- `cost_term = (a.energy_cost * (0.45 + 0.55*(1.0 - energy_budget))) + (a.safety_risk * (0.40 + 0.60*threat_sensitivity))`
- `fit_term = (0.30 * (1.0 - novelty_mismatch)) - (0.35 * overload_pressure)`

Final utility:

`U = comfort_term - cost_term + fit_term`

Hard penalties:
- If `effective_energy_margin < -0.25`, apply `U -= 0.35`.
- If `a.safety_risk > 0.75` and `threat_sensitivity > 0.60`, apply `U -= 0.40`.

Sampling:
- Keep stochastic choice via softmax temperature in later phase.
- Deterministic seed contract remains unchanged (Phase 0 invariant).

## 6) events.json extension contract

Proposed optional block per infant choice under `effects`:

```json
{
  "effects": {
    "temperament": {
      "Activity": 5,
      "Persistence": 3
    },
    "infant_appraisal": {
      "comfort_value": 0.45,
      "energy_cost": 0.75,
      "safety_risk": 0.15,
      "novelty_load": 0.70,
      "familiarity": 0.20,
      "social_soothing": 0.10
    }
  }
}
```

Rules:
- All keys optional at authoring time.
- Missing keys default to deterministic fallback values.
- Values outside `[0.0, 1.0]` are clamped during parsing.

## 7) Deterministic fallback when infant_appraisal is missing

Fallback uses existing temperament effects only. No randomness allowed.

Let `t` be mean signed temperament delta for that choice:

- `t = clamp(avg(temperament_effect_values) / 8.0, -1.0, 1.0)`  
  If no temperament effects, use `t = 0.0`.

Deterministic fallback appraisal:
- `comfort_value = clamp01(0.45 + 0.25*t)`
- `energy_cost = clamp01(0.40 + 0.20*max(t, 0.0) + 0.10*max(-t, 0.0))`
- `safety_risk = clamp01(0.25 + 0.20*max(-t, 0.0))`
- `novelty_load = clamp01(0.35 + 0.30*abs(t))`
- `familiarity = clamp01(0.55 - 0.20*abs(t))`
- `social_soothing = 0.30`

Note:
- This fallback is transitional and intentionally simple.
- It avoids the old mapping into `delta_happiness`/`novelty` utility features.

## 8) Validation checklist for this phase

- [x] Appraisal dimensions and ranges defined.
- [x] Infant state keys and defaults defined.
- [x] Temperament mapping equations defined and bounded.
- [x] Utility scoring equation with penalty rules defined.
- [x] `events.json` extension schema defined.
- [x] Deterministic fallback rules defined.
- [x] Runtime behavior unchanged in this phase.

## 9) Phase 1 exit criteria

Phase 1 is complete when:
- Engineering can implement infant model without inventing missing math or schema.
- Test design can derive deterministic assertions from this document.
- No runtime code paths are changed yet.
