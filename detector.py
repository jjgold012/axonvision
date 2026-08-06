"""
Detector Process - Performs motion detection using the pyimagesearch algorithm.
Based on: https://pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/
"""

import cv2
import imutils
import multiprocessing as mp

from utils import SENTINEL


def run_detector(input_queue: mp.Queue, output_queue: mp.Queue) -> None:
    """
    Detector process - receives frames from streamer, detects motion,
    sends (frame, time_ms, contours) to presenter.
    """
    print("[Detector] Starting")

    prev_frame = None

    try:
        while True:
            # Get frame from streamer
            try:
                msg = input_queue.get(timeout=1.0)
            except mp.queues.Empty:
                continue

            # Check for sentinel (end of stream)
            if msg is SENTINEL:
                print("[Detector] Received sentinel, forwarding and exiting")
                # Block until sentinel is delivered - presenter will drain the queue
                output_queue.put(SENTINEL)
                break

            frame, time_ms = msg

            # Convert to grayscale
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Initialize previous frame on first iteration
            if prev_frame is None:
                prev_frame = gray_frame
                try:
                    output_queue.put((frame, time_ms, []), timeout=1.0)
                except mp.queues.Full:
                    pass
                continue

            # Motion detection algorithm (pyimagesearch)
            diff = cv2.absdiff(gray_frame, prev_frame)
            thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)

            # Update previous frame
            prev_frame = gray_frame

            # Send frame with detected contours to presenter
            try:
                output_queue.put((frame, time_ms, cnts), timeout=1.0)
            except mp.queues.Full:
                continue

    except KeyboardInterrupt:
        print("[Detector] Interrupted")
    except Exception as e:
        print(f"[Detector] Error: {e}")
    finally:
        print("[Detector] Exiting")
