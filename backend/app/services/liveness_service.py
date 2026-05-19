"""
GeoFace Faculty Authentication System - Passive Liveness Detection Service

Implements anti-spoofing using MiniFASNetV2 via ONNX Runtime.
"""

from __future__ import annotations

import logging
import os
import statistics
from typing import List, Optional, Tuple, Dict
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Try to initialize the ONNX session
onnx_session = None
try:
    import onnxruntime as ort
    model_path = "/app/models/MiniFASNetV2.onnx"
    if os.path.exists(model_path):
        onnx_session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        logger.info("Successfully loaded MiniFASNetV2 anti-spoofing model.")
    else:
        logger.error(f"Anti-spoofing model not found at {model_path}")
except ImportError:
    logger.error("onnxruntime is not installed. Passive liveness will fail.")
except Exception as e:
    logger.error(f"Failed to load anti-spoofing model: {e}")


def get_crop(image: np.ndarray, bbox: List[float], scale: float = 2.7) -> Optional[np.ndarray]:
    """
    Crop the face based on the bounding box, scaled out to capture context 
    (crucial for spoof detection as it captures phone edges, paper edges, etc).
    """
    try:
        x1, y1, x2, y2 = bbox
        w = x2 - x1
        h = y2 - y1
        cx, cy = x1 + w / 2, y1 + h / 2

        # Scale the bounding box
        new_w = w * scale
        new_h = h * scale

        # Calculate new crop coordinates
        new_x1 = max(0, int(cx - new_w / 2))
        new_y1 = max(0, int(cy - new_h / 2))
        new_x2 = min(image.shape[1], int(cx + new_w / 2))
        new_y2 = min(image.shape[0], int(cy + new_h / 2))

        crop = image[new_y1:new_y2, new_x1:new_x2]
        if crop.size == 0:
            return None
        return crop
    except Exception as e:
        logger.warning(f"Failed to crop face for liveness: {e}")
        return None

def run_liveness_checks(
    images: List[Optional[np.ndarray]],
    bboxes: List[Optional[List[float]]],
    threshold: float = 0.85
) -> Tuple[bool, str]:
    """
    Run the passive liveness check on the provided frames using MiniFASNetV2.
    """
    if onnx_session is None:
        logger.error("ONNX Anti-spoofing model is not initialized — rejecting submission.")
        # Fail CLOSED: never let a submission through if the liveness model
        # is unavailable. This prevents spoofing attacks in a degraded state.
        return False, "Liveness check unavailable (system error). Please try again or contact support."

    valid_frames_tested = 0
    real_scores = []

    for img, bbox in zip(images, bboxes):
        if img is None or bbox is None:
            continue

        crop = get_crop(img, bbox)
        if crop is None:
            continue

        try:
            # Preprocess the image for MiniFASNet
            # Model expects 80x80 input
            resized = cv2.resize(crop, (80, 80))
            
            # Convert HWC to CHW (Channel, Height, Width)
            blob = np.transpose(resized, (2, 0, 1))
            
            # Add batch dimension (1, 3, 80, 80)
            blob = np.expand_dims(blob, axis=0).astype(np.float32)

            # Run inference
            input_name = onnx_session.get_inputs()[0].name
            out = onnx_session.run(None, {input_name: blob})
            
            # Output is shape (1, 3)
            logits = out[0][0]
            
            # Softmax to get probabilities
            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / np.sum(exp_logits)
            
            # Class 1 is 'Real'
            real_prob = probs[1]
            real_scores.append(real_prob)
            valid_frames_tested += 1

        except Exception as e:
            logger.error(f"Liveness inference failed: {e}")
            continue

    if valid_frames_tested == 0:
        return False, "Failed liveness check: Could not extract face from any frames."

    # Use MEDIAN real score — much harder to spoof than max() because a single
    # high-confidence frame can no longer override many spoof-scored frames.
    median_real_score = statistics.median(real_scores)

    logger.info(
        "Liveness Check — Frames Tested: %d, Median Real: %.4f, Max: %.4f, Min: %.4f",
        valid_frames_tested, median_real_score, max(real_scores), min(real_scores)
    )

    liveness_threshold = 0.80  # Stricter — was effectively max-based 0.85
    if median_real_score >= liveness_threshold:
        return True, "Liveness verified"
    else:
        return False, f"Failed liveness check: Spoof detected (confidence: {(1 - median_real_score)*100:.1f}%)"
