import tkinter as tk
import core.cfg as cfg
from core import geo_math
from ui.hud import HUD
from ui.input_handler import InputHandler
import math

class MapCanvas(tk.Canvas):
    def __init__(self, parent, bounds, width, height, resolution, on_redraw=None):
        super().__init__(parent, width=width, height=height, bg="white")
        
        self._initialized = False 
        
        self.dims = (width, height)
        self.padding = cfg.PADDING 
        self.resolution = resolution
        
        self.on_redraw = on_redraw
        
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
        self.draw_axes()
        self.update_grid_labels()
        
        if self._initialized and self.on_redraw:
            self.on_redraw()

    # --- ZOOM LOGIC ---
    def zoom(self, factor, center_x_px, center_y_px):
        pad_l, pad_t, pad_r, pad_b = self.padding
        w, h = self.dims
        
        active_w = w - pad_l - pad_r
        active_h = h - pad_t - pad_b
        
        screen_center_x = pad_l + (active_w / 2.0)
        screen_center_y = pad_t + (active_h / 2.0)
        
        dx_px = center_x_px - screen_center_x
        dy_px = center_y_px - screen_center_y
        
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

    # --- PANNING LOGIC ---
    def update_pan(self, dx, dy):
        self.move("drone", dx, dy)
        
        d_lon = -dx * self.resolution
        d_lat = dy * self.resolution
        
        min_lat, max_lat, min_lon, max_lon = self.bounds
        self.bounds = (
            min_lat + d_lat, max_lat + d_lat,
            min_lon + d_lon, max_lon + d_lon
        )
        self.update_grid_labels()

    def end_pan(self):
        pass

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

    # --- DRAWING METHODS ---
    def draw_hud(self, active_states, colors):
        self.hud.clear()
        self.hud.draw_keep_alive(active_states, colors, self.dims, self.padding)
        self.hud.draw_gps_fix(active_states, colors, self.dims, self.padding)

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
            self.create_text(pad_l - 10, y_pos, text="", anchor="e", 
                             font=("Arial", 8), tags=f"label_lat_{i}")

            x_pos = pad_l + (pct * draw_w)
            self.create_line(x_pos, h - pad_b, x_pos, h - pad_b + 5, fill="black", tags="static_ui")
            self.create_text(x_pos, h - pad_b + 15, text="", anchor="n", 
                             font=("Arial", 8), tags=f"label_lon_{i}")

    def update_grid_labels(self):
        min_lat, max_lat, min_lon, max_lon = self.bounds
        steps = 5
        for i in range(steps + 1):
            pct = i / steps
            lat = min_lat + pct * (max_lat - min_lat)
            self.itemconfigure(f"label_lat_{i}", text=f"{lat:.5f}")
            lon = min_lon + pct * (max_lon - min_lon)
            self.itemconfigure(f"label_lon_{i}", text=f"{lon:.5f}")

    def draw_drone(self, lat, lon, heading, color, v_north, v_east):
        cx, cy = geo_math.lat_lon_to_screen(lat, lon, self.bounds, self.dims, self.padding)
        real_r_px = 0.13 * self.px_per_meter
        draw_r = max(real_r_px, 1.5) 
        
        # 1. Body
        self.create_oval(cx - draw_r, cy - draw_r, cx + draw_r, cy + draw_r, 
                         fill=color, outline=color, tags="drone")
        
        # 2. Heading Line (Orientation)
        line_len = max(real_r_px * 2.0, 5.0) 
        rad = math.radians(heading)
        head_x = cx + line_len * math.sin(rad)
        head_y = cy - line_len * math.cos(rad)
        self.create_line(cx, cy, head_x, head_y, fill=color, width=2, tags="drone")

        # 3. Velocity Arrow (Movement)
        # Using direct screen space calculation for robustness
        # v_north (+) -> Up (Screen Y decrease)
        # v_east (+)  -> Right (Screen X increase)
        
        if abs(v_north) > 0.1 or abs(v_east) > 0.1:
            # 1 second prediction in pixels
            px_n = v_north * self.px_per_meter
            px_e = v_east * self.px_per_meter
            
            # Apply to screen coordinates (Inverting Y for North)
            tx = cx + px_e
            ty = cy - px_n
            
            self.create_line(cx, cy, tx, ty, fill=color, width=2, arrow=tk.LAST, arrowshape=(8,10,3), tags="drone")

    def clear_drones(self):
        self.delete("drone")