"""Subtle glowing stars background for synthwave aesthetic."""

from __future__ import annotations

import random


class Star:
    """A single glowing star with position, radius, and opacity."""

    def __init__(self, x: float, y: float, radius: float, base_opacity: float, width: float = 1200, height: float = 700) -> None:
        self.x = x
        self.y = y
        self.radius = radius
        self.base_opacity = base_opacity
        self.current_opacity = base_opacity
        self.width = width
        self.height = height
        
        # Opacity drift
        self.opacity_direction = 1 if random.random() > 0.5 else -1
        self.opacity_speed = random.uniform(0.008, 0.015)
        
        # Position drift - visible, gentle movement (updated every 50ms)
        self.vx = random.uniform(-1.5, 1.5)  # Pixels per 50ms
        self.vy = random.uniform(-1.5, 1.5)  # Pixels per 50ms

    def update(self) -> None:
        """Update opacity with pulsing and position with gentle drift."""
        # Update opacity
        self.current_opacity += self.opacity_direction * self.opacity_speed
        if self.current_opacity >= self.base_opacity + 0.15:
            self.opacity_direction = -1
        elif self.current_opacity <= self.base_opacity - 0.08:
            self.opacity_direction = 1
        
        # Update position with wrapping at edges
        self.x += self.vx
        self.y += self.vy
        
        # Wrap around screen edges
        if self.x < -50:
            self.x = self.width + 50
        elif self.x > self.width + 50:
            self.x = -50
        
        if self.y < -50:
            self.y = self.height + 50
        elif self.y > self.height + 50:
            self.y = -50

