import os
import json
import uuid
import time
import base64
import logging
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path


def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)


def env_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key, str(default)).strip().lower()
    return val in ("1", "true", "yes", "on")


def env_json(key: str, required: bool = False):
    raw = os.getenv(key)
    if not raw:
        if required:
            raise ValueError(f"Missing required env var: {key}")
        return None
    return json.loads(raw)


def to_base64_file(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def generate_id(prefix: Optional[str] = None) -> str:
    core = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
    return f"{prefix}_{core}" if prefix else core