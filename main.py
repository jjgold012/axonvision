#!/usr/bin/env python
"""
Main Orchestrator - Coordinates the Streamer, Detector, and Presenter processes.
"""

import argparse
import multiprocessing as mp
import os
import signal
import sys

from streamer import run_streamer
from detector import run_detector
from presenter import run_presenter


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Motion Detection System - 3 Process Architecture")
    parser.add_argument("video", nargs="?", default="People - 6387.mp4",
                        help="Path to video file (default: People - 6387.mp4)")
    parser.add_argument("--blur", action="store_true",
                        help="Blur detected motion regions instead of drawing contours")
    args = parser.parse_args()
    video_path = args.video
    blur = args.blur

    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    print(f"Motion Detection System - Processing: {video_path}")

    # Create queues for inter-process communication
    streamer_to_detector = mp.Queue()
    detector_to_presenter = mp.Queue()

    # Create processes
    streamer_proc = mp.Process(
        target=run_streamer,
        args=(video_path, streamer_to_detector),
        name="Streamer"
    )

    detector_proc = mp.Process(
        target=run_detector,
        args=(streamer_to_detector, detector_to_presenter),
        name="Detector"
    )

    presenter_proc = mp.Process(
        target=run_presenter,
        args=(detector_to_presenter, blur),
        name="Presenter"
    )

    processes = [streamer_proc, detector_proc, presenter_proc]

    # Handle graceful shutdown on SIGINT (Ctrl+C) and SIGTERM
    def shutdown():
        """Terminate all processes and wait for them to exit."""
        print("\n[Main] Shutting down...")
        for p in processes:
            if p.is_alive():
                p.terminate()
        for p in processes:
            p.join(timeout=2)

    def signal_handler(_signum, _frame):
        shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start all processes
    print("[Main] Starting processes...")
    for p in processes:
        p.start()
        print(f"[Main] Started {p.name} (PID: {p.pid})")

    # Wait for processes to complete.
    # Normal flow: Streamer finishes video -> sends sentinel -> exits.
    # Detector consumes all queued frames -> forwards sentinel -> exits.
    # Presenter consumes all queued frames -> exits.
    print("[Main] All processes running. Waiting for completion...")
    for p in processes:
        p.join()
        print(f"[Main] {p.name} exited (code: {p.exitcode})")

    print("[Main] All processes completed. Goodbye!")


if __name__ == "__main__":
    main()
