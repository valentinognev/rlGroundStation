import json
import struct
import time
import os
import sys
import argparse

# Define the struct format
# < = little endian
# h = short (2 bytes)
# f = float (4 bytes)
# 7f = 7 floats
# h = short
# h = short
# h = short (bitfields)
STRUCT_FMT = '<hfffffffhhh'

def load_recording(path):
    with open(path, 'r') as f:
        return json.load(f)

def pack_state(state):
    # state is a dict
    id_val = int(state.get('id', 0))
    lat = float(state.get('lat', 0.0))
    lon = float(state.get('lon', 0.0))
    alt = float(state.get('alt', 0.0))
    vn = float(state.get('velocity_north', 0.0))
    ve = float(state.get('velocity_east', 0.0))
    vd = float(state.get('velocity_down', 0.0))
    hdg = float(state.get('heading', 0.0))
    sm = int(state.get('sm_current_stat', 0))
    bat = int(state.get('battery_precentages', 0))
    
    keep_alive = int(state.get('drones_keep_alive', 0))
    gps_fix = int(state.get('gps_3d_fix', 0))
    
    # Pack bitfields
    # Assuming keep_alive (4 bits) at LSB, gps_fix (1 bit) next
    # Based on verification: keep_alive=10, gps=1 -> 26 (11010)
    # bits: 4(gps) 3 2 1 0(keep_alive)
    bitfield = (gps_fix << 4) | (keep_alive & 0x0F)
    
    return struct.pack(STRUCT_FMT, 
                       id_val, lat, lon, alt, vn, ve, vd, hdg, sm, bat, bitfield)

def main():
    parser = argparse.ArgumentParser(description="Stream simulated drone data to FIFO")
    parser.add_argument("--file", default="data/recording.json", help="Path to recording JSON")
    parser.add_argument("--output", default="/tmp/drone_serial", help="Path to output FIFO")
    parser.add_argument("--rate", type=float, default=10.0, help="Hz to stream at (approx)")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Recording file not found: {args.file}")
        sys.exit(1)

    data = load_recording(args.file)
    # data is List[List[Dict]] (List of Drones, each is List of Frames)
    # We need to transpose to iterate by Time Frame
    
    num_drones = len(data)
    if num_drones == 0:
        print("No drones in data.")
        sys.exit(0)
        
    num_frames = len(data[0])
    
    print(f"Loaded {num_drones} drones with {num_frames} frames each.")
    
    # Create FIFO if not exists
    if not os.path.exists(args.output):
        try:
            os.mkfifo(args.output)
            print(f"Created FIFO at {args.output}")
        except OSError as e:
            print(f"Failed to create FIFO: {e}")
            sys.exit(1)
    
    print(f"Opening FIFO {args.output} for writing... (Blocking until reader connects)")
    try:
        sys.stdout.flush()
        fifo = open(args.output, 'wb')
        print("Reader connected. Starting stream.")
    except Exception as e:
        print(f"Error opening FIFO: {e}")
        sys.exit(1)

    delay = 1.0 / args.rate
    
    try:
        for t in range(num_frames):
            for i in range(num_drones):
                if t < len(data[i]):
                    state = data[i][t]
                    packed = pack_state(state)
                    fifo.write(packed)
            
            fifo.flush()
            time.sleep(delay)
            
            if t % 10 == 0:
                print(f"Sent frame {t}/{num_frames}\r", end="")
                
    except BrokenPipeError:
        print("\nReader disconnected.")
    except KeyboardInterrupt:
        print("\nStream stopped.")
    finally:
        fifo.close()
        # Clean up FIFO? Maybe keep it for re-use.
        # os.remove(args.output)

if __name__ == "__main__":
    main()
