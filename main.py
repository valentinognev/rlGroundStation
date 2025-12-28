import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import sys

import core.cfg as cfg
from core.drone_state import DroneSelfState
from ui.app_window import DroneApp

def load_file_content(file_path, app):
    """
    Helper to read a JSON file and push data to the app.
    """
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return

    print(f"Loading file: {file_path}")
    try:
        with open(file_path, 'r') as f:
            raw_data = json.load(f)
        
        loaded_trajectories = []
        
        # Parse List[List[Dict]] -> List[List[DroneSelfState]]
        for raw_path in raw_data:
            parsed_path = []
            for state_dict in raw_path:
                state = DroneSelfState(**state_dict)
                parsed_path.append(state)
            loaded_trajectories.append(parsed_path)
        
        app.load_data(loaded_trajectories)
        print(f"Successfully loaded {len(loaded_trajectories)} trajectories.")
        
    except Exception as e:
        print(f"Failed to load file: {e}")
        messagebox.showerror("Load Error", f"Could not load file:\n{e}")

def main():
    args = cfg.parse_args()
    bounds = cfg.calculate_bounds(args)
    
    print(f"--- Configuration ---")
    print(f"Source: {args.source}")
    if args.source != 'none':
        print(f"Path: {args.path}")
    
    root = tk.Tk()
    root.title(f"Drone Viz (Res: {args.res})")

    # --- UI Callback for "Load" Button ---
    def handle_ui_load_request():
        file_path = filedialog.askopenfilename(
            title="Select Drone Recording",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialdir=os.getcwd()
        )
        if file_path:
            load_file_content(file_path, app)

    # Init App
    app = DroneApp(root, bounds, args.width, args.height, args.res, handle_ui_load_request)

    # --- CLI Auto-Load Logic ---
    if args.source == "file":
        # We use 'after' to let the GUI initialize first
        root.after(100, lambda: load_file_content(args.path, app))
    elif args.source == "stream":
        print(f"Stream mode selected. Connecting to {args.path} (Not Implemented yet)")

    root.mainloop()

if __name__ == "__main__":
    main()