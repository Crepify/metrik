"""metrikAI OCR backend — service info (lightweight, no model).

Served at /api and /api/index by Vercel.
"""
from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="metrikAI OCR (Vercel functions)", version="1.0.0")


@app.get("/api")
def base():
    return {"service": "metrikAI OCR", "health": "/api/health", "ocr": "POST /api/ocr (multipart field: file)"}


@app.get("/api/index")
def index():
    return {"service": "metrikAI OCR", "health": "/api/health", "ocr": "POST /api/ocr (multipart field: file)"}
