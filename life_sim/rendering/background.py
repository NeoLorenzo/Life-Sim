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
    
    def get_image(self, filename: str) -> Optional[pygame.Surface]:
        """
        Load and cache a background image.
        
        Args:
            filename: The image filename to load
            
        Returns:
            pygame.Surface: The loaded and scaled image surface, or None if failed
        """
        # Check cache first
        if filename in self._cache:
            return self._cache[filename]
        
        # Construct full path
        full_path = os.path.join(constants.ASSETS_BG_DIR, filename)
        
        try:
            # Load the image
            image = pygame.image.load(full_path)
            
            # Scale to screen size
            scaled_image = pygame.transform.scale(
                image, 
                (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
            )
            
            # Convert for performance
            converted_image = scaled_image.convert()
            
            # Cache and return
            self._cache[filename] = converted_image
            return converted_image
            
        except pygame.error as e:
            logging.warning(f"Failed to load background image '{filename}': {e}")
            return None
        except FileNotFoundError:
            logging.warning(f"Background image file not found: {full_path}")
            return None
    
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
    
    def update(self, sim_state):
        """
        Update the background based on simulation state.
        
        Args:
            sim_state: Current simulation state object
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
        if target_name != self.current_bg_name:
            self.current_bg = self.resource_manager.get_image(target_name)
            self.current_bg_name = target_name
    
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
