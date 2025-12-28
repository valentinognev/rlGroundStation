import tkinter as tk
from PIL import ImageTk 
import core.cfg as cfg
from core import geo_math
import core.tile_utils as tile_utils
from ui.hud import HUD
from ui.input_handler import InputHandler
from ui.tile_loader import TileLoader # New Import
import math

class MapCanvas(tk.Canvas):
    def __init__(self, parent, bounds, width, height, resolution, on_redraw=None):
        super().__init__(parent, width=width, height=height, bg="white")
        
        self._initialized = False 
        self.dims = (width, height)
        self.padding = cfg.PADDING 
        self.resolution = resolution
        self.on_redraw = on_redraw
        
        # --- MAP LAYERS ---
        self.tile_loader = TileLoader()
        self.tk_images = [] # Keep references to prevent Garbage Collection
        
        self.hud = HUD(self)
        self.input_handler = InputHandler(self)
        
        self.update_view_settings(bounds, resolution)
        self._initialized = True

    def update_view_settings(self, bounds, resolution):
        self.bounds = bounds
        self.resolution = resolution
        if self.resolution <= 1e-8: self.resolution = 1e-8
        
        self.meters_per_px = self.resolution * 111139
        self.px_per_meter = 1.0 / self.meters_per_px if self.meters_per_px > 0 else 1.0
        
        self.delete("all")
        
        # 1. Draw Map Tiles (Bottom Layer)
        self.draw_map_tiles()
        
        # 2. Draw Grid & UI
        self.draw_axes()
        self.update_grid_labels()
        
        if self._initialized and self.on_redraw:
            self.on_redraw()

    def draw_map_tiles(self):
        """
        Calculates visible tiles and draws them.
        """
        # Clear old tile images
        self.delete("map_tile")
        self.tk_images.clear()
        
        min_lat, max_lat, min_lon, max_lon = self.bounds
        
        # 1. Determine Zoom Level
        zoom = tile_utils.calculate_zoom_level(self.resolution)
        
        # 2. Determine Tile Range
        x_min, y_min = tile_utils.deg2num(max_lat, min_lon, zoom)
        x_max, y_max = tile_utils.deg2num(min_lat, max_lon, zoom)
        
        # Handle wrapping/edge cases simply
        x_range = range(x_min, x_max + 2)
        y_range = range(y_min, y_max + 2)
        
        missing_tiles = False
        
        for x in x_range:
            for y in y_range:
                # Get the Lat/Lon of the top-left corner of this tile
                tile_lat, tile_lon = tile_utils.num2deg(x, y, zoom)
                
                # Get Image
                pil_img = self.tile_loader.get_tile(x, y, zoom)
                
                if pil_img:
                    # Determine where to draw it on screen
                    # 1 Tile = 256x256 pixels usually, but we need to scale it to OUR zoom
                    
                    # Coordinate of Top-Left
                    screen_x, screen_y = geo_math.lat_lon_to_screen(
                        tile_lat, tile_lon, self.bounds, self.dims, self.padding
                    )
                    
                    # Coordinate of Bottom-Right (next tile)
                    next_lat, next_lon = tile_utils.num2deg(x + 1, y + 1, zoom)
                    end_x, end_y = geo_math.lat_lon_to_screen(
                        next_lat, next_lon, self.bounds, self.dims, self.padding
                    )
                    
                    # Calculate Scale Width/Height
                    w = int(end_x - screen_x) + 1 # +1 to avoid gap lines
                    h = int(end_y - screen_y) + 1
                    
                    if w > 0 and h > 0:
                        # Resize for display
                        resized = pil_img.resize((w, h), 0) # 0 = Nearest Neighbor (Fast)
                        tk_img = ImageTk.PhotoImage(resized)
                        self.tk_images.append(tk_img) # Keep ref
                        
                        self.create_image(screen_x, screen_y, image=tk_img, anchor="nw", tags="map_tile")
                else:
                    missing_tiles = True

        # If tiles were missing, they are downloading. Check back soon.
        if missing_tiles:
            self.after(200, self.refresh_tiles_only)

    def refresh_tiles_only(self):
        """Helper to redraw tiles without resetting the whole view logic."""
        # Only if we are initialized to avoid race conditions
        if self._initialized:
            self.draw_map_tiles()
            # We must raise the drones/grid above the new tiles
            self.tag_raise("static_ui") 
            self.tag_raise("drone")
            self.tag_raise("hud")

    # --- KEEP OTHER METHODS (zoom, pan, draw_axes, etc.) SAME ---
    # ... I will re-paste the crucial unmodified parts to ensure context ...
    
    def zoom(self, factor, cx, cy):
        # (Same implementation as previous step)
        # ...
        # Copy-paste logic from previous response's zoom
        pad_l, pad_t, pad_r, pad_b = self.padding
        w, h = self.dims
        active_w = w - pad_l - pad_r
        active_h = h - pad_t - pad_b
        screen_center_x = pad_l + (active_w / 2.0)
        screen_center_y = pad_t + (active_h / 2.0)
        dx_px = cx - screen_center_x
        dy_px = cy - screen_center_y
        cur_min_lat, cur_max_lat, cur_min_lon, cur_max_lon = self.bounds
        cur_center_lat = (cur_min_lat + cur_max_lat) / 2.0
        cur_center_lon = (cur_min_lon + cur_max_lon) / 2.0
        lat_mouse = cur_center_lat - (dy_px * self.resolution)
        lon_mouse = cur_center_lon + (dx_px * self.resolution)
        new_res = self.resolution * factor
        if new_res <= 1e-8: new_res = 1e-8
        new_center_lat = lat_mouse + (dy_px * new_res)
        new_center_lon = lon_mouse - (dx_px * new_res)
        self.resolution = new_res
        self.set_center(new_center_lat, new_center_lon)

    def update_pan(self, dx, dy):
        # Slightly modified to update tiles during pan
        self.move("drone", dx, dy)
        self.move("map_tile", dx, dy) # Move tiles too
        
        d_lon = -dx * self.resolution
        d_lat = dy * self.resolution
        
        min_lat, max_lat, min_lon, max_lon = self.bounds
        self.bounds = (
            min_lat + d_lat, max_lat + d_lat,
            min_lon + d_lon, max_lon + d_lon
        )
        self.update_grid_labels()
        
        # Redraw tiles occasionally during pan or at end? 
        # For smooth pan, we just move pixels. We load new tiles at end_pan.

    def end_pan(self):
        # When drag ends, we recalculate which tiles we need
        self.draw_map_tiles()
        self.tag_raise("static_ui")
        self.tag_raise("drone")
        self.tag_raise("hud")

    def set_center(self, lat, lon):
        w, h = self.dims
        pad_l, pad_t, pad_r, pad_b = self.padding
        active_w = w - pad_l - pad_r
        active_h = h - pad_t - pad_b
        lat_range = active_h * self.resolution
        lon_range = active_w * self.resolution
        min_lat = lat - (lat_range / 2.0)
        max_lat = lat + (lat_range / 2.0)
        min_lon = lon - (lon_range / 2.0)
        max_lon = lon + (lon_range / 2.0)
        self.update_view_settings((min_lat, max_lat, min_lon, max_lon), self.resolution)

    def draw_hud(self, active_states, colors):
        self.hud.clear()
        self.hud.draw_keep_alive(active_states, colors, self.dims, self.padding)
        self.hud.draw_gps_fix(active_states, colors, self.dims, self.padding)

    def draw_axes(self):
        # (Same as before)
        w, h = self.dims
        pad_l, pad_t, pad_r, pad_b = self.padding
        draw_w = w - pad_l - pad_r
        draw_h = h - pad_t - pad_b
        self.create_line(pad_l, pad_t, pad_l, h - pad_b, fill="black", width=2, tags="static_ui")
        self.create_line(pad_l, h - pad_b, w - pad_r, h - pad_b, fill="black", width=2, tags="static_ui")
        steps = 5
        for i in range(steps + 1):
            pct = i / steps
            y_pos = (h - pad_b) - (pct * draw_h)
            self.create_line(pad_l - 5, y_pos, pad_l, y_pos, fill="black", tags="static_ui")
            self.create_text(pad_l - 10, y_pos, text="", anchor="e", font=("Arial", 8), tags=f"label_lat_{i}")
            x_pos = pad_l + (pct * draw_w)
            self.create_line(x_pos, h - pad_b, x_pos, h - pad_b + 5, fill="black", tags="static_ui")
            self.create_text(x_pos, h - pad_b + 15, text="", anchor="n", font=("Arial", 8), tags=f"label_lon_{i}")

    def update_grid_labels(self):
        # (Same as before)
        min_lat, max_lat, min_lon, max_lon = self.bounds
        steps = 5
        for i in range(steps + 1):
            pct = i / steps
            lat = min_lat + pct * (max_lat - min_lat)
            self.itemconfigure(f"label_lat_{i}", text=f"{lat:.5f}")
            lon = min_lon + pct * (max_lon - min_lon)
            self.itemconfigure(f"label_lon_{i}", text=f"{lon:.5f}")

    def draw_drone(self, lat, lon, heading, color, v_north, v_east):
        # (Same as before)
        cx, cy = geo_math.lat_lon_to_screen(lat, lon, self.bounds, self.dims, self.padding)
        real_r_px = 0.13 * self.px_per_meter
        draw_r = max(real_r_px, 1.5) 
        self.create_oval(cx - draw_r, cy - draw_r, cx + draw_r, cy + draw_r, fill=color, outline=color, tags="drone")
        line_len = max(real_r_px * 2.0, 5.0) 
        rad = math.radians(heading)
        head_x = cx + line_len * math.sin(rad)
        head_y = cy - line_len * math.cos(rad)
        self.create_line(cx, cy, head_x, head_y, fill=color, width=2, tags="drone")
        if abs(v_north) > 0.1 or abs(v_east) > 0.1:
            px_n = v_north * self.px_per_meter
            px_e = v_east * self.px_per_meter
            tx = cx + px_e
            ty = cy - px_n
            self.create_line(cx, cy, tx, ty, fill=color, width=2, arrow=tk.LAST, arrowshape=(8,10,3), tags="drone")

    def clear_drones(self):
        self.delete("drone")