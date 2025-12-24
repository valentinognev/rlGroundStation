import tkinter as tk
import core.cfg as cfg
from core import geo_math
import math

class MapCanvas(tk.Canvas):
    def __init__(self, parent, bounds, width, height, resolution):
        super().__init__(parent, width=width, height=height, bg="white")
        self.dims = (width, height)
        self.padding = cfg.PADDING 
        
        # Initialize
        self.update_view_settings(bounds, resolution)

    def update_view_settings(self, bounds, resolution):
        """Helper to update all view parameters and redraw."""
        self.bounds = bounds
        self.resolution = resolution
        
        # Recalculate scaling factors
        # Safety check for 0 resolution
        if self.resolution <= 0: self.resolution = 1e-5
            
        self.meters_per_px = self.resolution * 111139
        self.px_per_meter = 1.0 / self.meters_per_px if self.meters_per_px > 0 else 1.0
        
        self.delete("all")
        self.draw_axes()

    def fit_to_bounds(self, min_lat, max_lat, min_lon, max_lon):
        """
        Adjusts zoom (resolution) and center to fit the provided bounds.
        """
        w, h = self.dims
        pad_l, pad_t, pad_r, pad_b = self.padding
        active_w = w - pad_l - pad_r
        active_h = h - pad_t - pad_b

        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        
        # Avoid division by zero if single point
        if lat_range == 0: lat_range = 0.001
        if lon_range == 0: lon_range = 0.001

        # Calculate required resolution to fit dimensions
        res_lat = lat_range / active_h
        res_lon = lon_range / active_w
        
        # Take the larger resolution (Zoom out enough to fit both)
        # We add a small buffer (10%) so points aren't exactly on the edge
        new_res = max(res_lat, res_lon) * 1.1
        
        # Re-center based on the new range
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        
        # Calculate new View Bounds
        view_lat_h = active_h * new_res
        view_lon_w = active_w * new_res
        
        new_bounds = (
            center_lat - view_lat_h/2, center_lat + view_lat_h/2,
            center_lon - view_lon_w/2, center_lon + view_lon_w/2
        )
        
        print(f"Auto-Fit: Res changed from {self.resolution:.2e} to {new_res:.2e}")
        self.update_view_settings(new_bounds, new_res)

    def set_center(self, lat, lon):
        """Centers view while KEEPING current resolution."""
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

    def draw_drone(self, lat, lon, heading, color):
        cx, cy = geo_math.lat_lon_to_screen(lat, lon, self.bounds, self.dims, self.padding)
        real_r_px = 0.13 * self.px_per_meter
        draw_r = max(real_r_px, 1.5) 
        self.create_oval(cx - draw_r, cy - draw_r, cx + draw_r, cy + draw_r, fill=color, outline=color, tags="drone")
        line_len = max(real_r_px * 2.0, 5.0) 
        rad = math.radians(heading)
        end_x = cx + line_len * math.sin(rad)
        end_y = cy - line_len * math.cos(rad)
        self.create_line(cx, cy, end_x, end_y, fill=color, width=2, tags="drone")

    def clear_drones(self):
        self.delete("drone")