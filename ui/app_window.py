import tkinter as tk
from tkinter import ttk
import math
from ui.map_canvas import MapCanvas
from ui.controls import ControlPanel
from ui.graph_panel import GraphPanel

class DroneApp:
    DRONE_COLORS = ["#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#46f0f0"]
    
    # Playback Settings
    RENDER_DELAY = 16       # ms (approx 60 FPS)
    PLAY_SPEED = 0.3        # Data frames to advance per render tick
    
    # --- OPTIMIZATION: Graph Update Throttle ---
    graph_update_counter = 0
    GRAPH_SKIP_FRAMES = 3   # Update graph every N render ticks (approx 20 FPS)

    def __init__(self, root, map_bounds, width, height, resolution, on_load_request):
        self.root = root
        self.is_running = False
        
        self.play_head = 0.0
        self.max_frames = 0
        self.trajectories = [] 
        self.has_centered_on_stream = False 

        # --- 1. SETUP TABS (NOTEBOOK) ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Tab 1: Map View
        self.tab_map = tk.Frame(self.notebook)
        self.notebook.add(self.tab_map, text="Map View")
        
        # Tab 2: Graph View
        self.tab_graphs = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(self.tab_graphs, text="Graph Analysis")
        
        # --- GRAPH PANEL INTEGRATION ---
        self.graph_panel = GraphPanel(self.tab_graphs)
        self.graph_panel.pack(fill=tk.BOTH, expand=True)

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
            
            # Update Graph Data
            self.graph_panel.set_data(trajectories, self.DRONE_COLORS)
            
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
            if not path:
                continue

            # Clamp index to available data for this drone
            # This prevents flickering if one drone lags behind the global max_frames
            curr_idx_clamped = min(idx_current, len(path) - 1)
            state_curr = path[curr_idx_clamped]
            
            # For interpolation, we also need to respect the path bounds
            next_idx_clamped = min(idx_next, len(path) - 1)
            
            if curr_idx_clamped != next_idx_clamped:
                state_next = path[next_idx_clamped]
                
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
            
            self.map_view.draw_drone(state_curr.id, lat, lon, heading, color, vn, ve)

        self.map_view.finish_frame()
        self.map_view.draw_hud(active_states, self.DRONE_COLORS)

        # --- Update Graphs (with throttling and visibility check) ---
        # Only update if the Graph tab is actually selected
        current_tab = self.notebook.select()  # Returns widget ID
        
        if str(current_tab) == str(self.tab_graphs):
            self.graph_update_counter += 1
            if self.graph_update_counter >= self.GRAPH_SKIP_FRAMES:
                # Refresh data cache before drawing
                self.graph_panel.refresh_active_plots()
                self.graph_panel.update_graph(idx_current)
                self.graph_update_counter = 0

    def animate_loop(self):
        if self.is_running:
            self.play_head += self.PLAY_SPEED
            if self.play_head >= self.max_frames:
                self.play_head = 0.0
            self.draw_frame()
        self.root.after(self.RENDER_DELAY, self.animate_loop)

    def process_new_state(self, state):
        """
        Ingests a new drone state from the live stream.
        """
        # Ensure we have a list for this drone
        # Assuming struct ID is 1-based, we map to index ID-1
        idx = state.id - 1
        
        # Check if this is a new drone to trigger UI rebuild
        is_new_drone = False
        while len(self.trajectories) <= idx:
            self.trajectories.append([])
            is_new_drone = True

        self.trajectories[idx].append(state)
        
        # In live mode, we treat the current frame count of this drone as the max
        # If we have multiple drones, they should be roughly synced, 
        # so max_frames is the length of the longest history.
        self.max_frames = max(len(t) for t in self.trajectories) - 1
        self.controls.set_slider_max(self.max_frames)

        # Auto-scroll to latest
        # In a real app we might want a "Live" toggle. 
        # For now, if we are receiving data, we jump to the latest.
        self.play_head = float(self.max_frames)
        self.draw_frame()
        
        if is_new_drone:
            self.graph_panel.set_data(self.trajectories, self.DRONE_COLORS)

        # Center map on Drone 1 if first time seeing it
        if not self.has_centered_on_stream and state.id == 1:
            print(f"Stream: Centering map on Drone 1 ({state.lat}, {state.lon})")
            self.map_view.set_center(state.lat, state.lon)
            self.has_centered_on_stream = True