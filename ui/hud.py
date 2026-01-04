import tkinter as tk

def darken_color(hex_color, factor=0.4):
    """Darkens a hex color string."""
    if hex_color.startswith('#'): hex_color = hex_color[1:]
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"

def get_text_color(hex_color):
    """Returns 'black' or 'white' depending on the background brightness."""
    if hex_color.startswith('#'): hex_color = hex_color[1:]
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Calculate Luminance (standard formula)
    lum = (0.299 * r + 0.587 * g + 0.114 * b)
    
    # Threshold: if bright (>150), use black text
    return "black" if lum > 150 else "white"

class HUD:
    COLOR_OK = "#2ecc71"  # Green
    COLOR_FAIL = "#e74c3c" # Red
    COLOR_NEUTRAL = "#bdc3c7" # Grey

    def __init__(self, canvas):
        self.canvas = canvas

    def clear(self):
        """Clears all HUD elements."""
        self.canvas.delete("hud")

    def draw_keep_alive(self, active_states, colors, dims, padding):
        # We don't use 'colors' anymore for identification, but keeping signature compatible
        pad_l, _, _, pad_b = padding
        w, h = dims
        axis_y = h - pad_b
        
        start_x = pad_l + 25  # Shift right for row labels
        start_y = axis_y + 55 
        spacing = 25
        dot_r = 6
        drone_ids = [1, 2, 3, 4]
        
        # Title
        self.canvas.create_text(start_x, start_y - 25, text="communication", 
                                anchor="w", font=("Arial", 10, "bold"), tags="hud")

        # Column Headers
        for col_idx, target_id in enumerate(drone_ids):
            col_x = start_x + 30 + (col_idx * spacing)
            self.canvas.create_text(col_x, start_y - 5, text=str(target_id), 
                                    font=("Arial", 8, "bold"), tags="hud")

        for row_idx, observer_id in enumerate(drone_ids):
            row_y = start_y + 10 + (row_idx * spacing)
            
            # Row Header (Observer)
            self.canvas.create_text(start_x, row_y, text=f"D{observer_id}", 
                                    font=("Arial", 8, "bold"), anchor="e", tags="hud")
            
            observer_data = active_states.get(observer_id)
            others = [d for d in drone_ids if d != observer_id]
            # Use fixed matrix order 1..4 to be clearer
            row_drones = drone_ids 
            
            for col_idx, target_id in enumerate(row_drones):
                col_x = start_x + 30 + (col_idx * spacing)
                
                # Logic: Is 'target_id' seen by 'observer_id'?
                # If target == observer, usually ON (Self).
                
                draw_color = self.COLOR_NEUTRAL
                
                if target_id == observer_id:
                     # Self-check? usually implicit, let's say Green if data exists
                     draw_color = self.COLOR_OK if observer_data else self.COLOR_FAIL
                else:
                    if observer_data:
                        # Protocol: bit mask
                        # Assuming LSB is unit 1? 
                        # Previous code: "4 bits member - MSB - unit 4..unit 1"
                        # struct: int16_t drones_keep_alive : 4;
                        # If bit 0 is unit 1:
                        bit_idx = target_id - 1
                        is_alive = (observer_data.drones_keep_alive >> bit_idx) & 1
                        draw_color = self.COLOR_OK if is_alive else self.COLOR_FAIL
                    else:
                        draw_color = self.COLOR_FAIL # No data from observer
                
                self.canvas.create_oval(col_x - dot_r, row_y - dot_r, col_x + dot_r, row_y + dot_r,
                                        fill=draw_color, outline="", tags="hud")

    def draw_gps_fix(self, active_states, colors, dims, padding):
        pad_l, _, _, pad_b = padding
        w, h = dims
        axis_y = h - pad_b
        
        start_x = pad_l + 180 # Adjusted spacing
        start_y = axis_y + 55 
        spacing = 30
        r = 10
        drone_ids = [1, 2, 3, 4]

        # Title
        self.canvas.create_text(start_x, start_y - 25, text="gps fix", 
                                anchor="w", font=("Arial", 10, "bold"), tags="hud")
        
        # Data Row
        row_y = start_y + 15 
        
        for col_idx, drone_id in enumerate(drone_ids):
            col_x = start_x + 15 + (col_idx * spacing)
            
            state = active_states.get(drone_id)
            
            # Color Logic
            if state and state.gps_3d_fix:
                fill_color = self.COLOR_OK
            else:
                fill_color = self.COLOR_FAIL
            
            self.canvas.create_oval(col_x - r, row_y - r, col_x + r, row_y + r,
                                    fill=fill_color, outline="", tags="hud")
            
            # Number
            self.canvas.create_text(col_x, row_y, text=str(drone_id), fill="white",
                                    font=("Arial", 9, "bold"), tags="hud")

    def draw_telemetry(self, active_states, colors, dims, padding):
        pad_l, _, _, pad_b = padding
        w, h = dims
        axis_y = h - pad_b
        
        # --- Base Coordinates ---
        base_y = axis_y + 55
        title_y = base_y - 25
        
        # --- Group 1: STATE ---
        state_x = pad_l + 330
        self.canvas.create_text(state_x, title_y, text="state", 
                                anchor="w", font=("Arial", 10, "bold"), tags="hud")
        
        # State Data Y 
        state_data_y = base_y + 15
        
        # --- Group 2: BATTERY ---
        bat_x = pad_l + 480
        self.canvas.create_text(bat_x, title_y, text="battery", 
                                anchor="w", font=("Arial", 10, "bold"), tags="hud")
        
        bat_data_y = base_y + 15
        
        drone_ids = [1, 2, 3, 4]
        
        for i, drone_id in enumerate(drone_ids):
            state = active_states.get(drone_id)
            
            # --- 1. Draw State Data ---
            sx = state_x + 15 + (i * 30)
            
            # Label Number
            self.canvas.create_text(sx, state_data_y - 20, text=str(drone_id), 
                                    font=("Arial", 7, "bold"), fill="black", tags="hud")
            
            r = 11
            val_text = str(state.sm_current_stat) if state else "-"
            
            # Circle
            self.canvas.create_oval(sx - r, state_data_y - r, sx + r, state_data_y + r,
                                    fill="white", outline="black", width=1, tags="hud")
            
            # Value
            self.canvas.create_text(sx, state_data_y, text=val_text, 
                                    fill="black", font=("Arial", 9, "bold"), tags="hud")

            # --- 2. Draw Battery Data ---
            bx = bat_x + 15 + (i * 40)
            
            # A. Drone Number Label
            self.canvas.create_text(bx, bat_data_y - 25, text=str(drone_id),
                                    font=("Arial", 7, "bold"), fill="black", tags="hud")

            # B. Battery Icon & Text
            if state:
                bat = state.battery_precentages
                
                # Colors based on Level
                fill_color = self.COLOR_OK # Green
                if bat < 20: fill_color = self.COLOR_FAIL # Red
                elif bat < 50: fill_color = "#e67e22" # Orange
                
                # Dimensions 
                icon_w = 14
                icon_h = 24
                nub_h = 2
                
                body_y = bat_data_y + 5 
                
                x1 = bx - icon_w / 2
                y1 = body_y - icon_h / 2
                x2 = x1 + icon_w
                y2 = y1 + icon_h
                
                # 1. Nub (Small rectangle on TOP)
                self.canvas.create_rectangle(bx - 3, y1 - nub_h, bx + 3, y1, 
                                             fill="black", outline="", tags="hud")
                
                # 2. Main Body (Outline)
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", width=1, tags="hud")
                
                # 3. Inner Bars
                gap = 1
                bar_h = 6
                inner_x1 = x1 + 2
                inner_x2 = x2 - 2
                inner_bottom = y2 - 2
                
                if bat > 0:
                    b1_y1 = inner_bottom - bar_h
                    self.canvas.create_rectangle(inner_x1, b1_y1, inner_x2, inner_bottom,
                                                 fill=fill_color, outline="", tags="hud")
                if bat > 33:
                    b2_y2 = inner_bottom - (bar_h + gap)
                    b2_y1 = b2_y2 - bar_h
                    self.canvas.create_rectangle(inner_x1, b2_y1, inner_x2, b2_y2,
                                                 fill=fill_color, outline="", tags="hud")
                if bat > 66:
                    b3_y2 = inner_bottom - 2 * (bar_h + gap)
                    b3_y1 = b3_y2 - bar_h
                    self.canvas.create_rectangle(inner_x1, b3_y1, inner_x2, b3_y2,
                                                 fill=fill_color, outline="", tags="hud")

                # C. Percentage Text
                self.canvas.create_text(bx, y2 + 8, text=f"{bat}%", 
                                        fill="black", font=("Arial", 7), tags="hud")
            else:
                self.canvas.create_text(bx, bat_data_y, text="--", fill="black", tags="hud")