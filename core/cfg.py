import argparse

# --- Constants ---
# Margins: (Left, Top, Right, Bottom)
# Bottom padding 150 creates the "Footer" area
PADDING = (60, 20, 20, 150) 

def parse_args():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Drone Visualization CLI")
    
    # --- Data Source Config ---
    parser.add_argument("-s", "--source", type=str, default="none", 
                        choices=["file", "stream", "none"],
                        help="Data source: 'file', 'stream', or 'none'")
    
    parser.add_argument("-p", "--path", type=str, 
                        help="Path to JSON file (if source=file) or Stream Address (if source=stream)")

    # --- Simulation Params ---
    parser.add_argument("--num_drones", type=int, default=4, help="Number of drones to simulate")

    # --- View Params ---
    parser.add_argument("--lat", type=float, default=32.0, help="Center Latitude")
    parser.add_argument("--lon", type=float, default=34.0, help="Center Longitude")
    parser.add_argument("--width", type=int, default=800, help="Window Width (px)")
    parser.add_argument("--height", type=int, default=600, help="Window Height (px)")
    parser.add_argument("--res", type=float, default=0.00001, help="Resolution (deg/px)")

    args = parser.parse_args()

    if args.source in ["file", "stream"] and not args.path:
        parser.error(f"argument --source {args.source} requires --path (-p) to be specified.")

    return args

def calculate_bounds(args):
    pad_l, pad_t, pad_r, pad_b = PADDING
    active_w = args.width - pad_l - pad_r
    active_h = args.height - pad_t - pad_b
    
    lat_range = active_h * args.res
    lon_range = active_w * args.res
    
    min_lat = args.lat - (lat_range / 2.0)
    max_lat = args.lat + (lat_range / 2.0)
    min_lon = args.lon - (lon_range / 2.0)
    max_lon = args.lon + (lon_range / 2.0)
    
    return min_lat, max_lat, min_lon, max_lon