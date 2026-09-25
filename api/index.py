"""
metrikAI OCR as a Vercel Serverless Function (same project as the website).

This removes the need for a separate Render/hosted backend:
  - no second service to deploy or keep awake
  - same origin -> no CORS problems
  - ~2-4 s per image (OCR-only mode; the YOLO detector is optional)

Setup (see DEPLOY_ON_VERCEL.md):
  1. copy api/ + ocr_pipeline.py + requirements.txt into the website repo
  2. set env var  OCR_API_URL = https://<your-site>.vercel.app/api
  3. redeploy

The frontend then calls:
  GET  https://<your-site>.vercel.app/api/health
  POST https://<your-site>.vercel.app/api/ocr   (multipart field `file`)
"""
from __future__ import annotations
import os
import sys
import time

from fastapi import FastAPI, File, UploadFile, HTTPException

# the website repo keeps ocr_pipeline.py next to this api/ folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("USE_DETECTOR", "false")  # keep the bundle small & fast

from ocr_pipeline import LabelOCRPipeline, DETECTOR_PATH  # noqa: E402

app = FastAPI(title="metrikAI OCR (Vercel function)", version="1.0.0")

START = time.time()
_pipeline: LabelOCRPipeline | None = None


def get_pipeline() -> LabelOCRPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = LabelOCRPipeline(detector_path=None)
    return _pipeline


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "engine": "rapidocr-onnxruntime (PaddleOCR PP-OCRv4)",
        "detector": None,
        "mode": "vercel-serverless / ocr-only",
        "model_loaded": _pipeline is not None,
        "uptime_s": round(time.time() - START, 1),
        # NOTE: never emit tesseract.available:false - the UI treats it as fatal
    }


@app.post("/api/ocr")
async def ocr(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Upload an image file (JPG/PNG/WEBP).")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload.")
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image too large (max 15 MB).")
    try:
        result = get_pipeline().run(data)
    except Exception as exc:  # the frontend always expects JSON
        raise HTTPException(status_code=500, detail=f"OCR failed: {exc}") from exc
    result["filename"] = file.filename
    result["mode"] = "vercel-serverless"
    return result


@app.get("/api")
def root():
    return {"service": "metrikAI OCR", "health": "/api/health", "ocr": "/api/ocr"}
