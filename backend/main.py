import os
import threading
import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from utils import setup_logging
from pipeline import WildfirePipeline

load_dotenv()
setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("main")

app = FastAPI(title="Wildfire Detection Backend", version="1.0.0")
pipeline = WildfirePipeline()


class ManualProcessRequest(BaseModel):
    blob_path: str
    location: Optional[Dict[str, float]] = None


@app.on_event("startup")
def startup_event():
    auto_run = os.getenv("AUTO_RUN_PIPELINE", "true").lower() in ("1", "true", "yes")
    if auto_run:
        thread = threading.Thread(target=pipeline.run_forever, daemon=True)
        thread.start()
        logger.info("Background pipeline thread started.")


@app.get("/health")
def health():
    return {"status": "ok", "service": "wildfire-backend"}


@app.get("/incidents")
def get_incidents():
    try:
        incidents = pipeline.firebase.get_all_incidents()
        return {"count": len(incidents), "incidents": incidents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-image")
def process_image(payload: ManualProcessRequest):
    try:
        result = pipeline.process_blob(payload.blob_path, payload.location)
        return result
    except Exception as e:
        logger.exception("Manual processing failed.")
        raise HTTPException(status_code=500, detail=str(e))