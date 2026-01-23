# main.py
"""
Life-Sim Entry Point.
Wires together Config, Logging, Simulation, and Rendering.
"""
import json
import logging
import sys
import pygame
import random
import numpy as np

# Import local modules
# Note: Assumes 'life_sim' package structure. 
# If running from root, ensure __init__.py exists in life_sim/
from life_sim import constants, logging_setup
from life_sim.simulation.state import SimState
from life_sim.simulation import logic
from life_sim.rendering.renderer import Renderer

def load_config():
    try:
        with open(constants.CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"CRITICAL: {constants.CONFIG_FILE} not found.")
        sys.exit(1)

def main():
    # 1. Load Config
    config = load_config()
    
    # 2. Setup Logging (Rule 2)
    logging_setup.setup_logging(config)
    logger = logging.getLogger("main")
    
    # 3. Initialize RNG (Rule 12)
    seed = config.get("seed", 0)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Life-Sim started. Seed: {seed}")
    
    # 4. Initialize Systems
    renderer = None
    try:
        sim_state = SimState(config)
        renderer = Renderer()
        clock = pygame.time.Clock()
        
        running = True
        
        # 5. Main Loop
        while running:
            # Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Pass event to UI
                action_id = renderer.handle_event(event, sim_state)
                
                if action_id:
                    logger.info(f"Action triggered: {action_id}")
                    if action_id == "AGE_UP":
                        logic.process_turn(sim_state)
                    elif action_id == "FIND_JOB":
                        logic.find_job(sim_state)
                    elif action_id == "WORK":
                        logic.work(sim_state)
                    elif action_id == "DOCTOR":
                        logic.visit_doctor(sim_state)
                    elif action_id == "TOGGLE_ATTR":
                        # Default to player when clicking the main menu button
                        renderer.toggle_attributes(target=sim_state.player)
                    else:
                        # Handle placeholders
                        sim_state.add_log(f"Feature {action_id} coming soon!", constants.COLOR_TEXT_DIM)

            # Render
            renderer.render(sim_state)
            
            # Cap FPS
            clock.tick(constants.FPS)
            
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        raise
    finally:
        if renderer:
            renderer.quit()
        logger.info("Simulation ended cleanly.")

if __name__ == "__main__":
    main()