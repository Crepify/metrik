#!/usr/bin/env python3
"""metrikAI local/static server with secure, short-lived phone-to-desktop image transfer.

The UI and API share one origin. A desktop creates a temporary transfer session, the
phone opens a QR deep link for that session, uploads one label image, and the desktop
polls the session until the image is available.
"""

from __future__ import annotations

import json
import os
import mimetypes
import re
import secrets
import shutil
import tempfile
import threading
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
UPLOAD_ROOT = Path(tempfile.gettempdir()) / "metrikai-phone-uploads"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

HOST = "0.0.0.0"
PORT = int(os.environ.get('PORT', '4173'))
OCR_API_URL = os.environ.get('OCR_API_URL', '').rstrip('/')
SESSION_TTL_SECONDS = 15 * 60
MAX_UPLOAD_BYTES = 12 * 1024 * 1024
SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{16,80}$")

SESSIONS: dict[str, dict] = {}
LOCK = threading.RLock()


def now() -> float:
    return time.time()


def is_expired(session: dict) -> bool:
    return now() >= session["expires_at"]


def cleanup_sessions() -> None:
    """Remove expired session records and their temporary image files."""
    with LOCK:
        expired = [sid for sid, session in SESSIONS.items() if is_expired(session)]
        for sid in expired:
            session = SESSIONS.pop(sid, None)
            if not session:
                continue
            upload_dir = session.get("upload_dir")
            if upload_dir:
                shutil.rmtree(upload_dir, ignore_errors=True)


def create_session() -> dict:
    cleanup_sessions()
    with LOCK:
        sid = secrets.token_urlsafe(24)
        upload_dir = UPLOAD_ROOT / sid
        upload_dir.mkdir(parents=True, exist_ok=True)
        session = {
            "id": sid,
            "created_at": now(),
            "expires_at": now() + SESSION_TTL_SECONDS,
            "upload_dir": upload_dir,
            "file_path": None,
            "filename": None,
            "mime": None,
            "size": None,
            "uploaded_at": None,
        }
        SESSIONS[sid] = session
        return session


def get_session(sid: str) -> dict | None:
    cleanup_sessions()
    if not SESSION_ID_RE.fullmatch(sid):
        return None
    with LOCK:
        session = SESSIONS.get(sid)
        if not session or is_expired(session):
            return None
        return session


def infer_image_type(data: bytes) -> tuple[str, str] | None:
    """Return (mime, extension) for supported image signatures."""
    if data.startswith(b"\xff\xd8\xff"):
        return ("image/jpeg", ".jpg")
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ("image/png", ".png")
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ("image/webp", ".webp")
    return None


def parse_multipart_file(body: bytes, content_type: str) -> tuple[str, bytes, str] | None:
    """Minimal multipart parser for one browser FormData image field.

    It intentionally accepts only a single field named `file`. This keeps the prototype
    dependency-free while limiting the endpoint's attack surface.
    """
    boundary_match = re.search(r"boundary=(?:\"([^\"]+)\"|([^;\s]+))", content_type, re.I)
    if not boundary_match:
        return None
    boundary = (boundary_match.group(1) or boundary_match.group(2)).encode("utf-8")
    marker = b"--" + boundary
    for part in body.split(marker):
        if b"name=\"file\"" not in part:
            continue
        if b"\r\n\r\n" not in part:
            continue
        header_bytes, file_data = part.split(b"\r\n\r\n", 1)
        # Splitting on the multipart boundary leaves exactly one framing CRLF.
        # Avoid rstrip() here so valid image bytes are never modified.
        if file_data.endswith(b"\r\n"):
            file_data = file_data[:-2]
        header_text = header_bytes.decode("utf-8", "replace")
        filename_match = re.search(r'filename="([^\"]*)"', header_text, re.I)
        if not filename_match:
            continue
        filename = Path(filename_match.group(1)).name or "phone-label"
        mimetype_match = re.search(r"Content-Type:\s*([^\r\n;]+)", header_text, re.I)
        declared_mime = mimetype_match.group(1).strip().lower() if mimetype_match else ""
        return filename, file_data, declared_mime
    return None


class MetrikAIHandler(SimpleHTTPRequestHandler):
    """Static UI plus same-origin temporary transfer API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        # Keep API responses private; uploads are short-lived and same-origin.
        if self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, fmt, *args):
        print("[metrikAI] " + (fmt % args))

    def send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def session_payload(self, session: dict) -> dict:
        ready = bool(session.get("file_path"))
        payload = {
            "id": session["id"],
            "ready": ready,
            "expires_in": max(0, int(session["expires_at"] - now())),
        }
        if ready:
            payload.update(
                {
                    "filename": session["filename"],
                    "mime": session["mime"],
                    "size": session["size"],
                    "image_url": f"/api/sessions/{session['id']}/image",
                }
            )
        return payload

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Allow", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/health":
            return self.send_json(HTTPStatus.OK, {"ok": True, "service": "metrikAI", "ocr_backend_configured": bool(OCR_API_URL)})
        if path == "/api/ocr-config":
            # Exposes only the public OCR service URL configured by the deployer.
            # No secret/token is stored or returned here.
            return self.send_json(HTTPStatus.OK, {"api_url": OCR_API_URL})

        match = re.fullmatch(r"/api/sessions/([A-Za-z0-9_-]+)", path)
        if match:
            session = get_session(match.group(1))
            if not session:
                return self.send_json(HTTPStatus.NOT_FOUND, {"error": "Transfer session expired or was not found."})
            return self.send_json(HTTPStatus.OK, self.session_payload(session))

        match = re.fullmatch(r"/api/sessions/([A-Za-z0-9_-]+)/image", path)
        if match:
            session = get_session(match.group(1))
            if not session or not session.get("file_path"):
                return self.send_json(HTTPStatus.NOT_FOUND, {"error": "No phone image is available for this session."})
            file_path: Path = session["file_path"]
            if not file_path.exists():
                return self.send_json(HTTPStatus.NOT_FOUND, {"error": "The temporary image is no longer available."})
            data = file_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", session["mime"])
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Content-Disposition", f'inline; filename="{session["filename"]}"')
            self.end_headers()
            return self.wfile.write(data)

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/sessions":
            session = create_session()
            return self.send_json(HTTPStatus.CREATED, self.session_payload(session))

        match = re.fullmatch(r"/api/sessions/([A-Za-z0-9_-]+)/upload", path)
        if not match:
            return self.send_json(HTTPStatus.NOT_FOUND, {"error": "Unknown API endpoint."})

        session = get_session(match.group(1))
        if not session:
            return self.send_json(HTTPStatus.NOT_FOUND, {"error": "Transfer session expired or was not found."})

        content_length = int(self.headers.get("Content-Length", "0") or 0)
        content_type = self.headers.get("Content-Type", "")
        if not content_type.lower().startswith("multipart/form-data"):
            return self.send_json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "Upload must use multipart/form-data."})
        if content_length <= 0 or content_length > MAX_UPLOAD_BYTES + 256 * 1024:
            return self.send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "Choose a label image smaller than 12 MB."})

        body = self.rfile.read(content_length)
        parsed_file = parse_multipart_file(body, content_type)
        if not parsed_file:
            return self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Could not find an image file in this upload."})
        original_name, data, _declared_mime = parsed_file
        if not data or len(data) > MAX_UPLOAD_BYTES:
            return self.send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "Choose a label image smaller than 12 MB."})

        detected = infer_image_type(data)
        if not detected:
            return self.send_json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "Use a JPEG, PNG or WEBP label image."})
        mime, extension = detected
        safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(original_name).stem).strip(".-") or "phone-label"
        filename = f"{safe_stem}{extension}"
        upload_path: Path = session["upload_dir"] / filename
        upload_path.write_bytes(data)

        with LOCK:
            old_path = session.get("file_path")
            if old_path and old_path != upload_path:
                try:
                    Path(old_path).unlink(missing_ok=True)
                except OSError:
                    pass
            session.update(
                {
                    "file_path": upload_path,
                    "filename": filename,
                    "mime": mime,
                    "size": len(data),
                    "uploaded_at": now(),
                }
            )
        return self.send_json(HTTPStatus.CREATED, {"ok": True, "message": "Label image sent to your desktop session.", **self.session_payload(session)})


def main() -> None:
    print(f"metrikAI server running at http://{HOST}:{PORT}")
    print("Phone-transfer sessions expire after 15 minutes; images are stored in the OS temporary directory.")
    server = ThreadingHTTPServer((HOST, PORT), MetrikAIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        shutil.rmtree(UPLOAD_ROOT, ignore_errors=True)


if __name__ == "__main__":
    main()
