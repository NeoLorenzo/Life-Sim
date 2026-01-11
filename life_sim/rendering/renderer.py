# life_sim/rendering/renderer.py
"""
Renderer Module.
Handles Pygame initialization and drawing.
"""
import pygame
import logging
from .. import constants
from .ui import Button, LogPanel

class Renderer:
    """
    Handles drawing the SimState to the screen using a 3-panel layout.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        pygame.init()
        self.screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        pygame.display.set_caption(constants.WINDOW_TITLE)
        
        # Fonts
        self.font_main = pygame.font.SysFont("Arial", constants.FONT_SIZE_MAIN)
        self.font_header = pygame.font.SysFont("Arial", constants.FONT_SIZE_HEADER, bold=True)
        self.font_log = pygame.font.SysFont("Consolas", constants.FONT_SIZE_LOG)
        
        # Layout Calculation
        self.rect_left = pygame.Rect(0, 0, constants.PANEL_LEFT_WIDTH, constants.SCREEN_HEIGHT)
        self.rect_right = pygame.Rect(constants.SCREEN_WIDTH - constants.PANEL_RIGHT_WIDTH, 0, constants.PANEL_RIGHT_WIDTH, constants.SCREEN_HEIGHT)
        
        center_w = constants.SCREEN_WIDTH - constants.PANEL_LEFT_WIDTH - constants.PANEL_RIGHT_WIDTH
        self.rect_center = pygame.Rect(constants.PANEL_LEFT_WIDTH, 0, center_w, constants.SCREEN_HEIGHT)
        
        # Initialize UI Elements
        self.log_panel = LogPanel(
            self.rect_center.x, 
            self.rect_center.y, 
            self.rect_center.width, 
            self.rect_center.height, 
            self.font_log
        )
        
        self.show_attributes = False
        
        self.buttons = {} # Dict[str, List[Button]]
        self.tabs = []    # List[Button] (Using Button class for tabs)
        self.active_tab = "Main"
        
        self._init_ui_structure()
        
        self.logger.info("Renderer initialized (Pygame) with 3-panel layout.")

    def _init_ui_structure(self):
        """Creates Tabs and Action Buttons."""
        # 1. Init Tabs
        tab_names = ["Main", "Social", "Assets"]
        tab_w = constants.PANEL_RIGHT_WIDTH // len(tab_names)
        tab_h = 30
        
        for i, name in enumerate(tab_names):
            x = self.rect_right.x + (i * tab_w)
            y = self.rect_right.y
            # Action ID for a tab is just "TAB_<NAME>"
            btn = Button(x, y, tab_w, tab_h, name, f"TAB_{name}", self.font_main)
            self.tabs.append(btn)

        # 2. Init Buttons per Tab
        btn_w = constants.PANEL_RIGHT_WIDTH - 40
        btn_h = 40
        start_x = self.rect_right.x + 20
        base_y = self.rect_right.y + 50 # Start below tabs
        gap = 10
        
        # Define Actions per Category
        # Format: (Text, ActionID)
        categories = {
            "Main": [
                ("Age Up (+1 Year)", "AGE_UP"),
                ("Find Job", "FIND_JOB"),
                ("Study (Smarts)", "STUDY"),
                ("Work Overtime", "WORK"),
                ("Visit Doctor ($100)", "DOCTOR"),
                ("Toggle Attributes", "TOGGLE_ATTR")
            ],
            "Social": [
                ("Call Parents", "SOCIAL_PARENTS"), # Placeholder
                ("Go Clubbing", "SOCIAL_CLUB")      # Placeholder
            ],
            "Assets": [
                ("Check Wallet", "ASSET_WALLET"),   # Placeholder
                ("Shopping", "ASSET_SHOP")          # Placeholder
            ]
        }
        
        for cat, actions in categories.items():
            self.buttons[cat] = []
            current_y = base_y
            for text, action_id in actions:
                btn = Button(start_x, current_y, btn_w, btn_h, text, action_id, self.font_main)
                self.buttons[cat].append(btn)
                current_y += btn_h + gap

    def handle_event(self, event, sim_state=None):
        """
        Processes input events.
        """
        # Pass to LogPanel (Scrolling + Clicking headers)
        # We need sim_state to toggle years
        if sim_state:
            self.log_panel.handle_event(event, sim_state)
        
        # 1. Check Tabs
        for tab in self.tabs:
            action = tab.handle_event(event)
            if action and action.startswith("TAB_"):
                self.active_tab = action.replace("TAB_", "")
                return None # Consumed locally
        
        # 2. Check Buttons in Active Tab
        if self.active_tab in self.buttons:
            for btn in self.buttons[self.active_tab]:
                action = btn.handle_event(event)
                if action:
                    return action
                    
        return None

    def render(self, sim_state):
        """Draws the full UI."""
        self.screen.fill(constants.COLOR_BG)
        
        # Update Log Panel Content
        # Now we pass the structured data generator
        self.log_panel.update_logs(sim_state.get_flat_log_for_rendering())
        
        # Draw Panels
        self._draw_left_panel(sim_state)
        
        if self.show_attributes:
            self._draw_attributes_modal(sim_state)
        else:
            self.log_panel.draw(self.screen)
            
        self._draw_right_panel(sim_state)
        
        pygame.display.flip()

    def toggle_attributes(self):
        self.show_attributes = not self.show_attributes

    def _draw_attributes_modal(self, sim_state):
        """Draws the detailed attributes overlay in the center panel."""
        # Draw Background
        pygame.draw.rect(self.screen, constants.COLOR_BG, self.rect_center)
        pygame.draw.rect(self.screen, constants.COLOR_BORDER, self.rect_center, 1)
        
        agent = sim_state.agent
        
        # Helper to draw a column
        def draw_column(title, lines, x, y):
            title_surf = self.font_header.render(title, True, constants.COLOR_ACCENT)
            self.screen.blit(title_surf, (x, y))
            y += 40
            for line in lines:
                text_surf = self.font_main.render(line, True, constants.COLOR_TEXT)
                self.screen.blit(text_surf, (x, y))
                y += 30

        # Layout Columns within Center Panel
        col_width = self.rect_center.width // 3
        start_x = self.rect_center.x + 20
        start_y = 50
        
        # Column 1: Identity
        bio_lines = [
            f"Gender: {agent.gender}",
            f"Origin: {agent.city}, {agent.country}",
            f"Height: {agent.height_cm} cm",
            f"Height Pot: {agent.genetic_height_potential} cm",
            f"Weight: {agent.weight_kg} kg",
            f"BMI: {agent.bmi}",
            f"Eyes: {agent.eye_color}",
            f"Hair: {agent.hair_color}",
            f"Skin: {agent.skin_tone}",
            f"Sexuality: {agent.sexuality}"
        ]
        draw_column("Identity", bio_lines, start_x, start_y)

        # Column 2: Physical
        phys_lines = [
            f"Max Health: {agent.max_health}",
            f"Strength: {agent.strength}",
            f"Athleticism: {agent.athleticism}",
            f"Endurance: {agent.endurance}",
            f"Body Fat: {agent.body_fat}%",
            f"Lean Mass: {agent.lean_mass} kg",
            f"Fertility: {agent.fertility}",
            f"Libido: {agent.libido}"
        ]
        draw_column("Physical", phys_lines, start_x + col_width, start_y)

        # Column 3: Personality
        pers_lines = [
            f"Discipline: {agent.discipline}",
            f"Willpower: {agent.willpower}",
            f"Generosity: {agent.generosity}",
            f"Religiousness: {agent.religiousness}",
            f"Craziness: {agent.craziness}",
            f"Karma: {agent.karma}",
            f"Luck: {agent.luck}"
        ]
        draw_column("Personality", pers_lines, start_x + (col_width * 2), start_y)
        
        # Skills (Bottom)
        if agent.skills:
            skill_lines = [f"{k}: {v}" for k, v in agent.skills.items()]
        else:
            skill_lines = ["No skills learned yet."]
        
        draw_column("Skills", skill_lines, start_x, start_y + 400)

    def _draw_left_panel(self, sim_state):
        pygame.draw.rect(self.screen, constants.COLOR_PANEL_BG, self.rect_left)
        pygame.draw.rect(self.screen, constants.COLOR_BORDER, self.rect_left, 1)
        
        agent = sim_state.agent
        
        # Helper for text
        x = self.rect_left.x + 20
        y = 30
        
        def draw_text(text, font=self.font_main, color=constants.COLOR_TEXT):
            surf = font.render(text, True, color)
            self.screen.blit(surf, (x, y))
            return surf.get_height() + 5

        y += draw_text(f"{agent.first_name} {agent.last_name}", self.font_header, constants.COLOR_ACCENT)
        y += 10
        y += draw_text(f"Age: {agent.age}")
        y += draw_text(f"Money: ${agent.money}", color=constants.COLOR_ACCENT)
        y += draw_text(f"Job: {agent.job['title'] if agent.job else 'Unemployed'}")
        y += 20
        y += draw_text("--- Vitals ---", color=constants.COLOR_TEXT_DIM)
        y += draw_text(f"Health: {agent.health}/{agent.max_health}")
        y += draw_text(f"Happiness: {agent.happiness}")
        y += draw_text(f"Smarts: {agent.smarts}")
        y += draw_text(f"Looks: {agent.looks}")
        y += 20
        y += draw_text("--- Physical ---", color=constants.COLOR_TEXT_DIM)
        y += draw_text(f"Energy: {agent.endurance}")
        y += draw_text(f"Fitness: {agent.athleticism}")

    def _draw_right_panel(self, sim_state):
        pygame.draw.rect(self.screen, constants.COLOR_PANEL_BG, self.rect_right)
        pygame.draw.rect(self.screen, constants.COLOR_BORDER, self.rect_right, 1)
        
        # Draw Tabs
        for tab in self.tabs:
            # Highlight active tab
            is_active = (tab.text == self.active_tab)
            tab.draw(self.screen, active_highlight=is_active)
        
        # Draw Buttons for Active Tab
        if self.active_tab in self.buttons:
            for btn in self.buttons[self.active_tab]:
                btn.draw(self.screen)

    def quit(self):
        pygame.quit()