# life_sim/simulation/affinity.py
"""
Affinity Calculation Module.
Pure functions for calculating psychometric compatibility.
"""
import logging
from .. import constants

logger = logging.getLogger(__name__)

def calculate_affinity(agent_a, agent_b):
    """
    Calculates the natural psychometric compatibility between two agents.
    Based on Actor-Partner Interdependence Model (APIM).
    Range: Approx -50 to +50.
    """
    score = 0.0
    
    # 1. Actor Effects (Individual Traits that affect ALL relationships)
    n_a = agent_a.get_personality_sum("Neuroticism")
    n_b = agent_b.get_personality_sum("Neuroticism")
    score -= (max(0, n_a - 60) * constants.AFFINITY_WEIGHT_ACTOR_N)
    score -= (max(0, n_b - 60) * constants.AFFINITY_WEIGHT_ACTOR_N)
    
    a_a = agent_a.get_personality_sum("Agreeableness")
    a_b = agent_b.get_personality_sum("Agreeableness")
    score += (max(0, a_a - 60) * constants.AFFINITY_WEIGHT_ACTOR_A)
    score += (max(0, a_b - 60) * constants.AFFINITY_WEIGHT_ACTOR_A)
    
    # 2. Dyadic Effects (Similarity/Clash between the pair)
    o_a = agent_a.get_personality_sum("Openness")
    o_b = agent_b.get_personality_sum("Openness")
    delta_o = abs(o_a - o_b)
    score -= (delta_o * constants.AFFINITY_WEIGHT_DYADIC_O)
    
    c_a = agent_a.get_personality_sum("Conscientiousness")
    c_b = agent_b.get_personality_sum("Conscientiousness")
    delta_c = abs(c_a - c_b)
    score -= (delta_c * constants.AFFINITY_WEIGHT_DYADIC_C)
    
    return max(-50, min(50, int(score)))