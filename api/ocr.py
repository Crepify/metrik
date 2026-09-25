"""metrikAI OCR backend — the OCR endpoint.

Served at POST /api/ocr by Vercel (file-based routing: api/ocr.py -> /api/ocr).
Accepts a multipart upload with field name `file` and returns the full JSON
contract the metrikAI frontend expects (text, words+bboxes, fields,
compliance, barcodes, annotated evidence image, timing, dimensions).

The model is loaded lazily on the first request of an instance; Vercel keeps
warm instances so repeated scans are ~2-4 s.
"""
from __future__ import annotations

import os
import time

from fastapi import FastAPI, File, HTTPException, UploadFile

# OCR-only mode: keep the function bundle under Vercel's 250 MB limit.
os.environ.setdefault("USE_DETECTOR", "false")

# Sibling module in the same api/ folder -> bundled by Vercel's build.
from ocr_pipeline import LabelOCRPipeline  # noqa: E402

app = FastAPI(title="metrikAI OCR", version="1.0.0")

START = time.time()
_pipeline: LabelOCRPipeline | None = None


def get_pipeline() -> LabelOCRPipeline:
    global _pipeline
    if _pipeline is None:
        t0 = time.time()
        _pipeline = LabelOCRPipeline(detector_path=None)
        print(f"[ocr] pipeline ready in {time.time() - t0:.1f}s")
    return _pipeline


@app.post("/api/ocr")
async def ocr(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Upload an image file (JPG/PNG/WEBP).")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload.")
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image too large (max 15 MB).")
    t0 = time.time()
    try:
        result = get_pipeline().run(data)
    except Exception as exc:  # the frontend always expects JSON, never a bare 500
        raise HTTPException(status_code=500, detail=f"OCR failed: {exc}") from exc
    result["filename"] = file.filename
    result["mode"] = "vercel-serverless"
    result.setdefault("processing_time_ms", int((time.time() - t0) * 1000))
    return result
