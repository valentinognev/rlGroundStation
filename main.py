import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import json
import os
import sys
import threading

import core.cfg as cfg
from core.drone_state import DroneSelfState
from ui.app_window import DroneApp
from gs_serial.serial_bridge import SerialBridge

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

import serial  # Ensure pyserial is installed

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
        serial_obj = None
        fd = None
        
        try:
            if path.startswith("/dev/tty"):
                # Real serial port requires configuration
                print(f"Opening Serial Port {path} at 115200 baud...")
                try:
                    # buffer_size=0 to minimize latency? Or default.
                    # timeout=None means blocking read (wait forever for data)
                    # This prevents read() returning b'' (EOF) just because of a timeout
                    serial_obj = serial.Serial(path, 115200, timeout=None)
                    fd = serial_obj.fileno()
                except serial.SerialException as e:
                    print(f"Failed to open serial port: {e}")
                    return
            else:
                # FIFO or file
                # Since serial_reader.cpp expects a read loop, we can just pass the FD.
                # But wait, read_drone_state does ONE read of a struct. It loops internally for partials of THAT struct.
                # We need to loop endlessly here.
                fd = os.open(path, os.O_RDONLY) # Blocks here for FIFO
                
            print("Stream Connected.")
            
            while True:
                # read_state returns DroneSelfState or None
                # Pass the serial object if it exists so we use its read() method (blocking)
                # Otherwise pass the FD (for pipes/files)
                if serial_obj:
                    state = bridge.read_state(serial_obj)
                else:
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
            
            if serial_obj:
                serial_obj.close()
            elif fd:
                os.close(fd)
            
        except Exception as e:
            print(f"Stream Error: {e}")
            import traceback
            traceback.print_exc()

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

    def handle_ui_connect_request():
        path = simpledialog.askstring("Connect to Stream", "Enter Serial Path:", initialvalue="/dev/ttyUSB0")
        if path:
            print(f"User requested connection to: {path}")
            start_stream(path, app)

    # Init App
    app = DroneApp(root, bounds, args.width, args.height, args.res, handle_ui_load_request, handle_ui_connect_request)

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