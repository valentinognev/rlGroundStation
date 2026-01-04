import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui.hud import darken_color

class CircularToggle(tk.Canvas):
    def __init__(self, parent, size, color, command, initial_state=True):
        super().__init__(parent, width=size, height=size, bg=parent["bg"], highlightthickness=0)
        self.size = size
        self.base_color = color
        self.command = command
        self.is_active = initial_state
        
        self.pad = 2
        self.bind("<Button-1>", self.on_click)
        self.draw()

    def on_click(self, event):
        self.is_active = not self.is_active
        self.draw()
        if self.command:
            self.command()

    def set_state(self, state):
        self.is_active = state
        self.draw()

    def draw(self):
        self.delete("all")
        
        fill_color = self.base_color if self.is_active else darken_color(self.base_color, 0.3)
        outline = "" if self.is_active else "#666"
        
        # Circle
        self.create_oval(self.pad, self.pad, self.size-self.pad, self.size-self.pad, 
                         fill=fill_color, outline=outline, width=1)

class GraphPanel(tk.Frame):
    FIELDS = {
        "None": None,
        "Latitude": "lat",
        "Longitude": "lon",
        "Altitude": "alt",
        "Heading": "heading",
        "Vel North": "velocity_north",
        "Vel East": "velocity_east", 
        "Vel Down": "velocity_down",
        "Battery": "battery_precentages",
        "GPS Fix": "gps_3d_fix",
        "State Machine": "sm_current_stat",
        "Drones Alive": "drones_keep_alive"
    }

    def __init__(self, parent):
        super().__init__(parent)
        
        # --- Layout ---
        self.main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=5, bg="#d0d0d0")
        self.main_pane.pack(fill=tk.BOTH, expand=True)
        
        # 1. Control Panel
        self.controls_frame = tk.Frame(self.main_pane, width=220, bg="#f0f0f0")
        self.main_pane.add(self.controls_frame, minsize=180)
        
        # 2. Graph Canvas
        self.graph_frame = tk.Frame(self.main_pane, bg="white")
        self.main_pane.add(self.graph_frame, minsize=400, stretch="always")
        
        # --- Init Controls (3 Slots) ---
        self.graph_configs = [] # List of dicts: {'combo': widget, 'toggles': {id: widget}, 'container': widget}
        
        # Default choices for the 3 slots
        defaults = ["Latitude", "Longitude", "None"]
        
        for i in range(3):
            # LabelFrame for Slot i
            lf = tk.LabelFrame(self.controls_frame, text=f"Graph {i+1}", bg="#f0f0f0", font="Arial 9 bold", padx=5, pady=5)
            lf.pack(fill=tk.X, padx=10, pady=5)
            
            # Combobox
            cb = ttk.Combobox(lf, values=list(self.FIELDS.keys()), state="readonly")
            cb.set(defaults[i])
            cb.pack(fill=tk.X, pady=(0, 5))
            cb.bind("<<ComboboxSelected>>", self.on_config_change)
            
            # Drone Toggles Container
            dc = tk.Frame(lf, bg="#f0f0f0")
            dc.pack(fill=tk.X)
            
            self.graph_configs.append({
                'combo': cb,
                'toggles': {},
                'container': dc
            })

        # --- Graph Setup ---
        self.fig = Figure(figsize=(5, 4), dpi=100)
        # We don't add subplots here immediately; rebuild_plots will do it.
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Data State
        self.trajectories = []
        self.colors = []
        
        # Rendering State
        # List of lists: self.active_plots[i] = list of (Line2D, DataArray) for subplot i
        self.active_plots = [] 

    def set_data(self, trajectories, colors):
        self.trajectories = trajectories
        self.colors = colors
        
        # Clear Toggles in all slots
        for cfg in self.graph_configs:
            for w in cfg['container'].winfo_children(): w.destroy()
            cfg['toggles'].clear()
        
        if not trajectories: return
        
        drone_ids = sorted([traj[0].id for traj in trajectories if traj])
        
        # Helper to create toggles
        def create_toggles_for_slot(cfg):
            frame_row = tk.Frame(cfg['container'], bg="#f0f0f0")
            frame_row.pack(fill=tk.X)
            
            for d_id in drone_ids:
                c_idx = (d_id - 1) % len(colors)
                color = colors[c_idx]
                
                box = tk.Frame(frame_row, bg="#f0f0f0")
                box.pack(side=tk.LEFT, padx=3)
                
                tk.Label(box, text=f"{d_id}", font="Arial 7", bg="#f0f0f0").pack(side=tk.TOP)
                
                toggle = CircularToggle(box, size=20, color=color, command=self.on_config_change)
                toggle.pack(side=tk.TOP)
                
                cfg['toggles'][d_id] = toggle

        for cfg in self.graph_configs:
            create_toggles_for_slot(cfg)

        self.rebuild_plots()

    def on_config_change(self, event=None):
        self.rebuild_plots()

    def _generate_plot_data(self, field_name, active_ids):
        # Return empty if None selected
        if field_name == "None": return []
        
        attr = self.FIELDS.get(field_name)
        if not attr: return []
        
        plot_items = []
        is_keep_alive = (attr == "drones_keep_alive")

        for path in self.trajectories:
            if not path: continue
            d_id = path[0].id
            
            if d_id not in active_ids: continue
            
            base_color = self.colors[(d_id - 1) % len(self.colors)]
            
            if is_keep_alive:
                raw_vals = [s.drones_keep_alive for s in path]
                for target_id in range(1, 5): 
                    target_color = self.colors[(target_id - 1) % len(self.colors)]
                    y_data = []
                    bit_mask = 1 << (target_id - 1)
                    for val in raw_vals:
                        is_active = (val & bit_mask) != 0
                        y_data.append(target_id if is_active else 0)
                    label = f"Obs {d_id}->T{target_id}"
                    plot_items.append((label, target_color, y_data))
            else:
                data = [getattr(s, attr) for s in path]
                plot_items.append((f"ID {d_id}", base_color, data))
        
        return plot_items

    def rebuild_plots(self):
        # 1. Clear Figure
        self.fig.clear()
        self.active_plots.clear()
        
        if not self.trajectories: 
            self.canvas.draw()
            return

        # 2. Identify Active Slots
        self.active_slots_info = [] # Store for fast refresh
        
        for i, cfg in enumerate(self.graph_configs):
            field_name = cfg['combo'].get()
            if field_name == "None": continue
            
            # Get toggles
            active_ids = [did for did, t in cfg['toggles'].items() if t.is_active]
            items = self._generate_plot_data(field_name, active_ids)
            
            # Store metadata for refresh: (slot_index, field_name, active_ids)
            # We need to re-generate items later, so we store inputs
            self.active_slots_info.append({
                'slot_idx': i, 
                'field': field_name, 
                'ids': active_ids,
                'items': items # Initial items
            })
            
        num_plots = len(self.active_slots_info)
        
        # 3. Create Subplots
        if num_plots == 0:
            self.canvas.draw()
            return
            
        for idx, info in enumerate(self.active_slots_info):
            field_name = info['field']
            items = info['items']
            
            # Add subplot: nrow, ncol, index
            ax = self.fig.add_subplot(num_plots, 1, idx + 1)
            
            # Plot Data
            current_ax_lines = []
            min_y, max_y = float('inf'), float('-inf')
            max_len = 0
            has_data = False
            
            for label, color, data in items:
                line, = ax.plot([], [], color=color, label=label, linewidth=1.5)
                # Store (line, label, color, d_id_ref?) 
                # We need to know which data maps to which line for refresh.
                # Actually, _generate_plot_data returns a list. 
                # We assume the ORDER is deterministic (based on trajectory/ID order).
                current_ax_lines.append(line)
                
                if data:
                    min_y = min(min_y, min(data))
                    max_y = max(max_y, max(data))
                    max_len = max(max_len, len(data))
                    has_data = True
            
            # Store lines in the info dict so we can reuse them
            info['lines'] = current_ax_lines
            # Also store ax for limits update
            info['ax'] = ax
            
            # Styling
            ax.set_ylabel(field_name)
            ax.grid(True)
            if idx == 0: 
                ax.set_title(f"{field_name} vs Frame")
            if idx == num_plots - 1:
                ax.set_xlabel("Frame Index")
                
            if has_data:
                # Legend limit
                if len(items) <= 8: ax.legend(loc='upper right', fontsize='x-small')
                
                # Limits
                ax.set_xlim(0, max_len)
                buf = (max_y - min_y) * 0.1 if max_y != min_y else 1.0
                ax.set_ylim(min_y - buf, max_y + buf)

        self.fig.tight_layout()
        self.canvas.draw()

    def refresh_active_plots(self):
        """
        Updates the internal data cache from trajectories.
        Does NOT necessarily redraw unless needed.
        """
        for info in getattr(self, 'active_slots_info', []):
            field_name = info['field']
            active_ids = info['ids']
            
            # Re-fetch data
            # new_items is list of (label, color, data_array)
            new_items = self._generate_plot_data(field_name, active_ids)
            
            # Store for update_graph to use
            # We only store the data arrays, assuming order matches 'lines'
            # active_slots_info['lines'] matches active_ids order?
            # Yes, _generate_plot_data iterates active_ids order if implementation is consistent.
            # _generate_plot_data iterates self.trajectories and checks d_id in active_ids.
            # We assume the order of lines created in rebuild_plots matches this order.
            
            # Update cache
            info['cached_data'] = [item[2] for item in new_items] # item[2] is data
            
            # Update limits based on full data
            # We can optimise to only do this occasionally
            min_y, max_y = float('inf'), float('-inf')
            max_len = 0
            has_data = False
            for data in info['cached_data']:
                if data:
                    min_y = min(min_y, min(data))
                    max_y = max(max_y, max(data))
                    max_len = max(max_len, len(data))
                    has_data = True
            
            if has_data:
                info['full_limits'] = (min_y, max_y, max_len)
                # We don't necessarily update axis limits here if we are zooming/panning,
                # but for auto-scale we might.
                # For now, let's update scalar limits.
                ax = info['ax']
                ax.set_xlim(0, max_len)
                buf = (max_y - min_y) * 0.1 if max_y != min_y else 1.0
                ax.set_ylim(min_y - buf, max_y + buf)

    def update_graph(self, frame_idx):
        frame_idx = int(frame_idx)
        any_draw = False
        
        for info in getattr(self, 'active_slots_info', []):
            lines = info['lines']
            cached_data = info.get('cached_data')
            
            if not cached_data or len(cached_data) != len(lines):
                continue
                
            for line, data in zip(lines, cached_data):
                limit = min(frame_idx + 1, len(data))
                # Slice logic
                line.set_data(range(limit), data[:limit])
                any_draw = True
                
        if any_draw:
            self.canvas.draw_idle()

