import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import sys
import threading

import core.cfg as cfg
from core.drone_state import DroneSelfState
from ui.app_window import DroneApp
from serial.serial_bridge import SerialBridge

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

def start_stream(path, app):
    """
    Starts a thread to read from the serial/pipe and update arguments.
    """
    print(f"Connecting to stream at {path}...")
    
    def read_loop():
        # Ensure FIFO exists if it's a pipe?
        # If it's a real device, it must exist. 
        # For our test, simulating with FIFO, we assume it's created by sender or we wait.
        # But open() on FIFO blocks until writer opens it.
        
        bridge = SerialBridge()
        
        try:
            # We open with os.open to be potentially non-blocking or just standard open
            # But the bridge takes a file descriptor (int).
            # Python's open() returns a file object, we need fileno().
            # Note: For FIFO, open() blocks until writer is active.
            
            # Since serial_reader.cpp expects a read loop, we can just pass the FD.
            # But wait, read_drone_state does ONE read of a struct. It loops internally for partials of THAT struct.
            # We need to loop endlessly here.
            
            fd = os.open(path, os.O_RDONLY) # Blocks here for FIFO
            print("Stream Connected.")
            
            while True:
                # read_state returns DroneSelfState or None
                state = bridge.read_state(fd)
                if state:
                    # Push to UI thread
                    app.root.after(0, app.process_new_state, state)
                else:
                    # read failure or closed?
                    # The C loop returns -1 on error/EOF.
                    # If EOF, we might want to exit or wait.
                    print("Stream Ended or Error.")
                    break
            
            os.close(fd)
            
        except Exception as e:
            print(f"Stream Error: {e}")

    t = threading.Thread(target=read_loop, daemon=True)
    t.start()

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
        print(f"Stream mode selected. Connecting to {args.path}")
        start_stream(args.path, app)

    root.mainloop()

if __name__ == "__main__":
    main()