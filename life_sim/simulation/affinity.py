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
    
    # 1. Actor Effects (Individual Traits that affect ALL relationships)
    # Neuroticism (Penalty)
    n_a = agent_a.get_personality_sum("Neuroticism")
    n_b = agent_b.get_personality_sum("Neuroticism")
    
    pen_n_a = -(max(0, n_a - 60) * constants.AFFINITY_WEIGHT_ACTOR_N)
    if pen_n_a != 0:
        breakdown.append((f"{agent_a.first_name}'s Neuroticism", pen_n_a))
        score += pen_n_a
        
    pen_n_b = -(max(0, n_b - 60) * constants.AFFINITY_WEIGHT_ACTOR_N)
    if pen_n_b != 0:
        breakdown.append((f"{agent_b.first_name}'s Neuroticism", pen_n_b))
        score += pen_n_b

    # Agreeableness (Bonus)
    a_a = agent_a.get_personality_sum("Agreeableness")
    a_b = agent_b.get_personality_sum("Agreeableness")
    
    bon_a_a = (max(0, a_a - 60) * constants.AFFINITY_WEIGHT_ACTOR_A)
    if bon_a_a != 0:
        breakdown.append((f"{agent_a.first_name}'s Agreeableness", bon_a_a))
        score += bon_a_a
        
    bon_a_b = (max(0, a_b - 60) * constants.AFFINITY_WEIGHT_ACTOR_A)
    if bon_a_b != 0:
        breakdown.append((f"{agent_b.first_name}'s Agreeableness", bon_a_b))
        score += bon_a_b
    
    # 2. Dyadic Effects (Similarity/Clash between the pair)
    # Openness (Value Clash)
    o_a = agent_a.get_personality_sum("Openness")
    o_b = agent_b.get_personality_sum("Openness")
    delta_o = abs(o_a - o_b)
    pen_o = -(delta_o * constants.AFFINITY_WEIGHT_DYADIC_O)
    # Always show if non-zero
    if abs(pen_o) > 0.1:
        breakdown.append(("Value Clash (Openness)", pen_o))
    score += pen_o
    
    # Conscientiousness (Lifestyle Clash)
    c_a = agent_a.get_personality_sum("Conscientiousness")
    c_b = agent_b.get_personality_sum("Conscientiousness")
    delta_c = abs(c_a - c_b)
    pen_c = -(delta_c * constants.AFFINITY_WEIGHT_DYADIC_C)
    # Always show if non-zero
    if abs(pen_c) > 0.1:
        breakdown.append(("Lifestyle Clash (Order)", pen_c))
    score += pen_c
    
    # Use round() for better intuition than int() truncation
    final_score = max(-50, min(50, int(round(score))))
    return final_score, breakdown

def calculate_affinity(agent_a, agent_b):
    """
    Calculates the natural psychometric compatibility between two agents.
    Based on Actor-Partner Interdependence Model (APIM).
    Range: Approx -50 to +50.
    """
    score, _ = get_affinity_breakdown(agent_a, agent_b)
    return score