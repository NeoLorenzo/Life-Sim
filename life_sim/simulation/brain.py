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


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


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
