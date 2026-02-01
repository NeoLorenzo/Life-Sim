# life_sim/rendering/modals.py
"""
Modal Dialog Components.
Displays interactive dialogs and events to the user.
"""
import pygame
from .. import constants

class EventModal:
    """
    Modal dialog for displaying and handling game events.
    """
    
    def __init__(self, rect: pygame.Rect, event_data):
        """
        Initialize the EventModal.
        
        Args:
            rect: Pygame Rect defining the modal's position and size.
            event_data: Event object containing title, description, choices, etc.
        """
        self.rect = rect
        self.event_data = event_data
        self.font_title = pygame.font.Font(None, 32)
        self.font_text = pygame.font.Font(None, 24)
        self.choice_buttons = []  # List of (rect, choice_text) tuples
        self.selected_choices = []  # List of selected choice indices
        self.confirm_button = None  # Rect for confirm button
        self.hovered_choice = None  # Index of currently hovered choice
        
        # Selection constraints from event data
        self.min_selections = self.event_data.ui_config.get("min_selections", 1) if hasattr(self.event_data, 'ui_config') else 1
        self.max_selections = self.event_data.ui_config.get("max_selections", 1) if hasattr(self.event_data, 'ui_config') else 1
        
    def draw(self, screen):
        """
        Draw the event modal to the screen.
        
        Args:
            screen: Pygame surface to draw on.
        """
        # Draw modal background
        pygame.draw.rect(screen, constants.COLOR_PANEL_BG, self.rect)
        pygame.draw.rect(screen, constants.COLOR_TEXT, self.rect, 2)  # Border
        
        # Draw event title
        title_surface = self.font_title.render(self.event_data.title, True, constants.COLOR_TEXT)
        title_rect = title_surface.get_rect(centerx=self.rect.centerx, y=self.rect.y + 20)
        screen.blit(title_surface, title_rect)
        
        # Draw event description (with word wrapping)
        description_lines = self._wrap_text(self.event_data.description, self.rect.width - 40)
        y_offset = self.rect.y + 60
        
        for line in description_lines:
            text_surface = self.font_text.render(line, True, constants.COLOR_TEXT)
            text_rect = text_surface.get_rect(centerx=self.rect.centerx, y=y_offset)
            screen.blit(text_surface, text_rect)
            y_offset += 30
        
        # Draw choice buttons
        self.choice_buttons = []  # Reset button list
        button_width = self.rect.width - 80
        button_height = 35
        button_x = self.rect.x + 40
        y_offset += 20  # Space after description
        
        for i, choice in enumerate(self.event_data.choices):
            # Handle both old string format and new dict format
            if isinstance(choice, str):
                choice_text = choice
            else:
                choice_text = choice.get("text", "Unknown Choice")
            
            button_rect = pygame.Rect(button_x, y_offset, button_width, button_height)
            
            # Choose color based on selection and hover state
            is_selected = i in self.selected_choices
            is_hovered = i == self.hovered_choice
            
            if is_selected:
                bg_color = constants.COLOR_ACCENT
                text_color = constants.COLOR_BG
            elif is_hovered:
                bg_color = constants.COLOR_BTN_HOVER
                text_color = constants.COLOR_TEXT
            else:
                bg_color = constants.COLOR_BTN_IDLE
                text_color = constants.COLOR_TEXT
            
            pygame.draw.rect(screen, bg_color, button_rect, border_radius=4)
            pygame.draw.rect(screen, constants.COLOR_BORDER, button_rect, 1, border_radius=4)
            
            choice_surface = self.font_text.render(choice_text, True, text_color)
            choice_rect = choice_surface.get_rect(center=button_rect.center)
            screen.blit(choice_surface, choice_rect)
            
            self.choice_buttons.append((button_rect, choice, i))
            y_offset += button_height + 10
        
        # Draw confirm button at bottom
        confirm_width = 120
        confirm_height = 40
        confirm_x = self.rect.centerx - confirm_width // 2
        confirm_y = self.rect.bottom - confirm_height - 20
        self.confirm_button = pygame.Rect(confirm_x, confirm_y, confirm_width, confirm_height)
        
        # Enable confirm only if selection count is within bounds
        selection_count = len(self.selected_choices)
        if self.min_selections <= selection_count <= self.max_selections:
            confirm_color = constants.COLOR_LOG_POSITIVE
            confirm_text_color = constants.COLOR_TEXT
        else:
            confirm_color = constants.COLOR_TEXT_DIM
            confirm_text_color = constants.COLOR_TEXT_DIM
        
        pygame.draw.rect(screen, confirm_color, self.confirm_button, border_radius=4)
        pygame.draw.rect(screen, constants.COLOR_BORDER, self.confirm_button, 1, border_radius=4)
        
        confirm_surface = self.font_text.render("Confirm", True, confirm_text_color)
        confirm_rect = confirm_surface.get_rect(center=self.confirm_button.center)
        screen.blit(confirm_surface, confirm_rect)
    
    def handle_event(self, event):
        """
        Handle mouse events for the modal.
        
        Args:
            event: Pygame event object.
            
        Returns:
            String action if event was handled, None otherwise.
        """
        if event.type == pygame.MOUSEMOTION:
            # Update hover state
            mouse_pos = event.pos
            self.hovered_choice = None
            
            for button_rect, choice_data, choice_index in self.choice_buttons:
                if button_rect.collidepoint(mouse_pos):
                    self.hovered_choice = choice_index
                    break
                    
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            mouse_pos = event.pos
            
            # Check choice buttons
            for button_rect, choice_data, choice_index in self.choice_buttons:
                if button_rect.collidepoint(mouse_pos):
                    # Toggle selection for multi-select, or single select
                    if choice_index in self.selected_choices:
                        self.selected_choices.remove(choice_index)
                    else:
                        # For single select, clear previous selection
                        if self.max_selections == 1:
                            self.selected_choices.clear()
                        # Add new selection if under max limit
                        if len(self.selected_choices) < self.max_selections:
                            self.selected_choices.append(choice_index)
                    return None  # Handled, but no action yet
            
            # Check confirm button (only if selection is valid)
            selection_count = len(self.selected_choices)
            if self.min_selections <= selection_count <= self.max_selections and self.confirm_button.collidepoint(mouse_pos):
                return "CONFIRM_EVENT"
        
        return None  # Event not handled
            
    def _wrap_text(self, text: str, max_width: int) -> list:
        """
        Wrap text to fit within the specified width.
        
        Args:
            text: Text to wrap.
            max_width: Maximum width in pixels.
            
        Returns:
            List of wrapped text lines.
        """
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = self.font_text.render(test_line, True, constants.COLOR_TEXT)
            
            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
                    
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines
