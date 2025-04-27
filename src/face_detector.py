#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Face detector for attendance system.
Detects and recognizes faces using camera input and trained encodings.
"""

import os
import cv2
import pickle
import numpy as np
import logging
import face_recognition
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/detection.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class FaceDetector:
    def __init__(self, encodings_path="models/encodings.pkl", detection_method="hog"):
        """
        Initialize the face detector.
        
        Args:
            encodings_path (str): Path to the pickled encodings file
            detection_method (str): Method for face detection ('hog' or 'cnn')
        """
        self.encodings_path = encodings_path
        self.detection_method = detection_method
        self.data = self.load_encodings()
        self.frame_count = 0
        self.last_recognition_time = {}  # To track last recognition time per person
        self.recognition_cooldown = 5    # Seconds between recognitions of the same person
        
        # Detection parameters
        self.frame_skip = 2              # Process every Nth frame for performance
        self.scale_factor = 0.5          # Scale factor for input frames
        self.min_confidence = 0.5        # Minimum confidence for recognition
        
        # Visualization settings
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.box_color = (0, 255, 0)     # Green bounding box for matches
        self.unknown_color = (0, 0, 255) # Red bounding box for unknown faces
        
    def load_encodings(self):
        """Load the known face encodings from the pickle file."""
        try:
            logger.info(f"Loading encodings from {self.encodings_path}")
            with open(self.encodings_path, "rb") as f:
                data = pickle.load(f)
            logger.info(f"Loaded {len(data['encodings'])} encodings")
            return data
        except Exception as e:
            logger.error(f"Error loading encodings: {str(e)}")
            return {"encodings": [], "ids": [], "names": []}
            
    def recognize_faces(self, frame):
        """
        Detect and recognize faces in the given frame.
        
        Args:
            frame: Video frame from camera
            
        Returns:
            Tuple of (processed frame, list of identified people)
        """
        # Skip frames for better performance
        self.frame_count += 1
        if self.frame_count % self.frame_skip != 0:
            return frame, []
            
        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=self.scale_factor, fy=self.scale_factor)
        
        # Convert from BGR (OpenCV format) to RGB (face_recognition format)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Find all face locations and encodings in the current frame
        face_locations = face_recognition.face_locations(rgb_frame, model=self.detection_method)
        
        if not face_locations:
            return frame, []
            
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        # Initialize lists for identification results
        recognized_ids = []
        recognized_names = []
        
        # Draw boxes and labels for each detected face
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Adjust coordinates to original frame size
            top = int(top / self.scale_factor)
            right = int(right / self.scale_factor)
            bottom = int(bottom / self.scale_factor)
            left = int(left / self.scale_factor)
            
            # Compare face with known encodings
            matches = face_recognition.compare_faces(
                self.data["encodings"], 
                face_encoding, 
                tolerance=0.6  # Lower value = more strict matching
            )
            
            name = "Unknown"
            student_id = "Unknown"
            color = self.unknown_color
            
            # If there's a match, use the first one
            if True in matches:
                # Find all indexes where there's a match
                matched_indexes = [i for i, match in enumerate(matches) if match]
                
                # Calculate face distances to find the closest match
                face_distances = face_recognition.face_distance(
                    self.data["encodings"], face_encoding
                )
                
                # Get index of the closest match (smallest distance)
                best_match_index = np.argmin(face_distances)
                
                # If the best match is in our matched indexes, use it
                if best_match_index in matched_indexes:
                    confidence = 1 - face_distances[best_match_index]
                    
                    # Only accept if confidence is high enough
                    if confidence >= self.min_confidence:
                        student_id = self.data["ids"][best_match_index]
                        name = self.data["names"][best_match_index]
                        color = self.box_color
                        
                        # Check if we need to apply cooldown for this person
                        current_time = time.time()
                        if student_id not in self.last_recognition_time or \
                           (current_time - self.last_recognition_time[student_id]) > self.recognition_cooldown:
                            recognized_ids.append(student_id)
                            recognized_names.append(name)
                            self.last_recognition_time[student_id] = current_time
                            
                            logger.info(f"Recognized: {name} (ID: {student_id}) with confidence: {confidence:.2f}")
            
            # Draw bounding box and label
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Draw a filled rectangle for the label background
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            
            # Add text with name/id
            label = f"{name} ({student_id})" if student_id != "Unknown" else "Unknown"
            cv2.putText(frame, label, (left + 6, bottom - 6), self.font, 0.6, (255, 255, 255), 1)
            
        # Return the processed frame and the list of recognized people
        return frame, list(zip(recognized_ids, recognized_names))
        
    def start_camera(self, camera_index=0, window_name="Face Recognition", callback=None):
        """
        Start the camera feed and face recognition process.
        
        Args:
            camera_index: Index of the camera to use
            window_name: Name of the display window
            callback: Function to call when a face is recognized (for attendance)
        """
        try:
            # Initialize the camera
            logger.info(f"Starting camera feed from index {camera_index}")
            camera = cv2.VideoCapture(camera_index)
            
            # Check if camera opened successfully
            if not camera.isOpened():
                logger.error("Unable to open camera")
                return False
                
            # Set camera properties if needed
            # camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            # camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            logger.info("Camera started successfully")
            
            while True:
                # Capture frame-by-frame
                ret, frame = camera.read()
                
                if not ret:
                    logger.error("Failed to capture image from camera")
                    break
                    
                # Display date and time on frame
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, now, (10, 30), self.font, 0.8, (255, 255, 255), 2)
                
                # Process the frame for face recognition
                processed_frame, recognized_people = self.recognize_faces(frame)
                
                # If there are recognized people and a callback is provided, call it
                if recognized_people and callback:
                    for student_id, name in recognized_people:
                        callback(student_id, name)
                
                # Display the resulting frame
                cv2.imshow(window_name, processed_frame)
                
                # Exit on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("Exiting on user command")
                    break
                    
            # When everything is done, release the camera
            camera.release()
            cv2.destroyAllWindows()
            return True
            
        except Exception as e:
            logger.error(f"Error in camera operation: {str(e)}")
            return False

# Example usage when run as standalone script
if __name__ == "__main__":
    # Define a simple callback function to demonstrate functionality
    def attendance_callback(student_id, name):
        print(f"Attendance recorded for: {name} (ID: {student_id})")
    
    # Create and start the face detector
    detector = FaceDetector()
    detector.start_camera(callback=attendance_callback)