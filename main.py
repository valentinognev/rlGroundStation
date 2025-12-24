import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os

import core.cfg as cfg
from core.drone_state import DroneSelfState
from ui.app_window import DroneApp

def main():
    args = cfg.parse_args()
    bounds = cfg.calculate_bounds(args)
    
    print(f"--- Configuration ---")
    print(f"Center: {args.lat}, {args.lon}")
    print(f"Window: {args.width}x{args.height}")
    
    root = tk.Tk()
    root.title(f"Drone Viz (Res: {args.res})")

    # --- Load Handler ---
    def handle_load_data():
        # 1. Open File Dialog
        file_path = filedialog.askopenfilename(
            title="Select Drone Recording",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialdir=os.getcwd()
        )
        
        if not file_path:
            return # User cancelled

        print(f"Loading file: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                raw_data = json.load(f)
            
            loaded_trajectories = []
            
            # Parse List[List[Dict]] -> List[List[DroneSelfState]]
            for raw_path in raw_data:
                parsed_path = []
                for state_dict in raw_path:
                    # Convert dict back to object
                    state = DroneSelfState(**state_dict)
                    parsed_path.append(state)
                loaded_trajectories.append(parsed_path)
            
            app.load_data(loaded_trajectories)
            print(f"Successfully loaded {len(loaded_trajectories)} trajectories.")
            
        except Exception as e:
            print(f"Failed to load file: {e}")
            messagebox.showerror("Load Error", f"Could not load file:\n{e}")

    # Init App
    app = DroneApp(root, bounds, args.width, args.height, args.res, handle_load_data)

    root.mainloop()

if __name__ == "__main__":
    main()