import math

def deg2num(lat_deg, lon_deg, zoom):
    """
    Converts Lat/Lon to Web Mercator Tile numbers (x, y).
    """
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def num2deg(xtile, ytile, zoom):
    """
    Converts Tile numbers (x, y) to Lat/Lon of the top-left corner.
    """
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def calculate_zoom_level(resolution_deg_per_px):
    """
    Estimates the appropriate zoom level for the current screen resolution.
    Target: ~1 tile pixel approx 1 screen pixel.
    """
    # 360 degrees / 256 pixels = 1.40625 deg/px at Zoom 0
    # Res = 1.40625 / (2^zoom)
    # => 2^zoom = 1.40625 / Res
    # => zoom = log2(1.40625 / Res)
    if resolution_deg_per_px <= 1e-9: return 19
    
    target = 1.40625 / resolution_deg_per_px
    zoom = math.log2(target)
    
    # Cap between 0 and 19 (standard max zoom)
    return max(0, min(19, int(zoom)))