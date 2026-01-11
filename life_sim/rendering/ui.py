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
            
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, constants.COLOR_BORDER, self.rect, 1)
        
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

    def update_logs(self, logs):
        """
        Processes raw logs into wrapped render lines.
        """
        self.logs = [] # We now render from self.render_lines, but keep this if needed
        self.render_lines = []
        
        # Width available for text (rect width - padding)
        max_width = self.rect.width - 20
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
                    start_y = self.rect.y
                else:
                    start_y = self.rect.y + visible_height - self.total_content_height + self.scroll_offset
                
                click_y = event.pos[1]
                clicked_index = int((click_y - start_y) // constants.LOG_LINE_HEIGHT)
                
                if 0 <= clicked_index < len(self.render_lines):
                    item = self.render_lines[clicked_index]
                    if item["is_header"]:
                        sim_state.toggle_year(item["index"])

    def draw(self, screen):
        pygame.draw.rect(screen, constants.COLOR_LOG_BG, self.rect)
        old_clip = screen.get_clip()
        screen.set_clip(self.rect)
        
        visible_height = self.rect.height
        if self.total_content_height < visible_height:
            start_y = self.rect.y
        else:
            start_y = self.rect.y + visible_height - self.total_content_height + self.scroll_offset

        y = start_y
        for item in self.render_lines:
            if y + constants.LOG_LINE_HEIGHT > self.rect.y and y < self.rect.bottom:
                # Render the pre-wrapped text
                text_surf = self.font.render(item["display_text"], True, item["color"])
                screen.blit(text_surf, (self.rect.x + 10 + item["indent"], y))
            y += constants.LOG_LINE_HEIGHT
            
        screen.set_clip(old_clip)
        pygame.draw.rect(screen, constants.COLOR_BORDER, self.rect, 1)