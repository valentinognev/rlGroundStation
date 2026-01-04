
import ctypes
import os
from core.drone_state import DroneSelfState

# Define the C structure in Python
class CDroneSelfState(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("id", ctypes.c_short),
        ("lat", ctypes.c_float),
        ("lon", ctypes.c_float),
        ("alt", ctypes.c_float),
        ("velocity_north", ctypes.c_float),
        ("velocity_east", ctypes.c_float),
        ("velocity_down", ctypes.c_float),
        ("heading", ctypes.c_float),
        ("sm_current_stat", ctypes.c_short),
        ("battery_precentages", ctypes.c_short),
        ("drones_keep_alive", ctypes.c_short), # Bit field handled as short
        ("gps_3d_fix", ctypes.c_short),        # Bit field handled as short
    ]

# Bit field extraction logic requires manual handling in Python equivalent of C bitfields
# But wait, ctypes does support bitfields!
# Let's redefine correctly to match the C bitfields if possible, OR
# Since we just read bytes, the memory layout matters.
# The C struct has bitfields:
# short drones_keep_alive : 4;
# short gps_3d_fix : 1;
# short padding : 11;
# All these 3 sit in one `short` (16 bits).
#
# To accurately map this in ctypes, we should treat the storage unit as c_short
# and do bitwise operations, OR use ctypes bitfields if valid.
# Standard ctypes Structures support bitfields.

class CDroneSelfState_BitFields(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("id", ctypes.c_short),
        ("lat", ctypes.c_float),
        ("lon", ctypes.c_float),
        ("alt", ctypes.c_float),
        ("velocity_north", ctypes.c_float),
        ("velocity_east", ctypes.c_float),
        ("velocity_down", ctypes.c_float),
        ("heading", ctypes.c_float),
        ("sm_current_stat", ctypes.c_short),
        ("battery_precentages", ctypes.c_short),
        # Bitfields: strictly typed to the storage unit type
        ("drones_keep_alive", ctypes.c_uint16, 4),
        ("gps_3d_fix", ctypes.c_uint16, 1),
        ("padding", ctypes.c_uint16, 11),
    ]

class SerialBridge:
    def __init__(self, lib_path=None):
        if lib_path is None:
            # Default to looking in the same directory as this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            lib_path = os.path.join(current_dir, "libserial_reader.so")
        
        self.lib = ctypes.CDLL(lib_path)
        
        # Setup function signature
        self.lib.read_drone_state.argtypes = [ctypes.c_int, ctypes.POINTER(CDroneSelfState_BitFields)]
        self.lib.read_drone_state.restype = ctypes.c_int

    def read_state(self, serial_fd):
        """
        Reads data from the serial FD and returns a DroneSelfState object.
        Returns None on failure.
        """
        c_state = CDroneSelfState_BitFields()
        result = self.lib.read_drone_state(serial_fd, ctypes.byref(c_state))
        
        if result == 0:
            # Convert to Python Dataclass
            return DroneSelfState(
                id=c_state.id,
                lat=c_state.lat,
                lon=c_state.lon,
                alt=c_state.alt,
                velocity_north=c_state.velocity_north,
                velocity_east=c_state.velocity_east,
                velocity_down=c_state.velocity_down,
                heading=c_state.heading,
                sm_current_stat=c_state.sm_current_stat,
                battery_precentages=c_state.battery_precentages,
                drones_keep_alive=c_state.drones_keep_alive,
                gps_3d_fix=c_state.gps_3d_fix
            )
        else:
            return None
