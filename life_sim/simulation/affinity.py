# life_sim/simulation/affinity.py
"""
Affinity Calculation Module.

Pure functions for calculating psychometric compatibility between two agents.

Data Contract:
    Inputs:  Two Agent objects with a working get_personality_sum(trait) method.
    Outputs: Integer score in [-100, +100] and an optional list of (label, value) pairs.
    Side effects: None. Both functions are pure and safe to call from anywhere.
    Invariants:
        - Symmetric:  affinity(A, B) == affinity(B, A)
        - Bounded:    score is strictly clamped to [AFFINITY_SCORE_MIN, AFFINITY_SCORE_MAX]
        - Additive:   all effects combine linearly; no term depends on another term's result
"""
import logging
from .. import constants

logger = logging.getLogger(__name__)

def get_affinity_breakdown(agent_a, agent_b):
    """
    Calculates full psychometric compatibility with a labeled breakdown.

    Args:
        agent_a: First Agent instance.
        agent_b: Second Agent instance.

    Returns:
        Tuple of (final_score: int, breakdown: list[tuple[str, float]]).
        breakdown contains one entry per effect that exceeded AFFINITY_LABEL_THRESHOLD.
    """
    breakdown = []
    score = 0.0

    # --- 1. Actor Effects (Individual Traits) ---
    # Each agent contributes a unilateral modifier that applies to ALL of their
    # relationships.  This models the idea that personality extremes have a
    # universal social cost or benefit independent of who they're paired with.

    # Neuroticism — a dominant negative trait drags down every relationship.
    # Weighted at 0.5x so even max Neuroticism (120) only contributes -25,
    # leaving dyadic compatibility as the primary driver.
    for agent in [agent_a, agent_b]:
        n_val = agent.get_personality_sum("Neuroticism")
        if n_val > constants.AFFINITY_ACTOR_THRESHOLD:
            pen = -(n_val - constants.AFFINITY_ACTOR_THRESHOLD) * constants.AFFINITY_ACTOR_WEIGHT
            score += pen
            breakdown.append((f"{agent.first_name}'s Neuroticism", pen))

    # Agreeableness — a dominant positive trait provides universal social
    # lubrication.  Symmetric with Neuroticism in structure and weight so
    # the two can meaningfully cancel each other out.
    for agent in [agent_a, agent_b]:
        a_val = agent.get_personality_sum("Agreeableness")
        if a_val > constants.AFFINITY_ACTOR_THRESHOLD:
            bon = (a_val - constants.AFFINITY_ACTOR_THRESHOLD) * constants.AFFINITY_ACTOR_WEIGHT
            score += bon
            breakdown.append((f"{agent.first_name}'s Agreeableness", bon))

    # --- 2. Dyadic Effects (Similarity / Homophily) ---
    # Compares the same trait across both agents.  The effect flips sign at
    # AFFINITY_DYADIC_THRESHOLD: deltas below it produce attraction (shared
    # ground), deltas above it produce repulsion (incompatible worldviews).
    # Formula per trait: (THRESHOLD - delta) * WEIGHT

    # Openness — governs core values and intellectual worldview.  Weighted
    # highest (tied with Conscientiousness) because value alignment is the
    # strongest predictor of long-term relationship viability.
    o_a = agent_a.get_personality_sum("Openness")
    o_b = agent_b.get_personality_sum("Openness")
    effect_o = (constants.AFFINITY_DYADIC_THRESHOLD - abs(o_a - o_b)) * constants.AFFINITY_OPENNESS_WEIGHT
    score += effect_o

    if effect_o > constants.AFFINITY_LABEL_THRESHOLD:
        breakdown.append(("Shared Interests (Openness)", effect_o))
    elif effect_o < -constants.AFFINITY_LABEL_THRESHOLD:
        breakdown.append(("Value Clash (Openness)", effect_o))

    # Conscientiousness — governs daily-life organisation and habits.
    # Weighted equally with Openness: people with incompatible routines
    # grind against each other constantly, even when values align.
    c_a = agent_a.get_personality_sum("Conscientiousness")
    c_b = agent_b.get_personality_sum("Conscientiousness")
    effect_c = (constants.AFFINITY_DYADIC_THRESHOLD - abs(c_a - c_b)) * constants.AFFINITY_CONSCIENTIOUSNESS_WEIGHT
    score += effect_c

    if effect_c > constants.AFFINITY_LABEL_THRESHOLD:
        breakdown.append(("Lifestyle Sync (Order)", effect_c))
    elif effect_c < -constants.AFFINITY_LABEL_THRESHOLD:
        breakdown.append(("Lifestyle Clash (Order)", effect_c))

    # Extraversion — governs social energy and preferred stimulation level.
    # Weighted lower than the two above: energy mismatch creates friction
    # but rarely breaks a relationship that is otherwise well-matched on
    # values and habits.
    e_a = agent_a.get_personality_sum("Extraversion")
    e_b = agent_b.get_personality_sum("Extraversion")
    effect_e = (constants.AFFINITY_DYADIC_THRESHOLD - abs(e_a - e_b)) * constants.AFFINITY_EXTRAVERSION_WEIGHT
    score += effect_e

    if effect_e > constants.AFFINITY_LABEL_THRESHOLD:
        breakdown.append(("Energy Match", effect_e))
    elif effect_e < -constants.AFFINITY_LABEL_THRESHOLD:
        breakdown.append(("Energy Mismatch", effect_e))

    # Clamp to documented invariant bounds
    final_score = max(constants.AFFINITY_SCORE_MIN,
                      min(constants.AFFINITY_SCORE_MAX, int(round(score))))
    return final_score, breakdown

def calculate_affinity(agent_a, agent_b):
    """
    Calculates psychometric compatibility without building a breakdown.

    Runs the identical math as get_affinity_breakdown but skips all label
    checks and list construction.  Use this for bulk initialisation (e.g.
    populating classmate networks); use get_affinity_breakdown when the
    breakdown is needed (e.g. social-graph tooltips).

    Args:
        agent_a: First Agent instance.
        agent_b: Second Agent instance.

    Returns:
        Integer compatibility score clamped to [AFFINITY_SCORE_MIN, AFFINITY_SCORE_MAX].
    """
    score = 0.0

    # Actor effects
    for agent in [agent_a, agent_b]:
        n_val = agent.get_personality_sum("Neuroticism")
        if n_val > constants.AFFINITY_ACTOR_THRESHOLD:
            score -= (n_val - constants.AFFINITY_ACTOR_THRESHOLD) * constants.AFFINITY_ACTOR_WEIGHT

        a_val = agent.get_personality_sum("Agreeableness")
        if a_val > constants.AFFINITY_ACTOR_THRESHOLD:
            score += (a_val - constants.AFFINITY_ACTOR_THRESHOLD) * constants.AFFINITY_ACTOR_WEIGHT

    # Dyadic effects
    score += (constants.AFFINITY_DYADIC_THRESHOLD - abs(
        agent_a.get_personality_sum("Openness") -
        agent_b.get_personality_sum("Openness")
    )) * constants.AFFINITY_OPENNESS_WEIGHT

    score += (constants.AFFINITY_DYADIC_THRESHOLD - abs(
        agent_a.get_personality_sum("Conscientiousness") -
        agent_b.get_personality_sum("Conscientiousness")
    )) * constants.AFFINITY_CONSCIENTIOUSNESS_WEIGHT

    score += (constants.AFFINITY_DYADIC_THRESHOLD - abs(
        agent_a.get_personality_sum("Extraversion") -
        agent_b.get_personality_sum("Extraversion")
    )) * constants.AFFINITY_EXTRAVERSION_WEIGHT

    return max(constants.AFFINITY_SCORE_MIN,
               min(constants.AFFINITY_SCORE_MAX, int(round(score))))