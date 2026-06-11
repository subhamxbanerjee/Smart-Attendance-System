import os
import glob
import pickle
from typing import Dict, List, Tuple

import importlib


def build_encodings(media_root: str) -> Tuple[Dict[str, List], int]:
    """
    Walk media/student_photos/<USN>/ and build face encodings.
    Returns (encodings_map, num_images_processed)
    encodings_map: { usn: [embedding_vectors...] }
    """
    base_dir = os.path.join(media_root, 'student_photos')
    encodings_map: Dict[str, List] = {}
    processed = 0

    if not os.path.isdir(base_dir):
        return encodings_map, 0

    for usn in os.listdir(base_dir):
        usn_dir = os.path.join(base_dir, usn)
        if not os.path.isdir(usn_dir):
            continue
        encs: List = []
        # common image extensions
        for pattern in ("*.jpg", "*.jpeg", "*.png"):
            for img_path in glob.glob(os.path.join(usn_dir, pattern)):
                try:
                    # Lazy import DeepFace to avoid module import errors at startup
                    try:
                        DeepFace = importlib.import_module('deepface.DeepFace')
                    except Exception:
                        # If DeepFace isn't available, skip building encodings
                        continue
                    # DeepFace will detect and compute embedding; enforce_detection=False to avoid hard failures
                    reps = DeepFace.represent(img_path=img_path, enforce_detection=False)
                    # represent returns list of dicts; take first embedding if exists
                    if isinstance(reps, list) and len(reps) > 0 and 'embedding' in reps[0]:
                        encs.append(reps[0]['embedding'])
                        processed += 1
                except Exception:
                    # ignore problematic images
                    continue
        if encs:
            encodings_map[usn] = encs
    return encodings_map, processed


def save_encodings(pickle_path: str, encodings_map: Dict[str, List]) -> None:
    os.makedirs(os.path.dirname(pickle_path), exist_ok=True)
    with open(pickle_path, 'wb') as f:
        pickle.dump(encodings_map, f)


def load_encodings(pickle_path: str) -> Dict[str, List]:
    if not os.path.isfile(pickle_path):
        return {}
    with open(pickle_path, 'rb') as f:
        return pickle.load(f)
