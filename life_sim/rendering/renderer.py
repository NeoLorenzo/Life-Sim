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
            
        pygame.display.flip()

    def _render_overview(self, sim_state):
        # Render Event Log (Only in Overview)
        visible_logs = sim_state.event_log[-constants.MAX_LOG_LINES:]
        log_y = constants.LOG_Y
        
        for line in visible_logs:
            log_surf = self.log_font.render(line, True, constants.COLOR_TEXT)
            self.screen.blit(log_surf, (constants.LOG_X, log_y))
            log_y += constants.LOG_LINE_HEIGHT

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
        
        # Helper to draw a column of text
        def draw_column(title, lines, x, y):
            title_surf = self.font.render(title, True, constants.COLOR_ACCENT)
            self.screen.blit(title_surf, (x, y))
            y += 30
            for line in lines:
                text_surf = self.font.render(line, True, constants.COLOR_TEXT)
                self.screen.blit(text_surf, (x, y))
                y += 25

        # Column 1: Status & Identity
        bio_lines = [
            f"Name: {agent.first_name} {agent.last_name}",
            f"Age: {agent.age}",
            f"Money: ${agent.money}",
            f"Job: {agent.job['title'] if agent.job else 'Unemployed'}",
            "---",
            f"Gender: {agent.gender}",
            f"Origin: {agent.city}, {agent.country}",
            f"Height: {agent.height_cm} cm",
            f"Weight: {agent.weight_kg} kg",
            f"Eyes: {agent.eye_color}",
            f"Hair: {agent.hair_color}",
            f"Skin: {agent.skin_tone}",
            f"Sexuality: {agent.sexuality}"
        ]
        draw_column("Status & Identity", bio_lines, 50, 50)

        # Column 2: Physical Stats
        phys_lines = [
            f"Health: {agent.health}",
            f"Strength: {agent.strength}",
            f"Athleticism: {agent.athleticism}",
            f"Endurance: {agent.endurance}",
            f"Body Fat: {agent.body_fat}%",
            f"Lean Mass: {agent.lean_mass} kg",
            f"Fertility: {agent.fertility}",
            f"Libido: {agent.libido}"
        ]
        draw_column("Physical", phys_lines, 300, 50)

        # Column 3: Personality & Hidden
        pers_lines = [
            f"Smarts: {agent.smarts}",
            f"Looks: {agent.looks}",
            f"Discipline: {agent.discipline}",
            f"Willpower: {agent.willpower}",
            f"Generosity: {agent.generosity}",
            f"Religiousness: {agent.religiousness}",
            f"Craziness: {agent.craziness}",
            f"Karma: {agent.karma}",
            f"Luck: {agent.luck}"
        ]
        draw_column("Personality", pers_lines, 550, 50)
        
        # Skills Section (Bottom)
        if agent.skills:
            skill_lines = [f"{k}: {v}" for k, v in agent.skills.items()]
        else:
            skill_lines = ["No skills learned yet."]
        
        # Moved down to avoid overlap with Identity column
        draw_column("Skills", skill_lines, 50, 450)

    def quit(self):
        pygame.quit()