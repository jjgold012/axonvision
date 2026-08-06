"""
Presenter Process - Receives frames with detections, blurs or draws contours, and displays.
"""

import cv2
import multiprocessing as mp

from utils import SENTINEL


def format_time(time_ms):
    """Format milliseconds as MM:SS."""
    total_seconds = int(time_ms) // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def blur_contours(frame, contours, block_size=10):
    """Pixelate the bounding box regions of the given contours (efficient ROI-based)."""
    if not contours:
        return frame

    result = frame.copy()
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        # Extract ROI, pixelate it by resizing down and back up, and put it back
        roi = result[y:y+h, x:x+w]
        small = cv2.resize(roi, (max(1, w // block_size), max(1, h // block_size)), interpolation=cv2.INTER_LINEAR)
        result[y:y+h, x:x+w] = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    return result


def run_presenter(input_queue: mp.Queue, blur: bool = False) -> None:
    """
    Presenter process - receives (frame, time_ms, contours) from detector,
    pixelates (blurs) or draws contours and current time on frames, and displays them.
    """
    print(f"[Presenter] Starting display window: 'Motion Detection' (blur={blur})")

    try:
        while True:
            # Get frame with detections from detector
            try:
                msg = input_queue.get(timeout=1.0)
            except mp.queues.Empty:
                continue

            # Check for sentinel (end of stream)
            if msg is SENTINEL:
                print("[Presenter] Received sentinel, exiting")
                break

            frame, time_ms, contours = msg

            # Blur or draw contours on frame
            if blur:
                frame = blur_contours(frame, contours)
            else:
                cv2.drawContours(frame, contours, -1, (0, 255, 0), 2)

            # Display current time overlay
            cv2.putText(frame, format_time(time_ms),
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Display frame
            cv2.imshow("Motion Detection", frame)
            cv2.waitKey(35)  # ~25 FPS


    except KeyboardInterrupt:
        print("[Presenter] Interrupted")
    except Exception as e:
        print(f"[Presenter] Error: {e}")
    finally:
        print("[Presenter] Cleaning up and exiting")
        cv2.destroyAllWindows()