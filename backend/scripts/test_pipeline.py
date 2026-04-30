"""
GeoFace Faculty Authentication System
CLI Utility: Test face recognition and liveness detection on a local video file.

Usage:
    python scripts/test_pipeline.py --video /path/to/video.mp4 --teacher-id <uuid>

This script runs the complete verification pipeline on a video file
without needing a mobile device — useful for tuning thresholds.
"""

import argparse
import base64
import os
import sys
import json
import time

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import cv2
import psycopg2


def extract_frames(video_path: str, target_fps: int = 5, max_frames: int = 25):
    """Extract frames from a video at target_fps."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌  Cannot open video: {video_path}")
        sys.exit(1)

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    step = max(1, int(video_fps / target_fps))
    frames_b64 = []
    frame_idx = 0

    while len(frames_b64) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % step == 0:
            _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            frames_b64.append(base64.b64encode(buf.tobytes()).decode('utf-8'))
        frame_idx += 1

    cap.release()
    print(f"📹  Extracted {len(frames_b64)} frames from {video_path}")
    return frames_b64


def get_teacher_encoding(teacher_id: str):
    db_url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT face_encoding FROM teachers WHERE teacher_id=%s", (teacher_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or not row[0]:
        print(f"❌  Teacher {teacher_id} not found or has no face encoding.")
        sys.exit(1)

    return json.loads(row[0]) if isinstance(row[0], str) else row[0]


def run_pipeline(frames_b64, teacher_encoding):
    """Run the full AI pipeline and print results."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    from app.services.face_service import process_frames, compare_encodings
    from app.services.liveness_service import run_liveness_checks

    print("\n🔄  Processing frames through AI pipeline…")
    start = time.time()

    images, encodings, landmarks_seq, face_count = process_frames(frames_b64)
    total = len(images)

    print(f"    Faces detected: {face_count}/{total} frames ({face_count/total*100:.0f}%)")

    if face_count / total < 0.6:
        print(f"❌  FAIL: Face detection — too few frames with faces")
        return

    matched, dist = compare_encodings(encodings, teacher_encoding)
    print(f"    Face distance:  {dist:.4f} (threshold: 1.1) → {'✅ MATCH' if matched else '❌ MISMATCH'}")

    if not matched:
        print(f"❌  FAIL: Face recognition — mismatch")
        return

    liveness_ok, liveness_reason = run_liveness_checks(landmarks_seq)
    print(f"    Liveness:       {'✅ PASSED' if liveness_ok else '❌ FAILED'} — {liveness_reason}")

    elapsed = time.time() - start
    print(f"\n{'🎉  Pipeline PASSED' if liveness_ok else '❌  Pipeline FAILED'} in {elapsed:.2f}s\n")


def main():
    parser = argparse.ArgumentParser(description="Test GeoFace AI pipeline on a local video")
    parser.add_argument('--video',      required=True, help="Path to video file (.mp4)")
    parser.add_argument('--teacher-id', required=True, help="Teacher UUID to test against")
    args = parser.parse_args()

    if not os.path.isfile(args.video):
        print(f"❌  Video file not found: {args.video}")
        sys.exit(1)

    frames = extract_frames(args.video)
    encoding = get_teacher_encoding(args.teacher_id)
    run_pipeline(frames, encoding)


if __name__ == '__main__':
    main()
