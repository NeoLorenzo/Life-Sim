# life_sim/rendering/renderer.py
"""
Main Game Renderer.
Handles all drawing operations and UI rendering.
"""
import pygame
import logging
import os
from .. import constants
from .ui import Button, LogPanel, APBar, NumberStepper, RelationshipPanel
from .family_tree import FamilyTreeLayout
from .social_graph import SocialGraphLayout
from .modals import EventModal
from .background import BackgroundManager

class Renderer:
    """
    Handles drawing the SimState to the screen using a 3-panel layout.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        pygame.init()
        self.screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption(constants.WINDOW_TITLE)
        
        # Track current screen dimensions
        self.screen_width = constants.SCREEN_WIDTH
        self.screen_height = constants.SCREEN_HEIGHT
        
        # Fonts
        self.font_main = pygame.font.SysFont("Arial", constants.FONT_SIZE_MAIN)
        self.font_header = pygame.font.SysFont("Arial", constants.FONT_SIZE_HEADER, bold=True)
        self.font_log = pygame.font.SysFont("Consolas", constants.FONT_SIZE_LOG)
        
        # Layout Calculation
        self._update_layout()
        
        # Initialize UI Elements
        self.log_panel = LogPanel(
            self.rect_center.x, 
            self.rect_center.y, 
            self.rect_center.width, 
            self.rect_center.height, 
            self.font_log
        )
        
        # Initialize Relationship Panel (will be positioned in _draw_right_panel)
        self.relationship_panel = RelationshipPanel(
            self.rect_right.x, 
            self.rect_right.y, 
            self.rect_right.width, 
            self.rect_right.height, 
            self.font_main,
            self.font_log
        )
        
        self.viewing_agent = None # None, or an Agent object
        self.event_modal = None  # EventModal instance when event is active
        
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
        
        # Tooltip zones for clickable grade areas
        self.tooltip_zones = []  # List of (Rect, subject_name) tuples
        self.attribute_tooltip_zones = []  # List of (Rect, attr_name, value, max_value)
        self.academics_scroll_offset = 0
        self.academics_scroll_max = 0
        self.academics_scroll_rect = None
        
        self.active_tab = "Main"
        
        # Visibility Logic (Action ID -> Lambda accepting player)
        self.visibility_rules = {
            "FIND_JOB": lambda player: player.age >= 16,
            "WORK": lambda player: player.job is not None,
            "SCHOOL_GRADES": lambda player: player.school is not None,
            "SCHOOL_CLASSMATES": lambda player: player.school is not None,
            "SCHOOL_STUDY": lambda player: player.school is not None and player.school.get("is_in_session", False),
            "SCHOOL_SKIP": lambda player: player.school is not None and player.school.get("is_in_session", False)
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
        
        # Initialize Background Manager
        self.background_manager = BackgroundManager()
        
        # Flag to track when social graph needs rebuild due to resize
        self._social_graph_needs_rebuild = False
        
        # Schedule Controls
        self.show_schedule_controls = False
        self.schedule_btn = None
        self.sleep_stepper = None
        self.attendance_stepper = None
        
        # Initialize schedule controls after all layout is set up
        self._init_schedule_controls()

    def _init_ui_structure(self):
        """Creates Tabs and Action Buttons."""
        # Clear existing UI elements before recreating
        self.tabs.clear()
        self.buttons.clear()
        
        # 1. Init Tabs
        tab_names = ["Main", "School", "Social", "Assets"]
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
            "School": [
                ("View Grades", "SCHOOL_GRADES"),
                ("View Classmates", "SCHOOL_CLASSMATES"),
                ("Study Hard", "SCHOOL_STUDY"),
                ("Skip Class", "SCHOOL_SKIP")
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
        
        # Schedule controls are now initialized in __init__ to ensure they appear on startup

    def _init_schedule_controls(self):
        """Initialize schedule button and steppers for the left panel."""
        # Schedule button positioned below AP bar area
        btn_x = self.rect_left.x + 20
        btn_y = self.rect_left.y + 170
        btn_w = self.rect_left.width - 40
        btn_h = 30
        
        self.schedule_btn = Button(btn_x, btn_y, btn_w, btn_h, "Schedule", "TOGGLE_SCHEDULE", self.font_main)
        
        # Number steppers (positioned when shown)
        stepper_x = self.rect_left.x + 20
        stepper_y = btn_y + btn_h + 40
        stepper_w = self.rect_left.width - 40
        stepper_h = 25
        
        self.sleep_stepper = NumberStepper(
            stepper_x, stepper_y, stepper_w, stepper_h,
            8.0, constants.MIN_SLEEP_PERMITTED, 24.0, 0.5, self.font_main, "Target Sleep"
        )
        
        self.attendance_stepper = NumberStepper(
            stepper_x, stepper_y + stepper_h + 40, stepper_w, stepper_h,
            1.0, 0.0, 1.0, 0.1, self.font_main, "Attendance %"
        )

    def _draw_panel_background(self, rect, alpha):
        """
        Draw a transparent panel background.
        
        Args:
            rect: pygame.Rect defining the panel area
            alpha: Alpha transparency value (0-255)
        """
        s = pygame.Surface((rect.width, rect.height))
        s.set_alpha(alpha)
        s.fill((20, 20, 20))  # Dark grey background
        self.screen.blit(s, (rect.x, rect.y))

    def _update_layout(self):
        """Update panel layout based on current screen dimensions."""
        self.rect_left = pygame.Rect(0, 0, constants.PANEL_LEFT_WIDTH + constants.AP_BAR_WIDTH, self.screen_height)
        self.rect_right = pygame.Rect(self.screen_width - constants.PANEL_RIGHT_WIDTH, 0, constants.PANEL_RIGHT_WIDTH, self.screen_height)
        
        # AP bar positioned within left panel area
        ap_bar_height = int(self.screen_height * constants.AP_BAR_HEIGHT_PERCENTAGE)
        self.rect_ap_bar = pygame.Rect(
            constants.PANEL_LEFT_WIDTH,  # At the edge of expanded left panel
            self.screen_height - ap_bar_height - 20,  # Snap to bottom (with 20 pixels of padding)
            constants.AP_BAR_WIDTH, 
            ap_bar_height
        )
        
        center_w = self.screen_width - constants.PANEL_LEFT_WIDTH - constants.AP_BAR_WIDTH - constants.PANEL_RIGHT_WIDTH
        self.rect_center = pygame.Rect(constants.PANEL_LEFT_WIDTH + constants.AP_BAR_WIDTH, 0, center_w, self.screen_height)
        
        # Update log panel if it exists
        if hasattr(self, 'log_panel'):
            self.log_panel.update_position(self.rect_center.x, self.rect_center.y, self.rect_center.width, self.rect_center.height)
        
        # Update relationship panel if it exists
        if hasattr(self, 'relationship_panel'):
            self.relationship_panel.update_position(self.rect_right.x, self.rect_right.y, self.rect_right.width, self.rect_right.height)
        
        # Rebuild UI structure with new dimensions
        if hasattr(self, 'tabs') and self.tabs:
            self._init_ui_structure()
        
        # Rebuild social graph if it's currently visible and has been built
        if hasattr(self, 'viewing_social_graph') and self.viewing_social_graph:
            if hasattr(self, 'social_graph') and self.social_graph.bounds is not None:
                # We need sim_state to rebuild, but we don't have it here
                # Mark for rebuild in next render cycle
                self._social_graph_needs_rebuild = True

    def _handle_resize(self, w, h):
        self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        self.screen_width = w
        self.screen_height = h
        self._update_layout()

    def handle_event(self, event, sim_state=None):
        """
        Processes input events.
        """
        # Scroll long academics list when cursor is over the academics viewport.
        if sim_state and self.academics_scroll_rect and sim_state.player.school:
            if event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                if self.academics_scroll_rect.collidepoint((mx, my)):
                    self._adjust_academics_scroll(-event.y)
                    return None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.academics_scroll_rect.collidepoint(event.pos):
                    if event.button == 4:  # Wheel up
                        self._adjust_academics_scroll(-1)
                        return None
                    if event.button == 5:  # Wheel down
                        self._adjust_academics_scroll(1)
                        return None

        # Handle window resize events
        if event.type == pygame.VIDEORESIZE:
            self._handle_resize(event.w, event.h)
            return None
        
        # 0. Check Event Modal (Highest Priority - blocks all other UI)
        if sim_state and sim_state.pending_event and self.event_modal:
            modal_result = self.event_modal.handle_event(event)
            if modal_result == "CONFIRM_EVENT":
                # Return special action with selected choice data
                return ("RESOLVE_EVENT", self.event_modal.selected_choices)
            return None  # Block all other UI when event is pending
        
        # 0d. Check Grade Tooltip Zones (Left Panel)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, subject_name in self.tooltip_zones:
                if rect.collidepoint(event.pos):
                    # Show subject tooltip (handled in render method)
                    return None

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

        # 2a. Check Schedule Button (Left Panel)
        if self.schedule_btn:
            action = self.schedule_btn.handle_event(event)
            if action == "TOGGLE_SCHEDULE":
                self.show_schedule_controls = not self.show_schedule_controls
                return None

        # 2b. Check Schedule Steppers (if visible)
        if self.show_schedule_controls and self.sleep_stepper and self.attendance_stepper:
            # Handle sleep stepper
            result = self.sleep_stepper.handle_event(event)
            if result and result[0] == "STEP_CHANGE":
                return ("UPDATE_SCHEDULE", {"sleep": result[1]})
            
            # Handle attendance stepper  
            result = self.attendance_stepper.handle_event(event)
            if result and result[0] == "STEP_CHANGE":
                return ("UPDATE_SCHEDULE", {"attendance": result[1]})

        # 3. Check Relationship Panel (Social Tab)
        if self.active_tab == "Social" and sim_state and self.relationship_panel:
            # Handle scrolling and button clicks in the relationship panel
            result = self.relationship_panel.handle_event(event, sim_state)
            if result:
                if result[0] == "VIEW_AGENT":
                    self.viewing_agent = result[1]
                    return None
                elif result[0] == "INTERACT":
                    return f"INTERACT_{result[1]}"

        return None

    def render(self, sim_state):
        """Draws the full UI."""
        self.ft_buttons = [] # Reset interactive buttons for this frame
        self.tooltip_zones = []  # Reset tooltip zones for this frame
        self.attribute_tooltip_zones = []  # Reset attribute tooltip zones for this frame
        
        # Physics Step
        if self.viewing_social_graph:
            self.social_graph.update_physics()
        
        # Update and draw background
        self.background_manager.update(sim_state, self.screen_width, self.screen_height)
        self.background_manager.draw(self.screen)
        
        # Update Log Panel Content
        self.log_panel.update_logs(sim_state.get_flat_log_for_rendering())
        
        # Draw Panels
        self._draw_left_panel(sim_state)
        self._draw_vertical_ap_bar(sim_state)
        
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
        
        # Draw event modal on top of everything if active
        if sim_state.pending_event:
            if self.event_modal is None:
                # Create modal with centered rectangle
                modal_width = 600
                # Double height for IGCSE event to accommodate all subject choices
                if sim_state.pending_event.id == "EVT_IGCSE_SUBJECTS":
                    modal_height = 800  # Double the regular height
                else:
                    modal_height = 400  # Regular height
                
                modal_x = (self.screen.get_width() - modal_width) // 2
                modal_y = (self.screen.get_height() - modal_height) // 2
                modal_rect = pygame.Rect(modal_x, modal_y, modal_width, modal_height)
                self.event_modal = EventModal(modal_rect, sim_state.pending_event)
            
            self.event_modal.draw(self.screen)
        else:
            # Clear modal when no pending event
            self.event_modal = None
        
        # Draw tooltips on top of everything
        self._draw_grade_tooltips(sim_state)
        self._draw_attribute_tooltips(sim_state)
        
        # Draw relationship panel tooltips if on Social tab
        if self.active_tab == "Social" and hasattr(self, 'relationship_panel'):
            mouse_pos = pygame.mouse.get_pos()
            self.relationship_panel.draw_tooltip(self.screen, mouse_pos, sim_state)
        
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
        # Rebuild social graph if needed due to resize
        if self._social_graph_needs_rebuild:
            self.social_graph.build(sim_state, self.rect_center)
            self._social_graph_needs_rebuild = False
        
        # Background
        self._draw_panel_background(self.rect_center, constants.UI_OPACITY_CENTER)
        
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
            
            if info.get("type") == "edge":
                # Edge Tooltip
                lines.append((f"{info['agent_a']} & {info['agent_b']}", constants.COLOR_ACCENT))
                
                # Total Score - use gradient color logic
                total = info['total']
                col_total = self.social_graph._get_relationship_color(total)
                lines.append((f"Total Score: {total}", col_total))
                
                lines.append(("--- Base Affinity ---", constants.COLOR_TEXT_DIM))
                # Color code the base affinity itself using gradient logic
                base_col = self.social_graph._get_relationship_color(info['score'])
                lines.append((f"Base: {info['score']}", base_col))
                
                for factor, val in info['affinity_breakdown']:
                    col = self.social_graph._get_relationship_color(val)
                    lines.append((f"  {factor}: {val:+.1f}", col))

                if info['modifiers']:
                    lines.append(("--- Active Modifiers ---", constants.COLOR_TEXT_DIM))
                    for mod_name, mod_val in info['modifiers']:
                        col = self.social_graph._get_relationship_color(mod_val)
                        lines.append((f"  {mod_name}: {mod_val:+.1f}", col))
                    
            else:
                # Node Tooltip (Legacy/Standard)
                lines.append((f"{info['name']} ({info['age']})", constants.COLOR_ACCENT))
                lines.append((info['job'], constants.COLOR_TEXT_DIM))
                if info['rel_type'] != "Self":
                    rel_txt = f"{info['rel_type']}: {info['rel_val']}/100"
                    col = self.social_graph._get_relationship_color(info['rel_val'])
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
            if bg_rect.right > self.screen.get_width():
                bg_rect.x -= box_w + 30
            if bg_rect.bottom > self.screen.get_height():
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
        self.attribute_tooltip_zones = []
        
        # Draw Background
        self._draw_panel_background(self.rect_center, constants.UI_OPACITY_CENTER)
        pygame.draw.rect(self.screen, constants.COLOR_BORDER, self.rect_center, 1)
        
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
        
        # 5 Columns (added Cognitive Profile)
        col_count = 5
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
                is_neuro = (name == "Neuroticism" or (agent.personality and name in agent.personality.get("Neuroticism", {})))
                
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
            self.attribute_tooltip_zones.append((rect.copy(), name, value, max_val))

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

        # Check if agent is an infant (age < 3)
        if agent.age < 3:
            # Infant Layout: Vitals + Temperament
            # Column 1: Vitals, Physical, Hidden
            draw_group(0, "Vitals", ["Health", "Happiness", "IQ", "Looks", "Money"])
            draw_group(0, "Physical", ["Energy", "Fitness", "Strength", "Agility", "Balance", "Coordination", "Reaction Time", "Flexibility", "Speed", "Power", "Fertility", "Libido"])
            draw_group(0, "Hidden", ["Religiousness"])
            
            # Columns 1-3: Temperament (3x3 grid layout)
            temperament_traits = list(agent.temperament.keys())
            for i in range(3):  # 3 columns
                start_idx = i * 3
                end_idx = start_idx + 3
                col_traits = temperament_traits[start_idx:end_idx]
                
                # Draw temperament header for first column only
                title = "Temperament" if i == 0 else None
                draw_group(i + 1, title, col_traits)
            
            # Column 4: Cognitive Profile (Aptitudes) - also show for infants
            draw_group(4, "Cognitive Profile", ["Analytical Reasoning", "Verbal Abilities", "Spatial Abilities", "Working Memory", "Long-term Memory", "Secondary Cognitive"])
                
        else:
            # Adult Layout: Vitals + Big 5 Personality
            # Column 1: Vitals, Physical, Hidden
            # Added "Money" to Vitals for verification
            draw_group(0, "Vitals", ["Health", "Happiness", "IQ", "Looks", "Money"])
            draw_group(0, "Physical", ["Energy", "Fitness", "Strength", "Agility", "Balance", "Coordination", "Reaction Time", "Flexibility", "Speed", "Power", "Fertility", "Libido"])
            draw_group(0, "Hidden", ["Religiousness"])
            
            # Column 2: Openness & Conscientiousness
            draw_group(1, "Openness", list(agent.personality["Openness"].keys()), is_personality=True)
            draw_group(1, "Conscientiousness", list(agent.personality["Conscientiousness"].keys()), is_personality=True)
            
            # Column 3: Extraversion & Agreeableness
            draw_group(2, "Extraversion", list(agent.personality["Extraversion"].keys()), is_personality=True)
            draw_group(2, "Agreeableness", list(agent.personality["Agreeableness"].keys()), is_personality=True)
            
            # Column 4: Neuroticism
            draw_group(3, "Neuroticism", list(agent.personality["Neuroticism"].keys()), is_personality=True)
            
            # Column 5: Cognitive Profile (Aptitudes)
            draw_group(4, "Cognitive Profile", ["Analytical Reasoning", "Verbal Abilities", "Spatial Abilities", "Working Memory", "Long-term Memory", "Secondary Cognitive"])

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
        self._draw_panel_background(self.rect_center, constants.UI_OPACITY_CENTER)
        
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

    def _draw_vertical_ap_bar(self, sim_state):
        """Draw vertical AP bar within the expanded left panel area."""
        # Calculate dynamic height and create AP bar
        ap_bar_height = int(self.screen_height * constants.AP_BAR_HEIGHT_PERCENTAGE)
        ap_bar = APBar(
            self.rect_ap_bar.x, 
            self.rect_ap_bar.y, 
            self.rect_ap_bar.width, 
            ap_bar_height,  # Use calculated height
            vertical=True
        )
        ap_bar.draw(self.screen, sim_state.player)

    def _draw_left_panel(self, sim_state):
        self._draw_panel_background(self.rect_left, constants.UI_OPACITY_PANEL)
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
        
        # Money Display
        y += draw_text(f"Money: ${player.money}", color=constants.COLOR_ACCENT)
        
        # Schedule Button
        if self.schedule_btn:
            self.schedule_btn.draw(self.screen)
            y = self.schedule_btn.rect.y + self.schedule_btn.rect.height + 10
        
        # Schedule Controls (if shown)
        if self.show_schedule_controls and self.sleep_stepper and self.attendance_stepper:
            # Update stepper values with current player settings
            self.sleep_stepper.value = player.target_sleep_hours
            self.attendance_stepper.value = player.attendance_rate
            
            # Draw labels and steppers
            y += draw_text("Target Sleep:", color=constants.COLOR_TEXT_DIM)
            self.sleep_stepper.draw(self.screen)
            
            y = self.sleep_stepper.rect.y + self.sleep_stepper.rect.height + 10
            
            # Only show attendance controls if enrolled in school
            if player.school:
                y += draw_text("Attendance %:", color=constants.COLOR_TEXT_DIM)
                self.attendance_stepper.draw(self.screen)
                
                # Draw preview line
                y = self.attendance_stepper.rect.y + self.attendance_stepper.rect.height + 15
                free_ap = player.free_ap
                y += draw_text(f"Free AP: {free_ap:.1f}h", color=constants.COLOR_ACCENT)
            else:
                # Draw preview line without attendance stepper
                y += draw_text(f"Free AP: {player.free_ap:.1f}h", color=constants.COLOR_ACCENT)
        
        # Job / School Display
        if player.school:
            status = "In Session" if player.school['is_in_session'] else "Summer Break"
            
            # Line 1: School Name
            y += draw_text(f"{player.school['school_name']}", color=constants.COLOR_ACCENT)
            
            # Line 2: Year + Form (e.g. "Year 9B")
            full_class = f"{player.school['year_label']}{player.school['form_label']}"
            y += draw_text(f"Class: {full_class} ({player.school['stage']})")
            
            # Line 3: Status
            y += draw_text(f"Status: {status}", color=constants.COLOR_TEXT_DIM)
        
        # Academics Section (only if in school)
        if player.school:
            y += draw_text("--- Academics ---", color=constants.COLOR_TEXT_DIM)
            
            # Helper function to get grade color
            def get_grade_color(grade):
                if grade >= 90: return constants.COLOR_LOG_POSITIVE  # Green
                elif grade >= 70: return constants.COLOR_LOG_HEADER  # Blue  
                elif grade >= 50: return (255, 255, 100)  # Yellow
                else: return constants.COLOR_LOG_NEGATIVE  # Red
            
            subjects = player.subjects
            subject_names = list(subjects.keys())
            row_height = self.font_main.get_height() + 5
            viewport_height = 190
            viewport_width = self.rect_left.width - 40
            viewport_y = y
            self.academics_scroll_rect = pygame.Rect(x - 2, viewport_y - 2, viewport_width + 4, viewport_height + 4)

            pygame.draw.rect(self.screen, constants.COLOR_BORDER, self.academics_scroll_rect, 1)

            max_visible_rows = max(1, viewport_height // row_height)
            self.academics_scroll_max = max(0, len(subject_names) - max_visible_rows)
            self.academics_scroll_offset = max(0, min(self.academics_scroll_offset, self.academics_scroll_max))

            visible_subjects = subject_names[
                self.academics_scroll_offset:self.academics_scroll_offset + max_visible_rows
            ]

            draw_y = viewport_y
            for subject in visible_subjects:
                grade = int(subjects[subject]["current_grade"])
                color = get_grade_color(grade)

                # Draw subject name and grade on same line with color
                subject_text = f"{subject}: "
                grade_text = str(grade)

                subject_surf = self.font_main.render(subject_text, True, constants.COLOR_TEXT)
                self.screen.blit(subject_surf, (x, draw_y))

                grade_x = x + subject_surf.get_width()
                grade_surf = self.font_main.render(grade_text, True, color)
                grade_rect = pygame.Rect(grade_x, draw_y, grade_surf.get_width(), grade_surf.get_height())
                self.screen.blit(grade_surf, (grade_x, draw_y))

                self.tooltip_zones.append((grade_rect, subject))
                draw_y += row_height

            # Scroll hint for long lists.
            if self.academics_scroll_max > 0:
                first_visible = self.academics_scroll_offset + 1
                last_visible = self.academics_scroll_offset + len(visible_subjects)
                hint = f"{first_visible}-{last_visible}/{len(subject_names)} (Mouse Wheel)"
                hint_surf = self.font_log.render(hint, True, constants.COLOR_TEXT_DIM)
                self.screen.blit(hint_surf, (x, viewport_y + viewport_height - hint_surf.get_height() - 2))

            y = viewport_y + viewport_height + 10
        else:
            self.academics_scroll_rect = None
            self.academics_scroll_offset = 0
            self.academics_scroll_max = 0

        y += 20
        
        for attr in player.pinned_attributes:
            val = player.get_attr_value(attr)
            
            # Special formatting for Health to show Max
            if attr == "Health":
                txt = f"{attr}: {val}/{player.max_health}"
            else:
                txt = f"{attr}: {val}"
                
            y += draw_text(txt)

    def _wrap_tooltip_text(self, text, max_width):
        """Wraps tooltip text to fit in a bounded width."""
        if not text:
            return []
        words = text.split()
        if not words:
            return []
        lines = []
        current = words[0]
        for word in words[1:]:
            test = f"{current} {word}"
            if self.font_log.size(test)[0] <= max_width:
                current = test
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    def _value_polarity(self, value, low=40, high=60):
        """Returns +, -, or ~ for a scalar state."""
        if value >= high:
            return "+"
        if value <= low:
            return "-"
        return "~"

    def _age_effect_polarity(self, multiplier):
        """Returns +, -, or ~ for age multiplier effect."""
        if multiplier >= 1.05:
            return "+"
        if multiplier <= 0.95:
            return "-"
        return "~"

    def _polarity_from_score(self, score, deadzone=0.05):
        """Returns +, -, or ~ from a signed normalized score."""
        if score > deadzone:
            return "+"
        if score < -deadzone:
            return "-"
        return "~"

    def _impact_word(self, score):
        """Human-readable impact strength from signed score."""
        abs_score = abs(score)
        if abs_score < 0.1:
            return "neutral"
        if score > 0:
            return "supporting" if abs_score < 0.35 else "strong support"
        return "limiting" if abs_score < 0.35 else "strong limit"

    def _band_word(self, value, low=40.0, high=60.0):
        """Simple low/mid/high label."""
        if value <= low:
            return "low"
        if value >= high:
            return "high"
        return "mid"

    def _age_phase_word(self, age):
        """General age phase label for tooltip context."""
        if age < 13:
            return "childhood"
        if age < 20:
            return "adolescence"
        if age < 36:
            return "prime years"
        if age < 56:
            return "midlife"
        return "senior years"

    def _top_driver_labels(self, drivers, limit=2):
        """Formats top driver labels from (name, signed_score[, context]) tuples."""
        if not drivers:
            return "Main drivers now: Stable/neutral"
        meaningful = [item for item in drivers if abs(item[1]) >= 0.1]
        if not meaningful:
            return "Main drivers now: Stable/neutral"
        ranked = sorted(meaningful, key=lambda item: abs(item[1]), reverse=True)
        top = ranked[:limit]
        labels = []
        for item in top:
            if len(item) >= 3 and item[2]:
                name, score, context = item[0], item[1], item[2]
                labels.append(f"{name} ({context}, {self._impact_word(score)})")
            else:
                name, score = item[0], item[1]
                labels.append(f"{name} ({self._impact_word(score)})")
        return "Main drivers now: " + ", ".join(labels)

    def _get_attribute_tooltip_data(self, agent, attr_name, value, max_value):
        """Builds concise tooltip data for an attribute card."""
        clean_name = attr_name.replace("_", " ")
        age = int(getattr(agent, "age", 0))
        traits = getattr(agent, "personality", None) or {}

        # Physical attributes with explicit formula dependencies.
        physical_defs = {
            "Strength": ("maximal_strength", "Peak force output.", ["Age", "Lean Mass", "Body Frame", "Fiber Type"]),
            "Fitness": ("aerobic_capacity", "Aerobic stamina and recovery.", ["Age", "Genetic Aerobic Base", "Health"]),
            "Energy": ("aerobic_capacity", "Resistance to fatigue over time.", ["Strength Endurance", "Fitness"]),
            "Speed": ("max_speed", "Top movement speed.", ["Age", "Height", "Fiber Type", "Coordination"]),
            "Power": ("maximal_strength", "Explosive force production.", ["Age", "Strength", "Speed"]),
            "Agility": (None, "Change-of-direction ability.", ["Speed", "Coordination", "Balance"]),
            "Balance": ("coordination", "Posture control and stability.", ["Age", "Coordination", "Strength"]),
            "Coordination": ("coordination", "Neuromuscular control quality.", ["Age", "Fiber Type", "Body Frame"]),
            "Reaction Time": (None, "Quickness to respond to stimuli.", ["Inherited Baseline"]),
            "Flexibility": (None, "Range-of-motion capacity.", ["Inherited Baseline"]),
        }

        if clean_name in physical_defs:
            age_curve_key, desc, factors = physical_defs[clean_name]
            if age_curve_key:
                age_mult = agent._get_physical_age_multiplier(age_curve_key)
                age_score = age_mult - 1.0
            else:
                age_score = 0.0

            if clean_name == "Strength":
                lean = float(getattr(agent, "lean_mass", 0.0))
                frame = float(getattr(agent, "body_frame_size", 1.0))
                fiber = float(getattr(agent, "muscle_fiber_composition", 50.0))
                now = self._top_driver_labels([
                    ("Age", age_score, self._age_phase_word(age)),
                    ("Lean Mass", (lean - 50.0) / 50.0, f"{round(lean, 1)}kg ({self._band_word(lean, 40, 60)})"),
                    ("Body Frame", frame - 1.0, self._band_word(frame * 100, 95, 105)),
                    ("Fiber Type", (fiber - 50.0) / 50.0, f"{int(fiber)} ({self._band_word(fiber)})"),
                ])
            elif clean_name == "Fitness":
                health = float(getattr(agent, "health", 0.0))
                aerobic = float(getattr(agent, "aerobic_capacity_genetic", 50.0))
                now = self._top_driver_labels([
                    ("Age", age_score, self._age_phase_word(age)),
                    ("Genetic Aerobic Base", (aerobic - 50.0) / 50.0, self._band_word(aerobic)),
                    ("Health", (health - 50.0) / 50.0, self._band_word(health)),
                ])
            elif clean_name == "Energy":
                strength_end = float(getattr(agent, "strength_endurance", 50.0))
                cardio = float(getattr(agent, "cardiovascular_endurance", 50.0))
                now = self._top_driver_labels([
                    ("Strength Endurance", ((strength_end - 50.0) / 50.0) * 0.7, self._band_word(strength_end)),
                    ("Fitness", ((cardio - 50.0) / 50.0) * 0.3, self._band_word(cardio)),
                ])
            elif clean_name == "Speed":
                height = float(getattr(agent, "height_cm", 170.0))
                fiber = float(getattr(agent, "muscle_fiber_composition", 50.0))
                coord = float(getattr(agent, "coordination", 50.0))
                now = self._top_driver_labels([
                    ("Age", age_score, self._age_phase_word(age)),
                    ("Coordination", ((coord - 50.0) / 50.0) * 0.3, self._band_word(coord)),
                    ("Fiber Type", ((fiber - 50.0) / 50.0) * 0.3, self._band_word(fiber)),
                    ("Height", (height - 170.0) / 70.0, f"{int(height)}cm"),
                ])
            elif clean_name == "Power":
                strength = float(getattr(agent, "maximal_strength", 50.0))
                speed = float(getattr(agent, "max_speed", 50.0))
                now = self._top_driver_labels([
                    ("Age", age_score, self._age_phase_word(age)),
                    ("Strength", (strength - 50.0) / 50.0, self._band_word(strength)),
                    ("Speed", (speed - 50.0) / 50.0, self._band_word(speed)),
                ])
            elif clean_name == "Agility":
                speed = float(getattr(agent, "max_speed", 50.0))
                coord = float(getattr(agent, "coordination", 50.0))
                balance = float(getattr(agent, "balance", 50.0))
                now = self._top_driver_labels([
                    ("Speed", ((speed - 50.0) / 50.0) * 0.4, self._band_word(speed)),
                    ("Coordination", ((coord - 50.0) / 50.0) * 0.4, self._band_word(coord)),
                    ("Balance", ((balance - 50.0) / 50.0) * 0.2, self._band_word(balance)),
                ])
            elif clean_name == "Balance":
                coord = float(getattr(agent, "coordination", 50.0))
                strength = float(getattr(agent, "maximal_strength", 50.0))
                now = self._top_driver_labels([
                    ("Age", age_score, self._age_phase_word(age)),
                    ("Coordination", ((coord - 50.0) / 50.0) * 0.2, self._band_word(coord)),
                    ("Strength", ((strength - 50.0) / 50.0) * 0.1, self._band_word(strength)),
                ])
            elif clean_name == "Coordination":
                fiber = float(getattr(agent, "muscle_fiber_composition", 50.0))
                frame = float(getattr(agent, "body_frame_size", 1.0))
                now = self._top_driver_labels([
                    ("Age", age_score, self._age_phase_word(age)),
                    ("Fiber Type", (fiber - 50.0) / 50.0, self._band_word(fiber)),
                    ("Body Frame", frame - 1.0, self._band_word(frame * 100, 95, 105)),
                ])
            elif clean_name == "Reaction Time":
                now = "Main drivers now: Inherited baseline (currently static)"
            else:
                now = "Main drivers now: Inherited baseline (currently static)"
            return clean_name, desc, factors, now

        if clean_name == "Health":
            desc = "Overall physical condition and survivability."
            factors = ["Age (via Max Health)", "Injuries/Illness", "Medical Care", "Lifestyle Events"]
            cap = float(max_value) if max_value else 100.0
            current = float(value)
            now = self._top_driver_labels([
                ("Current Condition", (current - 50.0) / 50.0, f"{int(current)}/{int(cap)}"),
                ("Age Cap", ((cap / 100.0) - 1.0) * 1.2, self._age_phase_word(age)),
            ])
            return clean_name, desc, factors, now

        if clean_name == "Happiness":
            desc = "Current emotional wellbeing."
            factors = ["Life Events", "School/Work Outcomes", "Relationships", "Health"]
            health = float(getattr(agent, "health", 50.0))
            rel_values = [getattr(rel, "total_score", 0.0) for rel in getattr(agent, "relationships", {}).values()]
            rel_avg = (sum(rel_values) / len(rel_values)) if rel_values else 0.0
            now = self._top_driver_labels([
                ("Relationships", rel_avg / 100.0, self._band_word(rel_avg + 50.0)),
                ("Health", (health - 50.0) / 50.0, self._band_word(health)),
            ])
            return clean_name, desc, factors, now

        if clean_name == "Looks":
            desc = "Perceived physical attractiveness."
            factors = ["Inherited Baseline", "Life Events (if applied)"]
            now = "Main drivers now: Inherited baseline (currently static)"
            return clean_name, desc, factors, now

        if clean_name == "Money":
            desc = "Available cash on hand."
            factors = ["Salary/Income", "Purchases", "Medical/School Costs", "Random Events"]
            has_job = bool(getattr(agent, "job", None))
            cash = float(getattr(agent, "money", 0.0))
            now = self._top_driver_labels([
                ("Income Flow", 0.6 if has_job else -0.6, "active" if has_job else "inactive"),
                ("Cash Buffer", (cash - 5000.0) / 5000.0, self._band_word(cash, 500, 5000)),
            ])
            return clean_name, desc, factors, now

        if clean_name == "Fertility":
            desc = "Current reproductive capability."
            factors = ["Age Curve", "Gender Curve", "Genetic Fertility Peak"]
            peak = max(1.0, float(getattr(agent, "_genetic_fertility_peak", 1)))
            ratio = max(0.0, min(1.0, float(value) / peak))
            now = self._top_driver_labels([
                ("Age Phase", ratio - 0.5, self._age_phase_word(age)),
                ("Genetic Fertility Peak", (peak - 50.0) / 50.0, f"peak {int(peak)} ({self._band_word(peak)})"),
            ])
            return clean_name, desc, factors, now

        if clean_name == "Genetic Fertility":
            desc = "Ceiling fertility potential from genetics."
            factors = ["Inherited at Birth"]
            now = "Main drivers now: Genetics only (no live modifiers)"
            return clean_name, desc, factors, now

        if clean_name == "Libido":
            desc = "Current sexual drive intensity."
            factors = ["Age Curve", "Genetic Libido Peak"]
            peak = max(1.0, float(getattr(agent, "_genetic_libido_peak", 1)))
            ratio = max(0.0, min(1.0, float(value) / peak))
            now = self._top_driver_labels([
                ("Age Phase", ratio - 0.5, self._age_phase_word(age)),
                ("Genetic Libido Peak", (peak - 50.0) / 50.0, f"peak {int(peak)} ({self._band_word(peak)})"),
            ])
            return clean_name, desc, factors, now

        if clean_name == "Genetic Libido":
            desc = "Ceiling libido potential from genetics."
            factors = ["Inherited at Birth"]
            now = "Main drivers now: Genetics only (no live modifiers)"
            return clean_name, desc, factors, now

        if clean_name == "IQ":
            desc = "Average of the six cognitive aptitudes."
            factors = ["Aptitude Phenotypes", "Age Development Curves"]
            aptitudes = getattr(agent, "aptitudes", {})
            if aptitudes:
                strongest = sorted(
                    [(k, float(v.get("phenotype", 100.0))) for k, v in aptitudes.items()],
                    key=lambda item: item[1],
                    reverse=True
                )[:2]
                drivers = [
                    (name, (score - 100.0) / 100.0, self._band_word(score, 90, 110))
                    for name, score in strongest
                ]
                now = self._top_driver_labels(drivers)
            else:
                now = "Main drivers now: Aptitude profile (insufficient data)"
            return clean_name, desc, factors, now

        if clean_name in constants.APTITUDES:
            desc = "One cognitive domain in the aptitude model."
            factors = ["Inherited Baseline", "Age Development Curve", "Sleep Penalty (effective value)"]
            base = int(agent.aptitudes.get(clean_name, {}).get("phenotype", value))
            penalty_pct = int(float(getattr(agent, "_temp_cognitive_penalty", 0.0)) * 100)
            now = self._top_driver_labels([
                ("Sleep Quality", -(penalty_pct / 100.0), f"{penalty_pct}% penalty"),
                ("Age Development", (base - 100.0) / 100.0, self._age_phase_word(age)),
            ])
            return clean_name, desc, factors, now

        if clean_name == "Religiousness":
            desc = "Personal inclination toward religion/spirituality."
            factors = ["Inherited Baseline", "Life Events (if applied)"]
            now = "Main drivers now: Inherited baseline (currently static)"
            return clean_name, desc, factors, now

        if traits and clean_name in traits:
            desc = "Big 5 main trait score (sum of six facets)."
            factors = ["Six Facets", "Inherited Baseline", "Life Events (if applied)"]
            trait_facets = list(traits.get(clean_name, {}).items())
            if trait_facets:
                strongest = sorted(trait_facets, key=lambda item: item[1], reverse=True)[:2]
                drivers = [
                    (facet, (float(score) - 10.0) / 10.0, self._band_word(float(score) * 5.0))
                    for facet, score in strongest
                ]
                now = self._top_driver_labels(drivers)
            else:
                now = "Main drivers now: Facet mix (insufficient data)"
            return clean_name, desc, factors, now

        if traits:
            for big5_trait, facets in traits.items():
                if clean_name in facets:
                    desc = f"{big5_trait} facet."
                    factors = ["Inherited Baseline", "Personality Development/Events"]
                    cluster_avg = sum(facets.values()) / max(1, len(facets))
                    now = self._top_driver_labels([
                        ("Facet Baseline", (float(value) - 10.0) / 10.0, self._band_word(float(value) * 5.0)),
                        (f"{big5_trait} Cluster", (float(cluster_avg) - 10.0) / 10.0, self._band_word(float(cluster_avg) * 5.0)),
                    ])
                    return clean_name, desc, factors, now

        if clean_name in [t.replace("_", " ") for t in constants.TEMPERAMENT_TRAITS]:
            desc = "Infant temperament trait."
            factors = ["Inherited Baseline", "Early Childhood Events"]
            now = self._top_driver_labels([
                ("Temperament Baseline", (float(value) - 50.0) / 50.0, self._band_word(float(value))),
                ("Early Events", 0.05, "minor so far"),
            ])
            return clean_name, desc, factors, now

        # Fallback for any unknown card
        desc = "Current simulation attribute."
        factors = ["Attribute-specific game logic", "Age/events where applicable"]
        now = "Main drivers now: Attribute-specific logic"
        return clean_name, desc, factors, now

    def _draw_attribute_tooltips(self, sim_state):
        """Draw hover tooltip for attribute cards in the attributes modal."""
        if not self.viewing_agent or self.viewing_family_tree_agent:
            return
        if not self.attribute_tooltip_zones:
            return

        mx, my = pygame.mouse.get_pos()
        for rect, attr_name, value, max_value in self.attribute_tooltip_zones:
            if not rect.collidepoint((mx, my)):
                continue

            agent = self.viewing_agent
            title, desc, factors, now = self._get_attribute_tooltip_data(agent, attr_name, value, max_value)

            raw_lines = [
                (f"{title}: {int(value) if isinstance(value, (int, float)) else value}", constants.COLOR_ACCENT),
                (desc, constants.COLOR_TEXT),
                ("Affects: " + ", ".join(factors[:5]), constants.COLOR_TEXT_DIM),
                (now, constants.COLOR_TEXT),
            ]

            wrapped = []
            max_line_width = 360
            for i, (text, color) in enumerate(raw_lines):
                if i == 0:
                    wrapped.append((text, color))
                    continue
                for chunk in self._wrap_tooltip_text(text, max_line_width):
                    wrapped.append((chunk, color))

            line_height = 18
            box_w = 0
            surfaces = []
            for text, color in wrapped:
                s = self.font_log.render(text, True, color)
                box_w = max(box_w, s.get_width())
                surfaces.append(s)

            box_w += 20
            box_h = (len(surfaces) * line_height) + 10
            bg_rect = pygame.Rect(mx + 15, my + 15, box_w, box_h)

            if bg_rect.right > self.screen_width:
                bg_rect.x -= box_w + 30
            if bg_rect.bottom > self.screen_height:
                bg_rect.y -= box_h + 30
            if bg_rect.x < 0:
                bg_rect.x = 0
            if bg_rect.y < 0:
                bg_rect.y = 0

            pygame.draw.rect(self.screen, (20, 20, 20), bg_rect)
            pygame.draw.rect(self.screen, constants.COLOR_BORDER, bg_rect, 1)

            curr_y = bg_rect.y + 5
            for s in surfaces:
                self.screen.blit(s, (bg_rect.x + 10, curr_y))
                curr_y += line_height
            break

    def _draw_grade_tooltips(self, sim_state):
        """Draw tooltips for grade hover/click zones."""
        mx, my = pygame.mouse.get_pos()
        
        for rect, subject_name in self.tooltip_zones:
            if rect.collidepoint((mx, my)):
                player = sim_state.player
                if subject_name in player.subjects:
                    subject_data = player.subjects[subject_name]

                    # Build tooltip lines
                    lines = []
                    lines.append((f"{subject_name} Details", constants.COLOR_ACCENT))
                    lines.append((f"Current Grade: {int(subject_data['current_grade'])}", constants.COLOR_TEXT))

                    # Rebuild natural-aptitude formula inputs for full transparency.
                    category = player._classify_subject_category(subject_name)
                    profile = player._get_subject_profile(category)
                    trait_inputs = player._subject_trait_inputs()
                    weights = profile.get("weights", {})

                    raw_sum = 0.0
                    lines.append((f"Natural Aptitude: {int(subject_data['natural_aptitude'])}", constants.COLOR_TEXT))
                    lines.append((f"Category: {category}", constants.COLOR_TEXT_DIM))
                    lines.append(("Aptitude Inputs:", constants.COLOR_TEXT_DIM))

                    label_map = {
                        "analytical": "Analytical",
                        "verbal": "Verbal",
                        "spatial": "Spatial",
                        "working_memory": "Working Memory",
                        "long_term_memory": "Long-term Memory",
                        "secondary_cognitive": "Secondary Cognitive",
                        "competence": "Conscientiousness-Competence",
                        "ideas": "Openness-Ideas",
                        "aesthetics": "Openness-Aesthetics",
                        "values": "Openness-Values",
                        "athleticism": "Athleticism"
                    }

                    for key, weight in weights.items():
                        value = float(trait_inputs.get(key, 50.0))
                        contribution = value * float(weight)
                        raw_sum += contribution
                        label = label_map.get(key, key.replace("_", " ").title())
                        lines.append((
                            f"{label}: {value:.1f} x {float(weight):.2f} = {contribution:.1f}",
                            constants.COLOR_TEXT
                        ))

                    computed_natural = max(0.0, min(100.0, raw_sum))
                    lines.append((f"Raw Sum: {raw_sum:.1f}", constants.COLOR_TEXT_DIM))
                    lines.append((f"Clamped (0-100): {computed_natural:.1f}", constants.COLOR_TEXT_DIM))
                    
                    # Monthly change with color
                    change = subject_data['monthly_change']
                    if change > 0:
                        change_text = f"This Month: +{change}"
                        change_color = constants.COLOR_LOG_POSITIVE
                    elif change < 0:
                        change_text = f"This Month: {change}"
                        change_color = constants.COLOR_LOG_NEGATIVE
                    else:
                        change_text = "This Month: 0"
                        change_color = constants.COLOR_TEXT_DIM
                    
                    lines.append((change_text, change_color))
                    
                    # Calculate box size
                    line_height = 20
                    box_w = 0
                    box_h = len(lines) * line_height + 10
                    
                    surfaces = []
                    for text, color in lines:
                        s = self.font_log.render(text, True, color)
                        box_w = max(box_w, s.get_width())
                        surfaces.append(s)
                    
                    box_w += 20  # Padding
                    
                    # Position tooltip
                    bg_rect = pygame.Rect(mx + 15, my + 15, box_w, box_h)
                    
                    # Keep tooltip on screen
                    if bg_rect.right > self.screen_width:
                        bg_rect.x -= box_w + 30
                    if bg_rect.bottom > self.screen_height:
                        bg_rect.y -= box_h + 30
                    if bg_rect.x < 0:
                        bg_rect.x = 0
                    if bg_rect.y < 0:
                        bg_rect.y = 0
                    
                    # Draw tooltip background and border
                    pygame.draw.rect(self.screen, (20, 20, 20), bg_rect)
                    pygame.draw.rect(self.screen, constants.COLOR_BORDER, bg_rect, 1)
                    
                    # Draw text
                    curr_y = bg_rect.y + 5
                    for s in surfaces:
                        self.screen.blit(s, (bg_rect.x + 10, curr_y))
                        curr_y += line_height
                    
                    break  # Only show one tooltip at a time

    def _adjust_academics_scroll(self, delta):
        """Adjusts academics viewport scroll offset safely."""
        if self.academics_scroll_max <= 0:
            self.academics_scroll_offset = 0
            return
        self.academics_scroll_offset = max(
            0,
            min(self.academics_scroll_max, self.academics_scroll_offset + delta)
        )

    def _draw_right_panel(self, sim_state):
        self._draw_panel_background(self.rect_right, constants.UI_OPACITY_PANEL)
        pygame.draw.rect(self.screen, constants.COLOR_BORDER, self.rect_right, 1)

        # Keep active tab valid when school enrollment changes.
        if self.active_tab == "School" and sim_state and sim_state.player.school is None:
            self.active_tab = "Main"
        
        # Draw Tabs
        for tab in self.tabs:
            # Skip School tab if player is not enrolled in school
            if tab.text == "School" and sim_state and sim_state.player.school is None:
                continue
                
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
            # Draw header outside the scrollable panel
            header_y = current_y + 10
            header_surf = self.font_header.render("Relationships", True, constants.COLOR_ACCENT)
            self.screen.blit(header_surf, (self.rect_right.x + 20, header_y))
            
            # Update relationship panel position and data (below header)
            panel_y = header_y + 30  # 30px space for header
            panel_height = self.rect_right.bottom - panel_y
            
            if panel_height > 100:  # Only show if there's enough space
                self.relationship_panel.update_position(
                    self.rect_right.x + 20, 
                    panel_y, 
                    self.rect_right.width - 40, 
                    panel_height
                )
                
                # Update relationship data
                relationships_data = []
                for uid, rel in sim_state.player.relationships.items():
                    relationships_data.append({'uid': uid, 'rel': rel})
                self.relationship_panel.update_relationships(relationships_data)
                
                # Draw the relationship panel
                self.relationship_panel.draw(self.screen, sim_state)

    def quit(self):
        pygame.quit()
