import tkinter as tk
from tkinter import ttk
import math
from ui.map_canvas import MapCanvas
from ui.controls import ControlPanel

class DroneApp:
    DRONE_COLORS = ["#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#46f0f0"]
    
    # Playback Settings
    RENDER_DELAY = 16       # ms (approx 60 FPS)
    PLAY_SPEED = 0.3        # Data frames to advance per render tick

    def __init__(self, root, map_bounds, width, height, resolution, on_load_request):
        self.root = root
        self.is_running = False
        
        self.play_head = 0.0
        self.max_frames = 0
        self.trajectories = [] 

        # --- 1. SETUP TABS (NOTEBOOK) ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Tab 1: Map View
        self.tab_map = tk.Frame(self.notebook)
        self.notebook.add(self.tab_map, text="Map View")
        
        # Tab 2: Graph View
        self.tab_graphs = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(self.tab_graphs, text="Graph Analysis")
        
        # Placeholder for Graphs
        self.lbl_graph = tk.Label(self.tab_graphs, text="Graphs Placeholder\n(Coming Soon)", 
                                  font=("Arial", 16), bg="#f0f0f0", fg="#888")
        self.lbl_graph.pack(expand=True)

        # --- 2. MAP CANVAS (Reparented to tab_map) ---
        self.map_view = MapCanvas(self.tab_map, map_bounds, width, height, resolution, 
                                  on_redraw=self.draw_frame)
        self.map_view.pack(fill=tk.BOTH, expand=True)

        # --- 3. CONTROLS (Common at bottom) ---
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
            
            initial_lats = []
            initial_lons = []
            for path in trajectories:
                if len(path) > 0:
                    state = path[0]
                    initial_lats.append(state.lat)
                    initial_lons.append(state.lon)
            
            if initial_lats and initial_lons:
                avg_lat = sum(initial_lats) / len(initial_lats)
                avg_lon = sum(initial_lons) / len(initial_lons)
                print(f"Centering view on Swarm Center of Mass: {avg_lat:.5f}, {avg_lon:.5f}")
                self.map_view.set_center(avg_lat, avg_lon)

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
        self.play_head = 0.0
        self.controls.set_slider_val(0)
        self.controls.update_status("Reset")
        self.draw_frame()

    def on_scrub(self, frame_idx):
        self.play_head = float(frame_idx)
        self.draw_frame()

    def lerp(self, a, b, t):
        return a + (b - a) * t

    def lerp_angle(self, a, b, t):
        diff = (b - a + 180) % 360 - 180
        return (a + diff * t) % 360

    def draw_frame(self):
        # Even if hidden, we update the map so it's ready when tab is switched
        self.map_view.clear_drones()
        
        idx_current = int(self.play_head)
        idx_next = idx_current + 1
        
        if idx_next > self.max_frames:
            idx_next = self.max_frames
            idx_current = self.max_frames 
        
        alpha = self.play_head - idx_current
        
        self.controls.update_frame_label(idx_current)
        if int(self.controls.slider.get()) != idx_current and self.is_running:
             self.controls.slider.set(idx_current)

        active_states = {} 
        
        for i, path in enumerate(self.trajectories):
            if idx_current < len(path):
                state_curr = path[idx_current]
                
                if idx_next < len(path):
                    state_next = path[idx_next]
                    
                    lat = self.lerp(state_curr.lat, state_next.lat, alpha)
                    lon = self.lerp(state_curr.lon, state_next.lon, alpha)
                    heading = self.lerp_angle(state_curr.heading, state_next.heading, alpha)
                    
                    vn = self.lerp(state_curr.velocity_north, state_next.velocity_north, alpha)
                    ve = self.lerp(state_curr.velocity_east, state_next.velocity_east, alpha)
                else:
                    lat = state_curr.lat
                    lon = state_curr.lon
                    heading = state_curr.heading
                    vn = state_curr.velocity_north
                    ve = state_curr.velocity_east

                # Store state for HUD
                active_states[state_curr.id] = state_curr
                
                color_idx = (state_curr.id - 1) % len(self.DRONE_COLORS)
                color = self.DRONE_COLORS[color_idx]
                
                self.map_view.draw_drone(lat, lon, heading, color, vn, ve)

        self.map_view.draw_hud(active_states, self.DRONE_COLORS)

    def animate_loop(self):
        if self.is_running:
            self.play_head += self.PLAY_SPEED
            if self.play_head >= self.max_frames:
                self.play_head = 0.0
            self.draw_frame()
        self.root.after(self.RENDER_DELAY, self.animate_loop)