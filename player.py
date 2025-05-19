import pygame
from typing import List

class Player:
    def __init__(self, x: int, y: int):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.resources = 0
        self.sprite = create_player_sprite()
        self.speed = 5
        self.isolation_level = 0
    
    def move(self, dx: int, dy: int, walls: List[pygame.Rect]) -> None:
        # Store original position
        original_x = self.rect.x
        original_y = self.rect.y
        
        # Try to move horizontally
        self.rect.x += dx
        for wall in walls:
            if self.rect.colliderect(wall):
                if dx > 0:  # Moving right
                    self.rect.right = wall.left
                else:  # Moving left
                    self.rect.left = wall.right
        
        # Try to move vertically
        self.rect.y += dy
        for wall in walls:
            if self.rect.colliderect(wall):
                if dy > 0:  # Moving down
                    self.rect.bottom = wall.top
                else:  # Moving up
                    self.rect.top = wall.bottom
    
    def collect_resource(self, resources: List['Resource']) -> bool:
        for resource in resources:
            if not resource.collected and self.rect.colliderect(resource.rect):
                resource.collected = True
                self.resources += 1
                return True
        return False

def create_player_sprite():
    """Create a simple humanoid sprite"""
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    
    # Body (dark gray)
    pygame.draw.rect(surface, (60, 60, 60), (12, 12, 8, 12))
    
    # Head (light gray)
    pygame.draw.circle(surface, (120, 120, 120), (16, 8), 6)
    
    # Arms (dark gray)
    pygame.draw.rect(surface, (60, 60, 60), (8, 12, 4, 8))   # Left arm
    pygame.draw.rect(surface, (60, 60, 60), (20, 12, 4, 8))  # Right arm
    
    # Legs (dark gray)
    pygame.draw.rect(surface, (60, 60, 60), (12, 24, 3, 8))  # Left leg
    pygame.draw.rect(surface, (60, 60, 60), (17, 24, 3, 8))  # Right leg
    
    return surface

def create_npc_sprite(state='needy'):
    """Create NPC sprite with different appearances based on state
    states: 'needy', 'helped', 'dead'"""
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    
    if state == 'dead':
        color = (50, 50, 50)  # Dark gray for dead NPCs
        # Fallen body
        pygame.draw.ellipse(surface, color, (8, 20, 16, 8))
        # X eyes
        pygame.draw.line(surface, color, (10, 16), (14, 20), 2)
        pygame.draw.line(surface, color, (14, 16), (10, 20), 2)
        pygame.draw.line(surface, color, (18, 16), (22, 20), 2)
        pygame.draw.line(surface, color, (22, 16), (18, 20), 2)
        return surface
    
    color = (200, 50, 50) if state == 'needy' else (100, 200, 100)  # Red if needy, green if helped
    
    # Body
    pygame.draw.rect(surface, color, (12, 12, 8, 12))
    
    # Head
    pygame.draw.circle(surface, color, (16, 8), 6)
    
    # Arms
    pygame.draw.rect(surface, color, (8, 14, 4, 6))   # Left arm
    pygame.draw.rect(surface, color, (20, 14, 4, 6))  # Right arm
    
    # Legs
    pygame.draw.rect(surface, color, (12, 24, 3, 8))  # Left leg
    pygame.draw.rect(surface, color, (17, 24, 3, 8))  # Right leg
    
    if state == 'needy':
        # Add a "!" symbol above head
        pygame.draw.rect(surface, (255, 255, 0), (14, 0, 4, 4))
        pygame.draw.circle(surface, (255, 255, 0), (16, 5), 2)
    
    return surface

def create_resource_sprite():
    """Create a glowing resource sprite"""
    surface = pygame.Surface((24, 24), pygame.SRCALPHA)
    
    # Outer glow (light green)
    pygame.draw.circle(surface, (100, 255, 100, 128), (12, 12), 10)
    
    # Inner crystal (darker green)
    points = [(12, 2), (22, 12), (12, 22), (2, 12)]
    pygame.draw.polygon(surface, (0, 180, 0), points)
    
    # Highlight
    pygame.draw.line(surface, (200, 255, 200), (8, 8), (16, 16), 2)
    
    return surface
