#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Train face recognition model for attendance system.
This script processes images from dataset/raw folder and creates encodings.pkl file.
"""

import os
import pickle
import logging
import time
import glob
import re
import face_recognition
import cv2
import pandas as pd
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/training.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def setup_directories():
    """Create necessary directories if they don't exist."""
    Path("dataset/processed").mkdir(parents=True, exist_ok=True)
    Path("models").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

def extract_info_from_filename(filename):
    """
    Extract ID and name from filename format: [ID9DIGIT]_[NAMA]_[NOMOR].jpg
    Example: 118130001_soara_01.jpg
    """
    try:
        base = os.path.basename(filename)
        pattern = r"(\d{9})_([a-zA-Z]+)_\d+\.jpg"
        match = re.match(pattern, base)
        
        if match:
            student_id = match.group(1)
            name = match.group(2)
            return student_id, name
        else:
            logger.warning(f"Filename does not match pattern: {base}")
            return None, None
    except Exception as e:
        logger.error(f"Error extracting info from {filename}: {str(e)}")
        return None, None

def process_images():
    """
    Process all images in dataset/raw folder, extract face encodings,
    and save to models/encodings.pkl
    """
    start_time = time.time()
    raw_dir = "dataset/raw"
    processed_dir = "dataset/processed"
    
    # Get all jpg files in the raw directory
    image_paths = glob.glob(os.path.join(raw_dir, "*.jpg"))
    
    if not image_paths:
        logger.error(f"No images found in {raw_dir}")
        return False
    
    logger.info(f"Found {len(image_paths)} images to process")
    
    # Initialize lists to store encodings and metadata
    known_encodings = []
    known_ids = []
    known_names = []
    
    # Process each image
    successful_encodings = 0
    processed_images = 0
    
    for i, image_path in enumerate(image_paths):
        # Extract ID and name from filename
        student_id, name = extract_info_from_filename(image_path)
        
        if not student_id or not name:
            logger.warning(f"Skipping {image_path} due to invalid filename format")
            continue
        
        # Load image
        logger.info(f"Processing image {i+1}/{len(image_paths)}: {os.path.basename(image_path)}")
        image = cv2.imread(image_path)
        
        if image is None:
            logger.warning(f"Could not load image: {image_path}")
            continue
        
        # Convert from BGR (OpenCV format) to RGB (face_recognition format)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect face locations
        face_locations = face_recognition.face_locations(rgb_image, model="hog")
        
        # Skip if no face or multiple faces detected
        if len(face_locations) != 1:
            logger.warning(f"Found {len(face_locations)} faces in {image_path}. Skipping...")
            continue
        
        # Compute face encodings
        encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        if len(encodings) > 0:
            # Add encoding and metadata to lists
            known_encodings.append(encodings[0])
            known_ids.append(student_id)
            known_names.append(name)
            successful_encodings += 1
            
            # Save processed image to processed directory
            processed_path = os.path.join(processed_dir, os.path.basename(image_path))
            cv2.imwrite(processed_path, image)
            
            logger.debug(f"Successfully encoded: {image_path}")
        else:
            logger.warning(f"Could not compute encoding for {image_path}")
        
        processed_images += 1
        
    # Save encodings to file if any were successful
    if successful_encodings > 0:
        data = {
            "encodings": known_encodings,
            "ids": known_ids,
            "names": known_names,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_faces": successful_encodings
        }
        
        # Save as pickle file
        with open("models/encodings.pkl", "wb") as f:
            pickle.dump(data, f)

        
        elapsed_time = time.time() - start_time
        
        logger.info(f"Training completed in {elapsed_time:.2f} seconds")
        logger.info(f"Processed {processed_images} images")
        logger.info(f"Created {successful_encodings} face encodings")
        logger.info(f"Saved encodings to models/encodings.pkl")
        
        return True
    else:
        logger.error("No valid encodings were created")
        return False

if __name__ == "__main__":
    logger.info("Starting face encoding training process")
    
    # Setup directories
    setup_directories()
    
    # Process images
    if process_images():
        logger.info("Training completed successfully")
    else:
        logger.error("Training failed")