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
        self.logs = logs
        self.total_content_height = len(logs) * constants.LOG_LINE_HEIGHT

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
                # Calculate which line was clicked
                # We need to reverse-engineer the Y position logic from draw()
                # This is tricky because draw() calculates start_y dynamically.
                # Let's recalculate start_y here.
                
                visible_height = self.rect.height
                if self.total_content_height < visible_height:
                    start_y = self.rect.y
                else:
                    start_y = self.rect.y + visible_height - self.total_content_height + self.scroll_offset
                
                # Relative Y click
                click_y = event.pos[1]
                
                # Find the index
                # line_y = start_y + (index * height)
                # index = (click_y - start_y) // height
                
                clicked_index = int((click_y - start_y) // constants.LOG_LINE_HEIGHT)
                
                if 0 <= clicked_index < len(self.logs):
                    item = self.logs[clicked_index]
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
        for item in self.logs:
            if y + constants.LOG_LINE_HEIGHT > self.rect.y and y < self.rect.bottom:
                # Draw expand/collapse indicator for headers
                prefix = ""
                if item["is_header"]:
                    prefix = "[-] " if item["expanded"] else "[+] "
                
                text_surf = self.font.render(prefix + item["text"], True, item["color"])
                screen.blit(text_surf, (self.rect.x + 10 + item["indent"], y))
            y += constants.LOG_LINE_HEIGHT
            
        screen.set_clip(old_clip)
        pygame.draw.rect(screen, constants.COLOR_BORDER, self.rect, 1)