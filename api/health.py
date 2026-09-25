"""metrikAI OCR backend — health check.

Served at GET /api/health by Vercel (file-based routing: api/health.py -> /api/health).
Deliberately dependency-light: no model loading here, so this responds in ms.
"""
from __future__ import annotations

import time

from fastapi import FastAPI

app = FastAPI(title="metrikAI OCR health", version="1.0.0")

START = time.time()


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "engine": "rapidocr-onnxruntime (PaddleOCR PP-OCRv4)",
        "detector": None,
        "mode": "vercel-serverless / ocr-only",
        "model_loaded": False,
        "uptime_s": round(time.time() - START, 1),
        # NOTE: never emit tesseract.available:false — the UI treats it as fatal.
    }
