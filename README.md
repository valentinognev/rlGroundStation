# rlGroundStation

rlGroundStation is a Python-based Ground Control Station (GCS) visualization tool designed for monitoring and analyzing swarms of drones. It provides real-time visualization of drone metrics on a map, graph analysis, and recording capabilities. It supports both live serial data streams and playback of recorded JSON flight data.

## Features

- **Map Visualization**: Real-time display of drone positions, headings, and trails on a 2D map.
- **HUD (Heads-Up Display)**: Overlay showing critical telemetry for active drones (ID, Lat/Lon, Heading, Velocity).
- **Graph Analysis**: Real-time plotting of various metrics (reserved for future implementation details based on `GraphPanel`).
- **Live Streaming**: Connect to a serial port or named pipe to receive live telemetry.
- **Recording**: Record live sessions to JSON files for later analysis.
- **Playback**: Load and replay recorded flight data with play/pause and scrub controls.
- **Multi-Drone Support**: Visualizes multiple drones simultaneously with distinct colors.

## Installation

Ensure you have Python 3 installed. The application depends on standard libraries and `tkinter` for the GUI.

Dependencies:
```bash
pip install pyserial
```
*Note: `tkinter` is usually included with Python, but on some Linux distros you might need to install `python3-tk`.*

## Usage

Run the application via the command line using `main.py`.

### Command Line Arguments

| Argument | Flag | Default | Description |
| :--- | :--- | :--- | :--- |
| **Source** | `-s`, `--source` | `none` | Data source mode: `file`, `stream`, or `none`. |
| **Path** | `-p`, `--path` | `None` | Path to JSON file (for `file` mode) or Serial Port/Pipe path (for `stream` mode). Required if source is not `none`. |
| **Num Drones** | `--num_drones` | `4` | Number of drones to simulate/expect (mostly for init). |
| **Center Lat** | `--lat` | `32.0` | Initial map center Latitude. |
| **Center Lon** | `--lon` | `34.0` | Initial map center Longitude. |
| **Width** | `--width` | `800` | Window width in pixels. |
| **Height** | `--height` | `600` | Window height in pixels. |
| **Resolution** | `--res` | `0.00001` | Map resolution (degrees per pixel). Lower value = higher zoom. |

### Examples

**1. Open in Default Mode (Manual Connect/Load):**
```bash
python main.py
```

**2. Playback a Recording:**
```bash
python main.py -s file -p ./recordings/flight_log.json
```

**3. Connect to a Live Serial Stream:**
```bash
python main.py -s stream -p /dev/ttyUSB0
```
*Note: Ensure you have execute permissions on the serial port.*

**4. Connect to a Named Pipe (Simulation):**
```bash
python main.py -s stream -p /tmp/flight_data_pipe
```

## Operation Guide

### Map View
- Shows the position of all connected drones.
- Drone icons are color-coded.
- Trails show the recent path of the drone.

### Controls
- **Play/Pause**: Controls playback of recorded data.
- **Slider**: Scrub through time in playback mode.
- **Reset**: Resets playback to the beginning.
- **Load Rec**: Open a file dialog to load a `.json` recording.
- **Connect**: Open a dialog to specify a serial port/pipe for live streaming.
- **Record**: Toggles recording of the current live stream. When stopped, prompts to save the data.

### Graph Analysis
- Switch to the "Graph Analysis" tab to view data plots.
*(Note: Graphing specifics depend on the active configuration in `ui/graph_panel.py`)*

## Data Format

Recordings are saved in JSON format. The structure is a list of trajectories, where each trajectory is a list of state objects.

```json
[
  [
    {
      "id": 1,
      "timestamp": 123456.789,
      "lat": 32.0001,
      "lon": 34.0001,
      "heading": 90.0,
      "velocity_north": 0.5,
      "velocity_east": 0.0,
      ...
    },
    ...
  ],
  ...
]
```