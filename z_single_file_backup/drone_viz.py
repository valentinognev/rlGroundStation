import tkinter as tk
import math

class DroneMap:
    def __init__(self, root, min_lat, max_lat, min_lon, max_lon, width=800, height=600):
        self.root = root
        self.min_lat = min_lat
        self.max_lat = max_lat
        self.min_lon = min_lon
        self.max_lon = max_lon
        
        # --- Layout ---
        # Top: Map
        self.map_frame = tk.Frame(root)
        self.map_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Bottom: Controls
        self.control_frame = tk.Frame(root, height=100, bg="#f0f0f0")
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Map Setup ---
        self.width = width
        self.height = height
        self.pad_left = 60
        self.pad_bottom = 40
        self.pad_right = 20
        self.pad_top = 20
        self.draw_w = self.width - self.pad_left - self.pad_right
        self.draw_h = self.height - self.pad_top - self.pad_bottom

        self.canvas = tk.Canvas(self.map_frame, width=self.width, height=self.height, bg="white")
        self.canvas.pack()
        self.draw_axes()

        # --- State ---
        self.is_running = False
        self.frame_idx = 0
        self.max_frames = 100 # Default, will update when data loads
        self.trajectories = []

        # --- Controls UI ---
        
        # 1. Timeline Slider (Full width at top of control panel)
        self.time_slider = tk.Scale(self.control_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                    command=self.on_slider_drag, showvalue=0, bg="#e0e0e0")
        self.time_slider.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # 2. Button Container
        self.btn_frame = tk.Frame(self.control_frame, bg="#f0f0f0")
        self.btn_frame.pack(side=tk.TOP, fill=tk.X)

        self.btn_play = tk.Button(self.btn_frame, text="Play", command=self.play, width=8, bg="#ddffdd")
        self.btn_play.pack(side=tk.LEFT, padx=10, pady=5)

        self.btn_pause = tk.Button(self.btn_frame, text="Pause", command=self.pause, width=8, bg="#ffffdd")
        self.btn_pause.pack(side=tk.LEFT, padx=10, pady=5)

        self.btn_reset = tk.Button(self.btn_frame, text="Reset", command=self.reset, width=8, bg="#ffdddd")
        self.btn_reset.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.lbl_status = tk.Label(self.btn_frame, text="Status: Stopped", font=("Arial", 10), bg="#f0f0f0")
        self.lbl_status.pack(side=tk.LEFT, padx=20)
        
        # Frame Counter Label
        self.lbl_frame = tk.Label(self.btn_frame, text="Frame: 0", font=("Arial", 9), bg="#f0f0f0")
        self.lbl_frame.pack(side=tk.RIGHT, padx=20)

        # Start Loop
        self.animate_loop()

    def set_trajectories(self, paths):
        """Load data and update slider range."""
        self.trajectories = paths
        if paths:
            # Set slider max to length of longest path
            self.max_frames = max(len(p) for p in paths) - 1
            self.time_slider.config(to=self.max_frames)
            
        self.draw_current_frame()

    # --- Callbacks ---
    def on_slider_drag(self, value):
        """Called when user drags the slider."""
        # Update internal frame index to match slider
        self.frame_idx = int(value)
        self.draw_current_frame()

    def play(self):
        self.is_running = True
        self.lbl_status.config(text="Status: Playing")

    def pause(self):
        self.is_running = False
        self.lbl_status.config(text="Status: Paused")

    def reset(self):
        self.is_running = False
        self.frame_idx = 0
        self.time_slider.set(0) # Reset visual slider
        self.draw_current_frame()
        self.lbl_status.config(text="Status: Reset")

    # --- Drawing ---
    def lat_lon_to_screen(self, lat, lon):
        x_pct = (lon - self.min_lon) / (self.max_lon - self.min_lon)
        y_pct = (lat - self.min_lat) / (self.max_lat - self.min_lat)
        screen_x = self.pad_left + (x_pct * self.draw_w)
        screen_y = (self.height - self.pad_bottom) - (y_pct * self.draw_h)
        return screen_x, screen_y

    def draw_drone(self, lat, lon, heading_deg, size=30, tag="drone"):
        cx, cy = self.lat_lon_to_screen(lat, lon)
        r = size / 2.0
        angles_deg = { "fl": heading_deg - 45, "fr": heading_deg + 45, "rl": heading_deg - 135, "rr": heading_deg + 135 }
        
        points = {}
        for key, angle in angles_deg.items():
            rad = math.radians(angle)
            px = cx + r * math.sin(rad)
            py = cy - r * math.cos(rad)
            points[key] = (px, py)

        self.canvas.create_line(cx, cy, points["fl"][0], points["fl"][1], fill="blue", width=3, tags=tag)
        self.canvas.create_line(cx, cy, points["fr"][0], points["fr"][1], fill="blue", width=3, tags=tag)
        self.canvas.create_line(cx, cy, points["rl"][0], points["rl"][1], fill="red", width=3, tags=tag)
        self.canvas.create_line(cx, cy, points["rr"][0], points["rr"][1], fill="red", width=3, tags=tag)

    def draw_axes(self):
        self.canvas.create_line(self.pad_left, self.pad_top, self.pad_left, self.height - self.pad_bottom, fill="black", width=2)
        self.canvas.create_line(self.pad_left, self.height - self.pad_bottom, self.width - self.pad_right, self.height - self.pad_bottom, fill="black", width=2)
        steps = 5
        for i in range(steps + 1):
            pct = i / steps
            lat_val = self.min_lat + pct * (self.max_lat - self.min_lat)
            y_pos = (self.height - self.pad_bottom) - (pct * self.draw_h)
            self.canvas.create_line(self.pad_left - 5, y_pos, self.pad_left, y_pos, fill="black")
            self.canvas.create_text(self.pad_left - 10, y_pos, text=f"{lat_val:.4f}", anchor="e", font=("Arial", 9))
            
            lon_val = self.min_lon + pct * (self.max_lon - self.min_lon)
            x_pos = self.pad_left + (pct * self.draw_w)
            self.canvas.create_line(x_pos, self.height - self.pad_bottom, x_pos, self.height - self.pad_bottom + 5, fill="black")
            self.canvas.create_text(x_pos, self.height - self.pad_bottom + 15, text=f"{lon_val:.4f}", anchor="n", font=("Arial", 9))

    # --- Animation Loop ---
    def draw_current_frame(self):
        self.canvas.delete("drone")
        if not self.trajectories: return

        # Loop the index or clamp it? Here we loop
        # But for a slider/timeline, clamping usually makes more sense.
        # Let's modulo it so it loops when playing, but respects slider limit
        idx = self.frame_idx % (self.max_frames + 1)
        
        # Update Label
        self.lbl_frame.config(text=f"Frame: {idx}")

        for path in self.trajectories:
            if idx < len(path):
                p = path[idx]
                self.draw_drone(lat=p[1], lon=p[0], heading_deg=p[2])

    def animate_loop(self):
        if self.is_running:
            self.frame_idx += 1
            # Check if we hit the end
            if self.frame_idx > self.max_frames:
                self.frame_idx = 0 # Loop back to start
            
            # IMPORTANT: Update the slider visual position
            # Note: set() does NOT trigger the command callback, so no infinite loop
            self.time_slider.set(self.frame_idx)
            
            # Draw
            self.draw_current_frame()
        
        self.root.after(50, self.animate_loop)

# --- Helper ---
def generate_circle_path(center_lat, center_lon, radius_deg, steps=200):
    path = []
    for i in range(steps):
        angle = (i / steps) * 2 * math.pi
        d_lat = radius_deg * math.cos(angle)
        d_lon = radius_deg * math.sin(angle)
        heading = (math.degrees(angle) + 90) % 360
        path.append([center_lon + d_lon, center_lat + d_lat, heading])
    return path

# --- Main ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Drone Playback")

    app = DroneMap(root, min_lat=32.0, max_lat=32.02, min_lon=34.0, max_lon=34.02, width=600, height=650)

    # Generate longer paths for better slider demo
    path1 = generate_circle_path(center_lat=32.01, center_lon=34.01, radius_deg=0.008, steps=300)
    path2 = list(reversed(generate_circle_path(center_lat=32.01, center_lon=34.01, radius_deg=0.004, steps=300)))

    app.set_trajectories([path1, path2])

    root.mainloop()