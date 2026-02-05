# life_sim/rendering/background.py
"""
Dynamic Background System - Resource Management
Handles loading and caching of background images.
"""

import pygame
import os
import logging
from typing import Optional, Dict

from life_sim import constants


class ResourceManager:
    """Manages loading and caching of background images."""
    
    def __init__(self):
        """Initialize the resource cache."""
        self._cache: Dict[str, pygame.Surface] = {}
    
    def get_image(self, filename: str, screen_width: int = None, screen_height: int = None) -> Optional[pygame.Surface]:
        """
        Load and cache a background image.
        
        Args:
            filename: The image filename to load
            screen_width: Current screen width for scaling
            screen_height: Current screen height for scaling
            
        Returns:
            pygame.Surface: The loaded and scaled image surface, or None if failed
        """
        # Create cache key that includes dimensions
        cache_key = f"{filename}_{screen_width}_{screen_height}"
        
        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Construct full path
        full_path = os.path.join(constants.ASSETS_BG_DIR, filename)
        
        try:
            # Load the image
            image = pygame.image.load(full_path)
            
            # Scale to screen size while maintaining aspect ratio
            scaled_image = self._scale_to_fit_screen(image, screen_width, screen_height)
            
            # Convert for performance
            converted_image = scaled_image.convert()
            
            # Cache and return
            self._cache[cache_key] = converted_image
            return converted_image
            
        except pygame.error as e:
            logging.warning(f"Failed to load background image '{filename}': {e}")
            return None
        except FileNotFoundError:
            logging.warning(f"Background image file not found: {full_path}")
            return None
    
    def _scale_to_fit_screen(self, image: pygame.Surface, screen_width: int, screen_height: int) -> pygame.Surface:
        """
        Scale image to fill screen while maintaining aspect ratio (cover mode).
        This may crop parts of the image but ensures no negative space.
        
        Args:
            image: The original image surface
            screen_width: Target screen width
            screen_height: Target screen height
            
        Returns:
            pygame.Surface: Scaled image surface that fills the entire screen
        """
        if screen_width is None or screen_height is None:
            # Fallback to original constants if dimensions not provided
            screen_width = constants.SCREEN_WIDTH
            screen_height = constants.SCREEN_HEIGHT
        
        # Get original image dimensions
        img_width, img_height = image.get_size()
        
        # Calculate scaling ratios
        width_ratio = screen_width / img_width
        height_ratio = screen_height / img_height
        
        # Use the LARGER ratio to ensure image covers entire screen
        scale_ratio = max(width_ratio, height_ratio)
        
        # Calculate new dimensions
        new_width = int(img_width * scale_ratio)
        new_height = int(img_height * scale_ratio)
        
        # Scale the image
        scaled_image = pygame.transform.smoothscale(image, (new_width, new_height))
        
        # Calculate crop position to center the image
        crop_x = (new_width - screen_width) // 2
        crop_y = (new_height - screen_height) // 2
        
        # Create a surface the size of the screen
        final_surface = pygame.Surface((screen_width, screen_height))
        
        # If the scaled image is larger than screen, crop and center it
        if new_width >= screen_width and new_height >= screen_height:
            final_surface.blit(scaled_image, (0, 0), (crop_x, crop_y, screen_width, screen_height))
        else:
            # Fallback (shouldn't happen with max ratio, but just in case)
            x = (screen_width - new_width) // 2
            y = (screen_height - new_height) // 2
            final_surface.fill(constants.COLOR_BG_FALLBACK)
            final_surface.blit(scaled_image, (x, y))
        
        return final_surface
    
    def clear_cache(self):
        """Clear all cached images."""
        self._cache.clear()
        logging.debug("Background image cache cleared")


class BackgroundManager:
    """Manages dynamic background selection and rendering."""
    
    def __init__(self):
        """Initialize the background manager."""
        self.resource_manager = ResourceManager()
        self.current_bg = None
        self.current_bg_name = ""
        self._last_screen_width = None
        self._last_screen_height = None
    
    def _get_season(self, month_index):
        """
        Determine the season based on month index.
        
        Args:
            month_index: 0-11 representing January to December
            
        Returns:
            str: "winter", "spring", "summer", or "autumn"
        """
        if month_index in [11, 0, 1]:
            return "winter"
        elif month_index in [2, 3, 4]:
            return "spring"
        elif month_index in [5, 6, 7]:
            return "summer"
        else:  # [8, 9, 10]
            return "autumn"
    
    def _get_wealth_tier(self, sim_state):
        """
        Calculate the wealth tier of the player (including family wealth if under 18).
        
        Args:
            sim_state: Current simulation state
            
        Returns:
            int: Wealth tier from 1-5 (1=lowest, 5=highest)
        """
        total_wealth = sim_state.player.money
        
        # If player is under 18, add parents' wealth
        if sim_state.player.age < 18:
            for rel_uid, relationship in sim_state.player.relationships.items():
                if relationship.rel_type in ["Mother", "Father"] and rel_uid in sim_state.npcs:
                    total_wealth += sim_state.npcs[rel_uid].money
        
        # Determine wealth tier
        for i, threshold in enumerate(constants.WEALTH_TIERS):
            if total_wealth < threshold:
                return i + 1
        
        return 5  # Highest tier if above all thresholds
    
    def update(self, sim_state, screen_width: int = None, screen_height: int = None):
        """
        Update the background based on simulation state.
        
        Args:
            sim_state: Current simulation state object
            screen_width: Current screen width for scaling
            screen_height: Current screen height for scaling
        """
        # Determine location
        # Check if it's the player's birth month (year 0, birth month)
        if sim_state.player.age == 0 and sim_state.month_index == sim_state.birth_month_index:
            location = "hospital"
        else:
            location = "home"  # Placeholder
        
        # Get season and wealth tier
        season = self._get_season(sim_state.month_index)
        tier = self._get_wealth_tier(sim_state)
        
        # Construct filename
        target_name = f"{location}_tier{tier}_{season}.png"
        
        # Only load new background if it's different
        if target_name != self.current_bg_name or screen_width != self._last_screen_width or screen_height != self._last_screen_height:
            self.current_bg = self.resource_manager.get_image(target_name, screen_width, screen_height)
            self.current_bg_name = target_name
            self._last_screen_width = screen_width
            self._last_screen_height = screen_height
    
    def draw(self, screen):
        """
        Draw the current background to the screen.
        
        Args:
            screen: pygame surface to draw on
        """
        if self.current_bg is not None:
            screen.blit(self.current_bg, (0, 0))
        else:
            screen.fill(constants.COLOR_BG_FALLBACK)
