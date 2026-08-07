"""
Detector Process - Performs motion detection using the pyimagesearch algorithm.
Based on: https://pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/
"""

import cv2
import imutils
import multiprocessing as mp

from utils import SENTINEL


def run_detector(input_conn: mp.connection.Connection,
                 output_conn: mp.connection.Connection) -> None:
    """
    Detector process - receives frames from streamer via a pipe, detects motion,
    sends (frame, time_ms, contours) to presenter via a pipe.
    """
    print("[Detector] Starting")

    prev_frame = None

    try:
        while True:
            # Wait for a frame from the streamer (poll with timeout so we can
            # still respond to KeyboardInterrupt periodically).
            if not input_conn.poll(timeout=1.0):
                continue

            msg = input_conn.recv()

            # Check for sentinel (end of stream)
            if msg is SENTINEL:
                print("[Detector] Received sentinel, forwarding and exiting")
                output_conn.send(SENTINEL)
                break

            frame, time_ms = msg

            # Convert to grayscale
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Initialize previous frame on first iteration
            if prev_frame is None:
                prev_frame = gray_frame
                output_conn.send((frame, time_ms, []))
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
            output_conn.send((frame, time_ms, cnts))

    except KeyboardInterrupt:
        print("[Detector] Interrupted")
    except Exception as e:
        print(f"[Detector] Error: {e}")
    finally:
        print("[Detector] Exiting")
