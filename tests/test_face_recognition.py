
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
from ml_models import FaceDetector


class TestFaceRecognitionApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition - Upload & Detect")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # Initialize detector
        self.detector = FaceDetector(confidence_threshold=0.6)
        self.model_loaded = False
        
        # Current image data
        self.current_image = None
        self.current_image_path = None
        self.detected_faces = []
        
        # Setup GUI
        self.setup_gui()
        
        # Auto-load model
        self.load_model()
    
    def setup_gui(self):
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # ===== Top Control Panel =====
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Buttons
        ttk.Button(
            control_frame, 
            text="📁 Upload Image", 
            command=self.upload_image,
            width=20
        ).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Button(
            control_frame, 
            text="🔍 Detect Faces", 
            command=self.detect_faces,
            width=20
        ).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(
            control_frame, 
            text="💾 Save Result", 
            command=self.save_result,
            width=20
        ).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Button(
            control_frame, 
            text="🔄 Clear", 
            command=self.clear_all,
            width=20
        ).grid(row=0, column=3, padx=5, pady=5)
        
        # Model status
        self.status_label = ttk.Label(
            control_frame, 
            text="Model: Not Loaded", 
            foreground="red",
            font=("Arial", 10, "bold")
        )
        self.status_label.grid(row=0, column=4, padx=20, pady=5)
        
        # Confidence threshold slider
        ttk.Label(control_frame, text="Confidence:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.confidence_var = tk.DoubleVar(value=0.6)
        self.confidence_slider = ttk.Scale(
            control_frame,
            from_=0.3,
            to=0.9,
            variable=self.confidence_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_confidence_label
        )
        self.confidence_slider.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        self.confidence_label = ttk.Label(control_frame, text="0.60")
        self.confidence_label.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        
        # ===== Left Panel - Image Display =====
        image_frame = ttk.LabelFrame(main_frame, text="Image", padding="10")
        image_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        image_frame.columnconfigure(0, weight=1)
        image_frame.rowconfigure(0, weight=1)
        
        # Image canvas with scrollbar
        canvas_frame = ttk.Frame(image_frame)
        canvas_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        
        self.image_canvas = tk.Canvas(
            canvas_frame, 
            bg="gray20", 
            width=600, 
            height=500
        )
        self.image_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.image_canvas.yview)
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.image_canvas.xview)
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.image_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Image info label
        self.image_info_label = ttk.Label(image_frame, text="No image loaded", foreground="gray")
        self.image_info_label.grid(row=1, column=0, pady=(5, 0))
        
        # ===== Right Panel - Results =====
        results_frame = ttk.LabelFrame(main_frame, text="Detection Results", padding="10")
        results_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Results text with scrollbar
        text_frame = ttk.Frame(results_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.results_text = tk.Text(
            text_frame,
            width=40,
            height=20,
            wrap=tk.WORD,
            font=("Consolas", 10)
        )
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        results_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        results_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        # Configure text tags for colored output
        self.results_text.tag_configure("header", font=("Arial", 12, "bold"), foreground="blue")
        self.results_text.tag_configure("success", foreground="green", font=("Arial", 10, "bold"))
        self.results_text.tag_configure("warning", foreground="orange")
        self.results_text.tag_configure("error", foreground="red")
        self.results_text.tag_configure("info", foreground="black")
    
    def load_model(self):
        try:
            if self.detector.load_model():
                self.model_loaded = True
                self.status_label.config(text="Model: Loaded ✓", foreground="green")
                
                stats = self.detector.get_statistics()
                self.log_result(f"Model loaded successfully!\n", "header")
                self.log_result(f"Total encodings: {stats['total_encodings']}\n", "info")
                self.log_result(f"Known persons: {stats['unique_persons']}\n", "info")
                self.log_result(f"Confidence threshold: {stats['confidence_threshold']}\n", "info")
                self.log_result(f"\nKnown persons:\n", "info")
                
                for name in stats['known_persons'][:20]:
                    self.log_result(f"  • {name}\n", "info")
                
                if len(stats['known_persons']) > 20:
                    self.log_result(f"  ... and {len(stats['known_persons']) - 20} more\n", "info")
            else:
                self.model_loaded = False
                self.status_label.config(text="Model: Not Found ✗", foreground="red")
                self.log_result("Model not found!\n", "error")
                self.log_result("Please train the model first using:\n", "warning")
                self.log_result("  python ml_models/face_trainer.py\n", "info")
        except Exception as e:
            self.model_loaded = False
            self.status_label.config(text="Model: Error ✗", foreground="red")
            self.log_result(f"Error loading model: {str(e)}\n", "error")
    
    def upload_image(self):
        file_path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # Load image with OpenCV
            image = cv2.imread(file_path)
            if image is None:
                messagebox.showerror("Error", "Could not read the image file!")
                return
            
            # Store current image
            self.current_image = image.copy()
            self.current_image_path = file_path
            self.detected_faces = []
            
            # Display image
            self.display_image(image)
            
            # Update info
            height, width = image.shape[:2]
            file_size = os.path.getsize(file_path) / 1024  # KB
            self.image_info_label.config(
                text=f"📸 {os.path.basename(file_path)} | {width}x{height} | {file_size:.1f} KB"
            )
            
            # Log
            self.log_result(f"\n{'='*50}\n", "info")
            self.log_result(f"Image uploaded successfully!\n", "success")
            self.log_result(f"File: {os.path.basename(file_path)}\n", "info")
            self.log_result(f"Size: {width}x{height} pixels\n", "info")
            self.log_result(f"{'='*50}\n\n", "info")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {str(e)}")
            self.log_result(f"Error loading image: {str(e)}\n", "error")
    
    def detect_faces(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "Please upload an image first!")
            return
        
        if not self.model_loaded:
            messagebox.showerror("Error", "Model not loaded! Please train the model first.")
            return
        
        try:
            # Update confidence threshold
            self.detector.confidence_threshold = self.confidence_var.get()
            
            # Log start
            self.log_result(f"\n{'='*50}\n", "info")
            self.log_result(f"🔍 Detecting faces...\n", "header")
            self.log_result(f"Confidence threshold: {self.detector.confidence_threshold:.2f}\n", "info")
            
            # Convert to RGB for face_recognition
            image_rgb = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            faces = self.detector.recognize_faces_in_image(image_rgb, model="hog")
            self.detected_faces = faces
            
            # Draw boxes on image
            result_image = self.detector.draw_face_boxes(self.current_image.copy(), faces)
            
            # Display result
            self.display_image(result_image)
            
            # Log results
            self.log_result(f"\n✓ Detection completed!\n", "success")
            self.log_result(f"Faces detected: {len(faces)}\n\n", "info")
            
            if faces:
                for idx, face in enumerate(faces, 1):
                    self.log_result(f"Face #{idx}:\n", "header")
                    self.log_result(f"  Name: {face['name']}\n", "success" if face['name'] != "Unknown" else "warning")
                    self.log_result(f"  Confidence: {face['confidence']:.2%}\n", "info")
                    
                    top, right, bottom, left = face['location']
                    self.log_result(f"  Location: ({left}, {top}) - ({right}, {bottom})\n", "info")
                    self.log_result(f"  Size: {right-left}x{bottom-top} pixels\n\n", "info")
                
                # Summary
                recognized = sum(1 for f in faces if f['name'] != "Unknown")
                unknown = len(faces) - recognized
                
                self.log_result(f"Summary:\n", "header")
                self.log_result(f"  ✓ Recognized: {recognized}\n", "success")
                if unknown > 0:
                    self.log_result(f"  ? Unknown: {unknown}\n", "warning")
            else:
                self.log_result("No faces detected in the image.\n", "warning")
                self.log_result("Try:\n", "info")
                self.log_result("  • Using a different image\n", "info")
                self.log_result("  • Adjusting confidence threshold\n", "info")
                self.log_result("  • Checking image quality\n", "info")
            
            self.log_result(f"{'='*50}\n", "info")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error during detection: {str(e)}")
            self.log_result(f"\n✗ Error during detection: {str(e)}\n", "error")
    
    def save_result(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image to save!")
            return
        
        if not self.detected_faces:
            answer = messagebox.askyesno(
                "No Detection", 
                "No faces have been detected yet. Save original image?"
            )
            if not answer:
                return
        
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            title="Save result image",
            defaultextension=".jpg",
            filetypes=[
                ("JPEG", "*.jpg"),
                ("PNG", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # Get current displayed image
            if self.detected_faces:
                image_rgb = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
                image_to_save = self.detector.draw_face_boxes(self.current_image.copy(), self.detected_faces)
            else:
                image_to_save = self.current_image.copy()
            
            # Save image
            cv2.imwrite(file_path, image_to_save)
            
            messagebox.showinfo("Success", f"Image saved successfully!\n{file_path}")
            self.log_result(f"\n💾 Image saved: {os.path.basename(file_path)}\n", "success")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving image: {str(e)}")
            self.log_result(f"Error saving image: {str(e)}\n", "error")
    
    def clear_all(self):
        self.current_image = None
        self.current_image_path = None
        self.detected_faces = []
        
        # Clear canvas
        self.image_canvas.delete("all")
        
        # Clear results
        self.results_text.delete(1.0, tk.END)
        
        # Reset labels
        self.image_info_label.config(text="No image loaded")
        
        self.log_result("Cleared all data.\n", "info")
        self.log_result("Ready for new image.\n", "success")
    
    def display_image(self, image):
        try:
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(image_rgb)
            
            # Resize if too large (maintain aspect ratio)
            max_width = 800
            max_height = 600
            
            width, height = pil_image.size
            if width > max_width or height > max_height:
                ratio = min(max_width/width, max_height/height)
                new_size = (int(width*ratio), int(height*ratio))
                pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(pil_image)
            
            # Clear canvas and display image
            self.image_canvas.delete("all")
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.image_canvas.image = photo  # Keep reference
            
            # Update scroll region
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))
            
        except Exception as e:
            self.log_result(f"Error displaying image: {str(e)}\n", "error")
    
    def log_result(self, text, tag="info"):
        self.results_text.insert(tk.END, text, tag)
        self.results_text.see(tk.END)
    
    def update_confidence_label(self, value):
        self.confidence_label.config(text=f"{float(value):.2f}")


def main():
    root = tk.Tk()
    app = TestFaceRecognitionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
