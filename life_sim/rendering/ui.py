# life_sim/rendering/ui.py
"""
UI Widget Module.
Contains classes for Buttons, Panels, and Scrollable elements.
"""
import pygame
from .. import constants

class Button:
    """A clickable button with text."""
    def __init__(self, x, y, w, h, text, action_id, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action_id = action_id # String ID returned when clicked
        self.font = font
        self.is_hovered = False
        
    def handle_event(self, event):
        """Returns action_id if clicked, else None."""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                return self.action_id
        return None

    def draw(self, screen, active_highlight=False):
        if active_highlight:
            color = constants.COLOR_ACCENT
            text_color = constants.COLOR_BG # Dark text on bright background
        elif self.is_hovered:
            color = constants.COLOR_BTN_HOVER
            text_color = constants.COLOR_TEXT
        else:
            color = constants.COLOR_BTN_IDLE
            text_color = constants.COLOR_TEXT
            
        # Draw with rounded corners
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        pygame.draw.rect(screen, constants.COLOR_BORDER, self.rect, 1, border_radius=6)
        
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

class LogPanel:
    """A scrollable text history panel."""
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.scroll_offset = 0 
        self.logs = [] # List of dicts from get_flat_log_for_rendering
        self.total_content_height = 0

    def update_position(self, x, y, w, h):
        """Update the panel's position and size."""
        # Ensure minimum valid dimensions
        w = max(w, 1)
        h = max(h, 1)
        self.rect = pygame.Rect(x, y, w, h)
        # Re-process logs with new width
        if self.logs:
            self.update_logs(self.logs)

    def update_logs(self, logs):
        """
        Processes raw logs into wrapped render lines.
        """
        self.logs = [] # We now render from self.render_lines, but keep this if needed
        self.render_lines = []
        
        # Width available for text (rect width - padding)
        max_width = max(self.rect.width - 20, 1)  # Ensure minimum width
        space_w = self.font.size(' ')[0]
        
        for item in logs:
            # Determine prefix for headers
            prefix = ""
            if item["is_header"]:
                prefix = "[-] " if item["expanded"] else "[+] "
            
            full_text = prefix + item["text"]
            indent = item["indent"]
            
            # Word Wrap Logic
            words = full_text.split(' ')
            current_line = []
            current_w = 0
            
            for word in words:
                word_w = self.font.size(word)[0]
                
                # Check if word fits
                if current_w + word_w <= max_width - indent:
                    current_line.append(word)
                    current_w += word_w + space_w
                else:
                    # Push current line
                    if current_line:
                        self.render_lines.append({
                            **item,
                            "display_text": ' '.join(current_line)
                        })
                    # Start new line with current word
                    current_line = [word]
                    current_w = word_w + space_w
            
            # Push remaining
            if current_line:
                self.render_lines.append({
                    **item,
                    "display_text": ' '.join(current_line)
                })

        self.total_content_height = len(self.render_lines) * constants.LOG_LINE_HEIGHT

    def handle_event(self, event, sim_state):
        """Handles mouse wheel scrolling and clicking."""
        if event.type == pygame.MOUSEWHEEL:
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                self.scroll_offset += event.y * constants.LOG_LINE_HEIGHT
                max_scroll = max(0, self.total_content_height - self.rect.height)
                self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                visible_height = self.rect.height
                if self.total_content_height < visible_height:
                    start_y = self.rect.y + constants.LOG_PADDING_TOP
                else:
                    start_y = self.rect.y + constants.LOG_PADDING_TOP + visible_height - self.total_content_height + self.scroll_offset
                
                click_y = event.pos[1]
                clicked_index = int((click_y - start_y) // constants.LOG_LINE_HEIGHT)
                
                if 0 <= clicked_index < len(self.render_lines):
                    item = self.render_lines[clicked_index]
                    if item["is_header"]:
                        sim_state.toggle_year(item["index"])

    def draw(self, screen):
        # Draw transparent background
        s = pygame.Surface((self.rect.width, self.rect.height))
        s.set_alpha(constants.UI_OPACITY_CENTER)
        s.fill((20, 20, 20))  # Dark grey background
        screen.blit(s, (self.rect.x, self.rect.y))
        
        old_clip = screen.get_clip()
        screen.set_clip(self.rect)
        
        visible_height = self.rect.height
        if self.total_content_height < visible_height:
            start_y = self.rect.y + constants.LOG_PADDING_TOP
        else:
            start_y = self.rect.y + constants.LOG_PADDING_TOP + visible_height - self.total_content_height + self.scroll_offset

        y = start_y
        for item in self.render_lines:
            if y + constants.LOG_LINE_HEIGHT > self.rect.y and y < self.rect.bottom:
                # Render the pre-wrapped text
                text_surf = self.font.render(item["display_text"], True, item["color"])
                screen.blit(text_surf, (self.rect.x + 10 + item["indent"], y))
            y += constants.LOG_LINE_HEIGHT
            
        screen.set_clip(old_clip)
        pygame.draw.rect(screen, constants.COLOR_BORDER, self.rect, 1)

class APBar:
    """
    Visualizes the 24-hour Action Point budget with enhanced visuals.
    Can be oriented horizontally or vertically.
    Segments: Locked (Red) -> Used (Gray) -> Free (Green) <- Sleep (Blue)
    """
    def __init__(self, x, y, w, h, vertical=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.vertical = vertical
        self.segments = 48  # 24 hours * 2 for half-hour steps
        if vertical:
            self.seg_h = h / self.segments  # Height of each segment
            self.seg_w = w
        else:
            self.seg_w = w / self.segments
            self.seg_h = h
        self.border_radius = 8
        self.segment_padding = 2

    def draw(self, screen, agent):
        # Draw background with rounded corners
        pygame.draw.rect(screen, (15, 15, 15), self.rect, border_radius=self.border_radius)
        
        # Create inner content area with padding
        inner_rect = pygame.Rect(
            self.rect.x + self.segment_padding,
            self.rect.y + self.segment_padding,
            self.rect.width - (self.segment_padding * 2),
            self.rect.height - (self.segment_padding * 2)
        )
        
        # Draw inner background
        pygame.draw.rect(screen, (25, 25, 25), inner_rect, border_radius=self.border_radius - 2)
        
        # Calculate segment counts (convert to half-hour segments)
        bio_sleep_segs = int(round(agent.ap_sleep * 2))  # Convert to half-hours
        target_sleep_segs = int(round(agent.target_sleep_hours * 2))
        locked_segs = int(round(agent.ap_locked * 2))
        attended_segs = int(round(agent.ap_locked * agent.attendance_rate * 2))
        used_segs = int(round(agent.ap_used * 2))
        
        # Calculate deficits
        sleep_deficit_segs = max(0, bio_sleep_segs - target_sleep_segs)
        truancy_segs = max(0, locked_segs - attended_segs)
        
        # Enhanced color palette
        colors = {
            'attended': (220, 80, 80),      # Softer red
            'used': (100, 100, 120),        # Muted gray-blue
            'free': (80, 180, 80),          # Softer green
            'sleep': (100, 140, 220),       # Softer blue
            'sleep_deficit': (200, 60, 60), # Brighter red for deficit
            'truancy': (120, 200, 120)      # Brighter green for truancy
        }
        
        if self.vertical:
            # Draw vertical segments (top to bottom = morning to night)
            for i in range(self.segments):
                seg_y = inner_rect.y + (i * self.seg_h)
                seg_rect = pygame.Rect(inner_rect.x, seg_y, inner_rect.width, self.seg_h - 1)
                
                # Determine base color (0 = top/morning, 47 = bottom/night)
                if i < attended_segs:
                    base_color = colors['attended']
                elif i < attended_segs + used_segs:
                    base_color = colors['used']
                elif i >= self.segments - target_sleep_segs:
                    base_color = colors['sleep']
                else:
                    base_color = colors['free']
                
                # Draw segment with gradient effect (left lighter, right darker for vertical)
                left_color = tuple(min(255, c + 30) for c in base_color)
                right_color = tuple(max(0, c - 20) for c in base_color)
                
                # Draw gradient manually
                gradient_steps = 3  # Fewer steps for narrow width
                for step in range(gradient_steps):
                    step_ratio = step / gradient_steps
                    interp_color = tuple(
                        int(left_color[j] * (1 - step_ratio) + right_color[j] * step_ratio)
                        for j in range(3)
                    )
                    step_rect = pygame.Rect(
                        seg_rect.x + (seg_rect.width * step // gradient_steps),
                        seg_rect.y,
                        seg_rect.width // gradient_steps + 1,
                        seg_rect.height
                    )
                    pygame.draw.rect(screen, interp_color, step_rect)
                
                # Add subtle highlight on left edge
                highlight_rect = pygame.Rect(seg_rect.x, seg_rect.y, 2, seg_rect.height)
                pygame.draw.rect(screen, tuple(min(255, c + 50) for c in base_color), highlight_rect)
            
            # Draw hatched overlays for vertical orientation
            if sleep_deficit_segs > 0:
                deficit_start = self.segments - bio_sleep_segs
                for i in range(deficit_start, deficit_start + sleep_deficit_segs):
                    seg_y = inner_rect.y + (i * self.seg_h)
                    seg_rect = pygame.Rect(inner_rect.x, seg_y, inner_rect.width, self.seg_h - 1)
                    self._draw_enhanced_hatch_vertical(screen, seg_rect, colors['sleep_deficit'])
            
            if truancy_segs > 0:
                truancy_start = attended_segs
                for i in range(truancy_start, truancy_start + truancy_segs):
                    seg_y = inner_rect.y + (i * self.seg_h)
                    seg_rect = pygame.Rect(inner_rect.x, seg_y, inner_rect.width, self.seg_h - 1)
                    self._draw_enhanced_hatch_vertical(screen, seg_rect, colors['truancy'])
            
            # Draw time markers for vertical orientation (right side)
            marker_font = pygame.font.SysFont("Arial", 8)
            for marker in range(0, 49):  # 0 to 48 half-hour segments
                marker_y = inner_rect.y + (marker * self.seg_h)
                if marker_y <= inner_rect.bottom:
                    is_hour = marker % 2 == 0  # Even numbers are full hours
                    hour_num = marker // 2
                    
                    if is_hour:
                        # Draw stronger horizontal marker for full hours
                        pygame.draw.line(screen, (80, 80, 80), 
                                       (inner_rect.right - 8, marker_y), 
                                       (inner_rect.right, marker_y), 2)
                        # Draw hour label for full hours
                        if hour_num <= 24 and hour_num % 6 == 0:  # Show every 6 hours
                            hour_text = f"{hour_num}h"
                            hour_surf = marker_font.render(hour_text, True, (140, 140, 140))
                            hour_rect = hour_surf.get_rect(midleft=(inner_rect.right + 2, marker_y))
                            screen.blit(hour_surf, hour_rect)
                    else:
                        # Draw subtle marker for half-hours
                        pygame.draw.line(screen, (50, 50, 50), 
                                       (inner_rect.right - 4, marker_y), 
                                       (inner_rect.right, marker_y), 1)
            
            # No text for vertical AP bar
            
        else:
            # Original horizontal drawing logic
            for i in range(self.segments):
                seg_x = inner_rect.x + (i * self.seg_w)
                seg_rect = pygame.Rect(seg_x, inner_rect.y, self.seg_w - 1, inner_rect.height)
                
                # Determine base color
                if i < attended_segs:
                    base_color = colors['attended']
                elif i < attended_segs + used_segs:
                    base_color = colors['used']
                elif i >= self.segments - target_sleep_segs:
                    base_color = colors['sleep']
                else:
                    base_color = colors['free']
                
                # Draw segment with gradient effect (top lighter, bottom darker)
                top_color = tuple(min(255, c + 30) for c in base_color)
                bottom_color = tuple(max(0, c - 20) for c in base_color)
                
                # Draw gradient manually
                gradient_steps = 5
                for step in range(gradient_steps):
                    step_ratio = step / gradient_steps
                    interp_color = tuple(
                        int(top_color[j] * (1 - step_ratio) + bottom_color[j] * step_ratio)
                        for j in range(3)
                    )
                    step_rect = pygame.Rect(
                        seg_rect.x,
                        seg_rect.y + (seg_rect.height * step // gradient_steps),
                        seg_rect.width,
                        seg_rect.height // gradient_steps + 1
                    )
                    pygame.draw.rect(screen, interp_color, step_rect)
                
                # Add subtle highlight on top edge
                highlight_rect = pygame.Rect(seg_rect.x, seg_rect.y, seg_rect.width, 2)
                pygame.draw.rect(screen, tuple(min(255, c + 50) for c in base_color), highlight_rect)
            
            # Draw hatched overlays with enhanced patterns
            if sleep_deficit_segs > 0:
                deficit_start = self.segments - bio_sleep_segs
                for i in range(deficit_start, deficit_start + sleep_deficit_segs):
                    seg_x = inner_rect.x + (i * self.seg_w)
                    seg_rect = pygame.Rect(seg_x, inner_rect.y, self.seg_w - 1, inner_rect.height)
                    self._draw_enhanced_hatch(screen, seg_rect, colors['sleep_deficit'])
            
            if truancy_segs > 0:
                truancy_start = attended_segs
                for i in range(truancy_start, truancy_start + truancy_segs):
                    seg_x = inner_rect.x + (i * self.seg_w)
                    seg_rect = pygame.Rect(seg_x, inner_rect.y, self.seg_w - 1, inner_rect.height)
                    self._draw_enhanced_hatch(screen, seg_rect, colors['truancy'])
            
            # Draw time markers (hour and half-hour intervals)
            marker_font = pygame.font.SysFont("Arial", 10)
            for marker in range(0, 49):  # 0 to 48 half-hour segments
                marker_x = inner_rect.x + (marker * self.seg_w)
                if marker_x <= inner_rect.right:
                    is_hour = marker % 2 == 0  # Even numbers are full hours
                    hour_num = marker // 2
                    
                    if is_hour:
                        # Draw stronger vertical marker for full hours
                        pygame.draw.line(screen, (80, 80, 80), 
                                       (marker_x, inner_rect.bottom - 8), 
                                       (marker_x, inner_rect.bottom), 2)
                        # Draw hour label for full hours
                        if hour_num <= 24:
                            hour_text = f"{hour_num}h"
                            hour_surf = marker_font.render(hour_text, True, (140, 140, 140))
                            hour_rect = hour_surf.get_rect(center=(marker_x, inner_rect.bottom + 10))
                            screen.blit(hour_surf, hour_rect)
                    else:
                        # Draw subtle marker for half-hours
                        pygame.draw.line(screen, (50, 50, 50), 
                                       (marker_x, inner_rect.bottom - 4), 
                                       (marker_x, inner_rect.bottom), 1)
            
            # Enhanced text with shadow effect
            font = pygame.font.SysFont("Arial", 14, bold=True)
            txt = f" Time: {agent.free_ap:.1f}h Free / {agent.target_sleep_hours:.1f}h Sleep"
            
            # Draw shadow
            shadow_surf = font.render(txt, True, (10, 10, 10))
            screen.blit(shadow_surf, (self.rect.x + 1, self.rect.y - 17))
            
            # Draw main text
            txt_surf = font.render(txt, True, (200, 200, 200))
            screen.blit(txt_surf, (self.rect.x, self.rect.y - 18))
        
        # Draw border with rounded corners
        pygame.draw.rect(screen, (80, 80, 80), self.rect, 2, border_radius=self.border_radius)
        
        # Draw inner border for depth
        pygame.draw.rect(screen, (40, 40, 40), inner_rect, 1, border_radius=self.border_radius - 2)

    def _draw_enhanced_hatch_vertical(self, screen, rect, color):
        """Draw enhanced hatched pattern overlay for vertical segments."""
        # Create a surface for the hatched pattern
        hatch_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Draw horizontal lines for vertical hatching effect
        spacing = 3
        for i in range(0, rect.height, spacing):
            # Draw with alpha for better blending
            pygame.draw.line(hatch_surface, (*color, 160), 
                           (0, i), (rect.width, i), 1)
        
        # Blit the hatched surface onto the screen
        screen.blit(hatch_surface, rect.topleft)
    
    def _draw_enhanced_hatch(self, screen, rect, color):
        """Draw enhanced hatched pattern overlay on a rectangle."""
        # Create a surface for the hatched pattern
        hatch_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Draw diagonal lines with better spacing and thickness
        spacing = 4
        for i in range(-rect.height, rect.width, spacing):
            start_x = max(0, i)
            start_y = max(0, -i)
            end_x = min(rect.width, i + rect.height)
            end_y = min(rect.height, i + rect.width)
            
            # Draw with alpha for better blending
            pygame.draw.line(hatch_surface, (*color, 180), 
                           (start_x, start_y), (end_x, end_y), 2)
        
        # Blit the hatched surface onto the screen
        screen.blit(hatch_surface, rect.topleft)
    
    def _draw_hatched(self, screen, rect, color):
        """Draw hatched pattern overlay on a rectangle (legacy method)."""
        # Draw diagonal lines for hatched effect
        for i in range(0, rect.width + rect.height, 3):
            start_x = rect.x + max(0, i - rect.height)
            start_y = rect.y + min(i, rect.height)
            end_x = rect.x + min(i, rect.width)
            end_y = rect.y + max(0, i - rect.width)
            pygame.draw.line(screen, color, (start_x, start_y), (end_x, end_y), 1)

class NumberStepper:
    """A numeric input widget with increment/decrement buttons."""
    def __init__(self, x, y, w, h, value, min_val, max_val, step, label_font, label="Value"):
        self.rect = pygame.Rect(x, y, w, h)
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.label_font = label_font
        self.label = label  # Store the label text
        
        # Create buttons for [-] and [+]
        button_w = h  # Square buttons
        button_h = h
        
        self.minus_btn = Button(x, y, button_w, button_h, "-", "STEPPER_MINUS", label_font)
        self.plus_btn = Button(x + w - button_w, y, button_w, button_h, "+", "STEPPER_PLUS", label_font)
        
        # Calculate text display area (between buttons)
        self.text_area = pygame.Rect(x + button_w, y, w - (button_w * 2), h)
        
    def handle_event(self, event):
        """Handle button clicks and return step changes."""
        # Handle button hover states
        self.minus_btn.handle_event(event)
        self.plus_btn.handle_event(event)
        
        # Check for button clicks
        result = self.minus_btn.handle_event(event)
        if result == "STEPPER_MINUS":
            self.value = max(self.min_val, self.value - self.step)
            return ("STEP_CHANGE", self.value)
            
        result = self.plus_btn.handle_event(event)
        if result == "STEPPER_PLUS":
            self.value = min(self.max_val, self.value + self.step)
            return ("STEP_CHANGE", self.value)
            
        return None
        
    def draw(self, screen):
        """Draw stepper component with integrated label."""
        # Calculate total height including label
        total_height = self.rect.height + 30  # 30 pixels for label
        total_rect = pygame.Rect(self.rect.x, self.rect.y - 30, self.rect.width, total_height)
        
        # Draw background for entire component
        pygame.draw.rect(screen, (40, 40, 40), total_rect, border_radius=4)
        
        # Draw label text at top
        label_surf = self.label_font.render(self.label, True, (200, 200, 200))
        label_rect = label_surf.get_rect(centerx=total_rect.centerx, top=total_rect.y + 5)
        screen.blit(label_surf, label_rect)
        
        # Draw buttons
        self.minus_btn.draw(screen)
        self.plus_btn.draw(screen)
        
        # Draw text display area
        text_rect = pygame.Rect(self.text_area.x + 2, self.text_area.y + 2, 
                               self.text_area.width - 4, self.text_area.height - 4)
        pygame.draw.rect(screen, (60, 60, 60), text_rect, border_radius=2)
        
        # Draw value text
        value_text = f"{self.value:.2f}"
        value_surf = self.label_font.render(value_text, True, (220, 220, 220))
        value_rect = value_surf.get_rect(center=self.text_area.center)
        screen.blit(value_surf, value_rect)
        
        # Draw border around entire component
        pygame.draw.rect(screen, (80, 80, 80), total_rect, 2, border_radius=4)

class RelationshipPanel:
    """A scrollable panel for displaying relationship cards."""
    def __init__(self, x, y, w, h, font_main, font_log):
        self.rect = pygame.Rect(x, y, w, h)
        self.font_main = font_main
        self.font_log = font_log
        self.scroll_offset = 0 
        self.relationships = []  # List of relationship data
        self.total_content_height = 0
        self.card_height = 90
        self.card_gap = 10
        
        # Scrollbar state
        self.scrollbar_width = 12
        self.scrollbar_color = (100, 100, 100)
        self.scrollbar_hover_color = (120, 120, 120)
        self.scrollbar_dragging = False
        self.scrollbar_drag_start_y = 0
        self.scrollbar_drag_start_offset = 0
        
    def update_position(self, x, y, w, h):
        """Update the panel's position and size."""
        w = max(w, 1)
        h = max(h, 1)
        self.rect = pygame.Rect(x, y, w, h)
        # Recalculate content height
        if self.relationships:
            self.total_content_height = len(self.relationships) * (self.card_height + self.card_gap)
    
    def update_relationships(self, relationships):
        """Update the relationships data and recalculate content height."""
        # Sort relationships by total_score (highest first)
        self.relationships = sorted(relationships, key=lambda x: x['rel'].total_score, reverse=True)
        # Reset scroll offset if content is shorter than panel
        if self.total_content_height < self.rect.height:
            self.scroll_offset = 0
    
    def handle_event(self, event, sim_state):
        """Handles mouse wheel scrolling, scrollbar dragging, and button clicks."""
        if event.type == pygame.MOUSEWHEEL:
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                # Inverted scroll: negative wheel scrolls down, positive scrolls up
                self.scroll_offset -= event.y * 30  # Inverted direction
                max_scroll = max(0, self.total_content_height - self.rect.height)
                self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check for scrollbar interaction
                if self.total_content_height > self.rect.height:
                    scrollbar_rect = self._get_scrollbar_rect()
                    if scrollbar_rect.collidepoint(event.pos):
                        # Start dragging scrollbar
                        self.scrollbar_dragging = True
                        self.scrollbar_drag_start_y = event.pos[1]
                        self.scrollbar_drag_start_offset = self.scroll_offset
                        return None
                
                # Check for card button clicks
                if self.rect.collidepoint(event.pos):
                    # Calculate which relationship card was clicked
                    click_y = event.pos[1]
                    padding_top = 15
                    start_y = self.rect.y + padding_top - self.scroll_offset
                    
                    for i, rel_data in enumerate(self.relationships):
                        card_y = start_y + i * (self.card_height + self.card_gap)
                        card_bottom = card_y + self.card_height
                        
                        if card_y <= click_y <= card_bottom:
                            # Check if buttons were clicked
                            x = self.rect.x + 20
                            w = self.rect.width - 40
                            btn_y = card_y + 50
                            btn_w = (w - 10) // 2
                            btn_h = 30
                            
                            # Attributes Button
                            rect_attr = pygame.Rect(x + 5, btn_y, btn_w, btn_h)
                            # Interact Button  
                            rect_int = pygame.Rect(x + 5 + btn_w + 5, btn_y, btn_w, btn_h)
                            
                            if rect_attr.collidepoint(event.pos):
                                # Ensure the NPC exists before trying to view
                                if rel_data['uid'] in sim_state.npcs:
                                    return ("VIEW_AGENT", sim_state.npcs[rel_data['uid']])
                            elif rect_int.collidepoint(event.pos):
                                return ("INTERACT", rel_data['uid'])
                            break
                            
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left click release
                # Stop scrollbar dragging
                self.scrollbar_dragging = False
                
        elif event.type == pygame.MOUSEMOTION:
            # Handle scrollbar dragging
            if self.scrollbar_dragging:
                self._handle_scrollbar_drag(event.pos[1])
                
        return None
    
    def draw(self, screen, sim_state):
        """Draw the scrollable relationship panel."""
        # Draw background
        s = pygame.Surface((self.rect.width, self.rect.height))
        s.set_alpha(200)  # Same as UI_OPACITY_CENTER
        s.fill((20, 20, 20))
        screen.blit(s, (self.rect.x, self.rect.y))
        
        # Clip drawing to panel bounds
        old_clip = screen.get_clip()
        screen.set_clip(self.rect)
        
        # Calculate starting Y position for cards with 15px padding
        padding_top = 15
        start_y = self.rect.y + padding_top - self.scroll_offset
        
        # Draw relationship cards
        x = self.rect.x + 20
        w = self.rect.width - 40
        
        for i, rel_data in enumerate(self.relationships):
            card_y = start_y + i * (self.card_height + self.card_gap)
            
            # Skip cards outside visible area
            if card_y + self.card_height < self.rect.y or card_y > self.rect.bottom:
                continue
            
            # Draw card background
            rect = pygame.Rect(x, card_y, w, self.card_height)
            pygame.draw.rect(screen, (60, 60, 60), rect, border_radius=4)
            pygame.draw.rect(screen, (80, 80, 80), rect, 1, border_radius=4)
            
            # Extract relationship data
            uid = rel_data['uid']
            rel = rel_data['rel']
            
            # Name & Status
            name_color = (200, 200, 200)  # COLOR_TEXT
            status_text = rel.rel_type
            
            if not rel.is_alive:
                name_color = (120, 120, 120)  # COLOR_TEXT_DIM
                status_text += " (Deceased)"
            
            name_surf = self.font_main.render(rel.target_name, True, name_color)
            type_surf = self.font_log.render(status_text, True, (120, 120, 120))
            
            screen.blit(name_surf, (x + 10, card_y + 5))
            
            # FT Button for NPC
            if uid in sim_state.npcs:
                npc_agent = sim_state.npcs[uid]
                ft_rect = pygame.Rect(x + 10 + name_surf.get_width() + 10, card_y + 5, 30, 20)
                self._draw_ft_button(screen, ft_rect, npc_agent)

            screen.blit(type_surf, (x + 10, card_y + 25))
            
            # Relationship Bar
            if rel.is_alive:
                # Define Bar Area
                bar_w = 100
                bar_h = 10
                bar_x = x + w - bar_w - 10
                bar_y = card_y + 10
                
                bar_bg = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
                pygame.draw.rect(screen, (30, 30, 30), bar_bg)
                
                # Draw Center Line
                center_x = bar_bg.centerx
                pygame.draw.line(screen, (80, 80, 80), (center_x, bar_y), (center_x, bar_y + bar_h))
                
                val = rel.total_score
                # Clamp for rendering safety
                val = max(-100, min(100, val))
                
                if val > 0:
                    # Draw Green to Right
                    pct = val / 100.0
                    fill_w = (bar_w / 2) * pct
                    fill_rect = pygame.Rect(center_x, bar_y, fill_w, bar_h)
                    
                    # Color Intensity
                    if val > 80: 
                        col = (100, 255, 100)  # COLOR_REL_BEST
                    else: 
                        col = (150, 255, 150)  # COLOR_REL_FRIEND
                    
                    pygame.draw.rect(screen, col, fill_rect)
                    
                elif val < 0:
                    # Draw Red to Left
                    pct = abs(val) / 100.0
                    fill_w = (bar_w / 2) * pct
                    fill_rect = pygame.Rect(center_x - fill_w, bar_y, fill_w, bar_h)
                    
                    # Color Intensity
                    if val < -50: 
                        col = (255, 100, 100)  # COLOR_REL_ENEMY
                    else: 
                        col = (255, 150, 150)  # COLOR_REL_DISLIKE
                    
                    pygame.draw.rect(screen, col, fill_rect)

                # Buttons
                btn_y = card_y + 50
                btn_w = (w - 10) // 2
                btn_h = 30
                
                # Draw "Attributes" Button
                attr_rect = pygame.Rect(x + 5, btn_y, btn_w, btn_h)
                pygame.draw.rect(screen, (40, 40, 40), attr_rect, border_radius=4)
                pygame.draw.rect(screen, (80, 80, 80), attr_rect, 1, border_radius=4)
                attr_txt = self.font_log.render("Attributes", True, (200, 200, 200))
                attr_txt_rect = attr_txt.get_rect(center=attr_rect.center)
                screen.blit(attr_txt, attr_txt_rect)

                # Draw "Interact" Button
                int_rect = pygame.Rect(x + 5 + btn_w + 5, btn_y, btn_w, btn_h)
                pygame.draw.rect(screen, (40, 40, 40), int_rect, border_radius=4)
                pygame.draw.rect(screen, (80, 80, 80), int_rect, 1, border_radius=4)
                int_txt = self.font_log.render("Interact", True, (200, 200, 200))
                int_txt_rect = int_txt.get_rect(center=int_rect.center)
                screen.blit(int_txt, int_txt_rect)
        
        # Restore clip and draw border
        screen.set_clip(old_clip)
        pygame.draw.rect(screen, (80, 80, 80), self.rect, 1)
        
        # Draw scrollbar if content is scrollable
        if self.total_content_height > self.rect.height:
            self._draw_scrollbar(screen)
    
    def get_hover_info(self, mouse_pos, sim_state):
        """Get relationship information for tooltip display."""
        if not self.rect.collidepoint(mouse_pos):
            return None
            
        # Calculate which relationship card is being hovered
        mouse_y = mouse_pos[1]
        padding_top = 15
        start_y = self.rect.y + padding_top - self.scroll_offset
        
        for i, rel_data in enumerate(self.relationships):
            card_y = start_y + i * (self.card_height + self.card_gap)
            card_bottom = card_y + self.card_height
            
            if card_y <= mouse_y <= card_bottom:
                # Found the hovered card
                uid = rel_data['uid']
                rel = rel_data['rel']
                
                # Get agent information
                if uid in sim_state.npcs:
                    agent = sim_state.npcs[uid]
                    
                    # Get affinity breakdown like the social graph does
                    from ..simulation import affinity
                    score, affinity_breakdown = affinity.get_affinity_breakdown(sim_state.player, agent)
                    
                    return {
                        'name': agent.first_name,
                        'age': agent.age,
                        'job': agent.job,
                        'rel_type': rel.rel_type,
                        'rel_val': rel.total_score,
                        'is_alive': rel.is_alive,
                        'total_score': rel.total_score,
                        'base_score': rel.base_affinity,
                        'affinity_breakdown': affinity_breakdown,  # Use calculated breakdown
                        'modifiers': [(mod.name, mod.value) for mod in rel.modifiers]
                    }
                break
        
        return None

    def draw_tooltip(self, screen, mouse_pos, sim_state):
        """Draw tooltip for hovered relationship card."""
        info = self.get_hover_info(mouse_pos, sim_state)
        if not info:
            return
            
        lines = []
        
        # Header with name and age
        age_text = f"{info['age']}" if info['is_alive'] else f"{info['age']} (Deceased)"
        lines.append((f"{info['name']} ({age_text})", (100, 200, 255)))  # COLOR_ACCENT
        lines.append((info['job'], (120, 120, 120)))  # COLOR_TEXT_DIM
        
        if info['rel_type'] != "Self":
            # Relationship score with color coding
            rel_txt = f"{info['rel_type']}: {info['rel_val']}/100"
            col = self._get_relationship_color(info['rel_val'])
            lines.append((rel_txt, col))
            
            # Detailed breakdown
            lines.append(("--- Base Affinity ---", (120, 120, 120)))  # COLOR_TEXT_DIM
            base_col = self._get_relationship_color(info['base_score'])
            lines.append((f"Base: {info['base_score']:+.1f}", base_col))
            
            # Show affinity breakdown factors (like social graph)
            for factor, val in info['affinity_breakdown']:
                col = self._get_relationship_color(val)
                lines.append((f"  {factor}: {val:+.1f}", col))

            # Active modifiers
            if info['modifiers']:
                lines.append(("--- Active Modifiers ---", (120, 120, 120)))  # COLOR_TEXT_DIM
                for mod_name, mod_val in info['modifiers']:
                    col = self._get_relationship_color(mod_val)
                    lines.append((f"  {mod_name}: {mod_val:+.1f}", col))
        
        # Calculate tooltip box size
        mx, my = mouse_pos
        line_height = 20
        box_w = 0
        box_h = len(lines) * line_height + 10
        
        surfaces = []
        for text, color in lines:
            # Ensure text is a string
            if not isinstance(text, str):
                text = str(text)
            s = self.font_log.render(text, True, color)
            box_w = max(box_w, s.get_width())
            surfaces.append(s)
        
        box_w += 20  # Padding
        
        # Position tooltip
        bg_rect = pygame.Rect(mx + 15, my + 15, box_w, box_h)
        
        # Keep tooltip on screen
        if bg_rect.right > screen.get_width():
            bg_rect.x -= box_w + 30
        if bg_rect.bottom > screen.get_height():
            bg_rect.y -= box_h + 30
            
        # Draw tooltip background and border
        pygame.draw.rect(screen, (20, 20, 20), bg_rect)
        pygame.draw.rect(screen, (80, 80, 80), bg_rect, 1)
        
        # Draw text
        curr_y = bg_rect.y + 5
        for s in surfaces:
            screen.blit(s, (bg_rect.x + 10, curr_y))
            curr_y += line_height

    def _get_relationship_color(self, score):
        """Get color based on relationship score (same as social graph)."""
        if score > 80:
            return (100, 255, 100)  # COLOR_REL_BEST
        elif score > 0:
            return (150, 255, 150)  # COLOR_REL_FRIEND
        elif score > -50:
            return (255, 150, 150)  # COLOR_REL_DISLIKE
        else:
            return (255, 100, 100)  # COLOR_REL_ENEMY

    def _draw_ft_button(self, screen, rect, agent):
        """Draw a small family tree button."""
        # Simple FT button - just draw "FT" text for now
        ft_surf = self.font_log.render("FT", True, (150, 150, 255))
        ft_rect = ft_surf.get_rect(center=rect.center)
        screen.blit(ft_surf, ft_rect)

    def _get_scrollbar_rect(self):
        """Get the scrollbar handle rectangle."""
        if self.total_content_height <= self.rect.height:
            return None
            
        # Calculate scrollbar position and size
        scrollbar_x = self.rect.right - self.scrollbar_width - 2
        scrollbar_y = self.rect.y + 2
        scrollbar_height = self.rect.height - 4
        
        # Calculate handle height (minimum 20px)
        max_scroll = max(0, self.total_content_height - self.rect.height)
        if max_scroll > 0:
            handle_height = max(20, int((self.rect.height / self.total_content_height) * scrollbar_height))
        else:
            handle_height = scrollbar_height
            
        # Calculate handle position
        if max_scroll > 0:
            handle_y = scrollbar_y + int((self.scroll_offset / max_scroll) * (scrollbar_height - handle_height))
        else:
            handle_y = scrollbar_y
            
        return pygame.Rect(scrollbar_x, handle_y, self.scrollbar_width, handle_height)
    
    def _draw_scrollbar(self, screen):
        """Draw the scrollbar."""
        if self.total_content_height <= self.rect.height:
            return
            
        # Draw scrollbar track
        scrollbar_x = self.rect.right - self.scrollbar_width - 2
        scrollbar_y = self.rect.y + 2
        scrollbar_height = self.rect.height - 4
        
        # Draw track background
        track_rect = pygame.Rect(scrollbar_x, scrollbar_y, self.scrollbar_width, scrollbar_height)
        pygame.draw.rect(screen, (40, 40, 40), track_rect, border_radius=6)

        # Draw handle
        handle_rect = self._get_scrollbar_rect()
        if handle_rect:
            # Change color if hovering or dragging
            mouse_pos = pygame.mouse.get_pos()
            color = self.scrollbar_hover_color if (handle_rect.collidepoint(mouse_pos) or self.scrollbar_dragging) else self.scrollbar_color
            pygame.draw.rect(screen, color, handle_rect, border_radius=6)

    def _handle_scrollbar_drag(self, mouse_y):
        """Handle scrollbar dragging."""
        if self.total_content_height <= self.rect.height:
            return
            
        # Calculate new scroll offset based on mouse position
        scrollbar_y = self.rect.y + 2
        scrollbar_height = self.rect.height - 4
        max_scroll = max(0, self.total_content_height - self.rect.height)
        
        if max_scroll > 0:
            # Calculate handle height
            handle_height = max(20, int((self.rect.height / self.total_content_height) * scrollbar_height))
            
            # Calculate the ratio of mouse movement to scroll movement
            mouse_delta = mouse_y - self.scrollbar_drag_start_y
            scroll_ratio = mouse_delta / (scrollbar_height - handle_height)
            new_offset = self.scrollbar_drag_start_offset + (scroll_ratio * max_scroll)
            
            # Clamp to valid range
            self.scroll_offset = max(0, min(max_scroll, new_offset))