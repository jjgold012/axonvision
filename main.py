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

    # Create pipes for inter-process communication.
    # mp.Pipe(duplex=False) returns (conn1, conn2) where conn1 is
    # read-only and conn2 is write-only — perfect for our unidirectional
    # pipeline: Streamer -> Detector -> Presenter.
    # Each pipe gives us natural backpressure: if the reader is slow the
    # writer blocks instead of buffering frames in memory.
    streamer_to_detector_r, streamer_to_detector_w = mp.Pipe(duplex=False)
    detector_to_presenter_r, detector_to_presenter_w = mp.Pipe(duplex=False)

    # Create processes
    # Streamer writes frames to the detector pipe
    streamer_proc = mp.Process(
        target=run_streamer,
        args=(video_path, streamer_to_detector_w),
        name="Streamer"
    )

    # Detector reads from the streamer pipe, writes results to the presenter pipe
    detector_proc = mp.Process(
        target=run_detector,
        args=(streamer_to_detector_r, detector_to_presenter_w),
        name="Detector"
    )

    # Presenter reads from the detector pipe
    presenter_proc = mp.Process(
        target=run_presenter,
        args=(detector_to_presenter_r, blur),
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
    # Detector consumes all piped frames -> forwards sentinel -> exits.
    # Presenter consumes all piped frames -> exits.
    print("[Main] All processes running. Waiting for completion...")
    for p in processes:
        p.join()
        print(f"[Main] {p.name} exited (code: {p.exitcode})")

    print("[Main] All processes completed. Goodbye!")


if __name__ == "__main__":
    main()
