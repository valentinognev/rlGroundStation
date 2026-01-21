import tkinter as tk
from PIL import ImageTk 
import core.cfg as cfg
from core import geo_math
import core.tile_utils as tile_utils
from ui.hud import HUD
from ui.input_handler import InputHandler
from ui.tile_loader import TileLoader 
import math

class MapCanvas(tk.Canvas):
    def __init__(self, parent, bounds, width, height, resolution, on_redraw=None):
        super().__init__(parent, width=width, height=height, bg="white")
        
        self._initialized = False 
        self.dims = (width, height)
        self.padding = cfg.PADDING 
        self.resolution = resolution
        self.on_redraw = on_redraw
        
        self.tile_loader = TileLoader()
        self.tk_images = [] 
        
        self.drone_graphics = {} # {drone_id: {body: id, head: id, arrow: id}}
        self.drawn_ids_this_frame = set()
        
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
        self.drone_graphics.clear()
        self.draw_map_tiles()
        self.draw_axes()
        self.update_grid_labels()
        
        if self._initialized and self.on_redraw:
            self.on_redraw()

    def draw_map_tiles(self):
        self.delete("map_tile")
        self.tk_images.clear()
        
        min_lat, max_lat, min_lon, max_lon = self.bounds
        zoom = tile_utils.calculate_zoom_level(self.resolution)
        x_min, y_min = tile_utils.deg2num(max_lat, min_lon, zoom)
        x_max, y_max = tile_utils.deg2num(min_lat, max_lon, zoom)
        
        x_range = range(x_min, x_max + 2)
        y_range = range(y_min, y_max + 2)
        
        missing_tiles = False
        
        for x in x_range:
            for y in y_range:
                tile_lat, tile_lon = tile_utils.num2deg(x, y, zoom)
                pil_img = self.tile_loader.get_tile(x, y, zoom)
                
                if pil_img:
                    screen_x, screen_y = geo_math.lat_lon_to_screen(
                        tile_lat, tile_lon, self.bounds, self.dims, self.padding
                    )
                    next_lat, next_lon = tile_utils.num2deg(x + 1, y + 1, zoom)
                    end_x, end_y = geo_math.lat_lon_to_screen(
                        next_lat, next_lon, self.bounds, self.dims, self.padding
                    )
                    
                    w = int(end_x - screen_x) + 1 
                    h = int(end_y - screen_y) + 1
                    
                    if w > 0 and h > 0:
                        resized = pil_img.resize((w, h), 0)
                        tk_img = ImageTk.PhotoImage(resized)
                        self.tk_images.append(tk_img)
                        self.create_image(screen_x, screen_y, image=tk_img, anchor="nw", tags="map_tile")
                else:
                    missing_tiles = True

        if missing_tiles:
            self.after(200, self.refresh_tiles_only)

    def refresh_tiles_only(self):
        if self._initialized:
            self.draw_map_tiles()
            self.tag_raise("static_ui") 
            self.tag_raise("drone")
            self.tag_raise("hud")

    def zoom(self, factor, cx, cy):
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
        self.move("drone", dx, dy)
        self.move("map_tile", dx, dy) 
        
        d_lon = -dx * self.resolution
        d_lat = dy * self.resolution
        
        min_lat, max_lat, min_lon, max_lon = self.bounds
        self.bounds = (
            min_lat + d_lat, max_lat + d_lat,
            min_lon + d_lon, max_lon + d_lon
        )
        self.update_grid_labels()

    def end_pan(self):
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
        # Call Telemetry Draw
        self.hud.draw_telemetry(active_states, colors, self.dims, self.padding)

    def draw_axes(self):
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
            self.create_text(
                pad_l - 10, y_pos, 
                text="", anchor="e", font=("Arial", 8), 
                tags=("static_ui", f"label_lat_{i}")
            )
            x_pos = pad_l + (pct * draw_w)
            self.create_line(x_pos, h - pad_b, x_pos, h - pad_b + 5, fill="black", tags="static_ui")
            self.create_text(
                x_pos, h - pad_b + 15, 
                text="", anchor="n", font=("Arial", 8), 
                tags=("static_ui", f"label_lon_{i}")
            )

    def update_grid_labels(self):
        min_lat, max_lat, min_lon, max_lon = self.bounds
        steps = 5
        for i in range(steps + 1):
            pct = i / steps
            lat = min_lat + pct * (max_lat - min_lat)
            self.itemconfigure(f"label_lat_{i}", text=f"{lat:.5f}")
            lon = min_lon + pct * (max_lon - min_lon)
            self.itemconfigure(f"label_lon_{i}", text=f"{lon:.5f}")

    def draw_drone(self, drone_id, lat, lon, heading, color, v_north, v_east):
        cx, cy = geo_math.lat_lon_to_screen(lat, lon, self.bounds, self.dims, self.padding)
        
        # Drone visual radius (0.26m = 2x original 0.13m for better visibility)
        real_r_px = 0.26 * self.px_per_meter
        draw_r = max(real_r_px, 3.0)  # Minimum 3px (2x original 1.5px)
         
        line_len = max(real_r_px * 2.0, 10.0)  # Heading line (2x original minimum) 
        rad = math.radians(heading)
        head_x = cx + line_len * math.sin(rad)
        head_y = cy - line_len * math.cos(rad)
        
        self.drawn_ids_this_frame.add(drone_id)
        
        if drone_id in self.drone_graphics:
            # Update existing
            gfx = self.drone_graphics[drone_id]
            self.coords(gfx['body'], cx - draw_r, cy - draw_r, cx + draw_r, cy + draw_r)
            self.itemconfigure(gfx['body'], fill=color, outline=color, state="normal")
            
            self.coords(gfx['head'], cx, cy, head_x, head_y)
            self.itemconfigure(gfx['head'], fill=color, state="normal")
            
            # Update Label
            self.coords(gfx['label'], cx + draw_r + 5, cy - draw_r - 5)
            self.itemconfigure(gfx['label'], state="normal")

            if abs(v_north) > 0.1 or abs(v_east) > 0.1:
                # Velocity vector scaled 2x to match drone size
                px_n = v_north * self.px_per_meter * 2
                px_e = v_east * self.px_per_meter * 2
                tx = cx + px_e
                ty = cy - px_n
                
                if gfx.get('arrow'):
                    self.coords(gfx['arrow'], cx, cy, tx, ty)
                    self.itemconfigure(gfx['arrow'], fill=color, state="normal")
                else:
                    arrow_id = self.create_line(cx, cy, tx, ty, fill=color, width=2, arrow=tk.LAST, arrowshape=(8,10,3), tags="drone")
                    gfx['arrow'] = arrow_id
            else:
                 if gfx.get('arrow'):
                     self.itemconfigure(gfx['arrow'], state="hidden")
        else:
            # Create new
            body_id = self.create_oval(cx - draw_r, cy - draw_r, cx + draw_r, cy + draw_r, fill=color, outline=color, tags="drone")
            head_id = self.create_line(cx, cy, head_x, head_y, fill=color, width=2, tags="drone")
            
            # Create Label
            label_id = self.create_text(cx + draw_r + 5, cy - draw_r - 5, text=str(drone_id), 
                                        anchor="sw", font=("Arial", 9, "bold"), fill="black", tags="drone")
            
            gfx = {'body': body_id, 'head': head_id, 'label': label_id, 'arrow': None}
            
            if abs(v_north) > 0.1 or abs(v_east) > 0.1:
                # Velocity vector scaled 2x to match drone size
                px_n = v_north * self.px_per_meter * 2
                px_e = v_east * self.px_per_meter * 2
                tx = cx + px_e
                ty = cy - px_n
                arrow_id = self.create_line(cx, cy, tx, ty, fill=color, width=2, arrow=tk.LAST, arrowshape=(8,10,3), tags="drone")
                gfx['arrow'] = arrow_id
            
            self.drone_graphics[drone_id] = gfx

    def clear_drones(self):
        # Determine tracking start (legacy name)
        self.drawn_ids_this_frame.clear()

    def finish_frame(self):
        # Hide/Delete drones not drawn
        to_remove = []
        for did, gfx in self.drone_graphics.items():
            if did not in self.drawn_ids_this_frame:
                self.itemconfigure(gfx['body'], state="hidden")
                self.itemconfigure(gfx['head'], state="hidden")
                self.itemconfigure(gfx['label'], state="hidden")
                if gfx.get('arrow'):
                    self.itemconfigure(gfx['arrow'], state="hidden")
        
        # Bring to front?
        self.tag_raise("drone")
        self.tag_raise("hud")