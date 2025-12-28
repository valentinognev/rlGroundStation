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
    def __init__(self, canvas):
        self.canvas = canvas

    def clear(self):
        """Clears all HUD elements."""
        self.canvas.delete("hud")

    def draw_keep_alive(self, active_states, colors, dims, padding):
        pad_l, _, _, pad_b = padding
        w, h = dims
        axis_y = h - pad_b
        
        start_x = pad_l
        start_y = axis_y + 55 
        spacing = 25
        dot_r = 6
        drone_ids = [1, 2, 3, 4]
        
        # Title
        self.canvas.create_text(start_x, start_y - 15, text="communication", 
                                anchor="w", font=("Arial", 10, "bold"), tags="hud")

        for row_idx, observer_id in enumerate(drone_ids):
            row_y = start_y + (row_idx * spacing)
            observer_data = active_states.get(observer_id)
            others = [d for d in drone_ids if d != observer_id]
            row_drones = [observer_id] + others
            
            for col_idx, target_id in enumerate(row_drones):
                col_x = start_x + (col_idx * spacing) + 10 
                base_color = colors[(target_id - 1) % len(colors)]
                draw_color = base_color
                
                if target_id == observer_id:
                    if not observer_data: draw_color = darken_color(base_color)
                else:
                    if observer_data:
                        bit_idx = target_id - 1
                        is_alive = (observer_data.drones_keep_alive >> bit_idx) & 1
                        if not is_alive: draw_color = darken_color(base_color)
                    else:
                        draw_color = darken_color(base_color)

                self.canvas.create_oval(col_x - dot_r, row_y - dot_r, col_x + dot_r, row_y + dot_r,
                                        fill=draw_color, outline="", tags="hud")

    def draw_gps_fix(self, active_states, colors, dims, padding):
        pad_l, _, _, pad_b = padding
        w, h = dims
        axis_y = h - pad_b
        
        start_x = pad_l + 160
        start_y = axis_y + 55 
        spacing = 25
        dot_r = 6
        drone_ids = [1, 2, 3, 4]

        # Title
        self.canvas.create_text(start_x, start_y - 15, text="gps fix", 
                                anchor="w", font=("Arial", 10, "bold"), tags="hud")
        
        # Data Row (Matches 2nd row of Comm matrix)
        row_y = start_y + 25 
        
        for col_idx, drone_id in enumerate(drone_ids):
            col_x = start_x + (col_idx * spacing) + 10
            
            base_color = colors[(drone_id - 1) % len(colors)]
            draw_color = base_color
            
            state = active_states.get(drone_id)
            
            if state and state.gps_3d_fix:
                pass 
            else:
                draw_color = darken_color(base_color)
            
            self.canvas.create_oval(col_x - dot_r, row_y - dot_r, col_x + dot_r, row_y + dot_r,
                                    fill=draw_color, outline="", tags="hud")

    def draw_telemetry(self, active_states, colors, dims, padding):
        pad_l, _, _, pad_b = padding
        w, h = dims
        axis_y = h - pad_b
        
        # --- Base Coordinates ---
        base_y = axis_y + 55
        title_y = base_y - 15
        
        # --- Group 1: STATE ---
        state_x = pad_l + 290
        self.canvas.create_text(state_x, title_y, text="state", 
                                anchor="w", font=("Arial", 10, "bold"), tags="hud")
        
        # State Data Y (Aligned with GPS Fix row)
        state_data_y = base_y + 25
        
        # --- Group 2: BATTERY ---
        bat_x = pad_l + 430
        self.canvas.create_text(bat_x, title_y, text="battery", 
                                anchor="w", font=("Arial", 10, "bold"), tags="hud")
        
        # Battery Data Y (Slightly adjusted because vertical battery is tall)
        # We want the *center* of the battery visual to look good.
        bat_data_y = base_y + 25
        
        drone_ids = [1, 2, 3, 4]
        
        for i, drone_id in enumerate(drone_ids):
            state = active_states.get(drone_id)
            base_color = colors[(drone_id - 1) % len(colors)]
            
            # --- 1. Draw State Data ---
            sx = state_x + 15 + (i * 30)
            r = 11
            val_text = str(state.sm_current_stat) if state else "-"
            
            # Circle
            self.canvas.create_oval(sx - r, state_data_y - r, sx + r, state_data_y + r,
                                    fill=base_color, outline="black", width=1, tags="hud")
            
            # Text
            txt_color = get_text_color(base_color)
            self.canvas.create_text(sx, state_data_y, text=val_text, 
                                    fill=txt_color, font=("Arial", 9, "bold"), tags="hud")

            # --- 2. Draw Battery Data ---
            bx = bat_x + 15 + (i * 40)
            
            # A. Drone Indicator (Above Battery)
            ind_r = 4
            ind_y = bat_data_y - 18 # Shift up
            self.canvas.create_oval(bx - ind_r, ind_y - ind_r, bx + ind_r, ind_y + ind_r,
                                    fill=base_color, outline="", tags="hud")

            # B. Battery Icon & Text
            if state:
                bat = state.battery_precentages
                
                # Colors
                fill_color = "#27ae60" # Green
                if bat < 20: fill_color = "#e74c3c" # Red
                elif bat < 50: fill_color = "#e67e22" # Orange
                
                # Dimensions (Vertical & Larger)
                icon_w = 14
                icon_h = 24
                nub_h = 2
                
                # Center coords for battery body
                # Shift body down slightly so indicator fits above
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
                
                # 3. Inner Bars (Vertical Stack)
                # Available height approx 20px (2px padding, 1px gaps)
                # 3 bars -> ~6px each
                gap = 1
                bar_h = 6
                
                inner_x1 = x1 + 2
                inner_x2 = x2 - 2
                inner_bottom = y2 - 2
                
                # Bar 1 (Bottom, > 0%)
                if bat > 0:
                    b1_y1 = inner_bottom - bar_h
                    self.canvas.create_rectangle(inner_x1, b1_y1, inner_x2, inner_bottom,
                                                 fill=fill_color, outline="", tags="hud")
                
                # Bar 2 (Middle, > 33%)
                if bat > 33:
                    b2_y2 = inner_bottom - (bar_h + gap)
                    b2_y1 = b2_y2 - bar_h
                    self.canvas.create_rectangle(inner_x1, b2_y1, inner_x2, b2_y2,
                                                 fill=fill_color, outline="", tags="hud")
                    
                # Bar 3 (Top, > 66%)
                if bat > 66:
                    b3_y2 = inner_bottom - 2 * (bar_h + gap)
                    b3_y1 = b3_y2 - bar_h
                    self.canvas.create_rectangle(inner_x1, b3_y1, inner_x2, b3_y2,
                                                 fill=fill_color, outline="", tags="hud")

                # C. Percentage Text (Below Battery)
                self.canvas.create_text(bx, y2 + 8, text=f"{bat}%", 
                                        fill="black", font=("Arial", 7), tags="hud")
            else:
                self.canvas.create_text(bx, bat_data_y, text="--", fill="black", tags="hud")