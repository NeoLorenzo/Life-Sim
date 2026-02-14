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

def _extraversion_compatibility(e_a, e_b):
    """
    Calculates extraversion compatibility with complementarity effects.
    
    Optimal compatibility when traits are complementary but not extreme.
    Sweet spot: 30-50 point difference (complementary but balanced).
    
    Args:
        e_a: First agent's extraversion sum (0-120)
        e_b: Second agent's extraversion sum (0-120)
        
    Returns:
        Float compatibility score
    """
    diff = abs(e_a - e_b)
    
    # Sweet spot: 30-50 point difference (complementary but balanced)
    if constants.AFFINITY_EXTRAVERSION_COMP_MIN <= diff <= constants.AFFINITY_EXTRAVERSION_COMP_MAX:
        bonus = constants.AFFINITY_EXTRAVERSION_COMP_PEAK - (diff - constants.AFFINITY_EXTRAVERSION_COMP_MIN) * constants.AFFINITY_EXTRAVERSION_COMP_TAPER
        return bonus * constants.AFFINITY_EXTRAVERSION_WEIGHT
    
    # Too similar OR too extreme = neutral/slight penalty
    elif diff < constants.AFFINITY_EXTRAVERSION_COMP_MIN:
        return (constants.AFFINITY_DYADIC_THRESHOLD - diff) * 0.25  # Reduced similarity bonus
    else:  # diff > AFFINITY_EXTRAVERSION_COMP_MAX
        return (constants.AFFINITY_DYADIC_THRESHOLD - diff) * constants.AFFINITY_EXTRAVERSION_WEIGHT  # Full penalty

def _get_life_stage(age):
    """Determine life stage based on age."""
    if constants.LIFE_STAGE_CHILD[0] <= age <= constants.LIFE_STAGE_CHILD[1]:
        return "child"
    elif constants.LIFE_STAGE_TEEN[0] <= age <= constants.LIFE_STAGE_TEEN[1]:
        return "teen"
    elif constants.LIFE_STAGE_YOUNG_ADULT[0] <= age <= constants.LIFE_STAGE_YOUNG_ADULT[1]:
        return "young_adult"
    elif constants.LIFE_STAGE_ADULT[0] <= age <= constants.LIFE_STAGE_ADULT[1]:
        return "adult"
    elif constants.LIFE_STAGE_MATURE[0] <= age <= constants.LIFE_STAGE_MATURE[1]:
        return "mature"
    elif constants.LIFE_STAGE_SENIOR[0] <= age <= constants.LIFE_STAGE_SENIOR[1]:
        return "senior"
    else:
        return "senior"  # Fallback for very old ages

def _life_stage_compatibility(age_a, age_b):
    """
    Calculate life stage compatibility bonus/penalty.
    
    Based on developmental psychology and real social dynamics.
    Same life stage = bonus, different stages = contextual penalties/bonuses.
    
    Args:
        age_a: First agent's age in years
        age_b: Second agent's age in years
        
    Returns:
        Tuple of (score_modifier, label_string)
    """
    stage_a = _get_life_stage(age_a)
    stage_b = _get_life_stage(age_b)
    
    # Same stage = bonus
    if stage_a == stage_b:
        return constants.AFFINITY_LIFE_STAGE_SAME_BONUS, f"Life Stage Sync ({stage_a})"
    
    # Cross-stage compatibility matrix
    compatibility_matrix = {
        ("child", "teen"): (5, "Big Sibling Dynamic"),
        ("teen", "child"): (5, "Little Sibling Dynamic"),
        ("teen", "young_adult"): (2, "Mentorship Potential"),
        ("young_adult", "teen"): (2, "Guidance Role"),
        ("young_adult", "adult"): (5, "Career Guidance"),
        ("adult", "young_adult"): (5, "Experience Sharing"),
        ("adult", "mature"): (8, "Life Experience"),
        ("mature", "adult"): (8, "Wisdom Transfer"),
        ("mature", "senior"): (10, "Peer Support"),
        ("senior", "mature"): (10, "Life Reflection"),
        
        # Incompatible pairs
        ("child", "adult"): (-15, "Different Priorities"),
        ("adult", "child"): (-15, "Parent-Child Gap"),
        ("teen", "senior"): (-20, "Generation Gap"),
        ("senior", "teen"): (-20, "Generation Gap"),
        ("young_adult", "senior"): (-10, "Life Phase Mismatch"),
        ("senior", "young_adult"): (-10, "Life Phase Mismatch"),
    }
    
    result = compatibility_matrix.get((stage_a, stage_b))
    if result:
        return result
    
    # Default penalty for undefined combinations
    return constants.AFFINITY_LIFE_STAGE_DEFAULT_PENALTY, "Life Stage Mismatch"

def _trait_specific_compatibility(trait_a, trait_b, trait_name):
    """
    Calculate trait-specific compatibility with asymmetric penalties.
    
    Different traits have different tolerance levels and penalty severities.
    Based on research showing some trait mismatches are more damaging than others.
    
    Args:
        trait_a: First agent's trait sum (0-120)
        trait_b: Second agent's trait sum (0-120)
        trait_name: Name of trait ("Openness" or "Conscientiousness")
        
    Returns:
        Tuple of (score_modifier, label_string)
    """
    diff = abs(trait_a - trait_b)
    
    if trait_name == "Openness":
        threshold = constants.AFFINITY_OPENNESS_THRESHOLD
        weight = constants.AFFINITY_OPENNESS_WEIGHT
        severity = constants.AFFINITY_OPENNESS_PENALTY_SEVERITY
        positive_label = "Shared Interests (Openness)"
        negative_label_base = "Value Clash"
    elif trait_name == "Conscientiousness":
        threshold = constants.AFFINITY_CONSCIENTIOUSNESS_THRESHOLD
        weight = constants.AFFINITY_CONSCIENTIOUSNESS_WEIGHT
        severity = constants.AFFINITY_CONSCIENTIOUSNESS_PENALTY_SEVERITY
        positive_label = "Lifestyle Sync (Order)"
        negative_label_base = "Lifestyle Clash"
    else:
        # Fallback to original calculation for unknown traits
        return (constants.AFFINITY_DYADIC_THRESHOLD - diff) * weight, f"Trait Compatibility ({trait_name})"
    
    # Calculate base effect
    if diff <= threshold:
        effect = (threshold - diff) * weight
        label = positive_label
    else:
        # Apply severity multiplier to penalties
        base_penalty = (threshold - diff) * weight
        effect = base_penalty * severity
        diff_from_threshold = diff - threshold
        
        # Determine severity label
        if diff_from_threshold <= constants.AFFINITY_MILD_INCOMPATIBILITY_THRESHOLD:
            label = f"Mild {negative_label_base}"
        elif diff_from_threshold >= constants.AFFINITY_SEVERE_INCOMPATIBILITY_THRESHOLD:
            label = f"Severe {negative_label_base}"
        else:
            label = negative_label_base
    
    return effect, label

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
    # Check if either agent is an infant (has temperament but no personality)
    if agent_a.temperament is not None or agent_b.temperament is not None:
        # Infants have neutral affinity - they don't form complex relationships yet
        return 0, []
    
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

    # --- 2. Dyadic Effects (Trait-Specific Compatibility) ---
    # Different traits have different tolerance levels and penalty severities
    # Based on research showing some trait mismatches are more damaging than others

    # Openness — governs core values and intellectual worldview.
    # Higher tolerance for differences, milder penalties.
    o_a = agent_a.get_personality_sum("Openness")
    o_b = agent_b.get_personality_sum("Openness")
    effect_o, label_o = _trait_specific_compatibility(o_a, o_b, "Openness")
    score += effect_o
    
    if abs(effect_o) > constants.AFFINITY_LABEL_THRESHOLD:
        breakdown.append((label_o, effect_o))

    # Conscientiousness — governs daily-life organisation and habits.
    # Lower tolerance for differences, severe penalties for routine incompatibility.
    c_a = agent_a.get_personality_sum("Conscientiousness")
    c_b = agent_b.get_personality_sum("Conscientiousness")
    effect_c, label_c = _trait_specific_compatibility(c_a, c_b, "Conscientiousness")
    score += effect_c
    
    if abs(effect_c) > constants.AFFINITY_LABEL_THRESHOLD:
        breakdown.append((label_c, effect_c))

    # Extraversion — governs social energy and preferred stimulation level.
    # Uses complementarity: optimal when traits are different but not extreme.
    e_a = agent_a.get_personality_sum("Extraversion")
    e_b = agent_b.get_personality_sum("Extraversion")
    effect_e = _extraversion_compatibility(e_a, e_b)
    score += effect_e

    # Determine appropriate label based on difference and effect
    diff = abs(e_a - e_b)
    if effect_e > constants.AFFINITY_LABEL_THRESHOLD:
        if constants.AFFINITY_EXTRAVERSION_COMP_MIN <= diff <= constants.AFFINITY_EXTRAVERSION_COMP_MAX:
            breakdown.append(("Social Complementarity", effect_e))
        else:
            breakdown.append(("Energy Match", effect_e))
    elif effect_e < -constants.AFFINITY_LABEL_THRESHOLD:
        if diff > constants.AFFINITY_EXTRAVERSION_COMP_MAX:
            breakdown.append(("Energy Clash", effect_e))
        else:
            breakdown.append(("Energy Mismatch", effect_e))

    # --- 3. Life Stage Compatibility ---
    # Based on developmental psychology and real social dynamics.
    life_stage_modifier, life_stage_label = _life_stage_compatibility(agent_a.age, agent_b.age)
    score += life_stage_modifier
    
    if abs(life_stage_modifier) > constants.AFFINITY_LABEL_THRESHOLD:
        breakdown.append((life_stage_label, life_stage_modifier))

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
    # Check if either agent is an infant (has temperament but no personality)
    if agent_a.temperament is not None or agent_b.temperament is not None:
        # Infants have neutral affinity - they don't form complex relationships yet
        return 0
    
    score = 0.0

    # Actor effects
    for agent in [agent_a, agent_b]:
        n_val = agent.get_personality_sum("Neuroticism")
        if n_val > constants.AFFINITY_ACTOR_THRESHOLD:
            score -= (n_val - constants.AFFINITY_ACTOR_THRESHOLD) * constants.AFFINITY_ACTOR_WEIGHT

        a_val = agent.get_personality_sum("Agreeableness")
        if a_val > constants.AFFINITY_ACTOR_THRESHOLD:
            score += (a_val - constants.AFFINITY_ACTOR_THRESHOLD) * constants.AFFINITY_ACTOR_WEIGHT

    # Dyadic effects with trait-specific compatibility
    effect_o, _ = _trait_specific_compatibility(
        agent_a.get_personality_sum("Openness"),
        agent_b.get_personality_sum("Openness"),
        "Openness"
    )
    score += effect_o

    effect_c, _ = _trait_specific_compatibility(
        agent_a.get_personality_sum("Conscientiousness"),
        agent_b.get_personality_sum("Conscientiousness"),
        "Conscientiousness"
    )
    score += effect_c

    # Extraversion uses complementarity logic
    score += _extraversion_compatibility(
        agent_a.get_personality_sum("Extraversion"),
        agent_b.get_personality_sum("Extraversion")
    )

    # Life stage compatibility
    life_stage_modifier, _ = _life_stage_compatibility(agent_a.age, agent_b.age)
    score += life_stage_modifier

    return max(constants.AFFINITY_SCORE_MIN,
               min(constants.AFFINITY_SCORE_MAX, int(round(score))))