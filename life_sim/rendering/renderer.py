# life_sim/rendering/renderer.py
"""
Renderer Module.
Handles Pygame initialization and drawing.
"""
import pygame
import logging
from .. import constants

class Renderer:
    """
    Handles drawing the SimState to the screen.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        pygame.init()
        self.screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        pygame.display.set_caption(constants.WINDOW_TITLE)
        self.font = pygame.font.SysFont("Arial", 24)
        self.log_font = pygame.font.SysFont("Consolas", constants.LOG_FONT_SIZE)
        
        self.logger.info("Renderer initialized (Pygame).")

    def render(self, sim_state):
        """
        Draws the current state.
        
        Args:
            sim_state (SimState): The current simulation state object.
        """
        self.screen.fill(constants.COLOR_BG)
        
        # Render Stats
        agent = sim_state.agent
        stats = [
            f"Age: {agent.age}",
            f"Health: {agent.health}",
            f"Happiness: {agent.happiness}",
            f"Smarts: {agent.smarts}",
            f"Looks: {agent.looks}"
        ]
        
        y_offset = 50
        for line in stats:
            text_surf = self.font.render(line, True, constants.COLOR_TEXT)
            self.screen.blit(text_surf, (50, y_offset))
            y_offset += 40
            
        # Render Instruction
        if sim_state.agent.is_alive:
            msg = "Press SPACE to Age Up"
            color = constants.COLOR_ACCENT
        else:
            msg = "GAME OVER - Check Logs"
            color = constants.COLOR_DEATH
            
        instr_surf = self.font.render(msg, True, color)
        self.screen.blit(instr_surf, (50, constants.SCREEN_HEIGHT - 50))
        
        # Render Event Log
        # Slice to show only the last N lines
        visible_logs = sim_state.event_log[-constants.MAX_LOG_LINES:]
        log_y = constants.LOG_Y
        
        for line in visible_logs:
            log_surf = self.log_font.render(line, True, constants.COLOR_TEXT)
            self.screen.blit(log_surf, (constants.LOG_X, log_y))
            log_y += constants.LOG_LINE_HEIGHT

        pygame.display.flip()

    def quit(self):
        pygame.quit()