import os
import logging
from typing import Dict, Any, List, Tuple
from PIL import Image
import numpy as np
import cv2

from ultralytics import YOLO

from utils import ensure_dir, generate_id, safe_float

logger = logging.getLogger("yolo_service")


class YoloService:
    def __init__(self):
        model_path = os.getenv("YOLO_MODEL_PATH", "fire_n.pt")
        self.conf_threshold = safe_float(os.getenv("YOLO_CONF_THRESHOLD", "0.25"), 0.25)
        self.output_dir = os.getenv("ANNOTATED_OUTPUT_DIR", "tmp/annotated")
        ensure_dir(self.output_dir)

        self.model = YOLO(model_path)
        logger.info(f"YOLO model loaded from: {model_path}")

    def detect(self, pil_img: Image.Image) -> Dict[str, Any]:
        img_np = np.array(pil_img)  # RGB
        results = self.model.predict(img_np, conf=self.conf_threshold, verbose=False)

        fire_detected = False
        max_conf = 0.0
        boxes_out: List[Dict[str, Any]] = []

        if not results:
            return {
                "fire_detected": False,
                "confidence": 0.0,
                "boxes": [],
                "annotated_local_path": None,
            }

        result = results[0]
        names = result.names if hasattr(result, "names") else {}

        if result.boxes is not None:
            for b in result.boxes:
                cls_id = int(b.cls.item()) if b.cls is not None else -1
                conf = float(b.conf.item()) if b.conf is not None else 0.0
                xyxy = b.xyxy[0].tolist() if b.xyxy is not None else [0, 0, 0, 0]
                label = names.get(cls_id, str(cls_id))

                boxes_out.append(
                    {
                        "class_id": cls_id,
                        "label": label,
                        "confidence": conf,
                        "bbox_xyxy": xyxy,
                    }
                )
                max_conf = max(max_conf, conf)

                if "fire" in label.lower() or cls_id == 0:  # adjust mapping as needed
                    fire_detected = True

        # Annotated image
        annotated_bgr = result.plot()  # BGR np array
        annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
        annotated_path = os.path.join(self.output_dir, f"{generate_id('annotated')}.jpg")
        Image.fromarray(annotated_rgb).save(annotated_path)

        return {
            "fire_detected": fire_detected,
            "confidence": max_conf,
            "boxes": boxes_out,
            "annotated_local_path": annotated_path,
        }