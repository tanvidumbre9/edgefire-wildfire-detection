# Wildfire Detection - Hugging Face App

This is the Hugging Face Gradio app for the Wildfire Detection System. It provides a web interface for uploading images and detecting fire using YOLOv8.

## Features

- 🔥 Fire detection using YOLOv8 object detection
- 📸 Image upload via web interface
- 🎯 Bounding box visualization on detected images
- 💾 Automatic saving to Firebase with detected images
- 🗜️ Image compression to keep under 500KB
- 🔐 Secure Firebase integration via environment variables

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export FIREBASE_CREDENTIALS='{"type":"service_account",...}'
export FIREBASE_URL='https://your-project.firebaseio.com'
```

3. Run the app:
```bash
python app.py
```

### Hugging Face Spaces Deployment

1. Create a new Space on Hugging Face
2. Upload `app.py` and `requirements.txt`
3. Add secrets in Space settings:
   - `FIREBASE_CREDENTIALS`: Your Firebase service account JSON (as a string)
   - `FIREBASE_URL`: Your Firebase Realtime Database URL

## How It Works

1. User uploads an image through the Gradio interface
2. YOLOv8 model analyzes the image for fire/smoke detection
3. If fire is detected:
   - Bounding boxes are drawn on the image
   - Image is compressed to Base64 format (<500KB)
   - Incident data is saved to Firebase with the detected image
4. Results are displayed in the web interface

## Firebase Data Structure

When fire is detected, the following data is saved to Firebase:

```json
{
  "fire_detected": true,
  "confidence": 0.92,
  "timestamp": "2025-12-03T12:30:45",
  "location": {
    "latitude": 12.9716,
    "longitude": 77.5946
  },
  "device_id": "HF_WEB_UPLOAD",
  "source": "manual-upload",
  "detected_image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "status": "active"
}
```

## Notes

- The current implementation uses a pretrained YOLOv8n model for demonstration
- For production use, train a custom YOLOv8 model on fire-specific datasets
- Images are compressed to JPEG quality 60-70 to stay under 500KB
- The `source` field is set to "manual-upload" for web uploads
- Future ESP32-CAM uploads will use `source: "esp32-cam"`

## Integration

This app integrates with:
- **Firebase Realtime Database**: Stores incident data
- **Dashboard**: Displays detected images and alerts
- **Telegram Bot**: Sends images with fire alerts
