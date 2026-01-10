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
        self.scroll_offset = 0 # 0 means showing the latest (bottom)
        self.logs = []
        self.total_content_height = 0

    def update_logs(self, logs):
        self.logs = logs
        self.total_content_height = len(logs) * constants.LOG_LINE_HEIGHT

    def handle_event(self, event):
        """Handles mouse wheel scrolling."""
        if event.type == pygame.MOUSEWHEEL:
            # Only scroll if mouse is over the panel
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                # Scroll speed (Inverted direction)
                self.scroll_offset += event.y * constants.LOG_LINE_HEIGHT
                
                # Clamp scrolling
                # Min: 0 (Bottom of log)
                # Max: Content Height - Panel Height (Top of log)
                max_scroll = max(0, self.total_content_height - self.rect.height)
                self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

    def draw(self, screen):
        # Draw Background
        pygame.draw.rect(screen, constants.COLOR_LOG_BG, self.rect)
        
        # Create a clipping area so text doesn't spill out
        old_clip = screen.get_clip()
        screen.set_clip(self.rect)
        
        # Calculate start position
        # We want to render from the bottom up if scroll is 0
        # But standard rendering is top-down.
        
        # Let's render top-down based on scroll.
        # If scroll_offset is 0, we want to see the LAST lines.
        # So y_start should be such that the last line is at the bottom.
        
        visible_height = self.rect.height
        
        # Y position of the very first log line relative to panel top
        # If total height < visible, start at top.
        # If total height > visible, start at (visible - total) + scroll_offset
        
        if self.total_content_height < visible_height:
            start_y = self.rect.y
        else:
            # Default: align bottom of content to bottom of panel
            # scroll_offset moves it DOWN (showing earlier logs)
            start_y = self.rect.y + visible_height - self.total_content_height + self.scroll_offset

        y = start_y
        for line_data in self.logs:
            text, color = line_data
            # Optimization: Only draw if within vertical bounds
            if y + constants.LOG_LINE_HEIGHT > self.rect.y and y < self.rect.bottom:
                text_surf = self.font.render(text, True, color)
                screen.blit(text_surf, (self.rect.x + 10, y))
            y += constants.LOG_LINE_HEIGHT
            
        # Restore clip
        screen.set_clip(old_clip)
        
        # Draw Border
        pygame.draw.rect(screen, constants.COLOR_BORDER, self.rect, 1)