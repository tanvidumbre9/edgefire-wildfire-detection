import os
import json
import logging
from typing import Dict, Any, Optional

import google.generativeai as genai

logger = logging.getLogger("gemini_service")


class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)
        logger.info(f"Gemini initialized with model: {self.model_name}")

    def analyze_detection(
        self,
        fire_detected: bool,
        confidence: float,
        boxes: list,
        image_base64: Optional[str] = None,
    ) -> Dict[str, Any]:
        prompt = f"""
Analyze this wildfire detection result and return STRICT JSON only.

Detection:
- fire_detected: {fire_detected}
- confidence: {confidence:.4f}
- boxes: {json.dumps(boxes)}

Return JSON with keys:
severity (Low/Medium/High),
risk_explanation (string),
suggested_action (string),
urgency_level (Low/Medium/High),
analysis_summary (string)
"""

        try:
            response = self.model.generate_content(prompt)
            raw = response.text.strip()

            # best effort JSON parse
            start = raw.find("{")
            end = raw.rfind("}")
            parsed = json.loads(raw[start : end + 1]) if start != -1 and end != -1 else {}

            return {
                "severity": parsed.get("severity", "Low"),
                "risk_explanation": parsed.get("risk_explanation", "No explanation provided."),
                "suggested_action": parsed.get("suggested_action", "Monitor the area."),
                "urgency_level": parsed.get("urgency_level", "Low"),
                "analysis_summary": parsed.get("analysis_summary", raw[:500]),
                "raw_response": raw,
            }
        except Exception as e:
            logger.exception("Gemini analysis failed.")
            return {
                "severity": "Unknown",
                "risk_explanation": f"Gemini error: {e}",
                "suggested_action": "Fallback to manual review.",
                "urgency_level": "Unknown",
                "analysis_summary": "Analysis unavailable due to API error.",
                "raw_response": "",
            }