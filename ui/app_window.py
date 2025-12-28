import tkinter as tk
from ui.map_canvas import MapCanvas
from ui.controls import ControlPanel

class DroneApp:
    DRONE_COLORS = ["#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#46f0f0"]

    def __init__(self, root, map_bounds, width, height, resolution, on_load_request):
        self.root = root
        self.is_running = False
        self.frame_idx = 0
        self.max_frames = 0
        self.trajectories = [] 

        self.map_view = MapCanvas(root, map_bounds, width, height, resolution)
        self.map_view.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        callbacks = {
            'play': self.play,
            'pause': self.pause,
            'reset': self.reset,
            'drag': self.on_scrub,
            'load': on_load_request 
        }
        self.controls = ControlPanel(root, callbacks)
        self.controls.pack(side=tk.BOTTOM, fill=tk.X)

        self.animate_loop()

    def load_data(self, trajectories):
        self.trajectories = trajectories
        if trajectories:
            self.max_frames = max(len(t) for t in trajectories) - 1
            self.controls.set_slider_max(self.max_frames)
            self.controls.update_status("Data Loaded")
            
            all_lats, all_lons = [], []
            for path in trajectories:
                for state in path:
                    all_lats.append(state.lat)
                    all_lons.append(state.lon)
            
            if all_lats and all_lons:
                self.map_view.fit_to_bounds(min(all_lats), max(all_lats), min(all_lons), max(all_lons))

            self.draw_frame()

    def play(self):
        if not self.trajectories: return
        self.is_running = True
        self.controls.update_status("Playing")

    def pause(self):
        self.is_running = False
        self.controls.update_status("Paused")

    def reset(self):
        self.is_running = False
        self.frame_idx = 0
        self.controls.set_slider_val(0)
        self.controls.update_status("Reset")
        self.draw_frame()

    def on_scrub(self, frame_idx):
        self.frame_idx = frame_idx
        self.draw_frame()

    def draw_frame(self):
        self.map_view.clear_drones()
        self.controls.update_frame_label(self.frame_idx)
        
        active_states = {} 
        
        for i, path in enumerate(self.trajectories):
            if self.frame_idx < len(path):
                state = path[self.frame_idx]
                active_states[state.id] = state
                
                lat = state.lat
                lon = state.lon
                heading = state.heading
                
                # Extract Velocity
                vn = state.velocity_north
                ve = state.velocity_east
                
                color_idx = (state.id - 1) % len(self.DRONE_COLORS)
                color = self.DRONE_COLORS[color_idx]
                
                # Pass velocity to draw_drone
                self.map_view.draw_drone(lat, lon, heading, color, vn, ve)

        self.map_view.draw_hud(active_states, self.DRONE_COLORS)

    def animate_loop(self):
        if self.is_running:
            self.frame_idx += 1
            if self.frame_idx > self.max_frames:
                self.frame_idx = 0
            
            self.controls.set_slider_val(self.frame_idx)
            self.draw_frame()
        
        self.root.after(50, self.animate_loop)