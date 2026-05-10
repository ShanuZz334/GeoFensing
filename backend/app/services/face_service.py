"""
GeoFace Faculty Authentication System - Frame Processing Service
(Powered by InsightFace)
"""

from __future__ import annotations

import base64
import logging
from typing import List, Optional, Tuple, Dict

import cv2
import numpy as np
from insightface.app import FaceAnalysis

logger = logging.getLogger(__name__)

# Initialize the face analysis model globally
try:
    face_app = FaceAnalysis(name='buffalo_l', root='/app/models', providers=['CPUExecutionProvider'])
    face_app.prepare(ctx_id=0, det_size=(640, 640))
except Exception as e:
    logger.error(f"Failed to initialize InsightFace model: {e}")
    face_app = None

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
    Process frames using InsightFace for recognition and landmarks.
    """
    frames = b64_frames[:max_frames]
    
    images: List[Optional[np.ndarray]] = []
    encodings_seq: List[Optional[List[float]]] = []
    landmarks_seq: List[Optional[Dict[str, List[Tuple[int, int]]]]] = []
    face_count = 0

    if face_app is None:
        logger.error("FaceAnalysis app is not initialized.")
        return [], [], [], 0

    for b64 in frames:
        image = decode_frame(b64)
        if image is None:
            images.append(None)
            encodings_seq.append(None)
            landmarks_seq.append(None)
            continue

        images.append(image)

        try:
            # InsightFace expects BGR images (which is cv2 default)
            faces = face_app.get(image)
            
            if not faces:
                encodings_seq.append(None)
                landmarks_seq.append(None)
                continue

            # We only care about the first face for authentication
            face_count += 1
            face = faces[0]
            
            # Get 512-d encodings
            if face.embedding is not None:
                encodings_seq.append(face.embedding.tolist())
            else:
                encodings_seq.append(None)

            # Get 5 landmarks (kps is 5x2 array)
            if face.kps is not None:
                kps = face.kps.astype(int)
                landmarks = {
                    'left_eye': [(kps[0][0], kps[0][1])],
                    'right_eye': [(kps[1][0], kps[1][1])],
                    'nose_bridge': [(kps[2][0], kps[2][1])],  # Named nose_bridge for backward compat with liveness script
                    'left_mouth': [(kps[3][0], kps[3][1])],
                    'right_mouth': [(kps[4][0], kps[4][1])]
                }
                landmarks_seq.append(landmarks)
            else:
                landmarks_seq.append(None)

        except Exception as exc:
            logger.error("InsightFace processing failed: %s", exc)
            encodings_seq.append(None)
            landmarks_seq.append(None)

    return images, encodings_seq, landmarks_seq, face_count

def compare_encodings(
    encodings: List[Optional[List[float]]],
    expected_teacher_encoding: List[float],
    threshold: float = 1.2,
) -> Tuple[bool, float]:
    """
    Check if the expected teacher encoding matches any of the frame encodings.
    Uses Euclidean distance on normalized embeddings.
    """
    best_distance = float('inf')
    matched = False

    if not expected_teacher_encoding or len(expected_teacher_encoding) != 512:
        return False, 2.0

    expected_np = np.array(expected_teacher_encoding)
    norm = np.linalg.norm(expected_np)
    if norm > 0:
        expected_np = expected_np / norm

    for enc in encodings:
        if enc is None:
            continue
        
        enc_np = np.array(enc)
        norm_enc = np.linalg.norm(enc_np)
        if norm_enc > 0:
            enc_np = enc_np / norm_enc
        
        # Calculate Euclidean distance
        distance = float(np.linalg.norm(expected_np - enc_np))
        
        if distance < best_distance:
            best_distance = distance
            
        if distance <= threshold:
            matched = True

    return matched, round(best_distance, 4) if best_distance != float('inf') else 2.0

def add_face_to_collection(
    b64_image: str,
) -> Optional[List[float]]:
    """
    Enroll a new face. Returns the 512d encoding.
    """
    image = decode_frame(b64_image)
    if image is None:
        return None
    
    if face_app is None:
        logger.error("FaceAnalysis app is not initialized.")
        return None
        
    try:
        faces = face_app.get(image)
        if not faces:
            return None
            
        return faces[0].embedding.tolist()
    except Exception as exc:
        logger.error("Face enrollment failed: %s", exc)
        return None
