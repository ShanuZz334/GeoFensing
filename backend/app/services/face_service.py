"""
GeoFace Faculty Authentication System - Frame Processing Service
(Powered by face_recognition)
"""

from __future__ import annotations

import base64
import logging
from typing import List, Optional, Tuple, Dict

import cv2
import numpy as np
import face_recognition

logger = logging.getLogger(__name__)

def decode_frame(b64_string: str) -> Optional[np.ndarray]:
    """Decode base64 JPEG string into OpenCV BGR image."""
    try:
        if "," in b64_string:
            b64_string = b64_string.split(",", 1)[1]
        image_bytes = base64.b64decode(b64_string)
        nparr = np.frombuffer(image_bytes, dtype=np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as exc:
        logger.warning("decode_frame failed: %s", exc)
        return None

def process_frames(
    b64_frames: List[str],
    max_frames: int = 25,
) -> Tuple[
    List[Optional[np.ndarray]],
    List[Optional[List[float]]],
    List[Optional[Dict[str, List[Tuple[int, int]]]]],
    int,
]:
    """
    Process frames using face_recognition for recognition and landmarks.
    """
    frames = b64_frames[:max_frames]
    
    images: List[Optional[np.ndarray]] = []
    encodings_seq: List[Optional[List[float]]] = []
    landmarks_seq: List[Optional[Dict[str, List[Tuple[int, int]]]]] = []
    face_count = 0

    for b64 in frames:
        image = decode_frame(b64)
        if image is None:
            images.append(None)
            encodings_seq.append(None)
            landmarks_seq.append(None)
            continue

        images.append(image)

        try:
            # face_recognition expects RGB images for full resolution
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Find face locations on full-size image
            face_locations = face_recognition.face_locations(rgb_image)
            
            if not face_locations:
                encodings_seq.append(None)
                landmarks_seq.append(None)
                continue

            actual_locations = face_locations
            
            # We only care about the first face for authentication
            face_count += 1
            
            # Get encodings (using the scaled-up locations)
            encodings = face_recognition.face_encodings(rgb_image, known_face_locations=actual_locations)
            if encodings:
                encodings_seq.append(encodings[0].tolist())
            else:
                encodings_seq.append(None)

            # Get landmarks (using the scaled-up locations)
            landmarks = face_recognition.face_landmarks(rgb_image, actual_locations)
            if landmarks:
                landmarks_seq.append(landmarks[0])
            else:
                landmarks_seq.append(None)

        except Exception as exc:
            logger.error("face_recognition processing failed: %s", exc)
            encodings_seq.append(None)
            landmarks_seq.append(None)

    return images, encodings_seq, landmarks_seq, face_count

def compare_encodings(
    encodings: List[Optional[List[float]]],
    expected_teacher_encoding: List[float],
    threshold: float = 0.6,
) -> Tuple[bool, float]:
    """
    Check if the expected teacher encoding matches any of the frame encodings.
    Uses Euclidean distance (lower is better, typically <= 0.6 means match).
    """
    best_distance = float('inf')
    matched = False

    if not expected_teacher_encoding or len(expected_teacher_encoding) != 128:
        return False, 1.0

    expected_np = np.array(expected_teacher_encoding)

    for enc in encodings:
        if enc is None:
            continue
        
        enc_np = np.array(enc)
        # Calculate Euclidean distance
        distance = float(np.linalg.norm(expected_np - enc_np))
        
        if distance < best_distance:
            best_distance = distance
            
        if distance <= threshold:
            matched = True

    return matched, round(best_distance, 4) if best_distance != float('inf') else 1.0

def add_face_to_collection(
    b64_image: str,
) -> Optional[List[float]]:
    """
    Enroll a new face. Returns the 128d encoding.
    """
    image = decode_frame(b64_image)
    if image is None:
        return None
    
    try:
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image)
        if not face_locations:
            return None
            
        encodings = face_recognition.face_encodings(rgb_image, known_face_locations=face_locations)
        if encodings:
            return encodings[0].tolist()
        return None
    except Exception as exc:
        logger.error("Face enrollment failed: %s", exc)
        return None
