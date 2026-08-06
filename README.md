# Axon Vision — Motion Detection System

A Python multiprocessing application that performs real-time motion detection on video files using the classic pyimagesearch frame-differencing algorithm.

## Architecture

A 3-process pipeline connected by `multiprocessing.Queue`:

```
┌──────────┐   (frame, time_ms)    ┌──────────┐   (frame, time_ms, contours)    ┌──────────┐
│ Streamer │ ────────────────────▶ │ Detector │ ───────────────────────────────── │ Presenter │
│  Process │                       │  Process │                                 │  Process │
│ Reads    │                       │ Motion   │                                 │ Display  │
│ frames   │                       │ detect   │                                 │ output   │
└──────────┘                       └──────────┘                                 └──────────┘
```

Shutdown is **sentinel-based**: the Streamer sends `None` at end-of-stream → the Detector forwards it → the Presenter exits. A signal handler in the main process handles graceful shutdown on Ctrl+C / SIGTERM.

## Prerequisites

- Python >= 3.14
- OpenCV (`opencv-python`)
- `imutils`

## Installation

Using [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv sync
```

Or with pip:

```bash
pip install opencv-python imutils
```

## Usage

```bash
# Run on the default test video
python main.py

# Specify a custom video file
python main.py path/to/video.mp4

# Blur motion regions instead of drawing contours
python main.py path/to/video.mp4 --blur
```

### Keyboard Controls

During playback in the Presenter window, press **Ctrl+C** to stop the pipeline.

## File Structure

```
axon/
├── main.py         # Entry point — process orchestration & signal handling
├── streamer.py     # Streamer process — reads video frames
├── detector.py     # Detector process — pyimagesearch motion detection
├── presenter.py    # Presenter process — renders & displays output
├── utils.py        # Shared constants (SENTINEL)
├── basic_vmd.py    # Original single-file reference implementation
├── PLAN.md         # Architecture and design documentation
├── pyproject.toml  # Project metadata & dependencies
└── People - 6387.mp4  # Default test video
```
