import sys
import os
import json
from dataclasses import asdict

# --- PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)
# ----------------

import core.cfg as cfg
from utils import simulation

def generate_file():
    args = cfg.parse_args()
    
    print(f"Generating data for {args.num_drones} drones...")
    
    bounds = cfg.calculate_bounds(args)
    min_lat, max_lat, min_lon, max_lon = bounds
    
    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon
    min_dim = min(lat_range, lon_range)
    base_radius = min_dim * 0.4
    
    trajectories = []
    for i in range(args.num_drones):
        r = base_radius * (1 - (i * 0.1))
        if r < 0: r = base_radius * 0.1
        
        is_reversed = (i % 2 != 0)
        
        # simulation.py is now purely a generator
        path = simulation.generate_recorded_trajectory(
            drone_id=i+1,
            center_lat=args.lat, 
            center_lon=args.lon, 
            radius_deg=r, 
            steps=300, 
            reverse=is_reversed
        )
        trajectories.append(path)
    
    # --- SAVE LOGIC (Moved here) ---
    output_path = os.path.join(current_dir, "recording.json")
    
    try:
        # Convert dataclasses to list of dicts for JSON serialization
        serializable_data = []
        for path in trajectories:
            path_dicts = [asdict(state) for state in path]
            serializable_data.append(path_dicts)
            
        with open(output_path, 'w') as f:
            json.dump(serializable_data, f, indent=2)
            
        print(f"Successfully saved recording to {output_path}")
        
    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    generate_file()