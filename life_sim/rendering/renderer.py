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
        
        # UI State
        self.view_mode = "OVERVIEW" # Options: OVERVIEW, ATTRIBUTES
        
        self.logger.info("Renderer initialized (Pygame).")

    def toggle_view(self):
        """Switches between UI tabs."""
        if self.view_mode == "OVERVIEW":
            self.view_mode = "ATTRIBUTES"
        else:
            self.view_mode = "OVERVIEW"

    def render(self, sim_state):
        """
        Draws the current state based on view mode.
        """
        self.screen.fill(constants.COLOR_BG)
        
        # Draw Tab Indicator
        tab_text = f"Tab: {self.view_mode} (Press TAB to switch)"
        tab_surf = self.font.render(tab_text, True, (150, 150, 150))
        self.screen.blit(tab_surf, (50, 10))

        if self.view_mode == "OVERVIEW":
            self._render_overview(sim_state)
        elif self.view_mode == "ATTRIBUTES":
            self._render_attributes(sim_state)
            
        # Render Event Log (Always visible)
        visible_logs = sim_state.event_log[-constants.MAX_LOG_LINES:]
        log_y = constants.LOG_Y
        
        for line in visible_logs:
            log_surf = self.log_font.render(line, True, constants.COLOR_TEXT)
            self.screen.blit(log_surf, (constants.LOG_X, log_y))
            log_y += constants.LOG_LINE_HEIGHT

        pygame.display.flip()

    def _render_overview(self, sim_state):
        agent = sim_state.agent
        stats = [
            f"Age: {agent.age}",
            f"Health: {agent.health}",
            f"Happiness: {agent.happiness}",
            f"Smarts: {agent.smarts}",
            f"Looks: {agent.looks}",
            f"Money: ${agent.money}",
            f"Job: {agent.job['title'] if agent.job else 'Unemployed'}"
        ]
        
        y_offset = 50
        for line in stats:
            text_surf = self.font.render(line, True, constants.COLOR_TEXT)
            self.screen.blit(text_surf, (50, y_offset))
            y_offset += 40
            
        # Render Controls
        if sim_state.agent.is_alive:
            controls = [
                "SPACE: Age Up",
                "J: Find Job",
                "S: Study (Smarts)",
                "W: Overtime",
                "D: Doctor (-$100)"
            ]
            color = constants.COLOR_ACCENT
        else:
            controls = ["GAME OVER - Check Logs"]
            color = constants.COLOR_DEATH
            
        y_instr = constants.SCREEN_HEIGHT - 180
        for line in controls:
            instr_surf = self.font.render(line, True, color)
            self.screen.blit(instr_surf, (50, y_instr))
            y_instr += 30

    def _render_attributes(self, sim_state):
        agent = sim_state.agent
        
        # Header
        header = self.font.render("--- Mind & Body ---", True, constants.COLOR_ACCENT)
        self.screen.blit(header, (50, 50))
        
        attrs = [
            f"Strength: {agent.strength}",
            f"Athleticism: {agent.athleticism}",
            f"Discipline: {agent.discipline}",
            f"Karma: {agent.karma}"
        ]
        
        y_offset = 90
        for line in attrs:
            text_surf = self.font.render(line, True, constants.COLOR_TEXT)
            self.screen.blit(text_surf, (50, y_offset))
            y_offset += 40
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