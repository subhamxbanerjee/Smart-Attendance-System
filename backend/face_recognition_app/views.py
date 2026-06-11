from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, status
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from attendance.models import Session, AttendanceRecord, SystemConfiguration
from accounts.models import Student

# Face recognition imports
import threading
import time
import os
from typing import Dict, List
import importlib
import numpy as np  # type: ignore

from .encodings import build_encodings, save_encodings, load_encodings
from attendance.utils import send_sms


def health(request):
    return JsonResponse({"status": "ok", "app": "face_recognition"})


# In-memory and on-disk encodings cache
ENCODINGS_PATH = os.path.join(settings.BASE_DIR, 'face_recognition_app', 'data', 'encodings.pkl')
KNOWN_ENCODINGS: Dict[str, List] = {}


def get_camera_source():
    """
    Resolve camera source from DB config.
    Returns evaluated source (int for webcam index '0', or string for URL) or None.
    """
    # 1. Check Database
    try:
        config = SystemConfiguration.objects.filter(key="camera_source").first()
        if config and config.value.strip():
            val = config.value.strip()
            # If value is exactly '0', convert to int for webcam
            if val == '0':
                return 0
            return val
    except Exception:
        pass
    
    # 2. Check settings.CAMERA_SOURCE (from .env)
    if settings.CAMERA_SOURCE:
        return settings.CAMERA_SOURCE
        
    # 3. No Fallback
    return None



def ensure_encodings_loaded():
    global KNOWN_ENCODINGS
    if not KNOWN_ENCODINGS:
        KNOWN_ENCODINGS = load_encodings(ENCODINGS_PATH)
        if not KNOWN_ENCODINGS:
            print(f"[ENCODINGS] No encodings found at {ENCODINGS_PATH}. Building from images...")
            KNOWN_ENCODINGS, count = build_encodings(settings.MEDIA_ROOT)
            if count > 0:
                save_encodings(ENCODINGS_PATH, KNOWN_ENCODINGS)
                print(f"[ENCODINGS] Built and saved {len(KNOWN_ENCODINGS)} encodings from {count} images")
            else:
                print("[ENCODINGS] No images found to build encodings.")
        else:
            print(f"[ENCODINGS] Loaded {len(KNOWN_ENCODINGS)} student encodings from {ENCODINGS_PATH}")
    else:
        print(f"[ENCODINGS] Already loaded {len(KNOWN_ENCODINGS)} encodings")


@api_view(["POST"]) 
@permission_classes([permissions.IsAdminUser])
def build_encodings_api(request):
    enc_map, processed = build_encodings(settings.MEDIA_ROOT)
    save_encodings(ENCODINGS_PATH, enc_map)
    # replace in-memory
    global KNOWN_ENCODINGS
    KNOWN_ENCODINGS = enc_map
    return Response({"encodings_for_usn": len(enc_map), "images_processed": processed})


# Live capture thread state
LIVE_THREAD = None
LIVE_STOP = False


def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    if a.ndim > 1:
        a = a.flatten()
    if b.ndim > 1:
        b = b.flatten()
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-8
    return float(1.0 - np.dot(a, b) / denom)


def _recognize_and_mark(session_id: int, frame_bgr, mark_db=True) -> List[str]:
    """
    Detect and recognize ALL faces in frame (optimized for large classes).
    Returns list of ALL recognized USNs in this frame.
    """
    recognized: List[str] = []
    if not KNOWN_ENCODINGS:
        print(f"[RECOGNITION ERROR] No encodings loaded! Run 'Build Encodings' first.")
        return recognized

    # Lazy-import DeepFace to avoid importing heavy native libs at module import time
    try:
        DeepFace = importlib.import_module('deepface.DeepFace')
    except Exception as e:
        print(f"[RECOGNITION ERROR] could not import DeepFace: {e}")
        return recognized

    # DeepFace detect ALL faces in frame with faster detector
    try:
        reps = DeepFace.represent(
            img_path=frame_bgr,
            enforce_detection=False,
            detector_backend='opencv',  # Faster detection for large classes
            align=False  # Skip alignment for speed
        )
    except Exception as e:
        print(f"[RECOGNITION ERROR] {e}")
        return recognized
    
    if not isinstance(reps, list) or len(reps) == 0:
        print(f"[RECOGNITION] No faces detected in frame")
        return recognized

    # Prepare known encodings as matrix for vectorized computation
    usn_index: List[str] = []
    known_vecs: List[np.ndarray] = []
    for usn, vecs in KNOWN_ENCODINGS.items():
        for v in vecs:
            known_vecs.append(np.array(v, dtype=np.float32))
            usn_index.append(usn)
    
    if not known_vecs:
        return recognized
    
    known_matrix = np.array(known_vecs)
    THRESHOLD = 0.6
    
    print(f"[RECOGNITION] Detected {len(reps)} face(s) in frame")
    
    # Process EACH detected face
    for face_idx, face_data in enumerate(reps):
        if 'embedding' not in face_data:
            continue
            
        frame_emb = np.array(face_data['embedding'], dtype=np.float32)
        
        # Vectorized distance computation (MUCH faster than loop!)
        # Cosine distance = 1 - (dot product / (norm1 * norm2))
        norms = np.linalg.norm(known_matrix, axis=1) * np.linalg.norm(frame_emb)
        distances = 1 - np.dot(known_matrix, frame_emb) / (norms + 1e-8)
        
        best_idx = np.argmin(distances)
        best_dist = distances[best_idx]
        
        # Log top 3 matches for first face only (avoid spam)
        if face_idx == 0:
            sorted_indices = np.argsort(distances)[:3]
            top_3 = [(usn_index[idx], float(distances[idx])) for idx in sorted_indices]
            print(f"[RECOGNITION DEBUG] Frame Face 1 | Best Dist: {best_dist:.4f} | Threshold: {THRESHOLD}")
            print(f"[RECOGNITION DEBUG] Top 3 Candidates: {top_3}")
        
        if best_dist <= THRESHOLD:
            best_usn = usn_index[best_idx]
            if best_usn not in recognized:  # Avoid duplicates in same frame
                recognized.append(best_usn)
                print(f"[RECOGNITION MATCH] Face {face_idx+1}: MATCHED {best_usn} (Dist: {best_dist:.4f})")
        else:
            print(f"[RECOGNITION NO MATCH] Face {face_idx+1}: Closest {usn_index[best_idx]} (Dist: {best_dist:.4f}) > {THRESHOLD}")
    
    # Mark all recognized students in database
    if mark_db and recognized:
        try:
            session = Session.objects.get(id=session_id, is_active=True)
            now = timezone.now()
            if (now - session.start_time) > timedelta(minutes=5):
                return recognized
            
            for best_usn in recognized:
                try:
                    student = Student.objects.get(usn=best_usn)
                    AttendanceRecord.objects.update_or_create(
                        student=student,
                        session=session,
                        defaults={"status": "present", "recognized_image_path": ""}
                    )
                except Student.DoesNotExist:
                    print(f"[RECOGNITION] Student {best_usn} not found in database")
        except Session.DoesNotExist:
            pass
    
    return recognized


def _finalize_attendance(session_id: int, recognized_usns: set[str]):
    """
    Mark all unrecognized students as ABSENT for this session.
    Send SMS notifications.
    """
    print(f"[ATTENDANCE] Finalizing attendance for session {session_id}")
    try:
        session_obj = Session.objects.get(id=session_id)
        # Verify we are still roughly in the session window or just finishing it
        # But we should probably mark absent regardless if the loop finished.
        
        all_students = Student.objects.all().values_list('usn', flat=True)
        count_absent = 0
        
        for usn in all_students:
            if usn in recognized_usns:
                continue
            
            try:
                st = Student.objects.get(usn=usn)
                # Use update_or_create to avoid duplicates, but only if not already present
                # If they were marked present, they are in recognized_usns, so we skip.
                # Use get_or_create for absent to avoid overwriting if somehow they were marked manually?
                # Ideally, we force absent if not present.
                
                AttendanceRecord.objects.update_or_create(
                    student=st,
                    session=session_obj,
                    defaults={"status": "absent", "recognized_image_path": ""}
                )
                count_absent += 1
                
                # Send SMS notifications to student and parent
                timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
                message = f"Your child is absent for today's class at {timestamp} in {session_obj.name}."
                try:
                    if st.student_phone:
                        send_sms(st.student_phone, message)
                    if st.parent_phone:
                        send_sms(st.parent_phone, message)
                except Exception:
                    # Fail silently if SMS fails
                    pass
            except Student.DoesNotExist:
                continue
        print(f"[ATTENDANCE] Marked {count_absent} students as absent.")
            
    except Session.DoesNotExist:
        print(f"[ATTENDANCE ERROR] Session {session_id} not found during finalization.")
    except Exception as e:
        print(f"[ATTENDANCE ERROR] Failed to finalize attendance: {e}")


def _live_loop(session_id: int):
    global LIVE_STOP
    
    # Lazy-import cv2 to avoid import-time native dependency errors
    try:
        cv2 = importlib.import_module('cv2')
    except Exception as e:
        print(f"[LIVE_LOOP] could not import cv2: {e}")
        LIVE_STOP = True
        return

    # Determine camera source
    source = get_camera_source()
    print(f"[LIVE_LOOP] Starting loop for session {session_id} with source: {source}")
    
    # Enforce CCTV: Do not convert to int (which would enable webcam index)
    if not source:
        print("[ERROR] CAMERA_SOURCE is not set. Cannot start live loop.")
        LIVE_STOP = True
        return
    
    # Add retry logic for camera connection
    max_retries = 3
    cap = None
    
    for attempt in range(max_retries):
        try:
            print(f"[LIVE_LOOP] Connection attempt {attempt + 1}/{max_retries}")
            cap = cv2.VideoCapture(source)
            
            # Set timeout for connection (5 seconds)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            
            if cap.isOpened():
                print("[LIVE_LOOP] Camera opened successfully")
                break
            else:
                print(f"[LIVE_LOOP] Could not open camera source: {source} (attempt {attempt + 1}/{max_retries})")
                if cap:
                    cap.release()
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
        except Exception as e:
            print(f"[LIVE_LOOP] Error opening camera on attempt {attempt + 1}: {e}")
            if cap:
                try:
                    cap.release()
                except:
                    pass
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    if not cap or not cap.isOpened():
        print(f"[LIVE_LOOP] ERROR: Could not open camera source after {max_retries} attempts: {source}")
        LIVE_STOP = True
        return
    # Prepare storage directory for frames
    frames_dir = os.path.join(settings.MEDIA_ROOT, 'session_frames', f'session_{session_id}')
    os.makedirs(frames_dir, exist_ok=True)
    # Warm up camera
    time.sleep(0.5)
    try:
        # Pre-compute session end time (5 minutes from start)
        try:
            session_obj = Session.objects.get(id=session_id)
            session_end = session_obj.start_time + timedelta(minutes=5)
        except Session.DoesNotExist:
            session_end = timezone.now()
        frame_counter = 0
        recog_frames = 0
        recognized_usns_overall: set[str] = set()
        usn_counts: Dict[str, int] = {}
        
        while not LIVE_STOP:
            # Auto-stop if session has ended (time window) or is no longer active
            if timezone.now() >= session_end:
                LIVE_STOP = True
                break
            s = Session.objects.filter(id=session_id).values('is_active').first()
            if not s or not s.get('is_active'):
                LIVE_STOP = True
                break
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            # Run recognition every 3rd frame to reduce CPU
            frame_counter += 1
            if frame_counter % 3 == 0:
                # Count only frames where we run recognition
                recog_frames += 1
                # Save the current frame to disk for audit/debug
                session_frame = None
                try:
                    fname = f"frame_{recog_frames:02d}_{int(time.time())}.jpg"
                    fpath = os.path.join(frames_dir, fname)
                    cv2.imwrite(fpath, frame)
                    
                    # Save frame record to database
                    from attendance.models import SessionFrame
                    session_frame = SessionFrame.objects.create(
                        session=session_obj,
                        image_path=f'session_frames/session_{session_id}/{fname}',
                        frame_number=recog_frames
                    )
                except Exception:
                    pass
                
                # Don't mark DB yet, just accumulate votes
                usns = _recognize_and_mark(session_id, frame, mark_db=False)
                
                # Link recognized students to this frame
                if session_frame and usns:
                    for u in usns:
                        try:
                            st = Student.objects.get(usn=u)
                            session_frame.recognized_students.add(st)
                        except Student.DoesNotExist:
                            pass
                
                for u in usns:
                    usn_counts[u] = usn_counts.get(u, 0) + 1
                    # If threshold reached (e.g. 3 frames), mark present
                    if usn_counts[u] >= 3 and u not in recognized_usns_overall:
                        try:
                            st = Student.objects.get(usn=u)
                            session_obj = Session.objects.get(id=session_id, is_active=True)
                            AttendanceRecord.objects.update_or_create(
                                student=st,
                                session=session_obj,
                                defaults={"status": "present", "recognized_image_path": ""}
                            )
                            recognized_usns_overall.add(u)
                        except (Student.DoesNotExist, Session.DoesNotExist):
                            pass

                # After 75 recognition frames, stop (absentees marked in finally)
                if recog_frames >= 75:
                    LIVE_STOP = True
                    break
            # small sleep to avoid 100% CPU
            time.sleep(0.02)
    finally:
        cap.release()
        
        # Only mark absent if session completed normally (frames target reached or time expired)
        # Verify session_end is defined (it should be from try block)
        completed_frames = ('recog_frames' in locals() and recog_frames >= 75)
        
        # Check if time expired (approximate check)
        time_expired = False
        try:
            if 'session_end' in locals() and timezone.now() >= session_end:
                time_expired = True
        except:
            pass
            
        if completed_frames or time_expired:
            _finalize_attendance(session_id, recognized_usns_overall)
        else:
            print(f"[LIVE_LOOP] Session stopped early (Frames: {locals().get('recog_frames',0)}, Time Expired: {time_expired}). Skipping absentee marking.")



def start_live_for_session(session_id):
    """
    Helper to start the live loop thread.
    Returns (success, message, remaining_seconds)
    """
    try:
        session = Session.objects.get(id=session_id, is_active=True)
    except Session.DoesNotExist:
        return False, "active session not found", 0
        
    # Enforce 5-minute window
    elapsed = (timezone.now() - session.start_time)
    if elapsed > timedelta(minutes=5):
        return False, "attendance window closed (5 minutes passed)", 0
    remaining_seconds = max(0, int((timedelta(minutes=5) - elapsed).total_seconds()))

    ensure_encodings_loaded()

    if not get_camera_source():
        return False, "CAMERA_SOURCE not configured (check Config/Admin)", 0

    global LIVE_THREAD, LIVE_STOP
    if LIVE_THREAD and LIVE_THREAD.is_alive():
        return False, "live already running", remaining_seconds

    LIVE_STOP = False
    LIVE_THREAD = threading.Thread(target=_live_loop, args=(int(session_id),), daemon=True)
    LIVE_THREAD.start()
    
    return True, "live started", remaining_seconds


@api_view(["POST"]) 
@permission_classes([permissions.IsAdminUser])
def start(request):
    """Start live camera recognition loop for a given session_id."""
    session_id = request.data.get('session_id')
    if not session_id:
        return Response({"detail": "session_id required"}, status=status.HTTP_400_BAD_REQUEST)
    
    success, msg, rem = start_live_for_session(session_id)
    if success:
        return Response({"detail": msg, "session_id": int(session_id), "remaining_window_seconds": rem})
    else:
        return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)



@api_view(["POST"]) 
@permission_classes([permissions.IsAdminUser])
def stop(request):
    """Stop live camera recognition loop."""
    global LIVE_THREAD, LIVE_STOP
    if not LIVE_THREAD or not LIVE_THREAD.is_alive():
        return Response({"detail": "live not running"})
    LIVE_STOP = True
    LIVE_THREAD.join(timeout=3)
    LIVE_THREAD = None
    return Response({"detail": "live stopped"})


@api_view(["POST"]) 
@permission_classes([permissions.IsAuthenticated])
def capture(request):
    """
    Single-shot recognition from an uploaded image to mark present.
    Body: { session_id }, Files: photo
    """
    session_id = request.data.get('session_id')
    file = request.FILES.get('photo')
    if not session_id or not file:
        return Response({"detail": "session_id and photo required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        session = Session.objects.get(id=session_id, is_active=True)
    except Session.DoesNotExist:
        return Response({"detail": "active session not found"}, status=status.HTTP_404_NOT_FOUND)

    ensure_encodings_loaded()
    # Decode file into numpy array for face_recognition
    data = file.read()
    import numpy as np  # local import to avoid global dependency if not used
    np_arr = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None:
        return Response({"detail": "invalid image"}, status=status.HTTP_400_BAD_REQUEST)

    recognized_usns = _recognize_and_mark(int(session_id), frame)
    if not recognized_usns:
        return Response({"detail": "no match"}, status=status.HTTP_200_OK)
    return Response({"detail": "marked present", "usns": recognized_usns})

# Create your views here.

@api_view(["GET"])
@permission_classes([permissions.IsAdminUser])
def test_camera(request):
    """
    Test the configured camera source and return a captured frame URL.
    """
    source = get_camera_source()
    if not source:
        return Response({"detail": "CAMERA_SOURCE not configured"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        cap = cv2.VideoCapture(source)
        
        # Set timeout for connection (5 seconds)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        
        if not cap.isOpened():
             return Response({"detail": f"Could not open camera source: {source}. Please verify the camera is powered on and the URL is correct."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Wait a moment for camera to stabilize
        time.sleep(0.5)
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return Response({"detail": "Failed to read frame from camera. Camera may be busy or stream may be unavailable."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Save frame to media root
        filename = "test_camera.jpg"
        filepath = os.path.join(settings.MEDIA_ROOT, filename)
        cv2.imwrite(filepath, frame)
        
        image_url = settings.MEDIA_URL + filename
        return Response({
            "detail": "Camera test successful", 
            "source": source, 
            "image_url": request.build_absolute_uri(image_url)
        })
        
    except Exception as e:
        return Response({"detail": f"Error testing camera: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@permission_classes([permissions.IsAdminUser])
def admin_test_camera_page(request):
    """
    Render the admin page for testing the camera.
    """
    return render(request, 'admin/test_camera.html')


def gen_frames():
    source = get_camera_source()
    print(f"[VIDEO_FEED] Starting feed from source: {source}")
    if not source:
        print("[VIDEO_FEED] No source configured")
        return
        
    # Retry logic with exponential backoff
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"[VIDEO_FEED] Connection attempt {attempt + 1}/{max_retries}")
            
            # Add a small delay to allow other threads to release camera if needed
            if attempt > 0:
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
            
            cap = cv2.VideoCapture(source)
            
            # Set timeout for connection (5 seconds)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            
            if not cap.isOpened():
                print(f"[VIDEO_FEED] Could not open camera source: {source} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    continue
                else:
                    print("[VIDEO_FEED] Max retries reached. Giving up.")
                    return

            print("[VIDEO_FEED] Camera opened successfully")
            frame_count = 0
            consecutive_failures = 0
            max_consecutive_failures = 10
            
            while True:
                success, frame = cap.read()
                if not success:
                    consecutive_failures += 1
                    print(f"[VIDEO_FEED] Failed to read frame ({consecutive_failures}/{max_consecutive_failures})")
                    
                    if consecutive_failures >= max_consecutive_failures:
                        print("[VIDEO_FEED] Too many consecutive failures - ending stream")
                        break
                    
                    time.sleep(0.1)
                    continue
                else:
                    consecutive_failures = 0  # Reset on successful read
                    frame_count += 1
                    if frame_count % 100 == 0:
                        print(f"[VIDEO_FEED] Streamed {frame_count} frames...")
                        
                    ret, buffer = cv2.imencode('.jpg', frame)
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                time.sleep(0.04) # Limit to ~25fps
                
            cap.release()
            break  # Exit retry loop if we successfully streamed
            
        except Exception as e:
            print(f"[VIDEO_FEED] Error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(f"[VIDEO_FEED] Retrying in {retry_delay * (2 ** attempt)} seconds...")
            else:
                print("[VIDEO_FEED] Max retries reached. Giving up.")
                return
        finally:
            try:
                if 'cap' in locals() and cap.isOpened():
                    cap.release()
                    print("[VIDEO_FEED] Camera released")
            except:
                pass


@api_view(["GET"])
@permission_classes([permissions.IsAdminUser])
def video_feed(request):
    """
    Stream live video from the camera.
    """
    return StreamingHttpResponse(gen_frames(), content_type='multipart/x-mixed-replace; boundary=frame')


