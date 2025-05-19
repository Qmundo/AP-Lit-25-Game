import pygame
import sys
import math
from enum import Enum
import random
from typing import List, Tuple, Optional
import time
import os

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SPEED = 3  # Reduced from 5 to 3 for better control
TILE_SIZE = 32

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
BROWN = (139, 69, 19)
BLUE = (0, 0, 255)
GREEN = (0, 128, 0)
RED = (255, 0, 0)

class GameState(Enum):
    INTRO = 1
    ZONE_SCARCITY = 2
    ZONE_MAZE = 3
    ZONE_RIVERBANK = 4
    VICTORY = 5

class Resource:
    def __init__(self, x: int, y: int):
        self.rect = pygame.Rect(x, y, 24, 24)
        self.collected = False
        self.sprite = None
        self.load_sprite()
    
    def load_sprite(self):
        # Create a simple green circle surface for the resource
        sprite_size = 24
        self.sprite = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
        pygame.draw.circle(self.sprite, GREEN, (sprite_size//2, sprite_size//2), 10)
        
    def draw(self, screen):
        if not self.collected and self.sprite:
            screen.blit(self.sprite, self.rect.topleft)

class NPC:
    def __init__(self, x: int, y: int, needs_help: bool = False, npc_type: str = 'generic'):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.needs_help = needs_help
        self.helped = False
        self.dead = False
        self.npc_type = npc_type
        self.gems_given = 0
        self.gems_required = 4
        self.sprite = None
        self.update_sprite()
    
    def update_sprite(self):
        # Create a more detailed NPC sprite based on type and state
        sprite_size = 32
        self.sprite = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
        
        if self.dead:
            # Draw a gray X for dead NPCs
            color = (100, 100, 100)
            pygame.draw.line(self.sprite, color, (5, 5), (sprite_size-5, sprite_size-5), 3)
            pygame.draw.line(self.sprite, color, (sprite_size-5, 5), (5, sprite_size-5), 3)
            return
            
        # Draw a humanoid figure
        if self.npc_type == 'elder' or self.npc_type == 'child':
            # Body color is red if needs help, green if helped, gray if neither
            if self.helped:
                body_color = (0, 200, 0)  # Green when helped
            elif self.needs_help:
                # Make the color more red based on how many gems are still needed
                progress = 1.0 - (self.gems_given / self.gems_required)
                red = 200
                green_blue = int(100 * progress)
                body_color = (red, green_blue, green_blue)
            else:
                body_color = (150, 150, 150)  # Gray when neutral
            
            # Draw head
            head_radius = 8 if self.npc_type == 'elder' else 6
            pygame.draw.circle(self.sprite, body_color, (sprite_size//2, sprite_size//4), head_radius)
            
            # Draw body
            body_height = 16 if self.npc_type == 'elder' else 12
            pygame.draw.rect(self.sprite, body_color, 
                            (sprite_size//2 - 4, sprite_size//4 + head_radius, 8, body_height))
            
            # Draw arms
            arm_y = sprite_size//4 + head_radius + 4
            pygame.draw.line(self.sprite, body_color, 
                            (sprite_size//2 - 4, arm_y), (sprite_size//2 - 12, arm_y + 6), 3)
            pygame.draw.line(self.sprite, body_color, 
                            (sprite_size//2 + 4, arm_y), (sprite_size//2 + 12, arm_y + 6), 3)
            
            # Draw legs
            leg_y = sprite_size//4 + head_radius + body_height
            pygame.draw.line(self.sprite, body_color, 
                            (sprite_size//2 - 2, leg_y), (sprite_size//2 - 6, sprite_size - 4), 3)
            pygame.draw.line(self.sprite, body_color, 
                            (sprite_size//2 + 2, leg_y), (sprite_size//2 + 6, sprite_size - 4), 3)
    
    def draw(self, screen, font):
        # Draw the NPC sprite
        if self.sprite:
            screen.blit(self.sprite, self.rect.topleft)
        
        # Add label above NPC if not dead
        if not self.dead:
            # Show NPC type and gem progress
            if self.helped:
                status = f"{self.npc_type.capitalize()} (Complete!)"
            elif self.needs_help:
                status = f"{self.npc_type.capitalize()} ({self.gems_given}/{self.gems_required})"
            else:
                status = self.npc_type.capitalize()
                
            label = font.render(status, True, WHITE)
            screen.blit(label, (self.rect.x - 10, self.rect.y - 25))

class Player:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        self.resources = 0
        # Base speed without gems
        self.base_speed = 0.5
        # Speed increases by 0.5 per gem
        # 0 gems: 0.5
        # 1 gem: 1.0
        # 2 gems: 1.5
        # 3 gems: 2.0
        self.speed_increase_per_gem = 0.5
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.sprite = None
        self.load_sprite()
    
    def get_speed(self):
        """Calculate current speed based on number of magic gems held.
        Speed increases by 0.5 per gem.
        """
        # Speed = base_speed + (speed_increase_per_gem * gems)
        # 0 gems: 0.5 + (0.5 * 0) = 0.5
        # 1 gem: 0.5 + (0.5 * 1) = 1.0
        # 2 gems: 0.5 + (0.5 * 2) = 1.5
        # 3 gems: 0.5 + (0.5 * 3) = 2.0
        return self.base_speed + (self.speed_increase_per_gem * self.resources)
    
    def load_sprite(self):
        # Create a more detailed player sprite (gray humanoid as shown in the image)
        sprite_size = 32
        self.sprite = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
        
        # Draw a humanoid figure in gray
        body_color = GRAY
        
        # Draw head
        head_radius = 7
        pygame.draw.circle(self.sprite, body_color, (sprite_size//2, sprite_size//4), head_radius)
        
        # Draw body
        body_height = 14
        pygame.draw.rect(self.sprite, body_color, 
                        (sprite_size//2 - 4, sprite_size//4 + head_radius, 8, body_height))
        
        # Draw arms
        arm_y = sprite_size//4 + head_radius + 4
        pygame.draw.line(self.sprite, body_color, 
                        (sprite_size//2 - 4, arm_y), (sprite_size//2 - 12, arm_y + 6), 3)
        pygame.draw.line(self.sprite, body_color, 
                        (sprite_size//2 + 4, arm_y), (sprite_size//2 + 12, arm_y + 6), 3)
        
        # Draw legs
        leg_y = sprite_size//4 + head_radius + body_height
        pygame.draw.line(self.sprite, body_color, 
                        (sprite_size//2 - 2, leg_y), (sprite_size//2 - 6, sprite_size - 4), 3)
        pygame.draw.line(self.sprite, body_color, 
                        (sprite_size//2 + 2, leg_y), (sprite_size//2 + 6, sprite_size - 4), 3)
    
    def move(self, dx: int, dy: int, walls: List[pygame.Rect]):
        # Get current speed based on gems
        speed = self.get_speed()
        
        # Apply speed to movement
        dx = dx * speed
        dy = dy * speed
        
        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.7071  # 1/√2 for diagonal movement
            dy *= 0.7071
        
        # Handle X movement
        if dx != 0:
            self.rect.x += dx
            # Check for wall collisions on X axis
            for wall in walls:
                if self.rect.colliderect(wall):
                    if dx > 0:  # Moving right
                        self.rect.right = wall.left
                    else:  # Moving left
                        self.rect.left = wall.right
                    break
        
        # Handle Y movement
        if dy != 0:
            self.rect.y += dy
            # Check for wall collisions on Y axis
            for wall in walls:
                if self.rect.colliderect(wall):
                    if dy > 0:  # Moving down
                        self.rect.bottom = wall.top
                    else:  # Moving up
                        self.rect.top = wall.bottom
                    break
        
        # Ensure player stays within screen bounds
        self.rect.x = max(0, min(SCREEN_WIDTH - self.rect.width, self.rect.x))
        self.rect.y = max(0, min(SCREEN_HEIGHT - self.rect.height, self.rect.y))
        
        # Update position variables
        self.x = self.rect.x
        self.y = self.rect.y
    
    def collect_resource(self, resources: List[Resource]) -> Tuple[Optional[Resource], bool]:
        """
        Attempt to collect a resource.
        Returns a tuple of (resource, all_collected) where:
        - resource is the collected resource or None if none collected
        - all_collected is True if this was the last resource
        """
        collected_resource = None
        
        for resource in resources:
            if not resource.collected and self.rect.colliderect(resource.rect):
                resource.collected = True
                self.resources += 1
                collected_resource = resource
                break
        
        # Check if all resources are collected (should be 3 gems)
        all_collected = len([r for r in resources if r.collected]) >= 3
        
        return collected_resource, all_collected
    
    def draw(self, screen):
        if self.sprite:
            screen.blit(self.sprite, self.rect.topleft)

class Game:
    def create_maze_zone(self) -> List[pygame.Rect]:
        """Create a structured maze with connected walls and 4 distinct exits."""
        walls = []
        wall_thickness = 15
        
        # Center of the screen
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        
        # Create exit points (north, east, south, west)
        exit_size = 60
        self.exit_rects = [
            pygame.Rect(center_x - exit_size//2, 0, exit_size, 5),  # North
            pygame.Rect(SCREEN_WIDTH - 5, center_y - exit_size//2, 5, exit_size),  # East
            pygame.Rect(center_x - exit_size//2, SCREEN_HEIGHT - 5, exit_size, 5),  # South
            pygame.Rect(0, center_y - exit_size//2, 5, exit_size)  # West
        ]
        
        # Set north exit (0) as the correct exit for Zone 3
        self.correct_exit = 0
        
        def add_wall(x, y, width, height):
            walls.append(pygame.Rect(x, y, width, height))
        
        # Calculate grid dimensions
        grid_cells = 4  # 4x4 grid
        cell_size = min(SCREEN_WIDTH, SCREEN_HEIGHT) // (grid_cells + 1)  # Leave room for margins
        margin_x = (SCREEN_WIDTH - (cell_size * grid_cells)) // 2
        margin_y = (SCREEN_HEIGHT - (cell_size * grid_cells)) // 2
        
        # Create the main grid structure with open paths
        # Vertical lines (only at the edges and center)
        add_wall(margin_x, margin_y, wall_thickness, cell_size * grid_cells)  # Left edge
        add_wall(margin_x + 2 * cell_size, margin_y, wall_thickness, cell_size * grid_cells)  # Middle
        add_wall(margin_x + 4 * cell_size, margin_y, wall_thickness, cell_size * grid_cells)  # Right edge
        
        # Horizontal lines (only at the edges and center)
        add_wall(margin_x, margin_y, cell_size * grid_cells, wall_thickness)  # Top edge
        add_wall(margin_x, margin_y + 2 * cell_size, cell_size * grid_cells, wall_thickness)  # Middle
        add_wall(margin_x, margin_y + 4 * cell_size, cell_size * grid_cells, wall_thickness)  # Bottom edge
        
        # Add the specific internal walls as shown in the image
        # Top row horizontal walls (leaving gaps for paths)
        add_wall(margin_x + cell_size, margin_y + cell_size, cell_size, wall_thickness)  # Top middle
        
        # Middle row vertical walls (leaving gaps for paths)
        add_wall(margin_x + cell_size, margin_y + cell_size, wall_thickness, cell_size)  # Left middle
        add_wall(margin_x + 3 * cell_size, margin_y + cell_size, wall_thickness, cell_size)  # Right middle
        
        # Bottom row horizontal walls (leaving gaps for paths)
        add_wall(margin_x + cell_size, margin_y + 3 * cell_size, cell_size, wall_thickness)  # Bottom middle
        
        # Clear the exits with larger clear areas
        exit_clear_size = 100  # Increased from 80 to 100
        
        # Clear north exit (top center)
        walls = [w for w in walls if not (
            w.top <= margin_y + 5 and  # Slightly below the top edge
            center_x - exit_clear_size//2 < w.centerx < center_x + exit_clear_size//2
        )]
        
        # Clear east exit (right center)
        walls = [w for w in walls if not (
            w.right >= SCREEN_WIDTH - margin_x - 5 and  # Slightly left of right edge
            center_y - exit_clear_size//2 < w.centery < center_y + exit_clear_size//2
        )]
        
        # Clear south exit (bottom center)
        walls = [w for w in walls if not (
            w.bottom >= SCREEN_HEIGHT - margin_y - 5 and  # Slightly above bottom edge
            center_x - exit_clear_size//2 < w.centerx < center_x + exit_clear_size//2
        )]
        
        # Clear west exit (left center)
        walls = [w for w in walls if not (
            w.left <= margin_x + 5 and  # Slightly right of left edge
            center_y - exit_clear_size//2 < w.centery < center_y + exit_clear_size//2
        )]
        
        return walls
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Echoes of Humanity")
        self.clock = pygame.time.Clock()
        self.state = GameState.INTRO
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.walls = []
        self.resources = []
        self.npcs = []
        self.messages = []
        self.message_timer = 0
        self.choice_active = False
        self.choice_made = None
        self.saved_npc_type = None  # Tracks which NPC was saved in Zone 1
        self.revived_npc = False    # Tracks if the dead NPC was revived in Zone 3
        self.font = pygame.font.Font(None, 24)
        self.exit_rects = []
        self.correct_exit = 0
        self.river = None
        self.rocks = []
        self.goal = None
        self.enlightenment_rect = None
        self.victory_shown = False
        self.setup_zones()
        self.position_player_in_safe_area()
        
    def create_riverbank_zone(self):
        """Create the riverbank environment for Zone 3"""
        # Clear existing objects but keep the NPCs
        self.walls = []
        self.rocks = []
        
        # Make sure we have exactly 2 NPCs (elder and child)
        if not hasattr(self, 'npcs') or len(self.npcs) != 2:
            # This should never happen if coming from Zone 1, but just in case
            self.npcs = [
                NPC(SCREEN_WIDTH - 150, 200, needs_help=True, npc_type='elder'),
                NPC(SCREEN_WIDTH - 150, 400, needs_help=True, npc_type='child')
            ]
            return
            
        # Reposition the existing NPCs
        elder = next((npc for npc in self.npcs if npc.npc_type == 'elder'), None)
        child = next((npc for npc in self.npcs if npc.npc_type == 'child'), None)
        
        # Reset positions and states for Zone 3
        if elder:
            elder.rect.x = SCREEN_WIDTH - 150
            elder.rect.y = 200
            elder.needs_help = True
            if not elder.helped and self.choice_made == 'child':
                elder.dead = True
                elder.needs_help = False
            elder.update_sprite()
            
        if child:
            child.rect.x = SCREEN_WIDTH - 150
            child.rect.y = 400
            child.needs_help = True
            if not child.helped and self.choice_made == 'elder':
                child.dead = True
                child.needs_help = False
            child.update_sprite()
        
        # Create the river (visual only, no collision)
        river_width = 120
        self.river = [
            pygame.Rect(100, -50, river_width, 200),  # Top curve start
            pygame.Rect(100, 150, 300, 100),          # First bend
            pygame.Rect(350, 200, 100, 200),          # Narrow section
            pygame.Rect(200, 350, 300, 100),          # Second bend
            pygame.Rect(100, 400, 200, 250),          # Bottom curve
        ]
        
        # Add rocks in the river (obstacles)
        rock_positions = [
            (150, 300, 30, 30),
            (300, 150, 40, 40),
            (250, 400, 35, 35),
            (400, 300, 45, 45),
            (180, 500, 30, 30)
        ]
        self.rocks = [pygame.Rect(*pos) for pos in rock_positions]
        
        # Add goal at the bottom of the river
        self.goal = pygame.Rect(SCREEN_WIDTH // 2 - 25, SCREEN_HEIGHT - 100, 50, 50)
        
        # Add some decorative elements
        # Left bank
        self.walls.extend([
            pygame.Rect(0, 0, 80, SCREEN_HEIGHT),  # Left border
            pygame.Rect(0, 0, SCREEN_WIDTH, 50),   # Top border
            pygame.Rect(SCREEN_WIDTH - 100, 0, 100, SCREEN_HEIGHT),  # Right border
            pygame.Rect(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50)  # Bottom border
        ])
        
        # Add some safe platforms to jump on
        platform_positions = [
            (50, 100, 100, 20),
            (200, 50, 100, 20),
            (400, 100, 100, 20),
            (300, 200, 100, 20),
            (150, 300, 100, 20),
            (350, 350, 100, 20),
            (200, 450, 100, 20),
            (400, 500, 100, 20)
        ]
        self.walls.extend([pygame.Rect(*pos) for pos in platform_positions])
        
        return self.walls
        
    def find_safe_position(self, object_rect, object_size=32, max_attempts=50):
        """Find a safe position for an object that doesn't overlap with walls"""
        for _ in range(max_attempts):
            # Try random positions
            x = random.randint(50, SCREEN_WIDTH - 50 - object_size)
            y = random.randint(50, SCREEN_HEIGHT - 50 - object_size)
            object_rect.x = x
            object_rect.y = y
            
            # Check if position is safe (not in walls or other objects)
            if not any(object_rect.colliderect(wall) for wall in self.walls):
                return True
        return False
        
    def setup_zones(self):
        """Set up the game zones based on the current state"""
        # Clear existing objects but keep NPCs
        self.walls = []
        self.resources = []
        self.exit_rects = []
        self.correct_exit = 0
        self.river = None
        self.rocks = []
        self.goal = None
        self.enlightenment_rect = None
        self.victory_shown = False
        
        # Reset choice_active when changing zones
        self.choice_active = False
        
        # Only clear NPCs if we're starting a new game
        if not hasattr(self, 'npcs') or self.state == GameState.INTRO:
            self.npcs = []
            
        if self.state == GameState.ZONE_SCARCITY:
            # Create Zone 1 layout with walls, NPCs, and resources
            self.walls = self.create_scarcity_zone()
            
            # Position player in a safe spot
            self.player.rect.x = 50
            self.player.rect.y = SCREEN_HEIGHT // 2
            
            # Show welcome message
            self.show_message("Collect resources and help the NPCs!", 180)
            
            # Add NPCs if they don't exist yet
            if not self.npcs:
                npc_positions = [
                    (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2),
                    (3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2)
                ]
                
                for x, y in npc_positions:
                    npc = NPC(x, y, True, 'elder' if x < SCREEN_WIDTH // 2 else 'child')
                    if self.find_safe_position(npc.rect, 32):
                        self.npcs.append(npc)
                        
        elif self.state == GameState.ZONE_MAZE:
            # Create Zone 2 - The Maze
            self.walls = self.create_maze_zone()
            # Position player in the center of the maze
            self.player.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            # Ensure player is not in a wall or exit
            self.position_player_in_safe_area()
            self.show_message("Find the correct exit to proceed to the next zone!", 180)
            
            # Store NPCs temporarily but don't display them in Zone 2
            for npc in self.npcs:
                npc.rect.x = -100  # Move off-screen
                npc.rect.y = -100
    
        elif self.state == GameState.ZONE_RIVERBANK:
            # Create the riverbank environment
            self.walls = self.create_riverbank_zone()
            # Position player at the start of the river
            self.player.rect.x = 50
            self.player.rect.y = SCREEN_HEIGHT // 2
            self.show_message("Welcome to the Riverbank! Cross the river to reach safety.", 180)
            
            # Make sure we have NPCs from Zone 1
            if not self.npcs or len(self.npcs) < 2:
                # Create default NPCs if none exist
                self.npcs = [
                    NPC(SCREEN_WIDTH - 150, 300, needs_help=True, npc_type='elder'),
                    NPC(SCREEN_WIDTH - 150, 400, needs_help=True, npc_type='child')
                ]
            else:
                # Reposition existing NPCs and restore their visibility
                elder = next((npc for npc in self.npcs if npc.npc_type == 'elder'), None)
                child = next((npc for npc in self.npcs if npc.npc_type == 'child'), None)
                
                if elder:
                    elder.rect.x = SCREEN_WIDTH - 150
                    elder.rect.y = 300
                
                if child:
                    child.rect.x = SCREEN_WIDTH - 150
                    child.rect.y = 400
            
            # Add gems to Zone 3
            for _ in range(5):
                gem = Resource(0, 0)
                if self.find_safe_position(gem.rect, 24):
                    gem.load_sprite()  # Make sure the sprite is loaded
                    self.resources.append(gem)
        
        else:
            # Default to Zone 1 if no valid state
            self.state = GameState.ZONE_SCARCITY
            self.setup_zones()

    def create_scarcity_zone(self) -> List[pygame.Rect]:
        """Create the exact layout for Zone 1 with walls, NPCs, and resources"""
        walls = []
        
        # Create outer walls (not visible in the image, but needed for boundary)
        wall_thickness = 5
        # Top wall
        walls.append(pygame.Rect(0, 0, SCREEN_WIDTH, wall_thickness))
        # Bottom wall
        walls.append(pygame.Rect(0, SCREEN_HEIGHT - wall_thickness, SCREEN_WIDTH, wall_thickness))
        # Left wall
        walls.append(pygame.Rect(0, 0, wall_thickness, SCREEN_HEIGHT))
        # Right wall
        walls.append(pygame.Rect(SCREEN_WIDTH - wall_thickness, 0, wall_thickness, SCREEN_HEIGHT))
        
        # Create the three vertical walls as shown in the reference image
        wall_width = 50
        wall_length = SCREEN_HEIGHT - 150  # Leave some space at top and bottom
        
        # First wall (left side)
        first_wall_x = SCREEN_WIDTH // 4 - wall_width // 2
        walls.append(pygame.Rect(first_wall_x, 75, wall_width, wall_length))
        
        # Second wall (middle) with gap
        second_wall_x = SCREEN_WIDTH // 2 - wall_width // 2
        gap_height = 150  # Height of the gap in the middle wall
        walls.append(pygame.Rect(second_wall_x, 75, wall_width, (wall_length - gap_height) // 2))
        walls.append(pygame.Rect(second_wall_x, 75 + (wall_length - gap_height) // 2 + gap_height, 
                                wall_width, (wall_length - gap_height) // 2))
        
        # Third wall (right side)
        third_wall_x = 3 * SCREEN_WIDTH // 4 - wall_width // 2
        walls.append(pygame.Rect(third_wall_x, 75, wall_width, wall_length))
        
        # Add 3 magic gems to the zone, ensuring they don't overlap with walls
        self.resources = []
        
        # Function to check if a position is safe for a gem (not overlapping walls)
        def is_position_safe(x, y, gem_size=24):
            gem_rect = pygame.Rect(x, y, gem_size, gem_size)
            return not any(gem_rect.colliderect(wall) for wall in walls)
        
        # Try to place gems in these positions, find alternatives if needed
        gem_attempts = [
            (150, 150),  # Top-left area
            (SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT // 2),  # Middle area
            (150, SCREEN_HEIGHT - 200)  # Bottom-left area
        ]
        
        for x, y in gem_attempts:
            gem = Resource(x, y)
            # If position is not safe, try nearby positions
            if not is_position_safe(x, y):
                # Try positions in a spiral pattern
                for radius in range(20, 200, 20):
                    for angle in range(0, 360, 45):
                        rad = math.radians(angle)
                        new_x = max(20, min(SCREEN_WIDTH - 44, x + int(radius * math.cos(rad))))
                        new_y = max(20, min(SCREEN_HEIGHT - 44, y + int(radius * math.sin(rad))))
                        if is_position_safe(new_x, new_y):
                            gem.rect.x = new_x
                            gem.rect.y = new_y
                            break
                    if is_position_safe(gem.rect.x, gem.rect.y):
                        break
            self.resources.append(gem)
        
        # Add 2 NPCs to the zone (1 elder and 1 child)
        self.npcs = [
            NPC(SCREEN_WIDTH - 150, 200, needs_help=True, npc_type='elder'),
            NPC(SCREEN_WIDTH - 150, 400, needs_help=True, npc_type='child')
        ]
        
        return walls
    
    def position_player_in_safe_area(self):
        """Position the player in a safe area without wall collisions"""
        # Start at the center of the screen
        self.player.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        # If player is in a wall, try to find a nearby safe position
        for wall in self.walls:
            if self.player.rect.colliderect(wall):
                # Try moving player in a spiral pattern until we find a safe spot
                for radius in range(10, 200, 10):
                    for angle in range(0, 360, 45):
                        rad = math.radians(angle)
                        self.player.rect.x = SCREEN_WIDTH // 2 + int(radius * math.cos(rad))
                        self.player.rect.y = SCREEN_HEIGHT // 2 + int(radius * math.sin(rad))
                        
                        # Ensure we're within screen bounds
                        self.player.rect.x = max(0, min(self.player.rect.x, SCREEN_WIDTH - self.player.width))
                        self.player.rect.y = max(0, min(self.player.rect.y, SCREEN_HEIGHT - self.player.height))
                        
                        # Check if this position is safe
                        if not any(self.player.rect.colliderect(w) for w in self.walls):
                            return
        
        # If we're in the maze zone, make sure we're not in an exit
        if self.state == GameState.ZONE_MAZE and self.exit_rects:
            for exit_rect in self.exit_rects:
                if self.player.rect.colliderect(exit_rect):
                    # Move player away from exit
                    self.player.rect.x = SCREEN_WIDTH // 2
                    self.player.rect.y = SCREEN_HEIGHT // 2
                    
    def help_npc(self, npc):
        """Help an NPC with a resource if available"""
        # Only allow helping NPCs in Zone 3
        if self.state != GameState.ZONE_RIVERBANK:
            return False
            
        # Handle reviving a dead NPC in Zone 3
        if npc.dead and self.state == GameState.ZONE_RIVERBANK:
            if self.player.resources >= 5:
                # Fully restore the NPC to 5/5 gems
                npc.dead = False
                npc.needs_help = False
                npc.helped = True
                npc.gems_given = 5
                npc.gems_required = 5
                self.player.resources -= 5
                self.revived_npc = True
                self.show_message(
                    f"You've fully revived and restored the {npc.npc_type} to full health with 5 gems!",
                    120
                )
                npc.update_sprite()
                return True
            else:
                self.show_message(f"You need 5 gems to revive the {npc.npc_type}.", 120)
                return False
            
        # Normal gem giving to living NPCs
        if self.player.resources > 0 and not npc.helped and not npc.dead:
            npc.gems_given += 1
            self.player.resources -= 1
            
            # Check if NPC has received enough gems
            gems_needed = npc.gems_required - npc.gems_given
            
            if gems_needed <= 0:
                npc.helped = True
                npc.needs_help = False
                self.show_message(
                    f"The {npc.npc_type} has received all {npc.gems_required} gems! "
                    f"You have {self.player.resources} gems left.", 
                    120
                )
            else:
                self.show_message(
                    f"Gave a gem to the {npc.npc_type}. {gems_needed} more needed. "
                    f"You have {self.player.resources} gems left.", 
                    90
                )
            
            npc.update_sprite()
            
            # Check if both NPCs have been fully helped
            living_npcs = [n for n in self.npcs if not n.dead]
            if all(n.helped for n in living_npcs if not n.dead):
                self.show_message("You've helped everyone in need! Find the enlightenment.", 180)
                # Create enlightenment rectangle when all living NPCs are helped
                self.enlightenment_rect = pygame.Rect(
                    SCREEN_WIDTH // 2 - 25,
                    SCREEN_HEIGHT - 100,
                    50,
                    50
                )
            return True
            
        # Handle various error cases
        if npc.dead:
            self.show_message(f"You need 5 gems to revive the {npc.npc_type}.", 90)
        elif npc.helped:
            self.show_message(f"The {npc.npc_type} has already received enough gems.", 90)
        elif self.player.resources <= 0:
            self.show_message("You don't have any gems to give!", 90)
            
        return False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                # Space bar to transition from intro to Zone 1
                if event.key == pygame.K_SPACE and self.state == GameState.INTRO:
                    self.state = GameState.ZONE_SCARCITY
                    self.setup_zones()
                    self.position_player_in_safe_area()
                    self.show_message("Welcome to Zone 1: Scarcity. Collect resources and help the NPCs.", 120)
                
                # Handle choices when active
                if self.choice_active:
                    if event.key == pygame.K_1:  # Help elder
                        # Elder gets 2 resources, player keeps 1
                        self.player.resources -= 2
                        self.npcs[0].helped = True
                        self.npcs[0].needs_help = False
                        self.npcs[0].update_sprite()
                        self.npcs[1].dead = True
                        self.npcs[1].update_sprite()
                        self.show_message(f"You gave 2 resources to the elder and kept 1. The child fades away...")
                        self.choice_made = 'elder'
                        self.choice_active = False
                    elif event.key == pygame.K_2:  # Help child
                        # Child gets 2 resources, player keeps 1
                        self.player.resources -= 2
                        self.npcs[1].helped = True
                        self.npcs[1].needs_help = False
                        self.npcs[1].update_sprite()
                        self.npcs[0].dead = True
                        self.npcs[0].update_sprite()
                        self.show_message(f"You gave 2 resources to the child and kept 1. The elder fades away...")
                        self.choice_made = 'child'
                        self.choice_active = False
                    elif event.key == pygame.K_3:  # Help both
                        # Each NPC gets 1.5 resources, player keeps 0
                        for npc in self.npcs:
                            npc.helped = True
                            npc.needs_help = False
                            npc.update_sprite()
                        self.player.resources = 0
                        self.show_message("You shared your resources equally. Both NPCs survive with 1.5 resources each, but you have none left...")
                        self.choice_made = 'both'
                        self.choice_active = False
                    elif event.key == pygame.K_4:  # Help neither
                        for npc in self.npcs:
                            npc.dead = True
                            npc.update_sprite()
                        self.show_message(f"You kept all {self.player.resources} resources for yourself, but both NPCs fade away...")
                        self.choice_made = 'neither'
                        self.choice_active = False
                    
                    # After any choice in Zone 1, transition to Zone 2 (the maze)
                    if self.choice_made:
                        self.state = GameState.ZONE_MAZE
                        self.setup_zones()
                        self.show_message("You feel a strange force pulling you into a mysterious maze...", 180)
                
                # Restart game with R key
                if event.key == pygame.K_r:
                    self.__init__()  # Restart the game
                    return True  # Return True to continue running
        
        # Handle continuous key presses for movement
        keys = pygame.key.get_pressed()
        
        # Debug info occasionally
        frame_count = pygame.time.get_ticks() // 16  # Approximate frame count
        if frame_count % 60 == 0:  # Only print once per second
            print(f"Player position: ({self.player.rect.x}, {self.player.rect.y})")
            print(f"Walls count: {len(self.walls)}")
        
        dx, dy = 0, 0
        speed = 3  # Base movement speed
        
        if not self.choice_active and self.state != GameState.INTRO:  # Don't move during choice or intro
            # Check for movement keys
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = speed
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = speed
            
            # Move the player if there's input
            if dx != 0 or dy != 0:
                self.player.move(dx, dy, self.walls)
        
        return True
    
    def check_exit_collision(self):
        """Check if player has reached an exit in the maze."""
        if self.state != GameState.ZONE_MAZE or not hasattr(self, 'exit_rects') or not self.exit_rects:
            return False
            
        player_rect = self.player.rect
        
        # Check which exit (if any) the player has reached
        for i, exit_rect in enumerate(self.exit_rects):
            if player_rect.colliderect(exit_rect):
                if i == self.correct_exit:
                    # Correct exit found - transition to Zone 3
                    self.state = GameState.ZONE_RIVERBANK
                    self.setup_zones()
                    self.position_player_in_safe_area()
                    self.show_message("You found the path to the riverbank!", 180)
                    return True
                else:
                    # Wrong exit - push player back and show message
                    self.show_message("This isn't the right way. Try another exit!", 120)
                    # Push player away from the exit
                    if i == 0:  # Top exit
                        self.player.rect.y = exit_rect.bottom + 10
                    elif i == 1:  # Right exit
                        self.player.rect.x = exit_rect.left - self.player.width - 10
                    elif i == 2:  # Bottom exit
                        self.player.rect.y = exit_rect.top - self.player.height - 10
                    else:  # Left exit
                        self.player.rect.x = exit_rect.right + 10
                    # Ensure player is still in bounds
                    self.player.rect.x = max(0, min(self.player.rect.x, SCREEN_WIDTH - self.player.width))
                    self.player.rect.y = max(0, min(self.player.rect.y, SCREEN_HEIGHT - self.player.height))
                    return False
        return False

    def update(self):
        # Update message timers
        if self.messages:
            text, duration = self.messages[0]
            self.message_timer += 1
            if self.message_timer > duration:
                self.messages.pop(0)
                self.message_timer = 0
        
        # Auto-transition from intro to Zone 1 after a delay
        if self.state == GameState.INTRO:
            if pygame.time.get_ticks() > 3000:  # 3 seconds
                self.state = GameState.ZONE_SCARCITY
                self.setup_zones()
                self.position_player_in_safe_area()
                self.show_message("Welcome to Zone 1: Scarcity. Collect magic gems and help the NPCs.", 120)
                return
        
        # Handle player movement if not in dialogue
        if not self.choice_active:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = 1
            
            # Only move if we have some input
            if dx != 0 or dy != 0:
                self.player.move(dx, dy, self.walls)
            
            # Check for space bar press to interact with NPCs in Zone 3
            if self.state == GameState.ZONE_RIVERBANK and keys[pygame.K_SPACE]:
                for npc in self.npcs:
                    if (abs(self.player.rect.centerx - npc.rect.centerx) < 50 and 
                        abs(self.player.rect.centery - npc.rect.centery) < 50):
                        self.help_npc(npc)
                        break
        
        # Check for resource collection in all zones
        if self.state in [GameState.ZONE_SCARCITY, GameState.ZONE_RIVERBANK]:
            resource, all_collected = self.player.collect_resource(self.resources)
            if resource is not None:
                self.show_message(f"Collected a magic gem! ({self.player.resources}/3)", 60)
                if all_collected and not self.choice_active and self.state == GameState.ZONE_SCARCITY:
                    self.choice_active = True
                    self.show_message("\n1. Help the elder\n2. Help the child\n3. Split resources between both\n4. Keep all resources", 300)
        
        # Zone-specific updates
        if self.state == GameState.ZONE_MAZE:
            self.check_exit_collision()  # This will handle the zone transition
        
        # Zone 3: Riverbank - free movement with wall collisions only
        elif self.state == GameState.ZONE_RIVERBANK:
            # Check if all NPCs have been helped and create enlightenment rectangle
            all_helped = all(npc.helped for npc in self.npcs if not npc.dead)
            
            # Create enlightenment rectangle in bottom right if all NPCs are helped
            if all_helped and self.enlightenment_rect is None:
                enlightenment_size = 100
                padding = 50
                self.enlightenment_rect = pygame.Rect(
                    SCREEN_WIDTH - enlightenment_size - padding,
                    SCREEN_HEIGHT - enlightenment_size - padding,
                    enlightenment_size,
                    enlightenment_size
                )
                self.show_message("The path to enlightenment has appeared in the bottom right!", 180)
            
            # Check for reaching the enlightenment rectangle
            # Only allow victory if both NPCs are alive and all have been helped
            both_npcs_alive = all(not npc.dead for npc in self.npcs)
            if self.enlightenment_rect and self.player.rect.colliderect(self.enlightenment_rect) and all_helped and both_npcs_alive:
                print("Victory condition met! Transitioning to VICTORY state")
                self.state = GameState.VICTORY
                self.victory_shown = True
                # Force a redraw immediately
                self.draw()
                pygame.display.flip()
                return  # Skip the rest of the update
            elif self.enlightenment_rect and self.player.rect.colliderect(self.enlightenment_rect) and not both_npcs_alive:
                self.show_message("You must revive both NPCs to achieve enlightenment!", 120)
                return  # Skip the rest of the update

    def draw(self):
        # Clear screen
        self.screen.fill(BLACK)
        
        # Debug output
        #print(f"Draw called. State: {self.state}, Victory shown: {self.victory_shown}")
        
        # Check for victory state first - only show the victory screen
        if self.state == GameState.VICTORY or self.victory_shown:
            # Fill with black background
            self.screen.fill(BLACK)
            
            # Create a white border rectangle
            border_size = 20
            border_rect = pygame.Rect(
                border_size,
                border_size,
                SCREEN_WIDTH - 2 * border_size,
                SCREEN_HEIGHT - 2 * border_size
            )
            pygame.draw.rect(self.screen, WHITE, border_rect, 2)  # 2 pixel thick border
            
            # Create fonts for the victory text
            title_font = pygame.font.Font(None, 60)  # Smaller title font
            message_font = pygame.font.Font(None, 32)  # Smaller message font
            
            # Title
            title_text = title_font.render("ENLIGHTENMENT ACHIEVED", True, WHITE)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 100))
            
            # Main messages
            message1 = "You can afford more goodness than you think!"
            message2 = "Goodness is the best investment for a better world."
            
            # Render and position first message
            message1_surface = message_font.render(message1, True, WHITE)
            message1_rect = message1_surface.get_rect(center=(SCREEN_WIDTH//2, 200))
            
            # Render and position second message below the first
            message2_surface = message_font.render(message2, True, WHITE)
            message2_rect = message2_surface.get_rect(center=(SCREEN_WIDTH//2, 240))
            
            # Draw the title and messages
            self.screen.blit(title_text, title_rect)
            self.screen.blit(message1_surface, message1_rect)
            self.screen.blit(message2_surface, message2_rect)
                
            # Add a prompt to exit
            prompt_font = pygame.font.Font(None, 30)
            prompt_text = prompt_font.render("Press ESC to exit or R to restart", True, WHITE)
            prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
            self.screen.blit(prompt_text, prompt_rect)
            
            self.victory_shown = True
            return  # Skip drawing everything else
            
        # Draw zone-specific elements
        if self.state == GameState.ZONE_RIVERBANK:
            # Draw the background (black for land)
            self.screen.fill(BLACK)
            
            # Draw river (blue)
            if self.river:
                for segment in self.river:
                    pygame.draw.rect(self.screen, (0, 100, 200), segment)
            
            # Draw rocks in the river
            for rock in self.rocks:
                pygame.draw.rect(self.screen, (100, 100, 100), rock)
            
            # Draw goal (green)
            if self.goal:
                pygame.draw.rect(self.screen, (0, 255, 0), self.goal)
        
        # Draw resources (gems)
        for resource in self.resources:
            resource.draw(self.screen)
        
        # Draw NPCs
        for npc in self.npcs:
            npc.draw(self.screen, self.font)
            
        # Draw the player (on top of everything else)
        self.player.draw(self.screen)
        
        # Draw the enlightenment rectangle if it exists
        if self.enlightenment_rect and self.state == GameState.ZONE_RIVERBANK:
            # Draw a glowing yellow circle for enlightenment
            glow_surface = pygame.Surface((self.enlightenment_rect.width * 2, self.enlightenment_rect.height * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (255, 255, 0, 64), 
                             (self.enlightenment_rect.width, self.enlightenment_rect.height), 
                             self.enlightenment_rect.width)
            self.screen.blit(glow_surface, 
                           (self.enlightenment_rect.x - self.enlightenment_rect.width//2, 
                            self.enlightenment_rect.y - self.enlightenment_rect.height//2))
            
            # Draw the main circle
            pygame.draw.circle(self.screen, (255, 255, 0), 
                             (self.enlightenment_rect.x + self.enlightenment_rect.width//2, 
                              self.enlightenment_rect.y + self.enlightenment_rect.height//2), 
                             self.enlightenment_rect.width//2)
            
            # Add a pulsing effect
            pulse_size = int(10 * abs(math.sin(pygame.time.get_ticks() * 0.005)))
            pygame.draw.circle(self.screen, (255, 255, 100), 
                             (self.enlightenment_rect.x + self.enlightenment_rect.width//2, 
                              self.enlightenment_rect.y + self.enlightenment_rect.height//2), 
                             self.enlightenment_rect.width//4 + pulse_size)
        
        # Draw walls for other zones
        if self.state != GameState.ZONE_RIVERBANK:
            for wall in self.walls:
                pygame.draw.rect(self.screen, WHITE, wall)
                
        # Draw exit indicators in Zone 2 (all exits look the same)
        if self.state == GameState.ZONE_MAZE and self.exit_rects:
            for exit_rect in self.exit_rects:
                # Draw a thin white line for all exits
                pygame.draw.rect(self.screen, WHITE, exit_rect, 1)

        # Draw messages
        if self.messages:
            text, _ = self.messages[0]
            text_surface = self.font.render(text, True, WHITE)
            self.screen.blit(text_surface, (10, 10))

        # Draw choice interface last (on top of everything else)
        if self.choice_active:
            # Semi-transparent overlay (covers everything)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))  # Semi-transparent black
            self.screen.blit(overlay, (0, 0))

            # Draw choice box
            box_width = 600
            box_height = 300
            box_x = (SCREEN_WIDTH - box_width) // 2
            box_y = (SCREEN_HEIGHT - box_height) // 2

            # Main box
            pygame.draw.rect(self.screen, (30, 30, 30), (box_x, box_y, box_width, box_height))
            pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_width, box_height), 2)

            # Draw title with a subtle highlight
            title_bg = pygame.Surface((box_width - 20, 40), pygame.SRCALPHA)
            title_bg.fill((255, 255, 255, 30))  # Slight white background for title
            self.screen.blit(title_bg, (box_x + 10, box_y + 10))

            title = self.font.render("A Difficult Choice", True, (255, 255, 150))  # Light yellow
            title_x = box_x + (box_width - title.get_width()) // 2
            self.screen.blit(title, (title_x, box_y + 20))

            # Draw choices
            choices = [
                "1. Help the elder (give 2, keep 1, child dies)",
                "2. Help the child (give 2, keep 1, elder dies)",
                "3. Help both (share equally, 1.5 each, you get 0)",
                f"4. Help neither (keep all {self.player.resources} resources, both die)"
            ]

            # Choice background
            choices_bg = pygame.Surface((box_width - 40, 200), pygame.SRCALPHA)
            choices_bg.fill((255, 255, 255, 20))  # Very subtle background for choices
            self.screen.blit(choices_bg, (box_x + 20, box_y + 70))

            for i, choice in enumerate(choices):
                y_offset = box_y + 70 + i * 40
                # Highlight the number key more prominently
                key_surface = self.font.render(str(i+1), True, (255, 255, 0))  # Yellow for keys
                self.screen.blit(key_surface, (box_x + 30, y_offset))
                # Draw choice text
                text = self.font.render(choice[3:], True, WHITE)  # Skip the number (already drawn)
                self.screen.blit(text, (box_x + 50, y_offset))

            # Draw instruction at bottom
            instruction = self.font.render("Press 1-4 to make your choice...", True, (200, 200, 200))
            self.screen.blit(instruction, (box_x + (box_width - instruction.get_width()) // 2, box_y + box_height - 40))

        # Update the display
        pygame.display.flip()

    def show_message(self, text: str, duration: int = 60):
        """
        Add a message to be displayed on screen
        Duration is in frames (60 frames = 1 second at 60 FPS)
        """
        self.messages.append((text, duration))

    def run(self):
        """Main game loop"""
        running = True
        while running:
            running = self.handle_events()
            
            # Only update game logic if not in victory state
            if self.state != GameState.VICTORY:
                self.update()
            
            # Always draw, but draw different things based on state
            self.draw()
            
            # Update the display
            pygame.display.flip()
            self.clock.tick(60)  # Cap at 60 FPS

if __name__ == "__main__":
    try:
        print("Initializing game...")
        game = Game()
        print("Game initialized. Starting main loop...")
        game.run()
    except Exception as e:
        import traceback
        print(f"An error occurred: {e}")
        traceback.print_exc()
        input("Press Enter to exit...")
    finally:
        pygame.quit()
        sys.exit()
