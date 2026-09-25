"""
metrikAI label OCR pipeline.

Two-stage design (works with only 38 labelled images):
  1. YOLOv8n region detector, fine-tuned on the 38 label photos, locates the
     declaration regions (mrp, net_quantity, mfd_date, exp_date, consumer_care,
     mfr_address, origin, barcode ...).
  2. RapidOCR (PaddleOCR ONNX models) reads the text - full image for complete
     evidence, plus a focused pass over each detected region crop, which is
     where small print (MRP, dates) becomes readable.

Then regex field extraction tuned for Indian packaged-commodity declarations,
and a response payload matching the metrikAI frontend contract exactly.
"""
from __future__ import annotations

import base64
import os
import re
import time
from typing import Any, Optional

import cv2
import numpy as np

# --------------------------------------------------------------------------
# Detection classes (must match dataset/label_data.yaml order)
# --------------------------------------------------------------------------
CLASS_NAMES = [
    "package", "label", "mrp", "net_quantity", "mfd_date", "exp_date",
    "consumer_care", "mfr_address", "origin", "barcode",
    "hazard_pictogram", "warning_text", "sticker",
]
CLASS_IDX = {name: i for i, name in enumerate(CLASS_NAMES)}

DETECTOR_PATH = os.environ.get(
    "LABEL_DETECTOR_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "runs/detect/label_detector/weights/best.pt"),
)

# Fields the frontend reads (keys consumed by enrichWithBackend)
FIELD_KEYS = [
    "commodity_name", "manufacturer", "brand_owner", "net_quantity",
    "mrp", "mfg_date", "use_before", "batch_number", "customer_care",
    "address", "country_of_origin",
]


# --------------------------------------------------------------------------
# Field extraction patterns (tolerant of OCR text with stripped spaces)
# --------------------------------------------------------------------------
# net quantity: number + unit, unit mandatory so stray digits don't match
_RE_NET_QTY = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(ml|millilit\w*|l\b|lit\w*|g\b|gm|gms|gram\w*|kg|kgs|kilogram\w*|"
    r"nos\b|no\.\s*of|pieces?|pcs\b|pcsset|sachets?|tablets?|tabs?\b|capsules?|units?|"
    r"pairs?|sheets?|metres?|meters?|m\b)", re.I)
# a price: 2-decimal number, optionally prefixed by a mangled rupee sign
_RE_PRICE_2DP = re.compile(r"(?<![\d.,])(\d{1,5}\.\d{2})(?![\d%])")
_RE_PRICE_1DP = re.compile(r"(?<![\d.,])(\d{1,5}\.\d{1})(?![\d%])")
_RE_MRP_INT = re.compile(r"mrp[^\d]{0,15}(\d{2,6})", re.I)
_RE_MRP_LINE = re.compile(r"mrp|m\.r\.p|max\.?\s*retail\s*price|retail\s*price", re.I)
# a 6-digit PIN, optionally with an internal space (122 018)
_RE_PIN = re.compile(r"(?<![\w/])([1-9]\d{2}\s?\d{3})(?![\d\w/])")
_RE_REGN_NOISE = re.compile(r"regn|reg\.|licen[cs]e|fssai|\bCIR\b|\bISO\b|\bCIN\b|gst|"
                            r"r\.?s\.?\s*no|m\.?l\.?\s*no|lic\b", re.I)
# dates: dd/mm/yyyy, dd.mm.yyyy, mm/yyyy, dd-Mon-yyyy, Mon yyyy
_RE_DATE_STRONG = re.compile(
    r"(\d{1,2}\s*[/.\-]\s*\d{1,2}\s*[/.\-]\s*\d{2,4}"     # 09.04.2026
    r"|\d{1,2}\s*[/.\-]\s*\d{4}"                            # 07/2026
    r"|\d{1,2}\s*[/.\-]\s*[A-Za-z]{3,9}\s*[/.\-]\s*\d{2,4}"  # 15-Jul-2026
    r"|[A-Za-z]{3,9}\s+\d{4})"                              # July 2026
)
_RE_DATE_WEAK = re.compile(r"(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})")  # 15 July 26
_RE_BATCH = re.compile(
    r"(?:batch|lot|b\.?\s*no\.?|batch\s*no\.?|lot\s*no\.?)\s*[:.#]?\s*"
    r"([A-Za-z0-9][A-Za-z0-9\-/]{3,})", re.I
)
_RE_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_RE_PHONE = re.compile(
    r"(?:\+?91[\s\-]?)?(?:\(?\d{3,5}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,5}"  # 011-41704999
    r"|1[8008]\d{2}[\s\-]?\d{3}[\s\-]?\d{3,4})"                        # toll-free 1800-xxx-xxxx
)
_RE_PIN = re.compile(r"\b([1-9]\d{5})\b")
_RE_ORIGIN = re.compile(
    r"(?:country\s*of\s*origin|made\s*in|mfg\.?\s*in|manufactured\s*in|product\s*of)\s*[:.]?\s*"
    r"([A-Za-z][A-Za-z .&]{2,40})", re.I
)

_MFG_HINT = re.compile(r"mfd|mfg|manufactur\w*|packed|pkg|date\s*of\s*packing", re.I)
_EXP_HINT = re.compile(r"exp\b|expiry|expiration|use\s*by|use\s*before|best\s*before|consume\s*within", re.I)
_CARE_HINT = re.compile(r"consumer\s*care|customer\s*care|complaint|grievance|contact|"
                        r"toll\s*free|toti\s*free|free\s*number|helpline|e-?mail|@", re.I)
_ADDR_HINT = re.compile(r"address|regd\.?|registered|office|pvt\.?\s*ltd|limited|llp|industries|works|plot|floor|tower|sector|road|nagar|mumbai|delhi|india", re.I)
_QTY_HINT = re.compile(r"net\s*(qty|quantity|wt|weight|volume|contents?)|net\s*wt", re.I)
_COMPANY_SUFFIX = re.compile(
    r"pvt\.?\s*ltd|private\s*limited|\bltd\b|\blimited\b|\bllp\b|\binc\b|incorporated|company|"
    r"products?|industries|corporation|\bcorp\b|enterprises|chemicals|foods|beverages|"
    r"consumer\s*products|consumer\s*goods|distributors|traders|agencies|packers", re.I)


def _norm(text: str) -> str:
    """Normalise common OCR confusions in numeric contexts."""
    t = text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    t = re.sub(r"[ \t]+", " ", t)
    return t


def _poly_to_xywh(poly) -> tuple[float, float, float, float]:
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    return x0, y0, x1 - x0, y1 - y0


def _iou(a, b) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x0, y0 = max(ax, bx), max(ay, by)
    x1, y1 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    inter = max(0.0, x1 - x0) * max(0.0, y1 - y0)
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


class LabelOCRPipeline:
    """Loads the OCR engine (and detector when available) once, then serves."""

    def __init__(self, detector_path: Optional[str] = DETECTOR_PATH):
        self.ocr_engine_name = "rapidocr-onnxruntime (PaddleOCR PP-OCRv4 models)"
        self.detector = None
        self.detector_name = None
        # USE_DETECTOR=false -> OCR-only mode: fits Render's free 512 MB tier
        # (no torch/ultralytics import, ~2x faster cold start)
        use_detector = os.environ.get("USE_DETECTOR", "auto").lower() not in {"0", "false", "no"}
        if use_detector and detector_path and os.path.exists(detector_path):
            try:
                from ultralytics import YOLO
                self.detector = YOLO(detector_path)
                self.detector_name = os.path.basename(os.path.dirname(os.path.dirname(detector_path)))
            except Exception as exc:  # keep OCR working even if torch is absent
                print(f"[pipeline] detector unavailable ({exc}); OCR-only mode")
        elif not use_detector:
            print("[pipeline] USE_DETECTOR=false -> OCR-only mode")

        # imported lazily so the module can be imported for tests without ONNX
        from rapidocr_onnxruntime import RapidOCR
        self._ocr = RapidOCR()

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def run(self, image_bytes: bytes) -> dict[str, Any]:
        t0 = time.perf_counter()
        img_np = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(img_np, cv2.IMREAD_COLOR)  # BGR
        if image is None:
            raise ValueError("Could not decode the image (corrupt or unsupported file).")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)   # OCR models expect RGB
        height, width = image.shape[:2]

        # ---- stage 1: region detection (optional) --------------------
        regions = []
        if self.detector is not None:
            regions = self._detect_regions(image, width, height)

        # ---- stage 2: OCR full image ----------------------------------
        result, _ = self._ocr(image)
        lines = []
        if result:
            for poly, text, conf in result:
                x, y, w, h = _poly_to_xywh(poly)
                lines.append({"text": _norm(str(text)), "confidence": round(float(conf), 4),
                              "bbox": [round(x, 1), round(y, 1), round(w, 1), round(h, 1)]})

        # ---- stage 3: focused OCR per region crop ---------------------
        for region in regions:
            crop_text, crop_conf = self._ocr_region(image, region)
            region["text"] = crop_text
            region["confidence_ocr"] = round(crop_conf, 4) if crop_conf else None
        # attach full-image lines to regions by overlap
        self._assign_lines_to_regions(lines, regions)

        # ---- stage 4: words (for font-size proxy & word count) --------
        words = self._split_words(lines)

        # ---- stage 5: structured fields --------------------------------
        full_text = "\n".join(l["text"] for l in lines)
        fields = self._extract_fields(full_text, regions, lines)

        compliance = self._compliance(fields, lines)

        mean_conf = (sum(l["confidence"] for l in lines) / len(lines)) if lines else 0.0
        barcodes = self._barcode_payload(regions, lines)

        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        return {
            "success": True,
            "engine": self.ocr_engine_name,
            "detector": self.detector_name,
            "text": full_text,
            "mean_confidence": round(mean_conf, 4),
            "words": words,
            "word_count": len(words),
            "lines": lines,
            "regions": regions,
            "fields": fields,
            "compliance": compliance,
            "barcodes": barcodes,
            "width": width,
            "height": height,
            "processing_time_ms": elapsed_ms,
            "annotated_image": self._annotated_data_uri(image, lines, regions),
        }

    # ------------------------------------------------------------------
    # stages
    # ------------------------------------------------------------------
    def _detect_regions(self, img_np, width, height) -> list[dict]:
        try:
            preds = self.detector.predict(img_np, verbose=False, conf=0.25, iou=0.5)[0]
        except Exception as exc:
            print(f"[pipeline] detection failed: {exc}")
            return []
        regions = []
        for box, cls, conf in zip(preds.boxes.xyxy.tolist(),
                                  preds.boxes.cls.tolist(),
                                  preds.boxes.conf.tolist()):
            x0, y0, x1, y1 = box
            regions.append({
                "class": CLASS_NAMES[int(cls)] if int(cls) < len(CLASS_NAMES) else str(int(cls)),
                "confidence": round(float(conf), 4),
                "bbox": [round(x0, 1), round(y0, 1), round(x1 - x0, 1), round(y1 - y0, 1)],
                "bbox_norm": [round(x0 / width, 5), round(y0 / height, 5),
                              round((x1 - x0) / width, 5), round((y1 - y0) / height, 5)],
                "text": "", "confidence_ocr": None, "lines": [],
            })
        return regions

    def _ocr_region(self, image: np.ndarray, region: dict) -> tuple[str, float]:
        """Crop the region, upscale small crops, OCR it."""
        x, y, w, h = [int(round(v)) for v in region["bbox"]]
        pad = int(0.06 * max(w, h))
        ih, iw = image.shape[:2]
        y0, y1 = max(0, y - pad), min(ih, y + h + pad)
        x0, x1 = max(0, x - pad), min(iw, x + w + pad)
        crop = image[y0:y1, x0:x1]
        if crop.shape[0] < 20 or crop.shape[1] < 40:
            return "", 0.0
        scale = max(1.0, min(3.0, 160.0 / max(1, crop.shape[0])))
        if scale > 1.05:
            crop = cv2.resize(crop, (int(crop.shape[1] * scale), int(crop.shape[0] * scale)),
                              interpolation=cv2.INTER_LANCZOS4)
        try:
            res, _ = self._ocr(crop)
        except Exception:
            return "", 0.0
        if not res:
            return "", 0.0
        texts, confs = [], []
        for _, text, conf in res:
            texts.append(_norm(str(text)))
            confs.append(float(conf))
        return " | ".join(texts), (sum(confs) / len(confs) if confs else 0.0)

    @staticmethod
    def _assign_lines_to_regions(lines, regions) -> None:
        for region in regions:
            rbox = region["bbox"]
            best, best_iou = None, 0.12
            for line in lines:
                score = _iou(rbox, line["bbox"])
                if score > best_iou:
                    best, best_iou = line, score
            if best is not None:
                region["lines"].append(best["text"])
                region["confidence_ocr"] = best["confidence"]

    @staticmethod
    def _split_words(lines) -> list[dict]:
        """Approximate word boxes by slicing each line box proportionally."""
        words = []
        for line in lines:
            text = line["text"].strip()
            if not text:
                continue
            x, y, w, h = line["bbox"]
            tokens = text.split()
            if len(tokens) <= 1:
                words.append({"text": text, "confidence": line["confidence"],
                              "bbox": [x, y, w, h]})
                continue
            total_chars = sum(len(t) for t in tokens) + (len(tokens) - 1)  # + spaces
            cursor = 0.0
            for tok in tokens:
                frac = len(tok) / total_chars
                ww = w * frac
                words.append({"text": tok, "confidence": line["confidence"],
                              "bbox": [round(x + cursor, 1), round(y, 1), round(ww, 1), round(h, 1)]})
                cursor += ww + (w / total_chars)  # advance past the space
        return words

    # ------------------------------------------------------------------
    # field extraction
    # ------------------------------------------------------------------
    def _extract_fields(self, text: str, regions: list[dict], ocr_lines: list[dict]) -> dict:
        lines = [l for l in text.splitlines() if l.strip()]
        flat = _norm(text)
        flat_ns = re.sub(r"\s+", "", flat)  # space-stripped variant for tight OCR

        fields: dict[str, Any] = {}

        # --- MRP: keyword line (value may sit on the same or a later line) ---
        mrp = self._extract_mrp(lines, regions)
        fields["mrp"] = self._field("mrp", mrp, 0.88 if mrp else 0.0,
                                    self._region_evidence(regions, "mrp"))

        # --- net quantity: prefer a labelled line, then any number+unit -----
        nq = self._extract_net_qty(lines, regions)
        fields["net_quantity"] = self._field("net_quantity", nq, 0.85 if nq else 0.0,
                                             self._region_evidence(regions, "net_quantity"))

        # --- dates ----------------------------------------------------------
        mfg, exp = self._dates(lines, regions)
        fields["mfg_date"] = self._field("mfg_date", mfg, 0.85 if mfg else 0.0,
                                         self._region_evidence(regions, "mfd_date"))
        fields["use_before"] = self._field("use_before", exp, 0.85 if exp else 0.0,
                                           self._region_evidence(regions, "exp_date"))

        # --- batch ----------------------------------------------------------
        batch = self._extract_batch(lines)
        fields["batch_number"] = self._field("batch_number", batch, 0.8 if batch else 0.0, "")

        # --- consumer care ---------------------------------------------------
        care = self._consumer_care(flat)
        fields["customer_care"] = self._field("customer_care", care, 0.85 if care else 0.0,
                                              self._region_evidence(regions, "consumer_care"))

        # --- manufacturer / address --------------------------------------------
        mfr, addr = self._manufacturer_address(lines)
        fields["manufacturer"] = self._field("manufacturer", mfr, 0.75 if mfr else 0.0,
                                             self._region_evidence(regions, "mfr_address"))
        fields["brand_owner"] = self._field("brand_owner", mfr, 0.6 if mfr else 0.0, "")
        fields["address"] = self._field("address", addr, 0.7 if addr else 0.0,
                                        self._region_evidence(regions, "mfr_address"))

        # --- country of origin --------------------------------------------------
        origin = self._extract_origin(flat, flat_ns)
        fields["country_of_origin"] = self._field("country_of_origin", origin, 0.8 if origin else 0.0,
                                                  self._region_evidence(regions, "origin"))

        # --- commodity name (largest descriptive text block) -------------------
        fields["commodity_name"] = self._field("commodity_name", self._commodity_name(ocr_lines), 0.65, "")
        return fields

    # ------------------------------------------------------------------
    # individual extractors
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_mrp(lines: list[str], regions) -> str:
        def price_from(text: str) -> str:
            # never read a price off a date/quantity line
            if _RE_DATE_STRONG.search(text) or _RE_DATE_WEAK.search(text):
                return ""
            if _QTY_HINT.search(text) or _RE_NET_QTY.search(text):
                return ""
            m = _RE_PRICE_2DP.search(text) or _RE_PRICE_1DP.search(text)
            return m.group(1) if m else ""

        # 1. detector region first (crop OCR is focused on the price)
        for r in regions:
            if r["class"] == "mrp":
                val = price_from(r.get("text", ""))
                if val:
                    return f"Rs. {val}"
        # 2. keyword line, value on same line or the next three lines
        for i, line in enumerate(lines):
            if _RE_MRP_LINE.search(line):
                for cand in (line, *lines[i + 1:i + 4]):
                    val = price_from(cand)
                    if val:
                        return f"Rs. {val}"
                # integer MRP directly after the keyword, e.g. "MRP: 159"
                m = _RE_MRP_INT.search(line)
                if m:
                    return f"Rs. {m.group(1)}"
        # 3. last resort: a standalone decimal price
        for line in lines:
            val = price_from(line)
            if val and float(val) >= 10:
                return f"Rs. {val}"
        return ""

    @staticmethod
    def _extract_net_qty(lines: list[str], regions) -> str:
        def qty_from(text: str) -> str:
            m = _RE_NET_QTY.search(text)
            if not m:
                return ""
            num, unit = m.group(1).replace(",", "."), m.group(2).lower()
            if unit == "l" and "." in num:
                num = num.rstrip("0").rstrip(".")
            return f"{num} {unit}"

        for r in regions:
            if r["class"] == "net_quantity":
                v = qty_from(r.get("text", ""))
                if v:
                    return v
        for line in lines:
            if _QTY_HINT.search(line):
                v = qty_from(line)
                if v:
                    return v
        for line in lines:
            v = qty_from(line)
            if v:
                return v
        return ""

    @staticmethod
    def _extract_batch(lines: list[str]) -> str:
        # label at/near the start of a line, followed by a compact code
        for i, line in enumerate(lines):
            m = re.match(r"\s*(?:batch|lot)\s*(?:no\.?|number|#)?\s*[:.#]?\s*([A-Za-z0-9\-/]{4,20})",
                         line, re.I)
            if m:
                val = m.group(1).strip("-. ")
                if sum(c.isdigit() for c in val) >= 1 and val.upper() != val.lower():
                    return val
                if sum(c.isdigit() for c in val) >= 2:
                    return val
            # label alone on a line, code on the next line
            if re.fullmatch(r"\s*(batch|lot)\s*(no\.?|number|#)?\s*[:.]?\s*", line, re.I) \
                    and i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                if re.fullmatch(r"[A-Za-z0-9\-/]{4,20}", nxt) and sum(c.isdigit() for c in nxt) >= 1:
                    return nxt
        return ""

    @staticmethod
    def _extract_origin(flat: str, flat_ns: str) -> str:
        for text in (flat, flat_ns):
            m = _RE_ORIGIN.search(text)
            if m:
                val = m.group(1).strip(" .,:;-'")
                if val.lower() in {"people", "peoples"} and "china" in text.lower():
                    val = "People's Republic of China"
                if len(val) >= 3:
                    return val.title() if val.isupper() else val
        return ""

    @staticmethod
    def _commodity_name(ocr_lines: list[dict]) -> str:
        """Largest-font line that reads like a product name (uses OCR bbox height)."""
        noise = re.compile(r"country\s*of\s*origin|made\s*in|inclusive|taxes|price|"
                           r"instructions?|warning|caution|directions?|ingredients?|"
                           r"nutrition|storage|use\s*only|not\s*depict|contents|packaging|"
                           r"registered|trademark|autorit|licen|www\.|\.com\b|\.in\b|\.net\b|"
                           r"scan\s*to|know\s*more|bar\s*code|qr\s*code|\bbatch\b|\blot\b|"
                           r"\brs\.?\b|\brd\.?\b|\bst\.?\b|\bno\.\s*\d|\d{3,}", re.I)

        def despace(text: str) -> str:
            # "PLADHESIVEHOOK5PCSSET" -> "PLADHESIVE HOOK 5 PCSSET"
            t = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
            t = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", t)
            return re.sub(r"\s+", " ", t).strip()

        candidates = []
        for l in ocr_lines:
            line = l["text"].strip().lstrip(":=>-–— ").strip()
            spaced = despace(line)
            words = spaced.split()
            if not (2 <= len(words) <= 9):
                continue
            if max((len(w.strip("(),.:[]")) for w in words), default=0) < 5:
                continue  # skip field labels like "Regn. No."
            if _CARE_HINT.search(line) or _ADDR_HINT.search(line) or _RE_EMAIL.search(line):
                continue
            if _RE_MRP_LINE.search(line) or _QTY_HINT.search(line) or _MFG_HINT.search(line):
                continue
            if _EXP_HINT.search(line) or _RE_BATCH.search(line) or noise.search(line):
                continue
            if line.endswith(":") or line.endswith("="):
                continue
            alpha = sum(c.isalpha() for c in line)
            if alpha / max(len(line), 1) < 0.6:
                continue
            candidates.append((l["bbox"][3], alpha, -l["bbox"][1], spaced))
        if not candidates:
            return ""
        # tallest text wins; tie-break: more letters, then higher on the label
        candidates.sort(reverse=True)
        return candidates[0][3]

    @staticmethod
    def _field(key, value, confidence, evidence):
        return {"key": key, "value": value, "confidence": round(confidence, 3),
                "evidence": evidence}

    @staticmethod
    def _region_evidence(regions, cls) -> str:
        for r in regions:
            if r["class"] == cls and (r.get("text") or r.get("lines")):
                return r.get("text") or " | ".join(r.get("lines", []))
        return ""

    def _dates(self, lines: list[str], regions) -> tuple[str, str]:
        """Pair dates with hints; fall back to earliest=manufacture, latest=use-by."""

        def valid(date: str) -> bool:
            """Reject impossible dates like 92/2012 (month 92) from licence numbers."""
            nums = re.findall(r"\d+", date)
            if len(nums) == 3:  # dd mm yyyy
                d, m = int(nums[0]), int(nums[1])
                return 1 <= d <= 31 and 1 <= m <= 12
            if len(nums) == 2:  # mm yyyy or mm-yyyy
                return 1 <= int(nums[0]) <= 12
            return bool(re.search(r"[A-Za-z]{3,9}", date))  # "July 2026"

        dated = []  # (line_index, date_string)
        for i, line in enumerate(lines):
            if _RE_REGN_NOISE.search(line):
                continue  # licence/registration numbers masquerade as dates
            if _RE_PHONE.search(line) or _RE_EMAIL.search(line):
                continue  # phone numbers contain date-like digit runs
            m = _RE_DATE_STRONG.search(line) or _RE_DATE_WEAK.search(line)
            if m and valid(m.group(1)):
                dated.append((i, m.group(1).strip()))

        mfg = exp = ""
        # 1. detector-labelled regions
        for r in regions:
            if r["class"] == "mfd_date" and not mfg:
                m = (_RE_DATE_STRONG.search(r.get("text", "")) or _RE_DATE_WEAK.search(r.get("text", "")))
                if m and valid(m.group(1)):
                    mfg = m.group(1).strip()
            if r["class"] == "exp_date" and not exp:
                m = (_RE_DATE_STRONG.search(r.get("text", "")) or _RE_DATE_WEAK.search(r.get("text", "")))
                if m and valid(m.group(1)):
                    exp = m.group(1).strip()

        # 2. hint words on the same or a neighbouring line
        for i, date in dated:
            window = " ".join(lines[max(0, i - 1):i + 2])
            if not mfg and _MFG_HINT.search(window):
                mfg = date
            elif not exp and _EXP_HINT.search(window):
                exp = date

        # 3. fallback: exactly two strong dates -> earlier mfg, later expiry
        if not mfg and not exp and len(dated) >= 2:
            uniq = list(dict.fromkeys(d for _, d in dated))
            if len(uniq) >= 2:
                mfg, exp = uniq[0], uniq[-1]
        if not mfg and not exp and len(dated) == 1:
            mfg = dated[0][1]
        return mfg, exp

    def _consumer_care(self, flat: str) -> str:
        """Look only at consumer-care lines so licence numbers aren't read as phones."""
        care_lines = [l for l in flat.splitlines()
                      if _CARE_HINT.search(l) or _RE_EMAIL.search(l)]
        scope = "\n".join(care_lines) if care_lines else flat
        emails = _RE_EMAIL.findall(scope)
        phones = [p for p in _RE_PHONE.findall(scope) if 7 <= len(re.sub(r"\D", "", p)) <= 14]
        if emails:
            return emails[0]
        return phones[0] if phones else ""

    def _manufacturer_address(self, lines: list[str]) -> tuple[str, str]:
        # manufacturer: "manufactured/marketed/packed ... by: <company>"
        generic = re.compile(r"^(product|products|the|and|for|by|marketed|manufactured|packed)$", re.I)
        by_candidates = []
        for line in lines:
            m = re.search(r"(?:mfd|mfg|manufactur\w*|mktd|marketed|packed)[^A-Za-z]{0,12}?"
                          r"by\s*[:\-.]?\s*(.+)", line, re.I)
            if m:
                name = re.split(r"[,;]|\bRegd\b|\bOffice\b|\bPlot\b|\bFloor\b|\bContact\b|\bAddress\b|"
                                r"\bNo\.|\bR\.?S\.?\s*No|\bLic\b|\bCIN\b|\bGST\b|\bRegn\b",
                                m.group(1))[0].strip(" :.-")
                if len(name) >= 6 and not generic.match(name) and not _CARE_HINT.search(name):
                    by_candidates.append(name)
        mfr = ""
        for cand in by_candidates:  # prefer one that names a company
            if _COMPANY_SUFFIX.search(cand):
                mfr = cand
                break
        if not mfr and by_candidates:
            mfr = by_candidates[0]
        # fallback: any line carrying a company suffix
        if not mfr:
            for line in lines:
                if _COMPANY_SUFFIX.search(line) and 10 < len(line) < 90 \
                        and not _CARE_HINT.search(line) and not generic.match(line) \
                        and not re.search(r"\bno\.?\s*$", line, re.I):
                    mfr = line.strip(" ,.:-")
                    break

        # address: line with a 6-digit PIN, skipping registration/licence numbers
        addr = ""
        best = None
        for i, line in enumerate(lines):
            if _RE_REGN_NOISE.search(line):
                continue
            if _RE_PIN.search(line) and (best is None or sum(c.isalpha() for c in line) > best[0]):
                best = (sum(c.isalpha() for c in line), i, line)
        if best is not None:
            _, i, line = best
            chunk = [line]
            if i + 1 < len(lines) and len(lines[i + 1]) < 60 \
                    and _ADDR_HINT.search(lines[i + 1]) and not _RE_EMAIL.search(lines[i + 1]):
                chunk.append(lines[i + 1])
            addr = " ".join(chunk).strip()
        if not addr:
            for line in lines:
                if _ADDR_HINT.search(line) and len(line) > 25 and not _COMPANY_SUFFIX.search(line):
                    addr = line.strip()
                    break
        return mfr, addr

    @staticmethod
    def _compliance(fields, lines) -> dict:
        missing, needs_review = [], []
        for key, spec in fields.items():
            value = (spec.get("value") or "").strip()
            if not value:
                missing.append(key)
            elif spec.get("confidence", 0) < 0.7:
                needs_review.append(key)
        return {"missing": missing, "needs_review": needs_review}

    @staticmethod
    def _barcode_payload(regions, lines) -> list:
        out = []
        for r in regions:
            if r["class"] == "barcode":
                digits = re.sub(r"\D", "", r.get("text", "") or "")
                if digits:
                    out.append({"value": digits, "source": "region_ocr",
                                "confidence": r.get("confidence_ocr") or r["confidence"]})
        return out

    # ------------------------------------------------------------------
    # annotated evidence image
    # ------------------------------------------------------------------
    @staticmethod
    def _annotated_data_uri(image: np.ndarray, lines, regions) -> Optional[str]:
        try:
            canvas = image.copy()
            max_side = 1100
            if max(canvas.shape[:2]) > max_side:
                scale = max_side / max(canvas.shape[:2])
                canvas = cv2.resize(canvas, (int(canvas.shape[1] * scale), int(canvas.shape[0] * scale)),
                                    interpolation=cv2.INTER_AREA)
                sx = scale
            else:
                sx = 1.0
            palette = {"mrp": (220, 38, 38), "net_quantity": (234, 88, 12),
                       "mfd_date": (22, 101, 192), "exp_date": (22, 101, 192),
                       "consumer_care": (5, 122, 85), "mfr_address": (124, 58, 237),
                       "origin": (190, 24, 93), "barcode": (75, 85, 99),
                       "label": (148, 163, 184), "package": (148, 163, 184)}
            for l in lines:  # green word boxes
                x, y, w, h = [int(round(v * sx)) for v in l["bbox"]]
                cv2.rectangle(canvas, (x, y), (x + w, y + h), (16, 185, 129), 1)
            for r in regions:  # coloured region boxes with class labels
                x, y, w, h = [int(round(v * sx)) for v in r["bbox"]]
                color = palette.get(r["class"], (234, 179, 8))
                cv2.rectangle(canvas, (x, y), (x + w, y + h), color, 3)
                label = r["class"].replace("_", " ")
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                ty = max(0, y - th - 6)
                cv2.rectangle(canvas, (x, ty), (x + tw + 8, ty + th + 6), color, -1)
                cv2.putText(canvas, label, (x + 4, ty + th + 1),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            ok, buf = cv2.imencode(".jpg", cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR),
                                   [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ok:
                return None
            return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()
        except Exception as exc:
            print(f"[pipeline] annotation failed: {exc}")
            return None
