# Developer Handoff Guide

## Overview

`rlGroundStation` is a Python/Tkinter application designed to visualize drone swarm telemetry in real-time or from recorded JSON logs. It acts as a Ground Control Station (GCS) for monitoring position, velocity, heading, and other states.

## Architecture Architecture

The application is structured around a central update loop (the `animate_loop`) that drives the UI, while a separate thread handles blocking I/O for data ingestion.

### Key Components

1.  **Entry Point (`main.py`)**:
    *   Parses CLI arguments (`core/cfg.py`).
    *   Initializes the `DroneApp` (UI Controller).
    *   Manages the data ingestion thread (`start_stream`).
    *   Handling the serial connection or FIFO pipe reading.

2.  **UI Controller (`ui/app_window.py`)**:
    *   The central hub (`DroneApp` class).
    *   Manages the `tk.Tk` root and `ttk.Notebook`.
    *   Holds the state of the world: `self.trajectories` (List of lists of `DroneSelfState`).
    *   **Playback Logic**: `on_scrub`, `play`, `pause`, and `animate_loop`.
    *   **Interpolation**: Smooths visual movement between discrete data frames using linear interpolation (`lerp`).
    *   **Live Stream Handling**: `process_new_state` receives data from the I/O thread, appends it to trajectories, and updates the view.

3.  **Visualization**:
    *   **Map (`ui/map_canvas.py`)**: 
        *   Custom `tk.Canvas`.
        *   Handles coordinate transformation (Lat/Lon <-> Screen Pixels) using `core/geo_math`.
        *   Manages Tile Loading (`ui/tile_loader.py` and `core/tile_utils`) to fetch or cache OpenStreetMap-style tiles.
        *   Draws drones as composed geometric shapes (Oval body + Line heading + Arrow velocity).
    *   **Graphing (`ui/graph_panel.py`)**:
        *   Embeds `matplotlib` using `FigureCanvasTkAgg`.
        *   Supports dynamic plotting of multiple fields (Lat, Lon, Alt, etc.) across 3 slots.
        *   Implements throttling (`GRAPH_SKIP_FRAMES`) to prevent UI lag during high-frequency updates.

4.  **Data Bridge (`gs_serial/serial_bridge.py`)**:
    *   Decodes the binary protocol used by the drones.
    *   **Protocol**: 64-byte packets.
        *   Header: `0xABCD`
        *   Structure: `ID` (uint16), `Pos` (3x float), `Vel` (3x float), `Hdg` (float), `Status` (uint16), etc.
    *   Implements a sliding window buffer to handle fragmentation and stream synchronization.

## Data Flow

### Live Streaming Mode
1.  `main.py` spawns a daemon thread `read_loop`.
2.  `read_loop` reads raw bytes from the Serial Port or Named Pipe.
3.  Bytes are fed into `SerialBridge.buffer`.
4.  `SerialBridge.read_state` scans for the sync marker (`0xABCD`) and unpacks the 64-byte struct.
5.  If valid, a `DroneSelfState` object is created.
6.  The object is passed to the UI thread via `root.after(0, app.process_new_state, state)`.
7.  `DroneApp` appends the state to the history and updates the current display.

### Playback Mode
1.  JSON file is loaded via `load_file_content`.
2.  Data is parsed into `DroneSelfState` objects.
3.  The `play_head` (float frame index) is incremented in `animate_loop`.
4.  `draw_frame` interpolates between `floor(play_head)` and `ceil(play_head)` to render smooth motion.

## Threading Model

*   **Main Thread (UI)**: Handles all Tkinter drawing, event processing, and the animation loop. **Accessing UI widgets from other threads is forbidden** and will cause crashes. Use `root.after` to marshal data to this thread.
*   **Reader Thread**: Only created in `stream` mode. Blocks on `serial.read` or `os.read`. Purely producer; handles no UI logic.

## Key Files for New Developers

*   `gs_serial/serial_bridge.py`: **Start here if protocol changes.** This defines exactly how bytes are interpreted.
*   `ui/app_window.py`: **Start here if adding UI features.** It connects the data to the visuals.
*   `ui/map_canvas.py`: **Start here if changing the map drawing.** (e.g., adding waypoints or geofences).
*   `ui/graph_panel.py`: **Start here if adding new plots.** Extend the `FIELDS` dictionary to map new `DroneSelfState` attributes to plot labels.

## Known Issues / TODOs

*   **Graph Performance**: Matplotlib can be slow. The `GRAPH_SKIP_FRAMES` constant in `app_window.py` throttles updates. If expanding graphing heavily, consider `blitting`.
*   **Tile Loading**: Currently synchronous in some parts? Check `tile_loader.py` if map stutters when panning to new areas.
*   **Protocol Hardcoding**: The 64-byte struct format is hardcoded in `serial_bridge.py`. Consider moving this to a config if it changes often.

## Debugging

*   **Simulation**: Use `simulate_serial_stream.py` (if available) or create a named pipe to push fake data to the app without real hardware.
    ```bash
    mkfifo /tmp/flight_data_pipe
    python main.py -s stream -p /tmp/flight_data_pipe
    # In another terminal, write binary data to the pipe
    ```
