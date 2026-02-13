"""
NPC brain core utilities.

Phase 1 scope:
- Canonical feature schema
- Deterministic decision RNG helper
- Utility scoring
- Softmax sampling

Phase 3 additions:
- Player style tracker helpers
- Event choice -> canonical feature extraction
- Weight blending with bounded alpha

Phase 3 infant engine additions:
- Infant appraisal schema
- Temperament -> infant parameter mapping
- Deterministic infant appraisal extraction with fallback
- Infant utility brain with probabilistic choice
"""
import math
import random


CANONICAL_FEATURE_KEYS = (
    "delta_happiness",
    "delta_health",
    "delta_money",
    "delta_school",
    "delta_relationship",
    "risk",
    "effort",
    "novelty",
)


DEFAULT_BASE_WEIGHTS = {
    "delta_happiness": 0.30,
    "delta_health": 0.25,
    "delta_money": 0.15,
    "delta_school": 0.20,
    "delta_relationship": 0.15,
    "risk": -0.30,
    "effort": -0.12,
    "novelty": 0.08,
}

CANONICAL_INFANT_APPRAISAL_KEYS = (
    "comfort_value",
    "energy_cost",
    "safety_risk",
    "novelty_load",
    "familiarity",
    "social_soothing",
)

DEFAULT_INFANT_PARAMS = {
    "novelty_tolerance": 0.5,
    "threat_sensitivity": 0.5,
    "energy_budget": 0.5,
    "self_regulation": 0.5,
    "comfort_bias": 0.5,
}

DEFAULT_INFANT_STATE = {
    "energy_level": 0.65,
    "satiety_level": 0.60,
    "security_level": 0.70,
    "stimulation_load": 0.25,
    "last_event_novelty": 0.20,
}

DEFAULT_INFANT_BRAIN_WEIGHTS = {
    "comfort": 1.0,
    "cost": 1.0,
    "fit": 1.0,
}

DEFAULT_INFANT_BRAIN_PENALTIES = {
    "energy_margin_threshold": -0.25,
    "energy_penalty": 0.35,
    "safety_risk_threshold": 0.75,
    "threat_sensitivity_threshold": 0.60,
    "safety_penalty": 0.40,
}


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _clamp01(value):
    return _clamp(float(value), 0.0, 1.0)


def _zscore_temperament(raw):
    """
    Converts a temperament trait from [0..100] to centered [-1..1].
    """
    return _clamp((float(raw) - 50.0) / 50.0, -1.0, 1.0)


def temperament_to_infant_params(temperament):
    """
    Maps temperament traits to infant decision parameters in [0,1].
    """
    temperament = temperament or {}

    def z(name):
        return _zscore_temperament(float(temperament.get(name, 50.0)))

    params = {
        "novelty_tolerance": _clamp01(
            0.50
            + (0.28 * z("Approach_Withdrawal"))
            + (0.20 * z("Adaptability"))
            + (0.12 * z("Activity"))
            - (0.15 * z("Threshold"))
        ),
        "threat_sensitivity": _clamp01(
            0.50
            - (0.24 * z("Threshold"))
            - (0.18 * z("Mood"))
            + (0.16 * z("Intensity"))
            - (0.10 * z("Adaptability"))
        ),
        "energy_budget": _clamp01(
            0.50
            + (0.30 * z("Activity"))
            + (0.20 * z("Persistence"))
            + (0.15 * z("Regularity"))
            - (0.12 * z("Distractibility"))
        ),
        "self_regulation": _clamp01(
            0.50
            + (0.22 * z("Regularity"))
            + (0.20 * z("Persistence"))
            + (0.16 * z("Adaptability"))
            - (0.18 * z("Intensity"))
            - (0.14 * z("Distractibility"))
        ),
        "comfort_bias": _clamp01(
            0.50
            + (0.25 * z("Mood"))
            + (0.15 * z("Regularity"))
            + (0.10 * z("Threshold"))
            - (0.10 * z("Intensity"))
        ),
    }
    for key in DEFAULT_INFANT_PARAMS:
        params[key] = _clamp01(params.get(key, DEFAULT_INFANT_PARAMS[key]))
    return params


def _fallback_infant_appraisal_from_choice(choice):
    effects = {}
    if isinstance(choice, dict):
        effects = choice.get("effects", {}) or {}
    temperament = effects.get("temperament", {}) or {}

    t = 0.0
    if temperament:
        vals = []
        for value in temperament.values():
            try:
                vals.append(float(value))
            except (TypeError, ValueError):
                continue
        if vals:
            t = _clamp((sum(vals) / float(len(vals))) / 8.0, -1.0, 1.0)

    return {
        "comfort_value": _clamp01(0.45 + (0.25 * t)),
        "energy_cost": _clamp01(0.40 + (0.20 * max(t, 0.0)) + (0.10 * max(-t, 0.0))),
        "safety_risk": _clamp01(0.25 + (0.20 * max(-t, 0.0))),
        "novelty_load": _clamp01(0.35 + (0.30 * abs(t))),
        "familiarity": _clamp01(0.55 - (0.20 * abs(t))),
        "social_soothing": 0.30,
    }


def choice_to_infant_appraisal(choice):
    """
    Extracts infant appraisal vector from event choice.
    If missing, derives deterministic fallback from temperament effects.
    """
    fallback = _fallback_infant_appraisal_from_choice(choice)
    out = dict(fallback)
    if not isinstance(choice, dict):
        return out
    effects = choice.get("effects", {}) or {}
    appraisal = effects.get("infant_appraisal", {}) or {}
    if not isinstance(appraisal, dict):
        return out

    for key in CANONICAL_INFANT_APPRAISAL_KEYS:
        if key in appraisal:
            try:
                out[key] = _clamp01(float(appraisal.get(key)))
            except (TypeError, ValueError):
                out[key] = fallback[key]
        else:
            out[key] = fallback[key]
    return out


def make_decision_rng(world_seed, agent_uid, month_step, domain, decision_key):
    """
    Creates deterministic per-decision RNG.
    """
    seed = f"{world_seed}|{agent_uid}|{month_step}|{domain}|{decision_key}"
    return random.Random(seed)


def default_player_style_tracker(beta=0.15):
    return {
        "version": "phase3_style_tracker_v1",
        "ema_beta": float(_clamp(float(beta), 0.01, 1.0)),
        "weights": {k: 0.0 for k in CANONICAL_FEATURE_KEYS},
        "observations": 0,
    }


def update_player_style_tracker(tracker, observed_features):
    """
    EMA update of player style preferences from one chosen option feature vector.
    """
    if not isinstance(tracker, dict):
        tracker = default_player_style_tracker()
    beta = float(_clamp(float(tracker.get("ema_beta", 0.15)), 0.01, 1.0))
    weights = tracker.get("weights", {}) or {}
    for key in CANONICAL_FEATURE_KEYS:
        prev = float(weights.get(key, 0.0))
        obs = float(observed_features.get(key, 0.0))
        weights[key] = prev + (beta * (obs - prev))
    tracker["weights"] = weights
    tracker["observations"] = int(tracker.get("observations", 0)) + 1
    return tracker


def event_choice_to_features(choice):
    """
    Maps event choice effects to canonical decision features.
    """
    features = {k: 0.0 for k in CANONICAL_FEATURE_KEYS}
    if not isinstance(choice, dict):
        return features

    effects = choice.get("effects", {}) or {}
    stats = effects.get("stats", {}) or {}
    temperament = effects.get("temperament", {}) or {}
    subjects = effects.get("subjects", {}) or {}

    # Stats
    features["delta_happiness"] += float(stats.get("happiness", 0.0)) / 10.0
    features["delta_health"] += float(stats.get("health", 0.0)) / 10.0
    features["delta_money"] += float(stats.get("money", 0.0)) / 1000.0

    # Temperament (infant events): positive aggregate interpreted as comfort/novel engagement.
    if temperament:
        vals = [float(v) for v in temperament.values()]
        avg = sum(vals) / float(len(vals))
        features["delta_happiness"] += avg / 10.0
        features["novelty"] += abs(avg) / 12.0

    # Subject effects
    if subjects:
        vals = [float(v) for v in subjects.values()]
        features["delta_school"] += (sum(vals) / float(len(vals))) / 10.0

    # Bounded canonical range for robust blending.
    for key in CANONICAL_FEATURE_KEYS:
        features[key] = _clamp(float(features[key]), -1.0, 1.0)
    return features


def blend_weights(base_weights, player_style_weights, alpha):
    """
    Blends base weights with player-style weights; alpha in [0, 1].
    """
    a = _clamp(float(alpha), 0.0, 1.0)
    out = {}
    for key in CANONICAL_FEATURE_KEYS:
        base = float((base_weights or {}).get(key, 0.0))
        style = float((player_style_weights or {}).get(key, 0.0))
        out[key] = _clamp(((1.0 - a) * base) + (a * style), -2.0, 2.0)
    return out


class NPCBrain:
    """
    Lightweight utility brain with probabilistic choice via softmax sampling.
    """

    def __init__(self, base_weights=None, temperature=1.0):
        self.base_weights = dict(DEFAULT_BASE_WEIGHTS)
        if isinstance(base_weights, dict):
            for key, value in base_weights.items():
                if key in CANONICAL_FEATURE_KEYS:
                    self.base_weights[key] = float(value)
        self.temperature = max(0.05, float(temperature))

    def _extract_features(self, option):
        raw = {}
        if isinstance(option, dict):
            raw = option.get("features", {}) or {}
        features = {}
        for key in CANONICAL_FEATURE_KEYS:
            value = raw.get(key, 0.0)
            try:
                features[key] = float(value)
            except (TypeError, ValueError):
                features[key] = 0.0
        return features

    def score_option(self, option):
        """
        Computes linear utility for one option.
        """
        features = self._extract_features(option)
        score = 0.0
        for key in CANONICAL_FEATURE_KEYS:
            score += self.base_weights.get(key, 0.0) * features.get(key, 0.0)
        return score, features

    def _softmax(self, scores):
        if not scores:
            return []
        t = max(0.05, self.temperature)
        max_score = max(scores)
        exp_scores = [math.exp((s - max_score) / t) for s in scores]
        total = sum(exp_scores)
        if total <= 0.0:
            uniform = 1.0 / float(len(scores))
            return [uniform for _ in scores]
        return [v / total for v in exp_scores]

    def _sample_index(self, probabilities, rng):
        if not probabilities:
            return -1
        x = rng.random()
        cumulative = 0.0
        for idx, p in enumerate(probabilities):
            cumulative += p
            if x <= cumulative:
                return idx
        return len(probabilities) - 1

    def choose(self, options, context=None, rng=None):
        """
        Chooses one option and returns traceable decision output.
        """
        if not options:
            return None

        rng = rng or random.Random(0)
        scored = []
        scores = []
        for idx, option in enumerate(options):
            score, features = self.score_option(option)
            scored.append(
                {
                    "index": idx,
                    "option_id": (
                        option.get("id")
                        if isinstance(option, dict) and option.get("id") is not None
                        else str(idx)
                    ),
                    "score": score,
                    "features": features,
                }
            )
            scores.append(score)

        probabilities = self._softmax(scores)
        chosen_idx = self._sample_index(probabilities, rng)
        return {
            "chosen_index": chosen_idx,
            "chosen_option": options[chosen_idx],
            "scores": scores,
            "probabilities": probabilities,
            "scored_options": scored,
            "context": context or {},
        }


class InfantBrain:
    """
    Infant utility brain based on comfort, safety, energy, and novelty fit.
    """

    def __init__(self, weights=None, penalties=None, temperature=1.0):
        self.weights = dict(DEFAULT_INFANT_BRAIN_WEIGHTS)
        if isinstance(weights, dict):
            for key in DEFAULT_INFANT_BRAIN_WEIGHTS.keys():
                if key in weights:
                    self.weights[key] = float(weights[key])

        self.penalties = dict(DEFAULT_INFANT_BRAIN_PENALTIES)
        if isinstance(penalties, dict):
            for key in DEFAULT_INFANT_BRAIN_PENALTIES.keys():
                if key in penalties:
                    self.penalties[key] = float(penalties[key])

        self.temperature = max(0.05, float(temperature))

    def _extract_appraisal(self, option):
        if isinstance(option, dict) and isinstance(option.get("appraisal"), dict):
            raw = option.get("appraisal", {}) or {}
            out = {}
            for key in CANONICAL_INFANT_APPRAISAL_KEYS:
                try:
                    out[key] = _clamp01(float(raw.get(key, 0.0)))
                except (TypeError, ValueError):
                    out[key] = 0.0
            return out
        return choice_to_infant_appraisal(option if isinstance(option, dict) else {})

    def _extract_params(self, context):
        params = dict(DEFAULT_INFANT_PARAMS)
        raw = {}
        if isinstance(context, dict):
            raw = context.get("infant_params", {}) or {}
        for key in DEFAULT_INFANT_PARAMS.keys():
            try:
                params[key] = _clamp01(float(raw.get(key, params[key])))
            except (TypeError, ValueError):
                params[key] = DEFAULT_INFANT_PARAMS[key]
        return params

    def _extract_state(self, context):
        state = dict(DEFAULT_INFANT_STATE)
        raw = {}
        if isinstance(context, dict):
            raw = context.get("infant_state", {}) or {}
        for key in DEFAULT_INFANT_STATE.keys():
            try:
                state[key] = _clamp01(float(raw.get(key, state[key])))
            except (TypeError, ValueError):
                state[key] = DEFAULT_INFANT_STATE[key]
        return state

    def _score_components(self, appraisal, params, state):
        need_comfort = 1.0 - ((0.5 * state["satiety_level"]) + (0.5 * state["security_level"]))
        effective_energy_margin = state["energy_level"] - appraisal["energy_cost"]
        novelty_mismatch = abs(appraisal["novelty_load"] - params["novelty_tolerance"])
        overload_pressure = _clamp01(
            (0.6 * state["stimulation_load"])
            + (0.4 * state["last_event_novelty"])
            + appraisal["novelty_load"]
            - params["self_regulation"]
        )

        comfort_term = (
            appraisal["comfort_value"] * (0.55 + (0.45 * params["comfort_bias"]))
            + appraisal["social_soothing"] * (0.35 + (0.65 * need_comfort))
            + appraisal["familiarity"] * (0.20 + (0.30 * params["threat_sensitivity"]))
        )
        cost_term = (
            appraisal["energy_cost"] * (0.45 + (0.55 * (1.0 - params["energy_budget"])))
            + appraisal["safety_risk"] * (0.40 + (0.60 * params["threat_sensitivity"]))
        )
        fit_term = (0.30 * (1.0 - novelty_mismatch)) - (0.35 * overload_pressure)
        return {
            "need_comfort": need_comfort,
            "effective_energy_margin": effective_energy_margin,
            "novelty_mismatch": novelty_mismatch,
            "overload_pressure": overload_pressure,
            "comfort_term": comfort_term,
            "cost_term": cost_term,
            "fit_term": fit_term,
        }

    def score_option(self, option, context=None):
        appraisal = self._extract_appraisal(option)
        params = self._extract_params(context)
        state = self._extract_state(context)
        components = self._score_components(appraisal, params, state)

        score = (
            (self.weights["comfort"] * components["comfort_term"])
            - (self.weights["cost"] * components["cost_term"])
            + (self.weights["fit"] * components["fit_term"])
        )

        if components["effective_energy_margin"] < float(self.penalties["energy_margin_threshold"]):
            score -= float(self.penalties["energy_penalty"])
        if (
            appraisal["safety_risk"] > float(self.penalties["safety_risk_threshold"])
            and params["threat_sensitivity"] > float(self.penalties["threat_sensitivity_threshold"])
        ):
            score -= float(self.penalties["safety_penalty"])

        trace = {
            "appraisal": appraisal,
            "params": params,
            "state": state,
            "components": components,
        }
        return float(score), trace

    def _softmax(self, scores):
        if not scores:
            return []
        t = max(0.05, self.temperature)
        max_score = max(scores)
        exp_scores = [math.exp((s - max_score) / t) for s in scores]
        total = sum(exp_scores)
        if total <= 0.0:
            uniform = 1.0 / float(len(scores))
            return [uniform for _ in scores]
        return [v / total for v in exp_scores]

    def _sample_index(self, probabilities, rng):
        if not probabilities:
            return -1
        x = rng.random()
        cumulative = 0.0
        for idx, p in enumerate(probabilities):
            cumulative += p
            if x <= cumulative:
                return idx
        return len(probabilities) - 1

    def choose(self, options, context=None, rng=None):
        if not options:
            return None

        rng = rng or random.Random(0)
        scores = []
        scored = []
        for idx, option in enumerate(options):
            score, trace = self.score_option(option, context=context)
            scores.append(score)
            scored.append(
                {
                    "index": idx,
                    "option_id": (
                        option.get("id")
                        if isinstance(option, dict) and option.get("id") is not None
                        else str(idx)
                    ),
                    "score": score,
                    "trace": trace,
                }
            )

        probabilities = self._softmax(scores)
        chosen_idx = self._sample_index(probabilities, rng)
        return {
            "chosen_index": chosen_idx,
            "chosen_option": options[chosen_idx],
            "scores": scores,
            "probabilities": probabilities,
            "scored_options": scored,
            "context": context or {},
        }
