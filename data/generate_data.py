import sys
import os
import json
import random
from dataclasses import asdict

# --- PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)
# ----------------

import core.cfg as cfg
from utils import simulation

# --- SIMULATION SETTINGS ---
# Probability that a status toggles (On <-> Off) in a given frame.
# 0.05 = 5% chance per step.
TOGGLE_CHANCE = 0.05 
# ---------------------------

def inject_failures(trajectories):
    """
    Simulates a 'Random Walk' for both Communication and GPS status.
    """
    chance_pct = int(TOGGLE_CHANCE * 100)
    print(f"Injecting random walk failures ({chance_pct}% toggle chance)...")
    
    num_drones = len(trajectories)
    if num_drones == 0: return
    num_frames = len(trajectories[0])

    # 1. Initialize Running States
    # Keep Alive: [observer_index][target_bit_index] (Initially Connected)
    connection_matrix = [[1 for _ in range(4)] for _ in range(num_drones)]
    
    # GPS Fix: [drone_index] (Initially Fixed)
    gps_states = [1 for _ in range(num_drones)]

    # 2. Iterate through time
    for t in range(num_frames):
        for i in range(num_drones):
            
            # --- A. Communication Matrix Logic ---
            new_mask = 0
            for target_bit in range(4):
                # Random Toggle Check
                if random.random() < TOGGLE_CHANCE:
                    connection_matrix[i][target_bit] ^= 1 # Flip 0->1 or 1->0
                
                # Build Mask
                if connection_matrix[i][target_bit]:
                    new_mask |= (1 << target_bit)
            
            trajectories[i][t].drones_keep_alive = new_mask
            
            # --- B. GPS Fix Logic ---
            # Random Toggle Check
            if random.random() < TOGGLE_CHANCE:
                gps_states[i] ^= 1 # Flip 0->1 or 1->0
            
            trajectories[i][t].gps_3d_fix = gps_states[i]

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
        
        path = simulation.generate_recorded_trajectory(
            drone_id=i+1,
            center_lat=args.lat, 
            center_lon=args.lon, 
            radius_deg=r, 
            steps=300, 
            reverse=is_reversed
        )
        trajectories.append(path)
    
    # --- INJECT FAILURES ---
    inject_failures(trajectories)
    # -----------------------

    # --- SAVE LOGIC ---
    output_path = os.path.join(current_dir, "recording.json")
    
    try:
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