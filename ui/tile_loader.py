import threading
import requests
from PIL import Image, ImageTk
import io
import os

# --- TILE SERVER CONFIG ---
# OpenStreetMap (Free, Standard Map)
TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

# Google Satellite (Requires API Hack or Valid Key usually, strict limits)
# If you have a key/server, replace this URL.
# --------------------------

class TileLoader:
    def __init__(self):
        self.cache = {}
        self.active_requests = set()
        self.lock = threading.Lock()
        
        # User-Agent is required by OSM policy
        self.headers = {
            'User-Agent': 'DroneViz/1.0 (Python-Tkinter)'
        }

    def get_tile(self, x, y, z):
        """
        Returns a PIL Image if cached.
        If not, returns None and starts a background download.
        """
        key = (x, y, z)
        
        with self.lock:
            if key in self.cache:
                return self.cache[key]
        
        if key not in self.active_requests:
            self.active_requests.add(key)
            threading.Thread(target=self._download_worker, args=(x, y, z), daemon=True).start()
            
        return None

    def _download_worker(self, x, y, z):
        url = TILE_URL.format(x=x, y=y, z=z)
        try:
            response = requests.get(url, headers=self.headers, timeout=2)
            if response.status_code == 200:
                img_data = response.content
                image = Image.open(io.BytesIO(img_data))
                
                with self.lock:
                    self.cache[(x, y, z)] = image
        except Exception as e:
            print(f"Tile fetch failed {x},{y},{z}: {e}")
        finally:
            if (x, y, z) in self.active_requests:
                self.active_requests.remove((x, y, z))