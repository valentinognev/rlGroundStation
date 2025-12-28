import tkinter as tk
import core.cfg as cfg
from core import geo_math
from ui.hud import HUD
import math

class MapCanvas(tk.Canvas):
    def __init__(self, parent, bounds, width, height, resolution):
        super().__init__(parent, width=width, height=height, bg="white")
        self.dims = (width, height)
        self.padding = cfg.PADDING 
        self.resolution = resolution
        
        self.hud = HUD(self)
        self.update_view_settings(bounds, resolution)

    def update_view_settings(self, bounds, resolution):
        self.bounds = bounds
        self.resolution = resolution
        if self.resolution <= 0: self.resolution = 1e-5
        self.meters_per_px = self.resolution * 111139
        self.px_per_meter = 1.0 / self.meters_per_px if self.meters_per_px > 0 else 1.0
        
        self.delete("all")
        self.draw_axes()

    def fit_to_bounds(self, min_lat, max_lat, min_lon, max_lon):
        w, h = self.dims
        pad_l, pad_t, pad_r, pad_b = self.padding
        active_w = w - pad_l - pad_r
        active_h = h - pad_t - pad_b

        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        
        if lat_range == 0: lat_range = 0.001
        if lon_range == 0: lon_range = 0.001

        res_lat = lat_range / active_h
        res_lon = lon_range / active_w
        # Reverted: Auto-calculate new resolution to fit data + 10% margin
        new_res = max(res_lat, res_lon) * 1.1
        
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        
        view_lat_h = active_h * new_res
        view_lon_w = active_w * new_res
        
        new_bounds = (
            center_lat - view_lat_h/2, center_lat + view_lat_h/2,
            center_lon - view_lon_w/2, center_lon + view_lon_w/2
        )
        print(f"Auto-Fit: Res changed from {self.resolution:.2e} to {new_res:.2e}")
        self.update_view_settings(new_bounds, new_res)

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
        min_lat, max_lat, min_lon, max_lon = self.bounds

        self.create_line(pad_l, pad_t, pad_l, h - pad_b, fill="black", width=2)
        self.create_line(pad_l, h - pad_b, w - pad_r, h - pad_b, fill="black", width=2)

        steps = 5
        for i in range(steps + 1):
            pct = i / steps
            lat = min_lat + pct * (max_lat - min_lat)
            y_pos = (h - pad_b) - (pct * draw_h)
            self.create_line(pad_l - 5, y_pos, pad_l, y_pos, fill="black")
            self.create_text(pad_l - 10, y_pos, text=f"{lat:.5f}", anchor="e", font=("Arial", 8))

            lon = min_lon + pct * (max_lon - min_lon)
            x_pos = pad_l + (pct * draw_w)
            self.create_line(x_pos, h - pad_b, x_pos, h - pad_b + 5, fill="black")
            self.create_text(x_pos, h - pad_b + 15, text=f"{lon:.5f}", anchor="n", font=("Arial", 8))

    def draw_drone(self, lat, lon, heading, color, v_north, v_east):
        cx, cy = geo_math.lat_lon_to_screen(lat, lon, self.bounds, self.dims, self.padding)
        real_r_px = 0.13 * self.px_per_meter
        draw_r = max(real_r_px, 1.5) 
        
        # 1. Body
        self.create_oval(cx - draw_r, cy - draw_r, cx + draw_r, cy + draw_r, 
                         fill=color, outline=color, tags="drone")
        
        # 2. Heading Line
        line_len = max(real_r_px * 2.0, 5.0) 
        rad = math.radians(heading)
        head_x = cx + line_len * math.sin(rad)
        head_y = cy - line_len * math.cos(rad)
        self.create_line(cx, cy, head_x, head_y, fill=color, width=2, tags="drone")

        # 3. Velocity Arrow
        d_lat = v_north / 111139.0
        d_lon = v_east / (111139.0 * math.cos(math.radians(lat)))
        
        target_lat = lat + d_lat
        target_lon = lon + d_lon
        
        tx, ty = geo_math.lat_lon_to_screen(target_lat, target_lon, self.bounds, self.dims, self.padding)
        
        if abs(v_north) > 0.1 or abs(v_east) > 0.1:
            self.create_line(cx, cy, tx, ty, fill=color, width=2, arrow=tk.LAST, arrowshape=(8,10,3), tags="drone")

    def clear_drones(self):
        self.delete("drone")