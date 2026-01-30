# life_sim/simulation/affinity.py
"""
Affinity Calculation Module.
Pure functions for calculating psychometric compatibility.
"""
import logging
from .. import constants

logger = logging.getLogger(__name__)

def get_affinity_breakdown(agent_a, agent_b):
    """
    Returns the detailed breakdown of the affinity score.
    """
    breakdown = []
    score = 0.0
    
    # --- 1. Actor Effects (Individual Traits) ---
    # These affect how much an agent likes *anyone*.
    
    # Neuroticism (The "Grump" Factor)
    # High Neuroticism drags down scores.
    for agent in [agent_a, agent_b]:
        n_val = agent.get_personality_sum("Neuroticism")
        # Threshold 70: Above this, you start being difficult.
        if n_val > 70:
            pen = -(n_val - 70) * 0.5
            score += pen
            breakdown.append((f"{agent.first_name}'s Neuroticism", pen))

    # Agreeableness (The "Nice" Factor)
    # High Agreeableness boosts scores.
    for agent in [agent_a, agent_b]:
        a_val = agent.get_personality_sum("Agreeableness")
        # Threshold 70: Above this, you are generally pleasant.
        if a_val > 70:
            bon = (a_val - 70) * 0.5
            score += bon
            breakdown.append((f"{agent.first_name}'s Agreeableness", bon))

    # --- 2. Dyadic Effects (Similarity/Homophily) ---
    # We compare traits. Small delta = Bonus. Large delta = Penalty.
    # Formula: (Threshold - Delta) * Weight
    
    # Openness (Shared Interests vs. Value Clash)
    # Threshold 20: If difference is < 20, it's a bonus. If > 20, it's a clash.
    o_a = agent_a.get_personality_sum("Openness")
    o_b = agent_b.get_personality_sum("Openness")
    delta_o = abs(o_a - o_b)
    
    effect_o = (20 - delta_o) * 0.8 # Weight 0.8
    score += effect_o
    
    if effect_o > 5:
        breakdown.append(("Shared Interests (Openness)", effect_o))
    elif effect_o < -5:
        breakdown.append(("Value Clash (Openness)", effect_o))

    # Conscientiousness (Lifestyle Sync vs. Clash)
    c_a = agent_a.get_personality_sum("Conscientiousness")
    c_b = agent_b.get_personality_sum("Conscientiousness")
    delta_c = abs(c_a - c_b)
    
    effect_c = (20 - delta_c) * 0.8
    score += effect_c
    
    if effect_c > 5:
        breakdown.append(("Lifestyle Sync (Order)", effect_c))
    elif effect_c < -5:
        breakdown.append(("Lifestyle Clash (Order)", effect_c))

    # Extraversion (Energy Match)
    # Two high extraverts = Fun. Two introverts = Chill. Mixed = Friction?
    # Actually, Extraversion is often complementary, but for simplicity, let's reward similarity slightly.
    e_a = agent_a.get_personality_sum("Extraversion")
    e_b = agent_b.get_personality_sum("Extraversion")
    delta_e = abs(e_a - e_b)
    
    effect_e = (20 - delta_e) * 0.5 # Lower weight
    score += effect_e
    
    if effect_e > 5:
        breakdown.append(("Energy Match", effect_e))

    # Final Clamp
    final_score = max(-100, min(100, int(round(score))))
    return final_score, breakdown

def calculate_affinity(agent_a, agent_b):
    """
    Calculates the natural psychometric compatibility between two agents.
    """
    score, _ = get_affinity_breakdown(agent_a, agent_b)
    return score