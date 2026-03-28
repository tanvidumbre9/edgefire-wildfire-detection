import gradio as gr
import firebase_admin
from firebase_admin import credentials, db
import json
import os
from datetime import datetime
from ultralytics import YOLO
from PIL import Image
import io
import base64
import numpy as np

# Initialize Firebase
def init_firebase():
    """Initialize Firebase connection"""
    try:
        if not firebase_admin._apps:
            # Try to load from environment variable (Hugging Face Spaces secret)
            firebase_creds = os.environ.get('FIREBASE_CREDENTIALS')
            firebase_url = os.environ.get('FIREBASE_URL')
            
            if firebase_creds and firebase_url:
                cred_dict = json.loads(firebase_creds)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': firebase_url
                })
                return True
            else:
                print("Firebase credentials not found in environment")
                return False
    except Exception as e:
        print(f"Firebase initialization failed: {e}")
        return False

# Initialize Firebase on startup
firebase_initialized = init_firebase()

# Load YOLOv8 model
try:
    # Using YOLOv8n (nano) for faster inference
    # For fire detection, we'll use a pretrained model
    # In production, you would use a custom-trained fire detection model
    model = YOLO('yolov8n.pt')  # Using pretrained COCO model for demo
    print("YOLOv8 model loaded successfully")
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    model = None

def compress_image(image, max_size_kb=500, quality=65):
    """
    Compress image to ensure it's under max_size_kb
    
    Args:
        image: PIL Image object
        max_size_kb: Maximum size in KB (default 500)
        quality: JPEG quality 1-100 (default 65)
    
    Returns:
        Compressed image as PIL Image
    """
    try:
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Start with the given quality
        current_quality = quality
        
        while current_quality > 10:
            # Save to bytes buffer
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=current_quality, optimize=True)
            size_kb = buffer.tell() / 1024
            
            if size_kb <= max_size_kb:
                buffer.seek(0)
                return Image.open(buffer)
            
            # Reduce quality by 5 if still too large
            current_quality -= 5
        
        # If still too large, resize the image
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=10, optimize=True)
        buffer.seek(0)
        return Image.open(buffer)
        
    except Exception as e:
        print(f"Error compressing image: {e}")
        return image

def image_to_base64(image):
    """
    Convert PIL Image to base64 string with data URI
    
    Args:
        image: PIL Image object
    
    Returns:
        Base64 encoded string with data URI prefix
    """
    try:
        # Compress image first
        compressed_image = compress_image(image, max_size_kb=500, quality=65)
        
        # Convert to bytes
        buffer = io.BytesIO()
        compressed_image.save(buffer, format='JPEG', quality=65, optimize=True)
        img_bytes = buffer.getvalue()
        
        # Encode to base64
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        # Add data URI prefix
        data_uri = f"data:image/jpeg;base64,{img_base64}"
        
        return data_uri
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        return None

def detect_fire(image):
    """
    Perform fire detection on uploaded image
    
    IMPORTANT: This is a DEMO implementation using a general-purpose COCO model.
    For production use, you MUST train a custom YOLOv8 model on fire-specific datasets.
    
    Current behavior: Detects any object with confidence > 0.7 as a test/demo.
    This will create false positives and is NOT suitable for real fire detection.
    
    Args:
        image: PIL Image or numpy array
    
    Returns:
        Tuple of (result_image, fire_detected, confidence, message)
    """
    try:
        if model is None:
            return image, False, 0.0, "❌ Model not loaded. Cannot perform detection."
        
        # Convert to PIL Image if numpy array
        if isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        # Run detection
        results = model(pil_image)
        
        # Get the first result
        result = results[0]
        
        # Check if any objects detected
        if len(result.boxes) == 0:
            return pil_image, False, 0.0, "✅ No objects detected in the image."
        
        # DEMO LOGIC - NOT FOR PRODUCTION
        # This demo uses a pretrained COCO model which doesn't have a 'fire' class
        # For demonstration purposes, we detect ANY object with high confidence
        # In production, replace with a custom-trained fire detection model
        
        fire_detected = False
        max_confidence = 0.0
        detected_objects = []
        
        for box in result.boxes:
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            
            # Get class name if available
            class_name = model.names[cls] if hasattr(model, 'names') else f"class_{cls}"
            
            # DEMO: Treat any detection with confidence > 0.7 as "potential fire"
            # This is ONLY for testing the pipeline and will produce false positives
            if conf > 0.7:
                fire_detected = True
                max_confidence = max(max_confidence, conf)
                detected_objects.append(f"{class_name} ({conf:.2f})")
        
        # Get annotated image with bounding boxes
        annotated_image = result.plot()
        
        # Convert back to PIL Image
        if isinstance(annotated_image, np.ndarray):
            result_image = Image.fromarray(annotated_image)
        else:
            result_image = annotated_image
        
        if fire_detected:
            # Save to Firebase
            if firebase_initialized:
                try:
                    # Convert annotated image to base64
                    image_base64 = image_to_base64(result_image)
                    
                    # Create incident data
                    incident_data = {
                        'fire_detected': True,
                        'confidence': float(max_confidence),
                        'timestamp': datetime.utcnow().isoformat(),
                        'location': {
                            'latitude': 12.9716,  # Default location (Bangalore)
                            'longitude': 77.5946
                        },
                        'device_id': 'HF_WEB_UPLOAD',
                        'source': 'manual-upload',
                        'status': 'active'
                    }
                    
                    # Add base64 image if conversion successful
                    if image_base64:
                        incident_data['detected_image_base64'] = image_base64
                    
                    # Save to Firebase
                    ref = db.reference('/incidents')
                    ref.push(incident_data)
                    
                    objects_str = ", ".join(detected_objects) if detected_objects else "objects"
                    message = f"⚠️ DEMO ALERT: Detected {objects_str}. Confidence: {max_confidence*100:.1f}% | Incident saved to Firebase with image.\n\n**Note: This is a DEMO using general object detection. For real fire detection, train a custom model.**"
                except Exception as e:
                    print(f"Error saving to Firebase: {e}")
                    message = f"⚠️ DEMO ALERT: Detection confidence {max_confidence*100:.1f}% | Warning: Could not save to Firebase: {e}"
            else:
                message = f"⚠️ DEMO ALERT: Detection confidence {max_confidence*100:.1f}% | Firebase not connected.\n\n**Note: Using general object detection model, not trained for fire.**"
            
            return result_image, True, max_confidence, message
        else:
            return result_image, False, 0.0, "✅ No high-confidence detections found."
            
    except Exception as e:
        error_msg = f"❌ Error during detection: {str(e)}"
        print(error_msg)
        return image, False, 0.0, error_msg

# Create Gradio interface
def create_interface():
    """Create and return Gradio interface"""
    
    with gr.Blocks(title="Wildfire Detection System - DEMO", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🔥 Wildfire Detection System (DEMO)")
        gr.Markdown("""
        Upload an image to test the fire detection pipeline using YOLOv8.
        
        ⚠️ **IMPORTANT**: This is a DEMO using a general-purpose object detection model.
        For production fire detection, you must train a custom YOLOv8 model on fire-specific datasets.
        """)
        
        with gr.Row():
            with gr.Column():
                input_image = gr.Image(type="pil", label="Upload Image")
                detect_btn = gr.Button("🔍 Run Detection (Demo)", variant="primary")
            
            with gr.Column():
                output_image = gr.Image(type="pil", label="Detection Result")
                result_message = gr.Textbox(label="Result", lines=5)
        
        # Status indicators
        with gr.Row():
            firebase_status = gr.Textbox(
                label="Firebase Status",
                value="🟢 Connected" if firebase_initialized else "🔴 Not Connected",
                interactive=False
            )
            model_status = gr.Textbox(
                label="Model Status",
                value="🟢 YOLOv8n Loaded (COCO - Demo)" if model else "🔴 Not Loaded",
                interactive=False
            )
        
        # Connect the button
        detect_btn.click(
            fn=detect_fire,
            inputs=[input_image],
            outputs=[output_image, gr.State(), gr.State(), result_message]
        )
        
        gr.Markdown("---")
        gr.Markdown("""
        **Production Deployment Notes:**
        - Train a custom YOLOv8 model on fire/smoke datasets (e.g., from Roboflow, Kaggle)
        - Replace `yolov8n.pt` with your custom trained model weights
        - Adjust confidence thresholds based on your model's performance
        - Add proper validation and testing before deployment
        """)
    
    return demo

# Launch the app
if __name__ == "__main__":
    demo = create_interface()
    demo.launch()
