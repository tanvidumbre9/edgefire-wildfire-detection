# Image Detection Feature - Implementation Guide

## Overview

This feature adds the capability to display detected fire images (with bounding boxes) in both the Dashboard and Telegram alerts. The system captures images from fire detection events and stores them as compressed Base64-encoded data in Firebase.

## Architecture

```
┌─────────────────┐         ┌──────────────┐         ┌─────────────────┐
│  Hugging Face   │         │   Firebase    │         │   Dashboard     │
│  Detection App  │────────▶│   Realtime   │◀────────│   (Streamlit)   │
│   (Gradio)      │         │   Database   │         │                 │
└─────────────────┘         └──────────────┘         └─────────────────┘
                                    │
                                    ▼
                            ┌──────────────┐
                            │   Telegram   │
                            │     Bot      │
                            └──────────────┘
```

## Components

### 1. Hugging Face App (`huggingface/app.py`)

**Purpose**: Web interface for uploading images and detecting fire using YOLOv8

**Key Features**:
- Gradio web interface for image uploads
- YOLOv8 object detection (demo mode - uses pretrained COCO model)
- Image compression to <500KB (JPEG quality 60-70)
- Base64 encoding with data URI format
- Firebase integration to save incidents

**Functions**:
- `compress_image()`: Compresses images to stay under 500KB
- `image_to_base64()`: Converts PIL Image to Base64 with data URI prefix
- `detect_fire()`: Main detection function (DEMO - needs custom model for production)
- `create_interface()`: Creates Gradio UI

**Data Saved to Firebase**:
```json
{
  "fire_detected": true,
  "confidence": 0.92,
  "timestamp": "2025-12-03T12:30:45",
  "location": {"latitude": 12.9716, "longitude": 77.5946},
  "device_id": "HF_WEB_UPLOAD",
  "source": "manual-upload",
  "detected_image_base64": "data:image/jpeg;base64,/9j/4AAQ...",
  "status": "active"
}
```

### 2. Dashboard (`dashboard/app.py`)

**Changes Made**:

1. **Added Imports**:
   ```python
   import base64
   import io
   ```

2. **Updated `send_telegram_alert()` Function**:
   - Checks for `detected_image_base64` in incident data
   - Sends image via Telegram's `sendPhoto` API if available
   - Falls back to text-only message if image send fails
   - Maintains backward compatibility

3. **Updated Active Alerts Section**:
   - Displays detected image using `st.image()` when available
   - Decodes Base64 images for display
   - Graceful fallback if no image or decode fails
   - Shows alerts without images as before

**Key Code Snippets**:

*Telegram Image Sending*:
```python
if image_base64:
    # Remove data URI prefix
    if image_base64.startswith('data:image'):
        image_base64 = image_base64.split(',', 1)[1]
    
    # Decode and send
    image_bytes = base64.b64decode(image_base64)
    
    # Send via Telegram API
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    files = {'photo': ('fire_detection.jpg', image_bytes, 'image/jpeg')}
    data = {'chat_id': chat_id, 'caption': message}
    response = requests.post(url, files=files, data=data, timeout=30)
```

*Dashboard Image Display*:
```python
image_base64 = alert.get('detected_image_base64')
if image_base64:
    if image_base64.startswith('data:image'):
        image_base64 = image_base64.split(',', 1)[1]
    
    image_bytes = base64.b64decode(image_base64)
    st.image(image_bytes, caption="Detected Fire Image", use_container_width=True)
```

## Dependencies

**Added to `requirements.txt`**:
- `ultralytics` - YOLOv8 model
- `Pillow` - Image processing
- `gradio` - Web interface for Hugging Face app

## Image Processing Pipeline

1. **Detection** (Hugging Face App):
   ```
   Upload Image → YOLOv8 Detection → Draw Bounding Boxes → Compress (<500KB)
   ```

2. **Encoding**:
   ```
   PIL Image → JPEG (quality 60-70) → Base64 → Add Data URI prefix
   ```

3. **Storage**:
   ```
   Firebase Incident: detected_image_base64 = "data:image/jpeg;base64,..."
   ```

4. **Display** (Dashboard):
   ```
   Firebase → Remove Data URI prefix → Base64 Decode → st.image()
   ```

5. **Telegram**:
   ```
   Firebase → Remove Data URI prefix → Base64 Decode → sendPhoto API
   ```

## Safety Features

### Error Handling
- Try/except blocks around all image processing code
- Graceful fallbacks if image processing fails
- Backward compatible (works with incidents that don't have images)

### Size Management
- Images compressed to <500KB to respect Firebase free tier limits
- Adaptive quality reduction if image is too large
- Uses optimized JPEG compression

### Validation
- Checks for image existence before processing
- Validates Base64 format before decoding
- Proper error messages for debugging

## Testing

Run the test script to verify functionality:

```bash
python3 /tmp/test_image_functions.py
```

Tests cover:
- ✅ Image compression (stays under 500KB)
- ✅ Base64 conversion (with data URI)
- ✅ Dashboard decode logic
- ✅ Telegram format compatibility

## Deployment

### Hugging Face Space

1. Create a new Hugging Face Space (Gradio)
2. Upload `huggingface/app.py` and `huggingface/requirements.txt`
3. Add secrets:
   - `FIREBASE_CREDENTIALS`: Firebase service account JSON (as string)
   - `FIREBASE_URL`: Firebase database URL

### Dashboard (Streamlit)

No additional configuration needed. The dashboard will automatically:
- Display images when available in Firebase incidents
- Fall back to text-only alerts for old incidents
- Send images via Telegram if available

## Production Recommendations

### 1. Custom Fire Detection Model

⚠️ **CRITICAL**: The current implementation uses a general COCO model for DEMO purposes.

**For production, you MUST**:
1. Collect fire/smoke image dataset (e.g., from Roboflow, Kaggle)
2. Train custom YOLOv8 model:
   ```bash
   yolo train model=yolov8n.pt data=fire_dataset.yaml epochs=100
   ```
3. Replace `yolov8n.pt` with your trained weights
4. Update detection threshold based on model performance

### 2. Security

- Store Firebase credentials securely (environment variables, secrets)
- Validate uploaded images before processing
- Implement rate limiting on uploads
- Add authentication for Hugging Face interface

### 3. Performance

- Consider using YOLOv8n (nano) for speed vs YOLOv8x for accuracy
- Optimize image compression based on network bandwidth
- Cache model loading
- Use async processing for large batches

### 4. Monitoring

- Log all detections and confidence scores
- Track false positive/negative rates
- Monitor image sizes in Firebase
- Set up alerts for model failures

## Data Structure Reference

### Firebase Schema

```json
{
  "incidents": {
    "-OfXxxxxx": {
      "fire_detected": true,
      "confidence": 0.92,
      "timestamp": "2025-12-03T12:30:45",
      "location": {
        "latitude": 12.97,
        "longitude": 77.59
      },
      "device_id": "ESP32_001",
      "source": "manual-upload",  // or "esp32-cam"
      "detected_image_base64": "data:image/jpeg;base64,/9j/4AAQ...",
      "status": "active"
    }
  }
}
```

### Source Field Values

- `"manual-upload"`: Images uploaded via Hugging Face web interface
- `"esp32-cam"`: Images from ESP32-CAM hardware (future implementation)

## Future Enhancements

- [ ] ESP32-CAM integration for real-time camera feeds
- [ ] Custom trained fire detection model
- [ ] Multi-image support (before/after shots)
- [ ] Image history/gallery in dashboard
- [ ] GPS coordinates from ESP32 for accurate location
- [ ] Smoke detection in addition to fire
- [ ] Video stream support
- [ ] Edge computing on ESP32 for pre-filtering

## Troubleshooting

### Images not appearing in Dashboard

1. Check Firebase data has `detected_image_base64` field
2. Verify Base64 format is valid
3. Check browser console for decode errors
4. Ensure Streamlit has proper permissions

### Telegram not sending images

1. Verify Telegram bot token and chat_id
2. Check image size (<10MB for Telegram)
3. Confirm Base64 decoding works
4. Check network connectivity
5. Verify bot has permission to send photos

### Image compression not working

1. Verify Pillow is installed
2. Check input image format (convert to RGB if needed)
3. Adjust quality parameters if needed
4. Monitor memory usage for large images

## Support

For issues or questions:
1. Check the test script output
2. Review error logs in Streamlit/Gradio console
3. Verify Firebase connection
4. Check image sizes and formats
