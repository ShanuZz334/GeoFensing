"""
GeoFace Faculty Authentication System
CLI Utility: Register a Teacher from an Image File

Usage:
    python scripts/register_teacher.py \
        --name "Dr. Jane Smith" \
        --email "jsmith@college.edu" \
        --password "SecurePass@123" \
        --image /path/to/photo.jpg

This script:
  1. Loads the image
  2. Detects the face and extracts a 128-d encoding
  3. Hashes the password with bcrypt
  4. Inserts the teacher record into PostgreSQL

Requirements:
    pip install face-recognition dlib opencv-python-headless flask-bcrypt psycopg2-binary python-dotenv
"""

import argparse
import os
import sys
import json

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import face_recognition
import cv2
import numpy as np
from flask_bcrypt import generate_password_hash
import psycopg2
import uuid
from datetime import datetime


def extract_encoding(image_path: str):
    """Extract face encoding from an image file."""
    image = face_recognition.load_image_file(image_path)
    locations = face_recognition.face_locations(image, model="hog")

    if not locations:
        print(f"❌  No face detected in: {image_path}")
        sys.exit(1)

    if len(locations) > 1:
        print(f"⚠️   Multiple faces detected ({len(locations)}). Using the first/largest.")

    encodings = face_recognition.face_encodings(image, known_face_locations=[locations[0]])
    if not encodings:
        print("❌  Could not extract face encoding.")
        sys.exit(1)

    return encodings[0].tolist()


def register_teacher(name: str, email: str, password: str, image_path: str):
    """Register a teacher in the database."""
    print(f"\n👤  Registering teacher: {name} ({email})")
    print(f"📸  Processing image: {image_path}")

    # Extract encoding
    encoding = extract_encoding(image_path)
    print(f"✅  Face encoding extracted (128 floats). First values: {encoding[:3]}")

    # Hash password
    password_hash = generate_password_hash(password).decode('utf-8')
    print(f"🔒  Password hashed.")

    # Connect to DB
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌  DATABASE_URL not set in .env")
        sys.exit(1)

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        teacher_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO teachers (teacher_id, full_name, email, password_hash, face_encoding, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, TRUE, %s, %s)
            ON CONFLICT (email) DO UPDATE
              SET full_name = EXCLUDED.full_name,
                  password_hash = EXCLUDED.password_hash,
                  face_encoding = EXCLUDED.face_encoding,
                  updated_at = EXCLUDED.updated_at
            RETURNING teacher_id, full_name, email
            """,
            (
                teacher_id,
                name,
                email.strip().lower(),
                password_hash,
                json.dumps(encoding),
                datetime.utcnow(),
                datetime.utcnow(),
            )
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        print(f"\n🎉  Teacher registered successfully!")
        print(f"    Teacher ID : {row[0]}")
        print(f"    Name       : {row[1]}")
        print(f"    Email      : {row[2]}")
        print(f"\nThe teacher can now log in on the mobile app.\n")

    except psycopg2.errors.UniqueViolation:
        print(f"⚠️   A teacher with email '{email}' already exists. Record updated.")
    except Exception as e:
        print(f"❌  Database error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Register a faculty member in GeoFace Authentication System"
    )
    parser.add_argument('--name',     required=True,  help="Teacher full name")
    parser.add_argument('--email',    required=True,  help="Teacher email address")
    parser.add_argument('--password', required=True,  help="Login password (min 8 chars)")
    parser.add_argument('--image',    required=True,  help="Path to clear front-face photo")

    args = parser.parse_args()

    if not os.path.isfile(args.image):
        print(f"❌  Image file not found: {args.image}")
        sys.exit(1)

    if len(args.password) < 8:
        print("❌  Password must be at least 8 characters.")
        sys.exit(1)

    register_teacher(args.name, args.email, args.password, args.image)


if __name__ == '__main__':
    main()
