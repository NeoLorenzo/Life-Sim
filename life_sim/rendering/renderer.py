# life_sim/rendering/renderer.py
"""
Renderer Module.
Handles Pygame initialization and drawing.
"""
import pygame
import logging
import os
from .. import constants
from .ui import Button, LogPanel, APBar
from .family_tree import FamilyTreeLayout
from .social_graph import SocialGraphLayout

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
        
        # Family Tree State
        self.viewing_family_tree_agent = None 
        self.ft_layout = FamilyTreeLayout()
        self.ft_built_for_uid = None # Cache key to avoid rebuilding every frame
        
        # Social Graph State
        self.viewing_social_graph = False
        self.social_graph = SocialGraphLayout()
        self.ft_offset_x = 0
        self.ft_offset_y = 0
        self.ft_is_dragging = False
        self.ft_last_mouse_pos = (0, 0)
        
        self.ft_buttons = [] # List of (Rect, Agent) for the current frame
        
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
        
        # Load Assets
        self.icon_ft = None
        try:
            path = os.path.join(constants.ASSETS_DIR, constants.ICON_FT_FILENAME)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                # Scale to fit inside a small button (e.g., 16x16 or 20x20)
                self.icon_ft = pygame.transform.smoothscale(img, (20, 20))
            else:
                self.logger.warning(f"Icon not found at {path}. Using text fallback.")
        except Exception as e:
            self.logger.error(f"Failed to load icon: {e}")

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
                ("Visit Doctor ($100)", "DOCTOR"),
                ("Find Job", "FIND_JOB"),
                ("Work Overtime", "WORK"),
                ("View Attributes", "TOGGLE_ATTR")
            ],
            "Social": [
                ("Social Map", "SOCIAL_MAP"),       # New Feature
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
        # 0. Check Social Graph Modal (Top Priority)
        if self.viewing_social_graph:
            # 1. Toggle Buttons
            # Button A: Show All/Known
            btn_a_rect = pygame.Rect(self.rect_center.x + 10, self.rect_center.y + 45, 120, 25)
            # Button B: Network On/Off
            btn_b_rect = pygame.Rect(self.rect_center.x + 140, self.rect_center.y + 45, 120, 25)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_a_rect.collidepoint(event.pos):
                    self.social_graph.show_all = not self.social_graph.show_all
                    self.social_graph.build(sim_state, self.rect_center)
                    return None
                elif btn_b_rect.collidepoint(event.pos):
                    self.social_graph.show_network = not self.social_graph.show_network
                    self.social_graph.build(sim_state, self.rect_center)
                    return None

            # 2. Close Button
            close_rect = pygame.Rect(self.rect_center.right - 30, self.rect_center.y + 10, 20, 20)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if close_rect.collidepoint(event.pos):
                    self.viewing_social_graph = False
                    return None
            
            # 3. Graph Interaction (Pan/Drag/Hover)
            # Calculate relative mouse pos
            mx, my = pygame.mouse.get_pos()
            rel_x = mx # We pass absolute X/Y because graph handles pan offset internally? 
            # Actually, graph expects relative to panel for logic? 
            # Let's pass absolute mouse pos, but graph needs to know panel offset?
            # In Stage 4 code, I wrote: "rel_mouse_pos: (x, y) relative to the center panel top-left."
            # So we must subtract panel X/Y.
            
            rel_mx = mx - self.rect_center.x
            rel_my = my - self.rect_center.y
            
            # Wait, the graph draws using absolute coordinates in Stage 1/2/3?
            # In Stage 2: "self.center = np.array([bounds.centerx, bounds.centery])"
            # So the graph uses SCREEN coordinates.
            # So we should pass SCREEN coordinates to handle_event.
            
            if self.rect_center.collidepoint((mx, my)):
                self.social_graph.handle_event(event, (mx, my))
                return None # Consume event

        # 0a. Check Family Tree Modal (Top Priority)
        if self.viewing_family_tree_agent:
            # Close Button Logic
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                close_rect = pygame.Rect(self.rect_center.right - 30, self.rect_center.y + 10, 20, 20)
                if close_rect.collidepoint(event.pos):
                    self.viewing_family_tree_agent = None
                    self.ft_built_for_uid = None # Reset cache
                    return None

            # Interaction Logic (Pan & Click)
            if self.rect_center.collidepoint(pygame.mouse.get_pos()):
                # Calculate relative mouse position in the "Tree World"
                # Center of panel is (0,0) in Tree World + Offset
                center_x = self.rect_center.centerx
                center_y = self.rect_center.centery
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                # Rel X = (Mouse - ScreenCenter) - Offset
                rel_x = (mouse_x - center_x) - self.ft_offset_x
                rel_y = (mouse_y - center_y) - self.ft_offset_y

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left Click
                        clicked_agent = self.ft_layout.get_node_at(rel_x, rel_y)
                        if clicked_agent:
                            # Select new focus
                            self.viewing_family_tree_agent = clicked_agent
                            # Don't reset offset, keeps context
                        else:
                            # Start Drag
                            self.ft_is_dragging = True
                            self.ft_last_mouse_pos = (mouse_x, mouse_y)
                    elif event.button == 3: # Right Click
                        clicked_agent = self.ft_layout.get_node_at(rel_x, rel_y)
                        if clicked_agent:
                            # Open Attributes
                            self.viewing_agent = clicked_agent
                            # Close FT? Or keep it open? 
                            # For now, let's close FT to show attributes, 
                            # or we could overlay. Let's close FT for simplicity.
                            self.viewing_family_tree_agent = None
                            self.ft_built_for_uid = None

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.ft_is_dragging = False

                elif event.type == pygame.MOUSEMOTION:
                    if self.ft_is_dragging:
                        dx = mouse_x - self.ft_last_mouse_pos[0]
                        dy = mouse_y - self.ft_last_mouse_pos[1]
                        self.ft_offset_x += dx
                        self.ft_offset_y += dy
                        self.ft_last_mouse_pos = (mouse_x, mouse_y)
                
                # Consume all events inside the modal rect
                if self.rect_center.collidepoint(pygame.mouse.get_pos()):
                    return None

        # 0b. Check Attributes Modal Interaction
        if self.viewing_agent and not self.viewing_family_tree_agent and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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

        # 0c. Check Family Tree Buttons (Global)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, agent in self.ft_buttons:
                if rect.collidepoint(event.pos):
                    self.viewing_family_tree_agent = agent
                    return None

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
                    if action == "SOCIAL_MAP":
                        self.viewing_social_graph = True
                        self.social_graph.build(sim_state, self.rect_center)
                        return None
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
        self.ft_buttons = [] # Reset interactive buttons for this frame
        
        # Physics Step
        if self.viewing_social_graph:
            self.social_graph.update_physics()
        
        self.screen.fill(constants.COLOR_BG)
        
        # Update Log Panel Content
        self.log_panel.update_logs(sim_state.get_flat_log_for_rendering())
        
        # Draw Panels
        self._draw_left_panel(sim_state)
        
        # Center Panel Logic
        if self.viewing_social_graph:
            self._draw_social_graph_modal(sim_state)
        elif self.viewing_family_tree_agent:
            self._draw_family_tree_modal(sim_state)
        elif self.viewing_agent:
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

    def _draw_social_graph_modal(self, sim_state):
        """Draws the Social Map overlay."""
        # Background
        pygame.draw.rect(self.screen, constants.COLOR_BG, self.rect_center)
        
        # Clip to center panel
        old_clip = self.screen.get_clip()
        self.screen.set_clip(self.rect_center)
        
        # Draw Graph
        self.social_graph.draw(self.screen, self.font_log)
        
        self.screen.set_clip(old_clip)
        pygame.draw.rect(self.screen, constants.COLOR_BORDER, self.rect_center, 1)
        
        # --- Overlays (Drawn on top) ---
        
        # Header Background
        header_bg = pygame.Rect(self.rect_center.x, self.rect_center.y, self.rect_center.width, 80) # Taller for toggle
        # Actually, let's keep header small and put toggle below it floating?
        # Or just make a standard toolbar.
        
        # Let's stick to the previous header style but add the toggle button.
        pygame.draw.rect(self.screen, (30, 30, 30), (self.rect_center.x, self.rect_center.y, self.rect_center.width, 40))
        pygame.draw.line(self.screen, constants.COLOR_BORDER, (self.rect_center.x, self.rect_center.y + 40), (self.rect_center.right, self.rect_center.y + 40))
        
        title = self.font_header.render("Social Map", True, constants.COLOR_ACCENT)
        self.screen.blit(title, (self.rect_center.x + 15, self.rect_center.y + 8))

        # Toggle Button A (Filter)
        btn_a_rect = pygame.Rect(self.rect_center.x + 10, self.rect_center.y + 45, 120, 25)
        pygame.draw.rect(self.screen, constants.COLOR_BTN_IDLE, btn_a_rect, border_radius=4)
        pygame.draw.rect(self.screen, constants.COLOR_BORDER, btn_a_rect, 1, border_radius=4)
        
        txt_str = "Show: All" if self.social_graph.show_all else "Show: Known"
        toggle_txt = self.font_log.render(txt_str, True, constants.COLOR_TEXT)
        self.screen.blit(toggle_txt, (btn_a_rect.x + 10, btn_a_rect.y + 4))

        # Toggle Button B (Network)
        btn_b_rect = pygame.Rect(self.rect_center.x + 140, self.rect_center.y + 45, 120, 25)
        pygame.draw.rect(self.screen, constants.COLOR_BTN_IDLE, btn_b_rect, border_radius=4)
        pygame.draw.rect(self.screen, constants.COLOR_BORDER, btn_b_rect, 1, border_radius=4)
        
        net_str = "Links: All" if self.social_graph.show_network else "Links: Direct"
        net_txt = self.font_log.render(net_str, True, constants.COLOR_TEXT)
        self.screen.blit(net_txt, (btn_b_rect.x + 10, btn_b_rect.y + 4))

        # Close Button
        close_rect = pygame.Rect(self.rect_center.right - 30, self.rect_center.y + 10, 20, 20)
        pygame.draw.rect(self.screen, constants.COLOR_DEATH, close_rect, border_radius=3)
        pygame.draw.line(self.screen, constants.COLOR_TEXT, close_rect.topleft, close_rect.bottomright, 2)
        pygame.draw.line(self.screen, constants.COLOR_TEXT, close_rect.bottomleft, close_rect.topright, 2)

        # Tooltip
        info = self.social_graph.get_hover_info(sim_state)
        if info:
            lines = []
            # Line 1: Name + Age
            lines.append((f"{info['name']} ({info['age']})", constants.COLOR_ACCENT))
            # Line 2: Job
            lines.append((info['job'], constants.COLOR_TEXT_DIM))
            # Line 3: Relationship
            if info['rel_type'] != "Self":
                rel_txt = f"{info['rel_type']}: {info['rel_val']}/100"
                col = constants.COLOR_LOG_POSITIVE if info['rel_val'] > 50 else constants.COLOR_LOG_NEGATIVE
                lines.append((rel_txt, col))
            
            # Calculate Box Size
            mx, my = pygame.mouse.get_pos()
            line_height = 20
            box_w = 0
            box_h = len(lines) * line_height + 10
            
            surfaces = []
            for text, color in lines:
                s = self.font_log.render(text, True, color)
                box_w = max(box_w, s.get_width())
                surfaces.append(s)
            
            box_w += 20 # Padding
            
            # Draw Box
            bg_rect = pygame.Rect(mx + 15, my + 15, box_w, box_h)
            
            # Keep tooltip on screen
            if bg_rect.right > constants.SCREEN_WIDTH:
                bg_rect.x -= box_w + 30
            if bg_rect.bottom > constants.SCREEN_HEIGHT:
                bg_rect.y -= box_h + 30
                
            pygame.draw.rect(self.screen, (20, 20, 20), bg_rect)
            pygame.draw.rect(self.screen, constants.COLOR_BORDER, bg_rect, 1)
            
            # Draw Text
            curr_y = bg_rect.y + 5
            for s in surfaces:
                self.screen.blit(s, (bg_rect.x + 10, curr_y))
                curr_y += line_height

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
        
        # FT Button in Modal
        ft_rect = pygame.Rect(self.rect_center.x + 20 + header_surf.get_width() + 15, self.rect_center.y + 15, 30, header_surf.get_height())
        self._draw_ft_button(ft_rect, agent)
        
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
            
            # Progress Bar (Skip for IQ)
            if name != "IQ":
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
        # Added "Money" to Vitals for verification
        draw_group(0, "Vitals", ["Health", "Happiness", "IQ", "Looks", "Money"])
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

    def _draw_dashed_rect(self, surface, color, rect, width=2, dash_len=5):
        """Helper to draw a dashed rectangle."""
        x, y, w, h = rect
        
        # Top Edge
        for i in range(x, x + w, dash_len * 2):
            end = min(i + dash_len, x + w)
            pygame.draw.line(surface, color, (i, y), (end, y), width)
            
        # Bottom Edge
        for i in range(x, x + w, dash_len * 2):
            end = min(i + dash_len, x + w)
            pygame.draw.line(surface, color, (i, y + h - 1), (end, y + h - 1), width)
            
        # Left Edge
        for i in range(y, y + h, dash_len * 2):
            end = min(i + dash_len, y + h)
            pygame.draw.line(surface, color, (x, i), (x, end), width)
            
        # Right Edge
        for i in range(y, y + h, dash_len * 2):
            end = min(i + dash_len, y + h)
            pygame.draw.line(surface, color, (x + w - 1, i), (x + w - 1, end), width)

    def _draw_family_tree_modal(self, sim_state):
        """Draws the Family Tree overlay."""
        # 1. Build Layout if needed
        agent = self.viewing_family_tree_agent
        if self.ft_built_for_uid != agent.uid:
            # Construct lookup of all agents
            all_agents = {**sim_state.npcs, sim_state.player.uid: sim_state.player}
            self.ft_layout.build(agent, all_agents)
            self.ft_built_for_uid = agent.uid
            # Center the view
            self.ft_offset_x = 0
            self.ft_offset_y = 0

        # 2. Draw Background
        pygame.draw.rect(self.screen, constants.COLOR_BG, self.rect_center)
        
        # 3. Setup Clipping
        old_clip = self.screen.get_clip()
        self.screen.set_clip(self.rect_center)
        
        cx = self.rect_center.centerx
        cy = self.rect_center.centery
        
        # 4. Draw Edges (Orthogonal Routing)
        for start_node, end_node, link_type in self.ft_layout.edges:
            # Calculate Screen Coords
            x1 = cx + start_node.x + self.ft_offset_x
            y1 = cy + start_node.y + self.ft_offset_y
            x2 = cx + end_node.x + self.ft_offset_x
            y2 = cy + end_node.y + self.ft_offset_y
            
            color = constants.COLOR_TEXT_DIM
            width = 2
            
            if link_type == "SpouseLink":
                # Parent to Hub: Draw from bottom of Parent to Center of Hub
                # But Hub is on same Y level usually? No, Hub is virtual.
                # In our layout, Hub is on same Y as parents.
                # Draw line from Parent Side to Hub Center?
                # Actually, let's draw: Parent Bottom -> Hub Center
                
                # Adjust start to bottom of parent
                start_y_edge = y1 + (start_node.height // 2)
                
                # Draw L-shape or straight?
                # If Hub is strictly between parents, straight line works if Y is same.
                # If Y is same, draw horizontal line.
                pygame.draw.line(self.screen, (100, 100, 100), (x1, y1), (x2, y2), 1)
                
            elif link_type == "ChildLink":
                # Hub to Child: Draw "Bus" style
                # Start at Hub Center
                # Go Down half way
                # Go Horizontal to Child X
                # Go Down to Child Top
                
                mid_y = y1 + (self.ft_layout.LAYER_HEIGHT // 2)
                target_y = y2 - (end_node.height // 2)
                
                # 1. Vertical Down from Hub
                pygame.draw.line(self.screen, color, (x1, y1), (x1, mid_y), width)
                # 2. Horizontal to Child Column
                pygame.draw.line(self.screen, color, (x1, mid_y), (x2, mid_y), width)
                # 3. Vertical Down to Child
                pygame.draw.line(self.screen, color, (x2, mid_y), (x2, target_y), width)

        # 5. Draw Nodes
        for node in self.ft_layout.nodes.values():
            if node.is_hub:
                # Optional: Draw a small dot for the marriage hub for debug/clarity
                # nx = cx + node.x + self.ft_offset_x
                # ny = cy + node.y + self.ft_offset_y
                # pygame.draw.circle(self.screen, (50, 50, 50), (nx, ny), 4)
                continue
                
            # Screen Coords
            nx = cx + node.x + self.ft_offset_x
            ny = cy + node.y + self.ft_offset_y
            
            # Rect Geometry
            w, h = node.width, node.height
            rect = pygame.Rect(nx - w//2, ny - h//2, w, h)
            
            # Skip if off-screen
            if not rect.colliderect(self.rect_center):
                continue
            
            # Colors
            bg_col = constants.COLOR_PANEL_BG
            border_col = constants.COLOR_BORDER
            text_col = constants.COLOR_TEXT
            
            node_agent = node.agent
            
            # Gender Border
            if node_agent.gender == "Male":
                border_col = (100, 150, 255)
            else:
                border_col = (255, 150, 150)
                
            # Highlight Focus Agent
            if node_agent == agent:
                border_col = (255, 215, 0) # Gold
                bg_col = (60, 60, 50)
                
            # Dead State
            if not node_agent.is_alive:
                bg_col = (30, 30, 30)
                text_col = constants.COLOR_TEXT_DIM
                border_col = (80, 80, 80)

            # Draw Background
            pygame.draw.rect(self.screen, bg_col, rect, border_radius=6)
            
            # Draw Border (Solid for Blood, Dashed for In-Laws)
            if node.is_blood:
                pygame.draw.rect(self.screen, border_col, rect, 2, border_radius=6)
            else:
                self._draw_dashed_rect(self.screen, border_col, rect, width=2, dash_len=6)
            
            # Text: Name
            name_surf = self.font_main.render(node_agent.first_name, True, text_col)
            name_rect = name_surf.get_rect(center=(nx, ny - 10))
            self.screen.blit(name_surf, name_rect)
            
            # Text: Age
            age_txt = f"Age: {node_agent.age}"
            if not node_agent.is_alive:
                age_txt = "Deceased"
            
            sub_surf = self.font_log.render(age_txt, True, constants.COLOR_TEXT_DIM)
            sub_rect = sub_surf.get_rect(center=(nx, ny + 10))
            self.screen.blit(sub_surf, sub_rect)

        # 6. Restore Clip & Draw UI Overlays
        self.screen.set_clip(old_clip)
        
        # ... (Rest of the UI Overlay code remains identical: Header, Instructions, Close Button)
        pygame.draw.rect(self.screen, constants.COLOR_BORDER, self.rect_center, 1)
        
        header_bg = pygame.Rect(self.rect_center.x, self.rect_center.y, self.rect_center.width, 50)
        pygame.draw.rect(self.screen, constants.COLOR_BG, header_bg)
        pygame.draw.line(self.screen, constants.COLOR_BORDER, header_bg.bottomleft, header_bg.bottomright)
        
        header_text = f"{agent.first_name}'s Family Tree"
        header_surf = self.font_header.render(header_text, True, constants.COLOR_ACCENT)
        self.screen.blit(header_surf, (self.rect_center.x + 20, self.rect_center.y + 15))
        
        instr = "Left-Drag to Pan | Click to Focus | Right-Click for Stats"
        instr_surf = self.font_log.render(instr, True, constants.COLOR_TEXT_DIM)
        self.screen.blit(instr_surf, (self.rect_center.x + 20, self.rect_center.y + 55))

        close_rect = pygame.Rect(self.rect_center.right - 30, self.rect_center.y + 10, 20, 20)
        pygame.draw.rect(self.screen, constants.COLOR_DEATH, close_rect, border_radius=3)
        pygame.draw.line(self.screen, constants.COLOR_TEXT, close_rect.topleft, close_rect.bottomright, 2)
        pygame.draw.line(self.screen, constants.COLOR_TEXT, close_rect.bottomleft, close_rect.topright, 2)

    def _draw_ft_button(self, rect, agent):
        """Helper to draw the Family Tree button (Icon or Text)."""
        # Draw Button Background
        pygame.draw.rect(self.screen, constants.COLOR_BTN_IDLE, rect, border_radius=4)
        pygame.draw.rect(self.screen, constants.COLOR_BORDER, rect, 1, border_radius=4)
        
        if self.icon_ft:
            # Center Icon
            icon_rect = self.icon_ft.get_rect(center=rect.center)
            self.screen.blit(self.icon_ft, icon_rect)
        else:
            # Fallback Text
            ft_txt = self.font_log.render("FT", True, constants.COLOR_TEXT)
            ft_txt_rect = ft_txt.get_rect(center=rect.center)
            self.screen.blit(ft_txt, ft_txt_rect)
            
        # Register Interaction
        self.ft_buttons.append((rect, agent))

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

        # Name & FT Button
        name_text = f"{player.first_name} {player.last_name}"
        name_surf = self.font_header.render(name_text, True, constants.COLOR_ACCENT)
        self.screen.blit(name_surf, (x, y))
        
        # FT Button
        ft_rect = pygame.Rect(x + name_surf.get_width() + 10, y, 30, name_surf.get_height())
        self._draw_ft_button(ft_rect, player)
        
        y += name_surf.get_height() + 5 + 10
        
        # Date Display
        month_name = constants.MONTHS[sim_state.month_index]
        y += draw_text(f"{month_name} {sim_state.year}", color=constants.COLOR_TEXT_DIM)
        
        # Age Display
        y += draw_text(f"Age: {player.age} ({player.age_months % 12} mos)")
        
        # AP Bar
        y += 5
        ap_bar = APBar(x, y + 15, self.rect_left.width - 40, 20)
        ap_bar.draw(self.screen, player)
        y += 45 # Bar height + padding + text offset
        
        y += draw_text(f"Money: ${player.money}", color=constants.COLOR_ACCENT)
        
        # Job / School Display
        if player.school:
            sys_name = player.school['system']
            # Get grade name from config
            edu_conf = sim_state.config.get("education", {}).get("systems", {}).get(sys_name, {})
            grades = edu_conf.get("grades", [])
            grade_idx = player.school['grade_index']
            
            grade_name = "Unknown"
            if 0 <= grade_idx < len(grades):
                grade_name = grades[grade_idx]['name']
                
            status = "In Session" if player.school['is_in_session'] else "Summer Break"
            y += draw_text(f"School: {grade_name}")
            y += draw_text(f"Status: {status}", color=constants.COLOR_TEXT_DIM)
        else:
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
            
            # FT Button for NPC
            if uid in sim_state.npcs:
                npc_agent = sim_state.npcs[uid]
                ft_rect = pygame.Rect(x + 10 + name_surf.get_width() + 10, y + 5, 30, 20) # Slightly wider for icon
                self._draw_ft_button(ft_rect, npc_agent)

            self.screen.blit(type_surf, (x + 10, y + 25))
            
            # Relationship Bar
            if rel['is_alive']:
                # Define Bar Area
                bar_w = 100
                bar_h = 10
                bar_x = x + w - bar_w - 10
                bar_y = y + 10
                
                bar_bg = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
                pygame.draw.rect(self.screen, (30, 30, 30), bar_bg)
                
                # Draw Center Line
                center_x = bar_bg.centerx
                pygame.draw.line(self.screen, (80, 80, 80), (center_x, bar_y), (center_x, bar_y + bar_h))
                
                val = rel['value']
                # Clamp for rendering safety
                val = max(constants.RELATIONSHIP_MIN, min(constants.RELATIONSHIP_MAX, val))
                
                if val > 0:
                    # Draw Green to Right
                    pct = val / 100.0
                    fill_w = (bar_w / 2) * pct
                    fill_rect = pygame.Rect(center_x, bar_y, fill_w, bar_h)
                    
                    # Color Intensity
                    if val > 80: col = constants.COLOR_REL_BEST
                    else: col = constants.COLOR_REL_FRIEND
                    
                    pygame.draw.rect(self.screen, col, fill_rect)
                    
                elif val < 0:
                    # Draw Red to Left
                    pct = abs(val) / 100.0
                    fill_w = (bar_w / 2) * pct
                    fill_rect = pygame.Rect(center_x - fill_w, bar_y, fill_w, bar_h)
                    
                    # Color Intensity
                    if val < -50: col = constants.COLOR_REL_ENEMY
                    else: col = constants.COLOR_REL_DISLIKE
                    
                    pygame.draw.rect(self.screen, col, fill_rect)

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