import pygame
from pygame.locals import *

import resourcemanager

import random
import math

class Tile(object):
    """A tile definition.
    """
    def __init__(self, image, is_blocked=False):
        self.image = image
        self.is_blocked = is_blocked

class TileMap(object):
    """A tilemap that handles display and collision with tiles.
    """

    def __init__(self, tileset, default_tile, w, h, tile_w, tile_h):
        self.tileset = tileset
        self.w, self.h = w, h
        self.tile_w, self.tile_h = tile_w, tile_h

        self.tiles = [[default_tile
                       for _ in range(h)]
                      for _ in range(w)]

    def random_fill(self, tile_list):
        for x in range(self.w):
            for y in range(self.h):
                self.tiles[x][y] = tile_list[random.randint(0, len(tile_list)-1)]

# Change to use mini tile_sets - (lists of names)
# Have a filter to fix based on rules - change tiles to their correct edge type                
    def add_box(self, x, y, w, h, tile_name):
        """Add a box of a given tile to the map.
        """
        tile = self.tileset[tile_name]
        
        for i in range(x, x + w):
            self.tiles[i][y] = tile
            self.tiles[i][y + h - 1] = tile 
            
        for i in range(y, y + h):
            self.tiles[x][i] = tile
            self.tiles[x + w - 1][i] = tile

    def add_filled_box(self, x, y, w, h, tile_name):
        """Add a box of a given tile to the map.
        """
        tile = self.tileset[tile_name]
        for i in range(x, x + w):
            for j in range(y, y + h):
                self.tiles[i][j] = tile
            
    def add_circle(self, x, y, radius, tile_name):
        """Add a filled circle.
        """
        tile = self.tileset[tile_name]
        
        def dist(x1, y1):
            return math.sqrt((x - x1) ** 2 + (y - y1) ** 2)
        
        for i in range(max(0, x-radius), min(x+radius, self.w-1)):
            for j in range(max(0, y-radius), min(y+radius, self.h-1)):
                if dist(i, j) <= radius:
                    self.tiles[i][j] = tile
        
    def add_edge_wall(self, tile_name):
        """Add walls to edge.
        """
        self.add_box(0, 0, self.w, self.h, tile_name)

    def add_line(self, x0, y0, x1, y1, tile_name):
        """Adds a line of the tile to the map.
        Uses bresenham's line algorithm
        """
        tile = self.tileset[tile_name]
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        error = dx - dy

        if x0 >= 0 and x0 < self.w and y0 >= 0 and y0 < self.h:        
            self.tiles[x0][y0] = tile
        while x0 != x1 or y0 != y1:
            e2 = 2 * error
            if e2 > -dy:
                error -= dy
                x0 += sx
            
            if e2 < dx:
                error += dx
                y0 += sy

            if x0 >= 0 and x0 < self.w and y0 >= 0 and y0 < self.h:
                self.tiles[x0][y0] = tile

    def fix_brick_walls(self):
        """After generation, this pass fixes up how walls connect to each other.
        """
        bricks = resourcemanager.tilesets["brick_tiles"]
        castlewalls = resourcemanager.tilesets["castle_tiles"] 
        
        for i in xrange(0, self.w):
            for j in xrange(0, self.h):
                if self.tiles[i][j] in bricks:
                    above = 0 if j == 0 else int(not self.tiles[i][j-1] in bricks)
                    below = 0 if j == self.h-1 else int(not self.tiles[i][j+1] in bricks)
                    left  = 0 if i == 0 else int(not self.tiles[i-1][j] in bricks)
                    right = 0 if i == self.w-1 else int(not self.tiles[i+1][j] in bricks)
                    self.tiles[i][j] = bricks[above * 8 + right * 4 + below * 2 + left]
                elif self.tiles[i][j] in castlewalls:
                    above = 0 if j == 0 else int(not self.tiles[i][j-1] in castlewalls)
                    below = 0 if j == self.h-1 else int(not self.tiles[i][j+1] in castlewalls)
                    left  = 0 if i == 0 else int(not self.tiles[i-1][j] in castlewalls)
                    right = 0 if i == self.w-1 else int(not self.tiles[i+1][j] in castlewalls)
                    self.tiles[i][j] = castlewalls[above * 8 + right * 4 + below * 2 + left]
        
    def collide(self, rect, dx, dy):
        """Tests for collision with the tilemap.
        Should not collide with a tile if entity is already inside that tile. (So we don't get stuck)
        """

        collision = False
        if dx == 0 and dy == 0:
            return 0, 0, collision
        
        x, y, w, h = rect

        # Handle largest movement first - means if we angle towards a corner, we will move to the
        # side that we are moving towards, not always biased to horizontal movement

        # Handle x movement
        if dx > 0:
            # X range to the right
            # From smallest to largest, so we stop as early as possible
            for tile_x in range(int((x + w) / self.tile_w) + 1,
                                int((x + w + dx) / self.tile_w) + 1):

                # Y range in centre             
                for tile_y in range(int(y / self.tile_h),
                                    int((y + h) / self.tile_h) + 1):

                    # This actually seems right, I can't even fucking believe it
                    if self.tiles[tile_x][tile_y].is_blocked:
                        # Keep dx limited to this value
                        x_to_be_hard_against = (tile_x - 1) * self.tile_w + self.tile_w
                        x_to_be_at = x_to_be_hard_against - w - 1 # Possibly -1
                        dx = x_to_be_at - x
                        collision = True
                        break
                
        else:
            # X range to the left            
            for tile_x in range(int((x) / self.tile_w) - 1,
                                int((x + dx) / self.tile_w) - 1, -1):
                
                # Y range in centre 
                for tile_y in range(int(y / self.tile_h),
                                    int((y + h) / self.tile_h) + 1):

                    # This actually seems right, I can't even fucking believe it                    
                    if self.tiles[tile_x][tile_y].is_blocked:
                        # Keep dx limited to this value
                        x_to_be_hard_against = (tile_x + 1) * self.tile_w
                        x_to_be_at = x_to_be_hard_against # Possibly +1
                        dx = x_to_be_at - x
                        collision = True
                        break

        # Handle y movement
        if dy > 0:
            # Y range below
            # From smallest to largest, so we stop as early as possible
            for tile_y in range(int((y + h) / self.tile_h) + 1,
                                int((y + h + dy) / self.tile_h) + 1):

                # X range in centre             
                for tile_x in range(int((x + dx) / self.tile_w),
                                    int((x + w + dx) / self.tile_w) + 1):

                    # This actually seems right, I can't even fucking believe it
                    if self.tiles[tile_x][tile_y].is_blocked:
                        # Keep dy limited to this value
                        y_to_be_hard_against = (tile_y - 1) * self.tile_h + self.tile_h
                        y_to_be_at = y_to_be_hard_against - h - 1 # Possibly -1
                        dy = y_to_be_at - y
                        collision = True
                        break
                
        else:
            # Y range above            
            for tile_y in range(int((y) / self.tile_h) - 1,
                                int((y + dy) / self.tile_h) - 1, -1):
                # X range in centre 
                for tile_x in range(int((x + dx) / self.tile_w),
                                    int((x + dx + w) / self.tile_w) + 1):
                    # This actually seems right, I can't even fucking believe it                    
                    if self.tiles[tile_x][tile_y].is_blocked:
                        # Keep dy limited to this value
                        y_to_be_hard_against = (tile_y + 1) * self.tile_h
                        y_to_be_at = y_to_be_hard_against # Possibly +1
                        dy = y_to_be_at - y
                        collision = True
                        break

        return dx, dy, collision

    def display(self, screen, camera):
        cx, cy, cw, ch = camera
        for i in xrange(max(0, cx / self.tile_w),
                        min((cx + cw) / self.tile_w + 1, len(self.tiles))):
            for j in xrange(max(0, cy / self.tile_h),
                            min((cy + ch) / self.tile_h + 1, len(self.tiles[i]))):

                self.tiles[i][j].image.draw(screen, (i * self.tile_w - cx, j * self.tile_h - cy))

