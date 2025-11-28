
import os
import pickle
import cv2
import numpy as np
import face_recognition
from typing import List, Tuple, Dict, Optional
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaceDetector:
    
    def __init__(self, model_dir: str = None, confidence_threshold: float = 0.6):
        # Get project root directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # Set default model directory
        if model_dir is None:
            self.model_dir = os.path.join(
                project_root, 'app', 'uploads', 'trained_models'
            )
        else:
            self.model_dir = model_dir
        
        self.confidence_threshold = confidence_threshold
        self.known_encodings = []
        self.known_names = []
        self.model_loaded = False
        
        logger.info(f"Face Detector initialized")
        logger.info(f"Model directory: {self.model_dir}")
        logger.info(f"Confidence threshold: {self.confidence_threshold}")
    
    def load_model(self, model_name: str = "face_encodings.pkl") -> bool:
        model_path = os.path.join(self.model_dir, model_name)
        
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            return False
        
        try:
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
            
            self.known_encodings = data.get('encodings', [])
            self.known_names = data.get('names', [])
            
            if not self.known_encodings or not self.known_names:
                logger.error("Model file is empty or invalid")
                return False
            
            self.model_loaded = True
            logger.info(f"Model loaded successfully")
            logger.info(f"Loaded {len(self.known_encodings)} face encodings")
            logger.info(f"Known persons: {len(set(self.known_names))}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def detect_faces(self, image: np.ndarray, 
                    model: str = "hog") -> Tuple[List, List]:
        if not self.model_loaded:
            logger.error("Model not loaded. Call load_model() first.")
            return [], []
        
        try:
            # Resize image if too large for faster processing
            max_dimension = 1024
            height, width = image.shape[:2]
            scale = 1.0
            
            if max(height, width) > max_dimension:
                scale = max_dimension / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))
                logger.debug(f"Resized image to: {new_width}x{new_height}")
            
            # Detect face locations
            face_locations = face_recognition.face_locations(image, model=model)
            
            if not face_locations:
                logger.debug("No faces detected in image")
                return [], []
            
            # Extract face encodings
            face_encodings = face_recognition.face_encodings(
                image, 
                face_locations,
                num_jitters=1  # Lower for real-time, higher for accuracy
            )
            
            # Scale back face locations if image was resized
            if scale != 1.0:
                face_locations = [
                    (
                        int(top / scale),
                        int(right / scale),
                        int(bottom / scale),
                        int(left / scale)
                    )
                    for (top, right, bottom, left) in face_locations
                ]
            
            logger.debug(f"Detected {len(face_locations)} face(s)")
            return face_locations, face_encodings
            
        except Exception as e:
            logger.error(f"Error detecting faces: {str(e)}")
            return [], []
    
    def recognize_face(self, face_encoding: np.ndarray) -> Tuple[Optional[str], float]:
        if not self.model_loaded:
            logger.error("Model not loaded. Call load_model() first.")
            return None, 0.0
        
        if not self.known_encodings:
            logger.warning("No known encodings available")
            return None, 0.0
        
        # Calculate face distances
        face_distances = face_recognition.face_distance(
            self.known_encodings, 
            face_encoding
        )
        
        # Find the best match
        best_match_index = np.argmin(face_distances)
        best_distance = face_distances[best_match_index]
        
        # Convert distance to confidence (0 to 1)
        # Distance typically ranges from 0 (perfect match) to 1 (no match)
        confidence = 1.0 - best_distance
        
        # Check if confidence meets threshold
        if confidence >= self.confidence_threshold:
            name = self.known_names[best_match_index]
            logger.debug(f"Recognized: {name} (confidence: {confidence:.2f})")
            return name, confidence
        else:
            logger.debug(f"No match found (best confidence: {confidence:.2f})")
            return None, confidence
    
    def recognize_faces_in_image(self, image: np.ndarray,
                                model: str = "hog") -> List[Dict]:
        face_locations, face_encodings = self.detect_faces(image, model=model)
        
        results = []
        for location, encoding in zip(face_locations, face_encodings):
            name, confidence = self.recognize_face(encoding)
            
            results.append({
                'location': location,
                'name': name if name else "Unknown",
                'confidence': confidence
            })
        
        return results
    
    def draw_face_boxes(self, image: np.ndarray, 
                       faces: List[Dict],
                       draw_confidence: bool = True) -> np.ndarray:
        image_copy = image.copy()
        
        for face in faces:
            top, right, bottom, left = face['location']
            name = face['name']
            confidence = face['confidence']
            
            # Choose color based on recognition
            if name != "Unknown":
                color = (0, 255, 0)  # Green for recognized
            else:
                color = (0, 0, 255)  # Red for unknown
            
            # Draw rectangle around face
            cv2.rectangle(image_copy, (left, top), (right, bottom), color, 2)
            
            # Prepare label
            if draw_confidence:
                label = f"{name} ({confidence:.2f})"
            else:
                label = name
            
            # Draw label background
            label_height = 25
            cv2.rectangle(
                image_copy,
                (left, bottom),
                (right, bottom + label_height),
                color,
                cv2.FILLED
            )
            
            # Draw label text
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(
                image_copy,
                label,
                (left + 6, bottom + 18),
                font,
                0.5,
                (255, 255, 255),
                1
            )
        
        return image_copy
    
    def process_image_file(self, image_path: str,
                          model: str = "hog",
                          save_result: bool = False,
                          output_dir: str = None) -> Dict:
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return {'success': False, 'message': 'Image file not found'}
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not read image: {image_path}")
                return {'success': False, 'message': 'Could not read image'}
            
            # Convert to RGB for face_recognition
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Recognize faces
            faces = self.recognize_faces_in_image(image_rgb, model=model)
            
            # Draw boxes on BGR image
            image_with_boxes = self.draw_face_boxes(image, faces)
            
            # Save result if requested
            output_path = None
            if save_result:
                if output_dir is None:
                    output_dir = os.path.dirname(image_path)
                
                os.makedirs(output_dir, exist_ok=True)
                
                filename = os.path.basename(image_path)
                name, ext = os.path.splitext(filename)
                output_filename = f"{name}_detected{ext}"
                output_path = os.path.join(output_dir, output_filename)
                
                cv2.imwrite(output_path, image_with_boxes)
                logger.info(f"Saved result to: {output_path}")
            
            return {
                'success': True,
                'faces_detected': len(faces),
                'faces': faces,
                'output_path': output_path,
                'image_with_boxes': image_with_boxes
            }
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def start_video_recognition(self, camera_index: int = 0,
                               model: str = "hog",
                               frame_skip: int = 2) -> None:
        if not self.model_loaded:
            logger.error("Model not loaded. Call load_model() first.")
            return
        
        logger.info("Starting video recognition...")
        logger.info("Press 'q' to quit, 's' to save snapshot")
        
        # Open video capture
        video_capture = cv2.VideoCapture(camera_index)
        
        if not video_capture.isOpened():
            logger.error("Could not open camera")
            return
        
        frame_count = 0
        
        try:
            while True:
                ret, frame = video_capture.read()
                
                if not ret:
                    logger.error("Failed to grab frame")
                    break
                
                # Process every Nth frame
                if frame_count % frame_skip == 0:
                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Recognize faces
                    faces = self.recognize_faces_in_image(rgb_frame, model=model)
                    
                    # Draw boxes on frame
                    frame = self.draw_face_boxes(frame, faces)
                
                # Display frame
                cv2.imshow('Face Recognition', frame)
                
                frame_count += 1
                
                # Handle key press
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    logger.info("Quitting...")
                    break
                elif key == ord('s'):
                    # Save snapshot
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    snapshot_path = f"snapshot_{timestamp}.jpg"
                    cv2.imwrite(snapshot_path, frame)
                    logger.info(f"Snapshot saved: {snapshot_path}")
        
        finally:
            video_capture.release()
            cv2.destroyAllWindows()
            logger.info("Video recognition stopped")
    
    def get_known_persons(self) -> List[str]:
        if not self.model_loaded:
            return []
        
        return sorted(list(set(self.known_names)))
    
    def get_statistics(self) -> Dict:
        return {
            'model_loaded': self.model_loaded,
            'total_encodings': len(self.known_encodings),
            'unique_persons': len(set(self.known_names)) if self.known_names else 0,
            'confidence_threshold': self.confidence_threshold,
            'known_persons': self.get_known_persons()
        }


def main():
    detector = FaceDetector(confidence_threshold=0.6)
    
    # Load model
    if not detector.load_model():
        print("Failed to load model. Please train the model first.")
        return
    
    # Print statistics
    stats = detector.get_statistics()
    print("\n" + "=" * 50)
    print("Face Detector Statistics:")
    print(f"Total encodings: {stats['total_encodings']}")
    print(f"Unique persons: {stats['unique_persons']}")
    print(f"Confidence threshold: {stats['confidence_threshold']}")
    print("=" * 50)
    
    # Start video recognition
    print("\nStarting video recognition...")
    print("Press 'q' to quit, 's' to save snapshot")
    detector.start_video_recognition(camera_index=0, model="hog", frame_skip=2)


if __name__ == "__main__":
    main()
