"""
Camera Feed Receiver for Autonomous Disaster-Response Drone.
Supports pre-recorded video files, laptop webcam, and RTSP/RTMP streams.

Usage:
    stream = CameraStream(source="path/to/video.mp4")
    stream = CameraStream(source="webcam")
    stream = CameraStream(source="rtsp://drone-ip:8554/live")
    
    for frame, metadata in stream:
        # frame is a numpy array (BGR)
        # metadata contains timestamp, frame_number, source_type
        ...
"""

import cv2
import time
import os
import urllib.request
import numpy as np
from typing import Generator, Tuple, Dict, Any, Optional


class CameraStream:
    """
    Unified camera feed interface.
    Reads frames from video files, webcam, RTSP streams, and HTTP MJPEG mobile IP Webcam feeds.
    """

    def __init__(self, source: str = "webcam", loop_video: bool = True):
        self.source = source
        self.loop_video = loop_video
        self.cap = None
        self.http_response = None
        self.byte_buffer = b""
        self.frame_count = 0
        self.fps = 30.0
        self.width = 0
        self.height = 0
        self.source_type = "unknown"
        self._is_open = False

    def open(self) -> bool:
        """Opens the video source. Returns True if successful."""
        src = self.source.strip()

        if src.lower() in ("webcam", "0"):
            self.source_type = "webcam"
            self.cap = cv2.VideoCapture(0)
        elif src.startswith("http://") or src.startswith("https://"):
            # Native robust HTTP MJPEG stream handler (immune to FFmpeg stream index bugs)
            self.source_type = "http_mjpeg"
            try:
                # If user typed just host like http://192.168.1.5:8080 without /video, auto append /video
                stream_url = src
                if not (stream_url.endswith("/video") or stream_url.endswith("/shot.jpg") or stream_url.endswith(".mjpeg") or stream_url.endswith("/stream")):
                    if stream_url.endswith("/"):
                        stream_url += "video"
                    else:
                        stream_url += "/video"

                req = urllib.request.Request(stream_url, headers={'User-Agent': 'RescueVisionAI/1.0'})
                self.http_response = urllib.request.urlopen(req, timeout=6.0)
                self.byte_buffer = b""
                self._is_open = True
                self.fps = 30.0
                print(f"[CameraStream] Connected natively to HTTP stream: {stream_url}")
                return True
            except Exception as e:
                print(f"[CameraStream] Native HTTP stream open failed: {e}. Trying cv2 fallback...")
                self.cap = cv2.VideoCapture(src)
        elif src.startswith("rtsp://") or src.startswith("rtmp://"):
            self.source_type = "rtsp_stream"
            self.cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        elif os.path.isfile(src):
            self.source_type = "video_file"
            self.cap = cv2.VideoCapture(src)
        else:
            print(f"[CameraStream] ERROR: Cannot resolve source '{src}'")
            return False

        if not self.cap or not self.cap.isOpened():
            print(f"[CameraStream] ERROR: Failed to open source '{src}'")
            return False

        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._is_open = True
        self.frame_count = 0

        print(f"[CameraStream] Opened '{self.source_type}' source: {src}")
        print(f"[CameraStream] Resolution: {self.width}x{self.height} @ {self.fps:.1f} FPS")
        return True

    def read_frame(self) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """
        Reads a single frame.
        Returns (frame_bgr, metadata) or None if no frame available.
        """
        if not self._is_open:
            return None

        # ── 1. HTTP MJPEG Stream Reader (Zero-Latency Live Frame Dropping) ──
        if self.source_type == "http_mjpeg" and self.http_response:
            try:
                # Read chunks until at least one complete JPEG is in the buffer
                for _ in range(15):
                    chunk = self.http_response.read(65536)
                    if not chunk:
                        return None
                    self.byte_buffer += chunk

                    # Prevent TCP buffer accumulation / lag buildup
                    if len(self.byte_buffer) > 262144:
                        self.byte_buffer = self.byte_buffer[-131072:]

                    # Find the LAST complete JPEG frame in the buffer (guarantees 0ms latency)
                    b = self.byte_buffer.rfind(b'\xff\xd9')
                    if b != -1:
                        a = self.byte_buffer.rfind(b'\xff\xd8', 0, b)
                        if a != -1 and b > a:
                            jpg = self.byte_buffer[a:b+2]
                            # Discard all previous bytes up to this newest frame
                            self.byte_buffer = self.byte_buffer[b+2:]

                            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if frame is not None:
                                h, w = frame.shape[:2]
                                if w > 1280:
                                    scale = 1280.0 / w
                                    frame = cv2.resize(frame, (1280, int(h * scale)), interpolation=cv2.INTER_LINEAR)

                                self.frame_count += 1
                                self.width = frame.shape[1]
                                self.height = frame.shape[0]
                                metadata = {
                                    "frame_number": self.frame_count,
                                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                    "timestamp_unix": time.time(),
                                    "source_type": self.source_type,
                                    "resolution": f"{self.width}x{self.height}",
                                    "fps": self.fps,
                                    "raw_jpg": jpg
                                }
                                return frame, metadata
                return None
            except Exception as e:
                print(f"[CameraStream] HTTP stream read error: {e}")
                return None


        # ── 2. Standard VideoCapture Reader (Webcam / RTSP / Video File) ──
        if self.cap is None:
            return None

        ret, frame = self.cap.read()

        if not ret:
            if self.source_type == "video_file" and self.loop_video:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    return None
            else:
                return None

        self.frame_count += 1
        metadata = {
            "frame_number": self.frame_count,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "timestamp_unix": time.time(),
            "source_type": self.source_type,
            "resolution": f"{self.width}x{self.height}",
            "fps": self.fps
        }

        return frame, metadata

    def frames(self, skip_frames: int = 0) -> Generator[Tuple[Any, Dict[str, Any]], None, None]:
        if not self._is_open:
            if not self.open():
                return

        while True:
            result = self.read_frame()
            if result is None:
                break
            frame, metadata = result
            if skip_frames > 0 and (self.frame_count % (skip_frames + 1)) != 0:
                continue
            yield frame, metadata

    def close(self):
        """Release camera resources."""
        if self.http_response:
            try:
                self.http_response.close()
            except Exception:
                pass
            self.http_response = None
            self.byte_buffer = b""

        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        self._is_open = False
        print("[CameraStream] Source closed.")


    @property
    def is_open(self) -> bool:
        return self._is_open

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def __iter__(self):
        return self.frames()
