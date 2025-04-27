import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")

try:
    import cv2
    print(f"OpenCV successfully imported, version: {cv2.__version__}")
except ImportError as e:
    print(f"Error importing cv2: {e}")
    
try:
    import face_recognition
    print("face_recognition successfully imported")
except ImportError as e:
    print(f"Error importing face_recognition: {e}")
