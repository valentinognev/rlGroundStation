import math

def lat_lon_to_screen(lat, lon, bounds, screen_dims, padding):
    """
    Converts Lat/Lon to screen X/Y.
    bounds: (min_lat, max_lat, min_lon, max_lon)
    screen_dims: (width, height)
    padding: (left, top, right, bottom)
    """
    min_lat, max_lat, min_lon, max_lon = bounds
    w, h = screen_dims
    pad_l, pad_t, pad_r, pad_b = padding

    draw_w = w - pad_l - pad_r
    draw_h = h - pad_t - pad_b

    # Normalize 0.0 -> 1.0
    try:
        x_pct = (lon - min_lon) / (max_lon - min_lon)
        y_pct = (lat - min_lat) / (max_lat - min_lat)
    except ZeroDivisionError:
        x_pct, y_pct = 0.5, 0.5

    screen_x = pad_l + (x_pct * draw_w)
    # Invert Y (Screen Y goes down, Latitude goes up)
    screen_y = (h - pad_b) - (y_pct * draw_h)

    return screen_x, screen_y

def calculate_drone_polygon(center_x, center_y, heading_deg, size):
    """
    Returns coordinate pairs for the 4 drone legs based on heading.
    """
    r = size / 2.0
    
    # Angles relative to North (0 deg)
    # Front-Left (-45), Front-Right (+45), Rear-Left (-135), Rear-Right (+135)
    # Note: We subtract heading because standard math rotates CCW, navigation rotates CW
    angles = {
        "fl": heading_deg - 45,
        "fr": heading_deg + 45,
        "rl": heading_deg - 135,
        "rr": heading_deg + 135
    }

    points = {}
    for key, ang in angles.items():
        rad = math.radians(ang)
        # x = sin, y = -cos (Navigation frame to Screen frame)
        px = center_x + r * math.sin(rad)
        py = center_y - r * math.cos(rad)
        points[key] = (px, py)
        
    return points