# Motion Detection System - 3-Process Architecture Plan

## Overview
A Python multiprocessing application with three processes:
1. **Streamer** - Reads video frames and sends to Detector
2. **Detector** - Performs motion detection using pyimagesearch algorithm
3. **Presenter** - Receives frames + detections, draws bounding boxes, displays

## Architecture

```
┌─────────────┐     Queue      ┌─────────────┐     Queue      ┌─────────────┐
│  Streamer   │ ─────────────▶ │  Detector   │ ─────────────▶ │  Presenter  │
│  (Process)  │  (frame,       │  (Process)  │  (frame,       │  (Process)  │
│             │   frame_num)   │             │   boxes)       │             │
└─────────────┘                └─────────────┘                └─────────────┘
```

## Implementation Details

### 1. Streamer Process (`streamer.py`)
- Opens video file using `cv2.VideoCapture`
- Reads frames in a loop
- Sends `(frame, frame_number)` tuples to detector queue
- Sends `None` sentinel to signal completion

### 2. Detector Process (`detector.py`)
- Implements the pyimagesearch motion detection algorithm from `basic_vmd.py`
- Maintains `prev_frame` for frame differencing
- Computes: absdiff → threshold → dilate → findContours
- Filters contours by minimum area (500)
- Converts contours to bounding boxes `(x, y, w, h)`
- Sends `(frame, frame_number, boxes_list)` to presenter queue

### 3. Presenter Process (`presenter.py`)
- Receives `(frame, frame_number, boxes)` from detector
- Draws bounding boxes on frame using `cv2.rectangle`
- Displays using `cv2.imshow("Motion Detection", frame)`
- Handles 'q' key press to signal shutdown

### 4. Main Orchestrator (`main.py`)
- Creates queues: `streamer_to_detector`, `detector_to_presenter`, `control_queue`
- Spawns 3 processes
- Handles graceful shutdown on 'q' or video end
- Joins all processes

### 5. Shared Utilities (`utils.py`)
- `SENTINEL` sentinel value to signal end of stream

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
- **multiprocessing.Queue** for IPC (simple, process-safe)
- **cv2.imshow** for real-time display
- **'q' key** for manual quit, auto-quit at video end
- **Bounding boxes (x,y,w,h) list** as detection output
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
6. Filter by area (500) and convert to bounding boxes