import os
import struct
import ctypes
from core.drone_state import DroneSelfState

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

class SerialBridge:
    def __init__(self, lib_path=None):
        self.buffer = b""

    def validate_packet(self, drone_id, lat, lon):
        """
        Simple heuristic to validate packet integrity.
        """
        # ID check
        if drone_id <= 0 or drone_id > 255:
            # print(f"DEBUG: Rejecting ID {drone_id}")
            return False
        # Data integrity check (roughly)
        if abs(lat) > 90.0 or abs(lon) > 180.0:
            # print(f"DEBUG: Rejecting Lat/Lon {lat}/{lon}")
            return False
        return True

    def read_state(self, stream_source):
        """
        Reads data from the source and returns a DroneSelfState object.
        Blocks until a valid packet is found or EOF is reached.
        Implements a sliding window to synchronize the stream.
        """
        while True:
            # 1. Sync: Look for Sync Marker
            header_idx = self.buffer.find(SYNC_MARKER)
            if header_idx == -1:
                # Header not found yet. Keep last byte just in case
                if len(self.buffer) > 0:
                     if self.buffer[-1] == 0xCD:
                         self.buffer = self.buffer[-1:]
                     else:
                         self.buffer = b""
                else:
                    self.buffer = b""
            else:
                # Header found at header_idx
                self.buffer = self.buffer[header_idx:]

                if len(self.buffer) >= STRUCT_SIZE:
                    candidate = self.buffer[:STRUCT_SIZE]
                    
                    try:
                        unpacked = struct.unpack(STRUCT_FMT, candidate)
                        
                        # Consume consumed bytes from buffer
                        self.buffer = self.buffer[STRUCT_SIZE:]
                        
                        drone_id = unpacked[11]
                        lat = unpacked[1]
                        lon = unpacked[2]
                        
                        if self.validate_packet(drone_id, lat, lon):
                            # Valid packet!
                            return DroneSelfState(
                                id=drone_id,
                                lat=lat,
                                lon=lon,
                                alt=unpacked[3],
                                velocity_north=unpacked[4],
                                velocity_east=unpacked[5],
                                velocity_down=unpacked[6],
                                heading=unpacked[7],       # Heading[0]
                                sm_current_stat=unpacked[12],
                                battery_precentages=100,   # Default
                                drones_keep_alive=15,      # Default (1111)
                                gps_3d_fix=1               # Default
                            )
                        else:
                            # Bad packet content (validation failed)
                            pass
                            
                    except struct.error:
                        # Should not happen
                        self.buffer = self.buffer[STRUCT_SIZE:]
                
                else:
                    # Header found but not enough data.
                    pass

            # 2. If we are here, we don't have enough valid data. Read more.
            try:
                # Blocking read. Will wait for at least 1 byte.
                if isinstance(stream_source, int):
                    chunk = os.read(stream_source, 256)
                else:
                    # Assume it's a file-like object (e.g. serial.Serial)
                    chunk = stream_source.read(256)
                    
                if not chunk:
                    # EOF (Connection closed)
                    print("DEBUG: Read returned empty bytes (EOF).")
                    return None
                
                self.buffer += chunk
            except Exception as e:
                print(f"Serial Read Error: {e}")
                return None
