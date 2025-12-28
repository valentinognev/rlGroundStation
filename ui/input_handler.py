import platform

class InputHandler:
    def __init__(self, canvas):
        self.canvas = canvas
        self.pan_start_x = 0
        self.pan_start_y = 0
        self._bind_events()

    def _bind_events(self):
        # Pan bindings
        self.canvas.bind("<ButtonPress-1>", self.on_pan_start)
        self.canvas.bind("<B1-Motion>", self.on_pan_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_pan_end)

        # Zoom bindings - NOW PASSING MOUSE COORDS
        system = platform.system()
        if system == "Linux":
            self.canvas.bind("<Button-4>", self.on_zoom_in)
            self.canvas.bind("<Button-5>", self.on_zoom_out)
        else:
            # Windows/MacOS
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)

    # --- PANNING ---
    def on_pan_start(self, event):
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def on_pan_drag(self, event):
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.canvas.update_pan(dx, dy)

    def on_pan_end(self, event):
        self.canvas.end_pan()

    # --- ZOOMING ---
    def on_zoom_in(self, event):
        # Zoom In (0.9x) at specific mouse location
        self.canvas.zoom(0.9, event.x, event.y)

    def on_zoom_out(self, event):
        # Zoom Out (1.1x) at specific mouse location
        self.canvas.zoom(1.1, event.x, event.y)

    def on_mouse_wheel(self, event):
        # Determine zoom factor based on scroll direction
        if event.delta > 0:
            factor = 0.9
        else:
            factor = 1.1
        
        # Pass event coordinates
        self.canvas.zoom(factor, event.x, event.y)