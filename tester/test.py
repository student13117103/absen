import sys
import os
print(sys.path)
try:
    import face_recognition_models
    print(f"face_recognition_models path: {os.path.dirname(face_recognition_models.__file__)}")
    print("Success!")
except Exception as e:
    print(f"Error: {e}")