#!/usr/bin/env python3
import serial
import struct
import argparse
import time

# Format from device_utils.py:
# Sync: H (2)
# Pos: 3f (12)
# Vel: 3f (12)
# Hdg: 3f (12)
# Time: q (8)
# ID: H (2)
# State: H (2)
# Spare: 14s (14)
# Total: 64 bytes
STRUCT_FMT = '<H3f3f3fqHH14s'
STRUCT_SIZE = 64
SYNC_MARKER = b'\xcd\xab' # 0xABCD little endian

def validate_packet(drone_id, lat, lon):
    if drone_id <= 0 or drone_id > 255: return False
    if abs(lat) > 90.0 or abs(lon) > 180.0: return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Verify Serial Stream")
    parser.add_argument("port", help="Serial port (e.g., /dev/ttyUSB1)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("--sync", action="store_true", help="Enable sync logic")
    
    args = parser.parse_args()
    
    print(f"Opening {args.port} at {args.baud} baud...")
    
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except Exception as e:
        print(f"Error opening port: {e}")
        return

    print(f"Reading... (Struct Size: {STRUCT_SIZE} bytes)")
    
    buffer = b""
    
    try:
        while True:
            chunk = ser.read(256) # Read whatever is available
            if not chunk:
                continue
            
            buffer += chunk
            
            # Process buffer
            while True:
                # Search for header
                header_idx = buffer.find(SYNC_MARKER)
                if header_idx == -1:
                    # Keep last byte
                    if len(buffer) > 0 and buffer[-1] == 0xCD:
                        buffer = buffer[-1:]
                    else:
                        buffer = b""
                    break
                
                # Header found
                buffer = buffer[header_idx:]

                if len(buffer) < STRUCT_SIZE:
                    break
                    
                # We have a candidate packet
                candidate = buffer[:STRUCT_SIZE]
                
                try:
                    unpacked = struct.unpack(STRUCT_FMT, candidate)
                    
                    # Unpack fields
                    drone_id = unpacked[11]
                    lat = unpacked[1]
                    lon = unpacked[2]
                    
                    if args.sync:
                        if validate_packet(drone_id, lat, lon):
                             print(f"[SYNCED] ID: {drone_id} | Pos: ({lat:.5f}, {lon:.5f}, {unpacked[3]:.2f}) | Vel: ({unpacked[4]:.2f}, {unpacked[5]:.2f}, {unpacked[6]:.2f}) | Hdg: {unpacked[7]:.2f} | Time: {unpacked[10]}")
                             buffer = buffer[STRUCT_SIZE:]
                        else:
                             # Bad packet despite header?
                             print(f"[INVALID] ID: {drone_id} (Bad Data)")
                             buffer = buffer[2:] # Skip header
                    else:
                         print(f"[RAW] ID: {drone_id} ...")
                         buffer = buffer[STRUCT_SIZE:]
                    
                except Exception as e:
                    print(f"Unpack error: {e}")
                    buffer = buffer[2:] # Skip header
                    
    except KeyboardInterrupt:
        print("\nStopping...")
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()
