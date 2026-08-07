# Motion Detection System - 3-Process Architecture Plan

## Overview
A Python multiprocessing application with three processes:
1. **Streamer** - Reads video frames and sends to Detector
2. **Detector** - Performs motion detection using pyimagesearch algorithm
3. **Presenter** - Receives frames + detections, draws/blurs contours, displays

## Architecture

```
┌─────────────┐     Pipe        ┌─────────────┐     Pipe       ┌─────────────┐
│  Streamer   │ ────────────▶ │  Detector   │ ────────────▶ │  Presenter  │
│  (Process)  │  (frame,       │  (Process)  │  (frame,       │  (Process)  │
│             │   time_ms)      │             │   contours)     │             │
└─────────────┘                └─────────────┘                └─────────────┘
```

Each connection uses an **unidirectional `mp.Pipe(duplex=False)`**:
- `streamer_to_detector` pipe: Streamer holds the write end, Detector holds the read end.
- `detector_to_presenter` pipe: Detector holds the write end, Presenter holds the read end.

## Implementation Details

### 1. Streamer Process (`streamer.py`)
- Opens video file using `cv2.VideoCapture`
- If video cannot be opened: prints error and returns (sentinel sent via `finally`)
- Reads frames in a loop
- Sends `(frame, time_ms)` tuples to detector via the write end of the `streamer_to_detector` pipe
- On end of video or error: sends `None` (SENTINEL) sentinel via `finally` block
- Cleanup in `finally`: sends sentinel, releases `cv2.VideoCapture`

### 2. Detector Process (`detector.py`)
- Implements the pyimagesearch motion detection algorithm from `basic_vmd.py`
- Maintains `prev_frame` for frame differencing
- Computes: absdiff → threshold → dilate → findContours
- Sends `(frame, time_ms, contours)` to presenter via the write end of the `detector_to_presenter` pipe
- On receiving sentinel: forwards sentinel to presenter, then breaks

### 3. Presenter Process (`presenter.py`)
- Receives `(frame, time_ms, contours)` from detector
- Either blurs (pixelates) contour bounding boxes or draws contours via `cv2.drawContours`
- Displays using `cv2.imshow("Motion Detection", frame)` with `cv2.waitKey(33)` (~30 FPS)
- On receiving sentinel: exits the loop
- Cleanup in `finally`: calls `cv2.destroyAllWindows()`

### 4. Main Orchestrator (`main.py`)
- Creates two unidirectional pipes: `streamer_to_detector` (Streamer write → Detector read) and `detector_to_presenter` (Detector write → Presenter read)
- Spawns 3 processes (Streamer, Detector, Presenter)
- Handles graceful shutdown on SIGINT (Ctrl+C) and SIGTERM via signal handler
  - Signal handler calls `shutdown()` which terminates alive processes and joins with timeout
- Waits for all processes to complete via `p.join()`
- Normal completion flow: Streamer → sentinel → Detector → sentinel → Presenter → exit

### 5. Shared Utilities (`utils.py`)
- `SENTINEL = None` sentinel value to signal end of stream

## File Structure
```
axon/
├── main.py              # Entry point, process orchestration
├── streamer.py          # Streamer process
├── detector.py          # Detector process (pyimagesearch algorithm)
├── presenter.py         # Presenter process
├── utils.py             # Shared constants (SENTINEL)
├── basic_vmd.py         # Original reference implementation
├── pyproject.toml       # Dependencies
└── People - 6387.mp4    # Test video
```

## Key Design Decisions
- **multiprocessing.Pipe** (one-way, `duplex=False`) for IPC — each pipe connects exactly
  one producer to one consumer in the linear pipeline, giving natural backpressure (the
  sender blocks if the receiver is slow instead of buffering frames in memory)
- **cv2.imshow** for real-time display (presenter only — other processes don't open windows)
- **SIGINT/SIGTERM signal handler** for graceful shutdown (terminate + join with 2s timeout)
- **Sentinel-based** pipeline shutdown: streamer sends sentinel → detector forwards it → presenter exits
- **Contours** (not bounding boxes) as detection output — presenter either draws them or pixelates their bounding boxes
- **cv2.destroyAllWindows()** only called in presenter (the only process that opens a window)
- **Simplified**: no extra configuration parameters; algorithm values hardcoded per pyimagesearch reference

## Dependencies
- opencv-python>=5.0.0.93
- imutils>=0.5.4
- Python >=3.14

## Algorithm Reference
Based on: https://pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/

The algorithm:
1. Convert frame to grayscale
2. Compute absolute difference with previous frame
3. Threshold the difference (25)
4. Dilate to fill holes (2 iterations)
5. Find contours
6. Filter by area (500)
