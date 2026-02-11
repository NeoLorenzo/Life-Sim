# life_sim/simulation/state.py
"""Backward-compatible exports for simulation state types."""
from .agent import Agent
from .sim_state import SimState

__all__ = ["Agent", "SimState"]