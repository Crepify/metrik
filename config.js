/*
 * metrikAI FastAPI OCR configuration.
 *
 * Default: same-origin Vercel serverless function (api/index.py in this repo)
 *   -> https://metrik-steel.vercel.app/api/health
 *   -> https://metrik-steel.vercel.app/api/ocr
 *
 * Overrides (in priority order):
 *   1. URL saved by the user via the in-app “OCR backend” button (localStorage)
 *   2. This window.METRIK_OCR_API_URL value
 *   3. OCR_API_URL env var exposed by api/ocr-config.js (Vercel dashboard)
 *
 * Legacy Render backend (kept as reference):
 *   window.METRIK_OCR_API_URL = 'https://metrix-1z5z.onrender.com';
 * Do not add a trailing slash.
 */
window.METRIK_OCR_API_URL = window.METRIK_OCR_API_URL || 'https://metrik-steel.vercel.app/api';
