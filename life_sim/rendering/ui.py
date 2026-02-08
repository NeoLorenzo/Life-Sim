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
    Visualizes the 24-hour Action Point budget.
    Segments: Locked (Red) -> Used (Gray) -> Free (Green) <- Sleep (Blue)
    """
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.segments = 24
        self.seg_w = w / self.segments

    def draw(self, screen, agent):
        # Background
        pygame.draw.rect(screen, (20, 20, 20), self.rect)
        
        # Calculate segment counts
        bio_sleep_segs = int(round(agent.ap_sleep))  # Biological sleep requirement
        target_sleep_segs = int(round(agent.target_sleep_hours))  # User's target sleep
        locked_segs = int(round(agent.ap_locked))  # Total obligation (school/work)
        attended_segs = int(round(agent.ap_locked * agent.attendance_rate))  # Actually attended
        used_segs = int(round(agent.ap_used))  # Used for activities
        
        # Calculate deficits
        sleep_deficit_segs = max(0, bio_sleep_segs - target_sleep_segs)
        truancy_segs = max(0, locked_segs - attended_segs)
        
        # Draw base segments
        for i in range(self.segments):
            seg_rect = pygame.Rect(self.rect.x + (i * self.seg_w), self.rect.y, self.seg_w, self.rect.height)
            
            color = constants.COLOR_LOG_POSITIVE # Default Green (Free)
            
            # Base coloring logic
            # 1. Attended (Left aligned) - Red
            if i < attended_segs:
                color = constants.COLOR_DEATH
            # 2. Used (After Attended) - Gray
            elif i < attended_segs + used_segs:
                color = constants.COLOR_BTN_IDLE
            # 3. Target Sleep (Right aligned) - Blue
            elif i >= self.segments - target_sleep_segs:
                color = (100, 150, 255)
            
            # Draw fill
            pygame.draw.rect(screen, color, seg_rect)
            
            # Draw grid line
            pygame.draw.line(screen, (0, 0, 0), seg_rect.topright, seg_rect.bottomright)
        
        # Draw hatched overlays
        # Sleep Deficit (Hatched Red) - shows biological need not being met
        if sleep_deficit_segs > 0:
            deficit_start = self.segments - bio_sleep_segs
            for i in range(deficit_start, deficit_start + sleep_deficit_segs):
                seg_rect = pygame.Rect(self.rect.x + (i * self.seg_w), self.rect.y, self.seg_w, self.rect.height)
                self._draw_hatched(screen, seg_rect, (200, 50, 50))  # Red hatched
        
        # Truancy (Hatched Green) - shows skipped school/work time
        if truancy_segs > 0:
            truancy_start = attended_segs
            for i in range(truancy_start, truancy_start + truancy_segs):
                seg_rect = pygame.Rect(self.rect.x + (i * self.seg_w), self.rect.y, self.seg_w, self.rect.height)
                self._draw_hatched(screen, seg_rect, (100, 255, 100))  # Green hatched
        
        # Border
        pygame.draw.rect(screen, constants.COLOR_BORDER, self.rect, 1)
        
        # Text Label
        font = pygame.font.SysFont("Arial", 14)
        txt = f"Time: {agent.free_ap:.1f}h Free / {agent.target_sleep_hours:.1f}h Sleep"
        txt_surf = font.render(txt, True, constants.COLOR_TEXT_DIM)
        screen.blit(txt_surf, (self.rect.x, self.rect.y - 18))
    
    def _draw_hatched(self, screen, rect, color):
        """Draw hatched pattern overlay on a rectangle."""
        # Draw diagonal lines for hatched effect
        for i in range(0, rect.width + rect.height, 3):
            start_x = rect.x + max(0, i - rect.height)
            start_y = rect.y + min(i, rect.height)
            end_x = rect.x + min(i, rect.width)
            end_y = rect.y + max(0, i - rect.width)
            pygame.draw.line(screen, color, (start_x, start_y), (end_x, end_y), 1)

class NumberStepper:
    """A numeric input widget with increment/decrement buttons."""
    def __init__(self, x, y, w, h, value, min_val, max_val, step, label_font):
        self.rect = pygame.Rect(x, y, w, h)
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.label_font = label_font
        
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
        """Draw the stepper component."""
        # Draw buttons
        self.minus_btn.draw(screen)
        self.plus_btn.draw(screen)
        
        # Draw value text centered between buttons
        value_text = str(self.value)
        text_surf = self.label_font.render(value_text, True, constants.COLOR_TEXT)
        text_rect = text_surf.get_rect(center=self.text_area.center)
        screen.blit(text_surf, text_rect)