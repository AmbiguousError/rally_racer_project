# classes/particle.py
# This file contains the Particle class and its derivatives (DustParticle, MudParticle)
# for the Rally Racer game.

import pygame
import random
import math 

# Assuming constants.py and utils.py are in the parent directory or project root is in PYTHONPATH.
import constants as const 
# MODIFIED: Added 'clamp' to the import from utils
from utils import lerp, clamp # Make sure clamp is imported here

class Particle:
    """
    Base class for a simple 2D particle with a lifetime, size transition, and drift.
    """
    def __init__(self, world_x, world_y, lifetime, start_size, end_size, color, 
                 initial_drift_x=0, initial_drift_y=0, drift_dampening=0.95):
        """
        Initializes a particle.

        Args:
            world_x (float): Initial world x-coordinate.
            world_y (float): Initial world y-coordinate.
            lifetime (float): Base lifetime of the particle in seconds. A random variation is added.
            start_size (int): Initial size (radius) of the particle in pixels.
            end_size (int): Final size (radius) of the particle at the end of its life.
            color (tuple): Color of the particle (R, G, B) or (R, G, B, A). Alpha is used if present.
            initial_drift_x (float, optional): Initial horizontal drift speed. Defaults to 0.
            initial_drift_y (float, optional): Initial vertical drift speed. Defaults to 0.
            drift_dampening (float, optional): Factor by which drift speed is reduced each update. Defaults to 0.95.
        """
        self.world_x = world_x
        self.world_y = world_y
        
        self.lifetime = lifetime + random.uniform(-lifetime * 0.2, lifetime * 0.2)
        self.max_lifetime = max(0.1, self.lifetime) 

        self.start_size = start_size
        self.end_size = end_size
        self.color = color 

        self.drift_x = initial_drift_x
        self.drift_y = initial_drift_y
        self.drift_dampening = drift_dampening

    def update(self, dt):
        """
        Updates the particle's state (lifetime, position due to drift).
        """
        self.lifetime -= dt
        if self.lifetime <= 0:
            return False

        self.world_x += self.drift_x * dt
        self.world_y += self.drift_y * dt

        self.drift_x *= (self.drift_dampening ** dt) 
        self.drift_y *= (self.drift_dampening ** dt)
        
        return True

    def draw(self, surface, camera_offset_x, camera_offset_y):
        """
        Draws the particle on the given surface, relative to the camera.
        """
        if self.lifetime <= 0:
            return

        screen_x = int(self.world_x - camera_offset_x + const.CENTER_X)
        screen_y = int(self.world_y - camera_offset_y + const.CENTER_Y)

        life_ratio = max(0, self.lifetime / self.max_lifetime) 
        current_size = int(lerp(self.end_size, self.start_size, life_ratio**0.5))

        if current_size < 1: 
            return

        if not (-current_size < screen_x < const.SCREEN_WIDTH + current_size and \
                -current_size < screen_y < const.SCREEN_HEIGHT + current_size):
            return

        base_alpha = 255
        if len(self.color) == 4: 
            base_alpha = self.color[3]
        
        current_alpha = int(lerp(0, base_alpha, life_ratio)) 
        current_alpha = clamp(current_alpha, 0, 255) # clamp is now defined

        try:
            final_color = (*self.color[:3], current_alpha)
            particle_surf = pygame.Surface((current_size * 2, current_size * 2), pygame.SRCALPHA)
            particle_surf.fill((0,0,0,0)) 
            pygame.draw.circle(particle_surf, final_color, (current_size, current_size), current_size)
            surface.blit(particle_surf, (screen_x - current_size, screen_y - current_size))
        except ValueError: 
            pygame.draw.circle(surface, self.color[:3], (screen_x, screen_y), current_size)


class DustParticle(Particle):
    """
    A specialized particle for dust effects, inheriting from Particle.
    """
    def __init__(self, world_x, world_y, initial_drift_x=0, initial_drift_y=0):
        super().__init__(
            world_x, world_y,
            const.DUST_LIFETIME,
            const.DUST_START_SIZE,
            const.DUST_END_SIZE,
            const.DUST_COLOR, 
            initial_drift_x * 0.1, 
            initial_drift_y * 0.1,
            drift_dampening=0.95 
        )

class MudParticle(Particle):
    """
    A specialized particle for mud splash effects, inheriting from Particle.
    """
    def __init__(self, world_x, world_y, initial_drift_x=0, initial_drift_y=0):
        super().__init__(
            world_x, world_y,
            const.MUD_LIFETIME,
            const.MUD_START_SIZE,
            const.MUD_END_SIZE,
            const.MUD_SPLASH_COLOR, 
            initial_drift_x * 0.2, 
            initial_drift_y * 0.2 - random.uniform(10, 40), 
            drift_dampening=0.90 
        )
