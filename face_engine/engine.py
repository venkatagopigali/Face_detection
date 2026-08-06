"""
High-accuracy face recognition engine using OpenCV.
Uses Haar Cascade face detection with histogram equalization,
L2-normalized feature descriptors, and cosine similarity matching.
"""

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Load Haar Cascade face detector
_CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(_CASCADE_PATH)


def _extract_feature_descriptor(gray_img):
    """
    Apply histogram equalization and resize face region to 128x128.
    Return L2-normalized feature descriptor vector.
    """
    # Apply histogram equalization to eliminate lighting variations
    equalized = cv2.equalizeHist(gray_img)
    resized = cv2.resize(equalized, (128, 128))

    # Convert to float and L2-normalize vector
    vector = resized.flatten().astype(np.float32)
    norm = np.linalg.norm(vector) + 1e-6
    return vector / norm


def _detect_face(gray_img):
    """Detect the largest face in a grayscale image. Returns cropped face ROI or None."""
    faces = face_cascade.detectMultiScale(
        gray_img,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(50, 50)
    )
    if len(faces) == 0:
        return None

    # Take the largest face
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    x, y, w, h = faces[0]
    return gray_img[y:y+h, x:x+w]


def generate_face_encoding(image_paths):
    """
    Given a list of 50 captured image paths, extract feature descriptors
    and return the L2-normalized mean face encoding.
    """
    descriptors = []

    for path in image_paths:
        img = cv2.imread(path)
        if img is None:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_roi = _detect_face(gray)
        if face_roi is None:
            # Fallback: if cascade missed in tightly cropped frame, use full frame
            face_roi = gray

        descriptor = _extract_feature_descriptor(face_roi)
        descriptors.append(descriptor)

    if len(descriptors) == 0:
        return None

    # Compute mean descriptor across all captured images
    mean_descriptor = np.mean(descriptors, axis=0)
    norm = np.linalg.norm(mean_descriptor) + 1e-6
    return mean_descriptor / norm


def recognize_face(frame, known_face_encodings, known_face_names):
    """
    Detect and recognize faces in a live frame.
    Returns face_locations, face_names, confidences.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(50, 50)
    )

    face_locations = []
    face_names = []
    confidences = []

    for (x, y, w, h) in faces:
        face_roi = gray[y:y+h, x:x+w]
        descriptor = _extract_feature_descriptor(face_roi)

        name = "Unknown Person"
        confidence = 0.0

        if len(known_face_encodings) > 0:
            similarities = []
            for known_enc in known_face_encodings:
                known_enc = np.array(known_enc, dtype=np.float32)
                # Cosine similarity between L2-normalized vectors = dot product
                sim = float(np.dot(descriptor, known_enc))
                similarities.append(sim)

            best_idx = int(np.argmax(similarities))
            best_score = similarities[best_idx]

            # Cosine similarity threshold >= 0.82 for high accuracy match
            if best_score >= 0.82:
                name = known_face_names[best_idx]
                confidence = round(float(best_score) * 100, 2)
                confidence = min(max(confidence, 0), 100)

        face_locations.append((y, x + w, y + h, x))
        face_names.append(name)
        confidences.append(confidence)

    return face_locations, face_names, confidences
