import math
from core.drone_state import DroneSelfState

def generate_recorded_trajectory(drone_id, center_lat, center_lon, radius_deg, steps=300, reverse=False):
    """
    Generates a list of DroneSelfState objects representing a flight path.
    """
    path = []
    for i in range(steps):
        angle = (i / steps) * 2 * math.pi
        
        d_lat = radius_deg * math.cos(angle)
        d_lon = radius_deg * math.sin(angle)
        
        lat = center_lat + d_lat
        lon = center_lon + d_lon
        
        # Calculate Heading
        # Tangent to circle is +90 deg from the radial angle
        heading = (math.degrees(angle) + 90) % 360
        
        if reverse:
            # If going the other way, flip the sequence logic (handled by caller typically, 
            # but here we just adjust heading to face the other way)
            heading = (heading + 180) % 360

        # Create the full data struct
        state = DroneSelfState.create_from_viz_data(drone_id, lat, lon, heading)
        path.append(state)
        
    if reverse:
        return list(reversed(path))
    return path