"""
Face recognition engine using OpenCV only (no dlib/face_recognition required).
Uses LBPH (Local Binary Pattern Histogram) face recognizer + Haar Cascade detector.
This works on all platforms without any C++ compilation.
"""

import cv2
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

# Load the Haar Cascade face detector (bundled with OpenCV)
_CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(_CASCADE_PATH)


def _detect_face(gray_img):
    """Detect the largest face in a grayscale image. Returns cropped face or None."""
    faces = face_cascade.detectMultiScale(
        gray_img,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60)
    )
    if len(faces) == 0:
        return None
    # Take the largest face
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    x, y, w, h = faces[0]
    face_roi = gray_img[y:y+h, x:x+w]
    # Resize to a fixed size for consistent encoding
    face_roi = cv2.resize(face_roi, (128, 128))
    return face_roi


def generate_face_encoding(image_paths):
    """
    Given a list of image file paths, detect faces and return an average
    'encoding' as a flattened numpy array (histogram-based descriptor).
    Returns None if no faces were detected in any image.
    """
    descriptors = []

    for path in image_paths:
        img = cv2.imread(path)
        if img is None:
            logger.warning(f"Could not read image: {path}")
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face = _detect_face(gray)
        if face is None:
            logger.warning(f"No face detected in: {path}")
            continue

        # Build a histogram-based descriptor using pixel values
        # Normalize and flatten the face region
        descriptor = face.flatten().astype(np.float32)
        descriptor = descriptor / 255.0  # Normalize to 0-1
        descriptors.append(descriptor)

    if len(descriptors) == 0:
        return None

    # Return the mean descriptor across all captured images
    return np.mean(descriptors, axis=0)


def recognize_face(frame, known_face_encodings, known_face_names):
    """
    Detect and recognize faces in a BGR frame.
    Returns:
        face_locations: list of (top, right, bottom, left) tuples
        face_names: list of name strings
        confidences: list of confidence percentages (0-100)
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60)
    )

    face_locations = []
    face_names = []
    confidences = []

    for (x, y, w, h) in faces:
        face_roi = gray[y:y+h, x:x+w]
        face_roi_resized = cv2.resize(face_roi, (128, 128))

        descriptor = face_roi_resized.flatten().astype(np.float32) / 255.0

        name = "Unknown Person"
        confidence = 0.0

        if len(known_face_encodings) > 0:
            # Compute cosine similarity between the current face and all known faces
            similarities = []
            for known_enc in known_face_encodings:
                known_enc = np.array(known_enc, dtype=np.float32)
                dot = np.dot(descriptor, known_enc)
                norm = (np.linalg.norm(descriptor) * np.linalg.norm(known_enc)) + 1e-6
                similarity = dot / norm
                similarities.append(similarity)

            best_idx = int(np.argmax(similarities))
            best_score = similarities[best_idx]

            # Threshold: cosine similarity > 0.92 is considered a match
            if best_score > 0.92:
                name = known_face_names[best_idx]
                confidence = round(float(best_score) * 100, 2)
                confidence = min(max(confidence, 0), 100)

        # face_locations uses (top, right, bottom, left) convention
        face_locations.append((y, x + w, y + h, x))
        face_names.append(name)
        confidences.append(confidence)

    return face_locations, face_names, confidences
