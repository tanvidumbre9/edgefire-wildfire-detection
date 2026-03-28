import os
import time
import shutil
import logging
from typing import Dict, Any, Optional
from PIL import Image

from firebase_service import FirebaseService
from yolo_service import YoloService
from gemini_service import GeminiService
from alert_service import AlertService
from utils import ensure_dir, utc_now_iso, to_base64_file, env_bool, generate_id

logger = logging.getLogger("pipeline")


class WildfirePipeline:
    def __init__(self):
        self.firebase = FirebaseService()
        self.yolo = YoloService()
        self.gemini = GeminiService()
        self.alerts = AlertService()

        self.poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))
        self.mock_mode = env_bool("MOCK_MODE", False)
        self.mock_source_dir = os.getenv("MOCK_IMAGE_FOLDER", "mock_images")
        self.mock_uploaded_dir = os.getenv("MOCK_UPLOADED_FOLDER", "tmp/mock_uploaded")
        ensure_dir(self.mock_uploaded_dir)

    def process_blob(self, blob_path: str, location: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        logger.info(f"Processing blob: {blob_path}")

        if self.firebase.get_processed_flag(blob_path):
            logger.info(f"Skipping already processed image: {blob_path}")
            return {"status": "skipped", "reason": "already_processed", "blob_path": blob_path}

        # 1) Download image
        pil_img = self.firebase.download_image_as_pil(blob_path)

        # 2) YOLO detection
        yolo_result = self.yolo.detect(pil_img)

        # 3) Upload annotated image
        annotated_url = None
        if yolo_result.get("annotated_local_path"):
            annotated_name = f"annotated_images/{generate_id('ann')}.jpg"
            annotated_url = self.firebase.upload_file(yolo_result["annotated_local_path"], annotated_name)

        # 4) Gemini analysis
        img_b64 = None
        if yolo_result.get("annotated_local_path"):
            img_b64 = to_base64_file(yolo_result["annotated_local_path"])

        gemini_result = self.gemini.analyze_detection(
            fire_detected=yolo_result["fire_detected"],
            confidence=yolo_result["confidence"],
            boxes=yolo_result["boxes"],
            image_base64=img_b64,
        )

        # 5) Build incident payload
        image_url = self.firebase.get_blob_public_url(blob_path)
        incident = {
            "timestamp": utc_now_iso(),
            "image_url": image_url,
            "annotated_image_url": annotated_url,
            "fire_detected": yolo_result["fire_detected"],
            "confidence": yolo_result["confidence"],
            "severity": gemini_result.get("severity", "Unknown"),
            "analysis": gemini_result.get("analysis_summary", ""),
            "recommended_action": gemini_result.get("suggested_action", ""),
            "risk_explanation": gemini_result.get("risk_explanation", ""),
            "urgency_level": gemini_result.get("urgency_level", "Unknown"),
            "boxes": yolo_result["boxes"],
            "location": location or {
                "lat": float(os.getenv("DEFAULT_LAT", "37.7749")),
                "lng": float(os.getenv("DEFAULT_LNG", "-122.4194")),
            },
            "status": "active" if yolo_result["fire_detected"] else "clear",
            "source_blob_path": blob_path,
        }

        # 6) Save to Firebase RTDB
        incident_id = self.firebase.push_incident(incident)
        self.firebase.set_processed_flag(blob_path, incident_id)

        # 7) Alert
        self.alerts.send_alert(incident)

        result = {"status": "processed", "incident_id": incident_id, "incident": incident}
        logger.info(f"Completed processing for blob: {blob_path}")
        return result

    def poll_once(self):
        image_paths = self.firebase.list_incoming_images(prefix="incoming_images/")
        logger.info(f"Found {len(image_paths)} image(s) in incoming_images/")
        for path in image_paths:
            try:
                self.process_blob(path)
            except Exception:
                logger.exception(f"Failed processing image: {path}")

    def run_forever(self):
        logger.info("Starting pipeline poll loop...")
        while True:
            try:
                if self.mock_mode:
                    self._mock_upload_tick()
                self.poll_once()
            except Exception:
                logger.exception("Pipeline loop error")
            time.sleep(self.poll_interval)

    def _mock_upload_tick(self):
        """
        MOCK mode: simulates ESP32 uploads by moving one image every tick
        from local folder to Firebase incoming_images/.
        """
        if not os.path.isdir(self.mock_source_dir):
            return

        candidates = [
            f for f in os.listdir(self.mock_source_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        ]
        if not candidates:
            return

        file_name = candidates[0]
        local_path = os.path.join(self.mock_source_dir, file_name)
        dest_blob = f"incoming_images/{generate_id('mock')}_{file_name}"

        try:
            url = self.firebase.upload_file(local_path, dest_blob)
            self.firebase.save_mock_upload_record(file_name)
            logger.info(f"[MOCK] Uploaded {file_name} -> {dest_blob} ({url})")
            shutil.move(local_path, os.path.join(self.mock_uploaded_dir, file_name))
        except Exception:
            logger.exception(f"[MOCK] Failed to upload {local_path}")