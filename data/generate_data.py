import sys
import os
import json
import random
import math
from dataclasses import asdict

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

import core.cfg as cfg
from utils import simulation

# --- SIMULATION SETTINGS ---
TOGGLE_CHANCE = 0.05 

# Target Center: 32°46'36.7"N 35°01'24.3"E
TARGET_LAT = 32.7768611
TARGET_LON = 35.0234167
# ---------------------------

def recalculate_kinematics(trajectories):
    """
    Overwrites velocity and heading to perfectly match the position changes.
    This ensures the arrows point exactly where the drone moves in the next frame.
    """
    print("Recalculating kinematics (Velocity & Heading)...")
    
    for path in trajectories:
        # Iterate up to the second-to-last frame
        for t in range(len(path) - 1):
            curr = path[t]
            next_state = path[t+1]
            
            # 1. Calculate Delta
            d_lat = next_state.lat - curr.lat
            d_lon = next_state.lon - curr.lon
            
            # 2. Convert to Meters (approx)
            # Lat: 1 deg = 111139 m
            # Lon: 1 deg = 111139 * cos(lat) m
            meters_north = d_lat * 111139.0
            avg_lat_rad = math.radians(curr.lat)
            meters_east = d_lon * 111139.0 * math.cos(avg_lat_rad)
            
            # We assume 1 step = 1 second for visualization scaling
            curr.velocity_north = meters_north
            curr.velocity_east = meters_east
            
            # 3. Calculate Heading (Navigation Convention: 0=North, 90=East)
            # atan2(y, x) gives angle from East (mathematical 0)
            math_angle_deg = math.degrees(math.atan2(meters_north, meters_east))
            
            # Convert Math angle to Nav heading
            # Nav = 90 - Math
            nav_heading = (90 - math_angle_deg) % 360
            curr.heading = nav_heading

        # Fix the last frame (copy from previous)
        if len(path) > 1:
            path[-1].velocity_north = path[-2].velocity_north
            path[-1].velocity_east = path[-2].velocity_east
            path[-1].heading = path[-2].heading

def inject_failures(trajectories):
    chance_pct = int(TOGGLE_CHANCE * 100)
    print(f"Injecting random walk failures ({chance_pct}% toggle chance)...")
    
    num_drones = len(trajectories)
    if num_drones == 0: return
    num_frames = len(trajectories[0])

    connection_matrix = [[1 for _ in range(4)] for _ in range(num_drones)]
    gps_states = [1 for _ in range(num_drones)]

    for t in range(num_frames):
        for i in range(num_drones):
            new_mask = 0
            for target_bit in range(4):
                if random.random() < TOGGLE_CHANCE:
                    connection_matrix[i][target_bit] ^= 1 
                if connection_matrix[i][target_bit]:
                    new_mask |= (1 << target_bit)
            
            trajectories[i][t].drones_keep_alive = new_mask
            
            if random.random() < TOGGLE_CHANCE:
                gps_states[i] ^= 1 
            
            trajectories[i][t].gps_3d_fix = gps_states[i]

def generate_file():
    args = cfg.parse_args()
    print(f"Generating data for {args.num_drones} drones...")
    print(f"Centering around: {TARGET_LAT}, {TARGET_LON}")

    # Use args for bounds calculation if you want dynamic sizing, 
    # but we are anchoring the center to the constants now.
    
    # Simple radius calculation logic based on config bounds or fixed
    # We will derive a radius from the args if provided, or default
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
            center_lat=TARGET_LAT,  # UPDATED: Using explicit constant
            center_lon=TARGET_LON,  # UPDATED: Using explicit constant
            radius_deg=r, 
            steps=300, 
            reverse=is_reversed
        )
        trajectories.append(path)
    
    # --- 1. RECALCULATE KINEMATICS ---
    recalculate_kinematics(trajectories)
    
    # --- 2. INJECT FAILURES ---
    inject_failures(trajectories)

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