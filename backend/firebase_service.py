import os
import io
import json
import tempfile
import logging
from typing import List, Dict, Any, Optional
from PIL import Image

import firebase_admin
from firebase_admin import credentials, storage, db

from utils import env_json, utc_now_iso

logger = logging.getLogger("firebase_service")


class FirebaseService:
    def __init__(self):
        self.bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
        self.db_url = os.getenv("FIREBASE_DATABASE_URL")
        self.creds_json = env_json("FIREBASE_CREDENTIALS", required=True)

        if not self.bucket_name or not self.db_url:
            raise ValueError("Missing FIREBASE_STORAGE_BUCKET or FIREBASE_DATABASE_URL")

        if not firebase_admin._apps:
            cred = credentials.Certificate(self.creds_json)
            firebase_admin.initialize_app(
                cred,
                {
                    "storageBucket": self.bucket_name,
                    "databaseURL": self.db_url,
                },
            )
            logger.info("Firebase initialized successfully.")

        self.bucket = storage.bucket()

    def list_incoming_images(self, prefix: str = "incoming_images/") -> List[str]:
        blobs = self.bucket.list_blobs(prefix=prefix)
        image_paths = []
        for blob in blobs:
            if blob.name.endswith("/") or blob.name.lower().endswith((".txt", ".json")):
                continue
            if blob.name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                image_paths.append(blob.name)
        return image_paths

    def get_processed_flag(self, image_path: str) -> bool:
        key = image_path.replace("/", "__")
        ref = db.reference(f"/processed_images/{key}")
        return bool(ref.get())

    def set_processed_flag(self, image_path: str, incident_id: str):
        key = image_path.replace("/", "__")
        ref = db.reference(f"/processed_images/{key}")
        ref.set(
            {
                "processed": True,
                "incident_id": incident_id,
                "processed_at": utc_now_iso(),
            }
        )

    def download_image_as_pil(self, blob_path: str) -> Image.Image:
        blob = self.bucket.blob(blob_path)
        image_bytes = blob.download_as_bytes()
        return Image.open(io.BytesIO(image_bytes)).convert("RGB")

    def upload_file(self, local_path: str, destination_blob_path: str) -> str:
        blob = self.bucket.blob(destination_blob_path)
        blob.upload_from_filename(local_path)
        blob.make_public()  # For demo; in production use signed URLs or restricted access.
        return blob.public_url

    def get_blob_public_url(self, blob_path: str) -> str:
        blob = self.bucket.blob(blob_path)
        blob.make_public()
        return blob.public_url

    def push_incident(self, payload: Dict[str, Any]) -> str:
        ref = db.reference("/incidents").push(payload)
        incident_id = ref.key
        logger.info(f"Incident saved to RTDB: {incident_id}")
        return incident_id

    def get_all_incidents(self) -> Dict[str, Any]:
        ref = db.reference("/incidents")
        return ref.get() or {}

    def save_mock_upload_record(self, image_name: str):
        ref = db.reference("/mock_uploads").push(
            {"image_name": image_name, "uploaded_at": utc_now_iso()}
        )
        return ref.key