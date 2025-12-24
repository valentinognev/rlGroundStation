import tkinter as tk

class ControlPanel(tk.Frame):
    def __init__(self, parent, callbacks):
        """
        callbacks: dict containing 'play', 'pause', 'reset', 'drag', 'load'
        """
        super().__init__(parent, height=100, bg="#f0f0f0")
        self.callbacks = callbacks
        
        # 1. Slider
        self.slider = tk.Scale(self, from_=0, to=100, orient=tk.HORIZONTAL, 
                               command=self._on_drag, showvalue=0, bg="#e0e0e0")
        self.slider.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # 2. Buttons Container
        btn_box = tk.Frame(self, bg="#f0f0f0")
        btn_box.pack(side=tk.TOP, fill=tk.X)

        # Left Side Buttons
        self._add_btn(btn_box, "Play", callbacks['play'], "#ddffdd")
        self._add_btn(btn_box, "Pause", callbacks['pause'], "#ffffdd")
        self._add_btn(btn_box, "Reset", callbacks['reset'], "#ffdddd")
        
        # Status
        self.lbl_status = tk.Label(btn_box, text="Status: Ready", font=("Arial", 10), bg="#f0f0f0")
        self.lbl_status.pack(side=tk.LEFT, padx=10)
        
        # Right Side - NEW LOAD BUTTON
        self.btn_load = tk.Button(btn_box, text="Load Data", command=callbacks['load'], bg="#ddddff")
        self.btn_load.pack(side=tk.RIGHT, padx=10, pady=5)

        self.lbl_frame = tk.Label(btn_box, text="Frame: 0", font=("Arial", 9), bg="#f0f0f0")
        self.lbl_frame.pack(side=tk.RIGHT, padx=10)

    def _add_btn(self, parent, text, cmd, color):
        tk.Button(parent, text=text, command=cmd, width=8, bg=color).pack(side=tk.LEFT, padx=5, pady=5)

    def _on_drag(self, value):
        self.callbacks['drag'](int(value))

    def update_status(self, text):
        self.lbl_status.config(text=f"Status: {text}")

    def update_frame_label(self, frame_num):
        self.lbl_frame.config(text=f"Frame: {frame_num}")

    def set_slider_max(self, max_val):
        self.slider.config(to=max_val)

    def set_slider_val(self, val):
        self.slider.set(val)