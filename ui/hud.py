import tkinter as tk

def darken_color(hex_color, factor=0.4):
    if hex_color.startswith('#'): hex_color = hex_color[1:]
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"

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
        """
        Draws a single row indicating GPS 3D Fix status.
        Placed to the right of the Communication Matrix.
        """
        pad_l, _, _, pad_b = padding
        w, h = dims
        axis_y = h - pad_b
        
        # Position: Shift right by ~160px from the Comm Matrix
        start_x = pad_l + 160
        start_y = axis_y + 55 
        spacing = 25
        dot_r = 6
        drone_ids = [1, 2, 3, 4]

        # Title
        self.canvas.create_text(start_x, start_y - 15, text="gps fix", 
                                anchor="w", font=("Arial", 10, "bold"), tags="hud")
        
        # Single Row
        row_y = start_y
        
        for col_idx, drone_id in enumerate(drone_ids):
            col_x = start_x + (col_idx * spacing) + 10
            
            base_color = colors[(drone_id - 1) % len(colors)]
            draw_color = base_color
            
            state = active_states.get(drone_id)
            
            # Logic: If state exists AND gps_3d_fix == 1, use bright color. Else dark.
            if state and state.gps_3d_fix:
                pass # draw_color remains base_color
            else:
                draw_color = darken_color(base_color)
            
            self.canvas.create_oval(col_x - dot_r, row_y - dot_r, col_x + dot_r, row_y + dot_r,
                                    fill=draw_color, outline="", tags="hud")