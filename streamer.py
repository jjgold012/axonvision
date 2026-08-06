"""
Streamer Process - Reads video frames and sends them to the Detector process.
"""

import cv2
import multiprocessing as mp

from utils import SENTINEL


def run_streamer(video_path: str, output_queue: mp.Queue) -> None:
    """
    Streamer process - reads video frames and sends (frame, time_ms) to detector.
    """
    print(f"[Streamer] Starting with video: {video_path}")

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"[Streamer] Error: Could not open video {video_path}")
        output_queue.put(SENTINEL)
        return

    try:
        while True:
            # Read next frame
            ret, frame = cap.read()

            if not ret:
                print("[Streamer] End of video reached")
                break

            # Get current timestamp in milliseconds
            time_ms = cap.get(cv2.CAP_PROP_POS_MSEC)

            # Send frame to detector
            output_queue.put((frame, time_ms))


    except KeyboardInterrupt:
        print("[Streamer] Interrupted")
    except Exception as e:
        print(f"[Streamer] Error: {e}")
    finally:
        # Send sentinel to signal end of stream
        print("[Streamer] Sending sentinel and exiting")
        output_queue.put(SENTINEL)
        cap.release()
        cv2.destroyAllWindows()