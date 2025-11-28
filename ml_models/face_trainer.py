
import os
import pickle
import cv2
import numpy as np
import face_recognition
from typing import List, Tuple, Dict
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaceTrainer:
    
    def __init__(self, student_faces_dir: str = None, model_dir: str = None):
        # Get project root directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # Set default directories
        if student_faces_dir is None:
            self.student_faces_dir = os.path.join(
                project_root, 'app', 'uploads', 'student_faces'
            )
        else:
            self.student_faces_dir = student_faces_dir
            
        if model_dir is None:
            self.model_dir = os.path.join(
                project_root, 'app', 'uploads', 'trained_models'
            )
        else:
            self.model_dir = model_dir
            
        # Create model directory if not exists
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Supported image extensions
        self.supported_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        
        logger.info(f"Face Trainer initialized")
        logger.info(f"Student faces directory: {self.student_faces_dir}")
        logger.info(f"Model directory: {self.model_dir}")
    
    def load_images_from_folder(self, person_folder: str) -> List[np.ndarray]:
        images = []
        
        if not os.path.exists(person_folder):
            logger.warning(f"Folder not found: {person_folder}")
            return images
        
        for filename in os.listdir(person_folder):
            if filename.lower().endswith(self.supported_extensions):
                img_path = os.path.join(person_folder, filename)
                try:
                    # Load image using OpenCV
                    img = cv2.imread(img_path)
                    if img is not None:
                        # Convert BGR to RGB (face_recognition uses RGB)
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        images.append(img_rgb)
                        logger.debug(f"Loaded image: {filename}")
                    else:
                        logger.warning(f"Could not read image: {img_path}")
                except Exception as e:
                    logger.error(f"Error loading image {img_path}: {str(e)}")
        
        return images
    
    def extract_face_encodings(self, image: np.ndarray, 
                              model: str = "hog") -> List[np.ndarray]:
        try:
            # Resize image if too large for faster processing
            max_dimension = 1024
            height, width = image.shape[:2]
            
            if max(height, width) > max_dimension:
                scale = max_dimension / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))
                logger.debug(f"Resized image to: {new_width}x{new_height}")
            
            # Detect face locations
            face_locations = face_recognition.face_locations(image, model=model)
            
            if not face_locations:
                logger.warning("No face detected in image")
                return []
            
            # Extract face encodings
            face_encodings = face_recognition.face_encodings(
                image, 
                face_locations,
                num_jitters=10  # Higher value = more accurate but slower
            )
            
            logger.debug(f"Found {len(face_encodings)} face(s) in image")
            return face_encodings
            
        except Exception as e:
            logger.error(f"Error extracting face encodings: {str(e)}")
            return []
    
    def train_person(self, person_name: str, 
                    model: str = "hog",
                    min_images: int = 3) -> Tuple[bool, str, List[np.ndarray]]:
        person_folder = os.path.join(self.student_faces_dir, person_name)
        
        if not os.path.exists(person_folder):
            return False, f"Folder not found for {person_name}", []
        
        # Load images
        images = self.load_images_from_folder(person_folder)
        
        if len(images) < min_images:
            return False, f"Not enough images for {person_name}. Found {len(images)}, need at least {min_images}", []
        
        logger.info(f"Training {person_name} with {len(images)} images...")
        
        # Extract encodings from all images
        all_encodings = []
        for idx, img in enumerate(images):
            encodings = self.extract_face_encodings(img, model=model)
            
            if encodings:
                # Take the first (or best) face encoding from each image
                all_encodings.append(encodings[0])
                logger.debug(f"Processed image {idx + 1}/{len(images)}")
            else:
                logger.warning(f"No face found in image {idx + 1} for {person_name}")
        
        if not all_encodings:
            return False, f"No valid face encodings extracted for {person_name}", []
        
        success_rate = len(all_encodings) / len(images) * 100
        message = f"Successfully trained {person_name}: {len(all_encodings)}/{len(images)} images ({success_rate:.1f}%)"
        
        return True, message, all_encodings
    
    def train_all(self, model: str = "hog", 
                  min_images: int = 3,
                  save_model: bool = True) -> Dict:
        if not os.path.exists(self.student_faces_dir):
            logger.error(f"Student faces directory not found: {self.student_faces_dir}")
            return {
                'success': False,
                'message': 'Student faces directory not found',
                'trained_persons': [],
                'failed_persons': []
            }
        
        logger.info("=" * 50)
        logger.info("Starting face recognition training...")
        logger.info(f"Detection model: {model}")
        logger.info(f"Minimum images per person: {min_images}")
        logger.info("=" * 50)
        
        # Get all person folders
        person_folders = [
            f for f in os.listdir(self.student_faces_dir)
            if os.path.isdir(os.path.join(self.student_faces_dir, f))
        ]
        
        if not person_folders:
            logger.warning("No person folders found")
            return {
                'success': False,
                'message': 'No person folders found',
                'trained_persons': [],
                'failed_persons': []
            }
        
        logger.info(f"Found {len(person_folders)} person folders")
        
        # Train each person
        known_encodings = []
        known_names = []
        trained_persons = []
        failed_persons = []
        
        for idx, person_name in enumerate(person_folders):
            logger.info(f"\n[{idx + 1}/{len(person_folders)}] Processing: {person_name}")
            
            success, message, encodings = self.train_person(
                person_name, 
                model=model, 
                min_images=min_images
            )
            
            if success:
                # Add all encodings for this person
                for encoding in encodings:
                    known_encodings.append(encoding)
                    known_names.append(person_name)
                
                trained_persons.append({
                    'name': person_name,
                    'encodings_count': len(encodings),
                    'message': message
                })
                logger.info(f"✓ {message}")
            else:
                failed_persons.append({
                    'name': person_name,
                    'message': message
                })
                logger.warning(f"✗ {message}")
        
        # Save model if requested
        model_path = None
        if save_model and known_encodings:
            model_path = self.save_model(known_encodings, known_names)
        
        # Prepare results
        results = {
            'success': len(trained_persons) > 0,
            'total_persons': len(person_folders),
            'trained_count': len(trained_persons),
            'failed_count': len(failed_persons),
            'total_encodings': len(known_encodings),
            'trained_persons': trained_persons,
            'failed_persons': failed_persons,
            'model_path': model_path,
            'message': f"Training completed: {len(trained_persons)}/{len(person_folders)} persons trained successfully"
        }
        
        logger.info("\n" + "=" * 50)
        logger.info("Training Summary:")
        logger.info(f"Total persons: {results['total_persons']}")
        logger.info(f"Successfully trained: {results['trained_count']}")
        logger.info(f"Failed: {results['failed_count']}")
        logger.info(f"Total face encodings: {results['total_encodings']}")
        if model_path:
            logger.info(f"Model saved to: {model_path}")
        logger.info("=" * 50)
        
        return results
    
    def save_model(self, encodings: List[np.ndarray], 
                   names: List[str],
                   model_name: str = "face_encodings.pkl") -> str:
        model_path = os.path.join(self.model_dir, model_name)
        
        try:
            data = {
                'encodings': encodings,
                'names': names
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"Model saved successfully to: {model_path}")
            return model_path
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            return None
    
    def load_model(self, model_name: str = "face_encodings.pkl") -> Tuple[List, List]:
        model_path = os.path.join(self.model_dir, model_name)
        
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            return [], []
        
        try:
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
            
            encodings = data.get('encodings', [])
            names = data.get('names', [])
            
            logger.info(f"Model loaded successfully: {len(encodings)} encodings")
            return encodings, names
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return [], []


def main():
    trainer = FaceTrainer()
    
    # Train all persons
    results = trainer.train_all(
        model="hog",  # Use "cnn" for better accuracy with GPU
        min_images=2,
        save_model=True
    )
    
    if results['success']:
        print("\n✓ Training completed successfully!")
        print(f"Trained {results['trained_count']} persons")
        print(f"Total face encodings: {results['total_encodings']}")
    else:
        print("\n✗ Training failed or no persons trained")


if __name__ == "__main__":
    main()
