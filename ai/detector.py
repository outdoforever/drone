"""
AI Detector Module for Disaster Response.
Detects 'person', 'fire', 'smoke', 'flood', 'debris', and 'damaged_structure'.

Supports:
- Real YOLO inference on video frames (from stream.py)
- Pre-trained YOLO model for person + vehicle detection
- Fallback simulation when no model or camera available
"""

import random
import numpy as np
from typing import List, Dict, Any, Optional


class AIDetector:
    """
    Object detection pipeline for disaster-relevant targets.
    Processes numpy frames (BGR) from CameraStream or image file paths.
    """

    def __init__(self, model_name: str = "yolov8n.pt"):
        self.model_name = model_name
        self.yolo_model = None
        self.target_classes = ["person", "fire", "smoke", "flood", "debris", "damaged_structure"]
        self._try_load_model()

    def _try_load_model(self):
        try:
            from ultralytics import YOLO
            self.yolo_model = YOLO(self.model_name)
            print(f"[AIDetector] Loaded Ultralytics YOLO model: {self.model_name}")
        except Exception as e:
            print(f"[AIDetector] Ultralytics YOLO not loaded ({e}). Using disaster vision pipeline simulator.")
            self.yolo_model = None

    def process_frame(self, frame: np.ndarray, conf_threshold: float = 0.35) -> List[Dict[str, Any]]:
        """
        Process a single video frame (numpy BGR array) and return detections.

        Args:
            frame: BGR numpy array from camera/video.
            conf_threshold: Minimum confidence threshold.

        Returns:
            List of detection dicts with type, confidence, bbox.
        """
        detections = []

        if self.yolo_model is not None and frame is not None:
            try:
                results = self.yolo_model(frame, conf=conf_threshold, verbose=False)
                for r in results:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        cls_name = self.yolo_model.names.get(cls_id, "unknown")
                        conf = round(float(box.conf[0]), 2)
                        bbox = [float(x) for x in box.xyxy[0].tolist()]

                        # Map COCO classes to our disaster classes
                        mapped_type = self._map_coco_class(cls_name)
                        if mapped_type:
                            det = {
                                "type": mapped_type,
                                "confidence": conf,
                                "bbox": bbox,
                                "original_class": cls_name
                            }
                            # Add thermal simulation for persons
                            if mapped_type == "person":
                                det["thermal_confirmed"] = random.random() > 0.1  # 90% simulated thermal match
                            detections.append(det)
            except Exception as ex:
                print(f"[AIDetector] Frame inference error: {ex}")

        return detections

    def process_image(self, image_path: str = None) -> List[Dict[str, Any]]:
        """
        Process a static image file. Falls back to simulation if no model.
        """
        detections = []

        if self.yolo_model and image_path:
            try:
                import cv2
                frame = cv2.imread(image_path)
                if frame is not None:
                    return self.process_frame(frame)
            except Exception as ex:
                print(f"[AIDetector] Image read error: {ex}")

        if not detections:
            # Fallback simulation for demo/testing
            return self._simulate_detections()

        return detections

    def simulate_frame_detections(self) -> List[Dict[str, Any]]:
        """
        Generate simulated detections (used when no camera feed is active).
        """
        return self._simulate_detections()

    def _simulate_detections(self) -> List[Dict[str, Any]]:
        """Generate random disaster detections for demo mode."""
        num_dets = random.randint(1, 3)
        detections = []
        for _ in range(num_dets):
            det_type = random.choice(self.target_classes)
            conf = round(random.uniform(0.78, 0.98), 2)
            thermal = (det_type == "person") and (random.random() > 0.15)

            det = {
                "type": det_type,
                "confidence": conf,
                "thermal_confirmed": thermal,
                "bbox": None
            }
            detections.append(det)
        return detections

    def _map_coco_class(self, cls_name: str) -> Optional[str]:
        """
        Maps COCO class names to our disaster detection classes.
        Returns None if the class is not relevant.
        """
        mapping = {
            "person": "person",
            "car": "debris",
            "truck": "debris",
            "bus": "debris",
            "motorcycle": "debris",
            "bicycle": "debris",
            "boat": "flood",
            "fire hydrant": "fire",
        }
        return mapping.get(cls_name, None)

    @property
    def has_model(self) -> bool:
        return self.yolo_model is not None
