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
        
        self.viewing_agent = None # None, or an Agent object
        
        self.buttons = {} # Dict[str, List[Button]]
        self.tabs = []    # List[Button] (Using Button class for tabs)
        self.active_tab = "Main"
        
        # Visibility Logic (Action ID -> Lambda accepting player)
        self.visibility_rules = {
            "FIND_JOB": lambda player: player.age >= 16,
            "WORK": lambda player: player.job is not None
        }
        
        # Storage for interactive rects in the modal (recalculated every frame)
        self.modal_click_zones = [] 
        
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
                ("Age Up (+1 Month)", "AGE_UP"),
                ("Study (Smarts)", "STUDY"),
                ("Visit Doctor ($100)", "DOCTOR"),
                ("Find Job", "FIND_JOB"),
                ("Work Overtime", "WORK"),
                ("View Attributes", "TOGGLE_ATTR")
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
        # 0. Check Modal Interaction (Priority)
        if self.viewing_agent and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check Close Button
            close_rect = pygame.Rect(self.rect_center.right - 30, self.rect_center.y + 10, 20, 20)
            if close_rect.collidepoint(event.pos):
                self.viewing_agent = None
                return None
            
            # Check Attribute Cards (Pinning)
            # Only allow pinning if viewing the Player
            if self.viewing_agent == sim_state.player:
                for rect, attr_name in self.modal_click_zones:
                    if rect.collidepoint(event.pos):
                        if attr_name in sim_state.player.pinned_attributes:
                            sim_state.player.pinned_attributes.remove(attr_name)
                        else:
                            sim_state.player.pinned_attributes.append(attr_name)
                        return None # Consumed

        # Pass to LogPanel (Scrolling + Clicking headers)
        if sim_state and not self.viewing_agent:
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
                # Check Visibility Rule
                if sim_state:
                    rule = self.visibility_rules.get(btn.action_id)
                    if rule and not rule(sim_state.player):
                        continue

                action = btn.handle_event(event)
                if action:
                    return action

        # 3. Check Dynamic Relationship Buttons (Social Tab)
        if self.active_tab == "Social" and sim_state:
            # Re-calculate layout to find clicks (Must match _draw_relationship_list)
            current_y = self.rect_right.y + 60
            gap = 12
            
            # Calculate where the static buttons ended
            for btn in self.buttons["Social"]:
                # Only count visible buttons
                rule = self.visibility_rules.get(btn.action_id)
                if not rule or rule(sim_state.player):
                    current_y += btn.rect.height + gap
            
            start_y = current_y + 10
            x = self.rect_right.x + 20
            w = self.rect_right.width - 40
            card_h = 90 
            
            # Offset for the "Relationships" header text (Matches _draw_relationship_list)
            start_y += 30

            for uid, rel in sim_state.player.relationships.items():
                # Button Geometry (Must match _draw_relationship_list exactly)
                btn_y = start_y + 50
                btn_w = (w - 10) // 2
                btn_h = 30
                
                # Attributes Button
                # Draw used: x + 5
                rect_attr = pygame.Rect(x + 5, btn_y, btn_w, btn_h)
                
                # Interact Button
                # Draw used: x + 5 + btn_w + 5
                rect_int = pygame.Rect(x + 5 + btn_w + 5, btn_y, btn_w, btn_h)
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if rect_attr.collidepoint(event.pos):
                        # Ensure the NPC exists before trying to view
                        if uid in sim_state.npcs:
                            self.viewing_agent = sim_state.npcs[uid]
                        return None
                    elif rect_int.collidepoint(event.pos):
                        return f"INTERACT_{uid}"
                
                start_y += card_h + 10

        return None

    def render(self, sim_state):
        """Draws the full UI."""
        self.screen.fill(constants.COLOR_BG)
        
        # Update Log Panel Content
        self.log_panel.update_logs(sim_state.get_flat_log_for_rendering())
        
        # Draw Panels
        self._draw_left_panel(sim_state)
        
        if self.viewing_agent:
            self._draw_attributes_modal(sim_state)
        else:
            self.log_panel.draw(self.screen)
            
        self._draw_right_panel(sim_state)
        
        pygame.display.flip()

    def toggle_attributes(self, target=None):
        if target:
            self.viewing_agent = target
        elif self.viewing_agent:
            self.viewing_agent = None
        else:
            # Default to player if opening from main menu
            # We need access to player, but this method is usually called from main.py
            # We'll handle the "Default" logic in main.py or pass it here.
            # For now, if target is None and we are closed, we assume Player is handled by caller
            pass

    def _draw_attributes_modal(self, sim_state):
        """Draws the detailed attributes overlay in the center panel."""
        # Reset click zones
        self.modal_click_zones = []
        
        # Draw Background
        pygame.draw.rect(self.screen, constants.COLOR_BG, self.rect_center)
        pygame.draw.rect(self.screen, constants.COLOR_BORDER, self.rect_center, 1)
        
        # Close Button
        close_rect = pygame.Rect(self.rect_center.right - 30, self.rect_center.y + 10, 20, 20)
        pygame.draw.rect(self.screen, constants.COLOR_DEATH, close_rect, border_radius=3)
        pygame.draw.line(self.screen, constants.COLOR_TEXT, close_rect.topleft, close_rect.bottomright, 2)
        pygame.draw.line(self.screen, constants.COLOR_TEXT, close_rect.bottomleft, close_rect.topright, 2)

        agent = self.viewing_agent
        is_player = (agent == sim_state.player)
        
        # --- Header ---
        header_text = f"{agent.first_name}'s Attributes"
        if is_player: header_text += " (Click to Pin)"
        header_surf = self.font_header.render(header_text, True, constants.COLOR_ACCENT)
        self.screen.blit(header_surf, (self.rect_center.x + 20, self.rect_center.y + 15))
        
        # --- Static Bio Text (Top Section) ---
        bio_x = self.rect_center.x + 20
        bio_y = self.rect_center.y + 50
        
        # Line 1: Identity
        line1 = f"{agent.gender}, {agent.age} years old. Born in {agent.city}, {agent.country}."
        self.screen.blit(self.font_main.render(line1, True, constants.COLOR_TEXT), (bio_x, bio_y))
        
        # Line 2: Appearance
        line2 = f"{agent.sexuality}. {agent.eye_color} Eyes, {agent.hair_color} Hair, {agent.skin_tone} Skin."
        self.screen.blit(self.font_main.render(line2, True, constants.COLOR_TEXT), (bio_x, bio_y + 25))
        
        # Line 3: Body
        line3 = f"Height: {agent.height_cm}cm | Weight: {agent.weight_kg}kg | BMI: {agent.bmi}"
        self.screen.blit(self.font_main.render(line3, True, constants.COLOR_TEXT), (bio_x, bio_y + 50))

        # --- Columnar Layout Configuration ---
        start_x = self.rect_center.x + 20
        start_y = bio_y + 90 
        
        # 4 Columns
        col_count = 4
        col_w = (self.rect_center.width - 40) // col_count
        card_w = col_w - 10
        card_h = 40 # Compact height
        gap_y = 8
        
        # Track Y position for each column
        col_y_offsets = [start_y] * col_count

        # Helper to draw a card at specific coordinates
        def draw_card_at(x, y, name, value, max_val=100, is_header=False):
            rect = pygame.Rect(x, y, card_w, card_h)
            
            # Background
            bg_col = constants.COLOR_PANEL_BG
            if is_player and name in agent.pinned_attributes:
                bg_col = (60, 60, 70)
            
            if is_header:
                pygame.draw.rect(self.screen, (30, 30, 30), rect, border_radius=5)
                pygame.draw.rect(self.screen, constants.COLOR_ACCENT, rect, 1, border_radius=5)
            else:
                pygame.draw.rect(self.screen, bg_col, rect, border_radius=5)
                pygame.draw.rect(self.screen, constants.COLOR_BORDER, rect, 1, border_radius=5)
            
            # Text
            name_surf = self.font_main.render(name, True, constants.COLOR_TEXT)
            val_surf = self.font_header.render(str(value), True, constants.COLOR_ACCENT)
            
            self.screen.blit(name_surf, (rect.x + 10, rect.y + 5))
            self.screen.blit(val_surf, (rect.right - val_surf.get_width() - 10, rect.y + 5))
            
            # Progress Bar
            bar_bg = pygame.Rect(rect.x + 10, rect.bottom - 8, rect.width - 20, 4)
            pygame.draw.rect(self.screen, (10, 10, 10), bar_bg)
            
            pct = max(0, min(1, value / max_val))
            bar_fill = pygame.Rect(rect.x + 10, rect.bottom - 8, (rect.width - 20) * pct, 4)
            
            # Color Logic
            bar_col = constants.COLOR_ACCENT
            # Check if this is a neuroticism-related stat
            is_neuro = (name == "Neuroticism" or name in agent.personality.get("Neuroticism", {}))
            
            if is_neuro:
                if value > (max_val * 0.75): bar_col = constants.COLOR_LOG_NEGATIVE
                elif value < (max_val * 0.25): bar_col = constants.COLOR_LOG_POSITIVE
            else:
                if value < (max_val * 0.25): bar_col = constants.COLOR_LOG_NEGATIVE
                elif value > (max_val * 0.75): bar_col = constants.COLOR_LOG_POSITIVE
                
            pygame.draw.rect(self.screen, bar_col, bar_fill)
            
            # Pin Icon
            if is_player and name in agent.pinned_attributes:
                pygame.draw.circle(self.screen, constants.COLOR_TEXT, (rect.right - 8, rect.top + 8), 3)

            # Register Click Zone
            self.modal_click_zones.append((rect, name))

        # Helper to draw a group in a specific column
        def draw_group(col_idx, title, attrs, is_personality=False):
            x = start_x + (col_idx * col_w)
            y = col_y_offsets[col_idx]
            
            # Draw Header
            if title:
                if is_personality:
                    # Personality Headers are clickable cards (The Main Trait)
                    val = agent.get_personality_sum(title)
                    draw_card_at(x, y, title, val, 120, is_header=True)
                    y += card_h + gap_y
                else:
                    # Standard Text Header
                    head_surf = self.font_header.render(title, True, constants.COLOR_TEXT_DIM)
                    self.screen.blit(head_surf, (x, y))
                    y += 30
            
            # Draw Attributes
            for attr in attrs:
                val = agent.get_attr_value(attr)
                max_v = 20 if is_personality else 100
                if attr == "Health": max_v = agent.max_health
                
                draw_card_at(x, y, attr, val, max_v)
                y += card_h + gap_y
            
            y += 15 # Gap between groups
            col_y_offsets[col_idx] = y

        # --- Execute Layout ---
        
        # Column 1: Vitals, Physical, Hidden
        draw_group(0, "Vitals", ["Health", "Happiness", "Smarts", "Looks"])
        draw_group(0, "Physical", ["Energy", "Fitness", "Strength", "Fertility", "Genetic Fertility", "Libido", "Genetic Libido"])
        draw_group(0, "Hidden", ["Karma", "Luck", "Religiousness"])
        
        # Column 2: Openness & Conscientiousness
        draw_group(1, "Openness", list(agent.personality["Openness"].keys()), is_personality=True)
        draw_group(1, "Conscientiousness", list(agent.personality["Conscientiousness"].keys()), is_personality=True)
        
        # Column 3: Extraversion & Agreeableness
        draw_group(2, "Extraversion", list(agent.personality["Extraversion"].keys()), is_personality=True)
        draw_group(2, "Agreeableness", list(agent.personality["Agreeableness"].keys()), is_personality=True)
        
        # Column 4: Neuroticism
        draw_group(3, "Neuroticism", list(agent.personality["Neuroticism"].keys()), is_personality=True)

    def _draw_left_panel(self, sim_state):
        pygame.draw.rect(self.screen, constants.COLOR_PANEL_BG, self.rect_left)
        pygame.draw.rect(self.screen, constants.COLOR_BORDER, self.rect_left, 1)
        
        player = sim_state.player
        
        # Helper for text
        x = self.rect_left.x + 20
        y = 30
        
        def draw_text(text, font=self.font_main, color=constants.COLOR_TEXT):
            surf = font.render(text, True, color)
            self.screen.blit(surf, (x, y))
            return surf.get_height() + 5

        y += draw_text(f"{player.first_name} {player.last_name}", self.font_header, constants.COLOR_ACCENT)
        y += 10
        
        # Date Display
        month_name = constants.MONTHS[sim_state.month_index]
        y += draw_text(f"{month_name} {sim_state.year}", color=constants.COLOR_TEXT_DIM)
        
        # Age Display
        y += draw_text(f"Age: {player.age} ({player.age_months % 12} mos)")
        
        y += draw_text(f"Money: ${player.money}", color=constants.COLOR_ACCENT)
        y += draw_text(f"Job: {player.job['title'] if player.job else 'Unemployed'}")
        y += 20
        
        # Dynamic Pinned Attributes
        y += draw_text("--- Attributes ---", color=constants.COLOR_TEXT_DIM)
        
        for attr in player.pinned_attributes:
            val = player.get_attr_value(attr)
            
            # Special formatting for Health to show Max
            if attr == "Health":
                txt = f"{attr}: {val}/{player.max_health}"
            else:
                txt = f"{attr}: {val}"
                
            y += draw_text(txt)

    def _draw_right_panel(self, sim_state):
        pygame.draw.rect(self.screen, constants.COLOR_PANEL_BG, self.rect_right)
        pygame.draw.rect(self.screen, constants.COLOR_BORDER, self.rect_right, 1)
        
        # Draw Tabs
        for tab in self.tabs:
            # Highlight active tab
            is_active = (tab.text == self.active_tab)
            tab.draw(self.screen, active_highlight=is_active)
        
        # Draw Buttons for Active Tab with Dynamic Layout
        current_y = self.rect_right.y + 60
        
        if self.active_tab in self.buttons:
            gap = 12
            
            for btn in self.buttons[self.active_tab]:
                # Check Visibility
                rule = self.visibility_rules.get(btn.action_id)
                if rule and not rule(sim_state.player):
                    continue
                
                # Update Position (Dynamic Layout)
                btn.rect.y = current_y
                btn.draw(self.screen)
                
                # Advance Y
                current_y += btn.rect.height + gap

        # Draw Relationship List (Only on Social Tab)
        if self.active_tab == "Social":
            self._draw_relationship_list(sim_state, current_y + 10)

    def _draw_relationship_list(self, sim_state, start_y):
        """Draws the list of known people in the right panel."""
        x = self.rect_right.x + 20
        y = start_y
        w = self.rect_right.width - 40
        h = 90 # Increased height for buttons
        
        # Header
        header_surf = self.font_header.render("Relationships", True, constants.COLOR_ACCENT)
        self.screen.blit(header_surf, (x, y))
        y += 30
        
        for uid, rel in sim_state.player.relationships.items():
            # Background Box
            rect = pygame.Rect(x, y, w, h)
            pygame.draw.rect(self.screen, constants.COLOR_BTN_IDLE, rect, border_radius=4)
            pygame.draw.rect(self.screen, constants.COLOR_BORDER, rect, 1, border_radius=4)
            
            # Name & Status
            name_color = constants.COLOR_TEXT
            status_text = rel['type']
            
            if not rel['is_alive']:
                name_color = constants.COLOR_TEXT_DIM
                status_text += " (Deceased)"
            
            name_surf = self.font_main.render(rel['name'], True, name_color)
            type_surf = self.font_log.render(status_text, True, constants.COLOR_TEXT_DIM)
            
            self.screen.blit(name_surf, (x + 10, y + 5))
            self.screen.blit(type_surf, (x + 10, y + 25))
            
            # Relationship Bar
            if rel['is_alive']:
                bar_bg = pygame.Rect(x + w - 110, y + 10, 100, 10)
                pygame.draw.rect(self.screen, (30, 30, 30), bar_bg)
                
                pct = rel['value'] / 100.0
                bar_fill = pygame.Rect(x + w - 110, y + 10, 100 * pct, 10)
                
                # Color based on value
                if rel['value'] > 80: col = constants.COLOR_LOG_POSITIVE
                elif rel['value'] < 30: col = constants.COLOR_LOG_NEGATIVE
                else: col = constants.COLOR_ACCENT
                
                pygame.draw.rect(self.screen, col, bar_fill)
                
                # Buttons
                btn_y = y + 50
                btn_w = (w - 10) // 2
                btn_h = 30
                
                # Draw "Attributes" Button
                attr_rect = pygame.Rect(x + 5, btn_y, btn_w, btn_h)
                pygame.draw.rect(self.screen, constants.COLOR_PANEL_BG, attr_rect, border_radius=4)
                pygame.draw.rect(self.screen, constants.COLOR_BORDER, attr_rect, 1, border_radius=4)
                attr_txt = self.font_log.render("Attributes", True, constants.COLOR_TEXT)
                attr_txt_rect = attr_txt.get_rect(center=attr_rect.center)
                self.screen.blit(attr_txt, attr_txt_rect)

                # Draw "Interact" Button
                int_rect = pygame.Rect(x + 5 + btn_w + 5, btn_y, btn_w, btn_h)
                pygame.draw.rect(self.screen, constants.COLOR_PANEL_BG, int_rect, border_radius=4)
                pygame.draw.rect(self.screen, constants.COLOR_BORDER, int_rect, 1, border_radius=4)
                int_txt = self.font_log.render("Interact", True, constants.COLOR_TEXT)
                int_txt_rect = int_txt.get_rect(center=int_rect.center)
                self.screen.blit(int_txt, int_txt_rect)
            
            y += h + 10

    def quit(self):
        pygame.quit()