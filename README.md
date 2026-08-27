# metrikAI

> **AI-assisted, evidence-led compliance pre-screening for packaged commodities under the Legal Metrology (Packaged Commodities) Rules, 2011.**

**SIH 2026**  
**Problem Statement ID:** 26034  
**Theme:** Agriculture, FoodTech & Rural Development  
**Team:** 404 ERROR FOUND

---

## What metrikAI does

metrikAI helps enforcement teams, marketplaces and compliant sellers make a **fast first-pass review** of packaged-product labels and e-commerce listings.

It transforms a product image or pasted listing text into:

1. **Structured declarations** — product name, responsible entity, address, net quantity, MRP, manufacture date, consumer-care contact, importer and country of origin.
2. **Rule-linked checks** — clear pass / warning / gap / human-review statuses.
3. **Evidence-led outputs** — matched declaration text, selected rule context, compliance pre-screen score and exportable case notes.

The prototype is designed as **decision support**, not an automated final enforcement system.

---

## Feature list

### 1. Multi-channel evidence capture

| Feature | What it does |
|---|---|
| **Package-image upload** | Upload JPG, PNG or WEBP label images. |
| **Mobile camera capture** | Uses the device camera capture input on supported mobile browsers. |
| **Drag and drop** | Quick label upload from a desktop workflow. |
| **E-commerce listing mode** | Paste product-listing text without scraping a website. |
| **Phone-to-PC QR transfer** | The desktop creates a temporary QR code; a phone can scan it, capture a label photo and send it directly back to the open desktop workspace. |
| **Mobile camera-first uploader** | The QR landing page uses the phone camera capture input and also supports gallery selection. |
| **Automatic desktop handoff** | The desktop polls the temporary session and loads the received image into the standard OCR / analysis flow automatically. |
| **Synthetic demos** | Built-in declaration-rich, non-compliant, imported-product and multipack examples for a reliable SIH demo. |

### 2. OCR and declaration extraction

| Feature | What it does |
|---|---|
| **Optional in-browser OCR** | Uses Tesseract.js when online to read uploaded label images. |
| **Editable OCR text** | Officers can correct extracted text before running rule checks. |
| **Structured field extraction** | Detects product name, manufacturer/packer/importer, address, net quantity, MRP, date, consumer care and country of origin. |
| **Evidence traceability** | Displays the value that was matched or clearly marks it as not detected. |
| **Confidence-aware flow** | OCR confidence and image evidence are surfaced as review cues rather than hidden. |
| **Image-quality audit** | Records image dimensions, OCR confidence and declaration-bounding-box availability. |
| **Calibrated font-height proxy** | Combines OCR word geometry, label width in mm and a configurable threshold; it explicitly routes physical confirmation to an officer. |
| **Placement evidence** | Records declaration-anchor geometry for review of principal display panel placement. |

### 3. Legal Metrology pre-screening

| Feature | What it does |
|---|---|
| **Commodity name check** | Looks for a common/generic commodity declaration. |
| **Responsible-entity check** | Checks for manufacturer, packer, importer or relevant responsible entity information. |
| **Address check** | Flags a likely missing complete address near the responsible entity. |
| **Net-quantity check** | Detects quantity and common standard-unit formatting. |
| **MRP check** | Detects retail sale price in Indian currency and tax-inclusive wording. |
| **Unit-sale-price cue** | Flags when unit-sale-price review may be needed; handles multipack context as a review/exception path. |
| **Manufacture month/year check** | Applies to the on-pack workflow; listing mode keeps it separate for package review. |
| **Consumer-care check** | Detects phone/email and consumer-care information. |
| **Imported-product flow** | Adds importer and country-of-origin checks when an imported-product context is selected. |
| **E-commerce review cue** | Adds an origin-filter verification cue for imported e-commerce products. |
| **Scope awareness** | Supports retail, institutional/industrial and multipack context to reduce blind flags. |
| **Visual-review cue** | Clearly routes print legibility, contrast and principal-display assessment to human review. |
| **Font-size and placement proxy** | Performs an image/OCR-based pre-screen when calibration inputs are available; it never replaces physical verification. |

### 4. Explainable decision support

| Feature | What it does |
|---|---|
| **Compliance pre-screen score** | Combines missing declarations and context conditions into a transparent triage score. |
| **Rule-linked findings** | Every finding carries a reference label and a plain-language explanation. |
| **Pass / warning / gap / review states** | Avoids a simplistic compliant/non-compliant black-box result. |
| **PDF report** | Generates a downloadable PDF with findings and eligible attached image evidence. |
| **Editable DOC report** | Generates a Word-compatible editable document report. |
| **Officer-ready case note** | Downloads a readable text case summary with evidence text and findings. |
| **JSON export** | Exports structured declarations, visual audit and rule-linked findings for later integration. |
| **Print view** | Provides a print-friendly findings view. |

### 5. Workflow and analytics screens

| Feature | What it does |
|---|---|
| **Review queue** | Demonstrates risk-based triage and sample case prioritisation. |
| **Inspection repository** | Saves real user scans in the browser, with search, open, delete and report retrieval controls. |
| **Dynamic enforcement dashboard** | Aggregates locally saved cases, average score, priority cases and common declaration gaps. |
| **Rule library** | Makes the selected prototype rule baseline visible to reviewers. |
| **Role-aware prototype view** | Demonstrates Inspector, Supervisor and Admin workflow separation; production security is documented separately. |
| **Human-in-the-loop design** | Keeps low-confidence, visual and exception cases in an officer-review path. |

### 6. Trust, privacy and governance safeguards

- **No live product-page scraping** — listing mode accepts user-pasted text only.
- **Temporary phone transfer** — QR sessions expire after 15 minutes; image files are held only in the server's temporary directory for the active session.
- **Same-origin handoff** — the QR page and desktop workspace communicate through the same metrikAI server, without a third-party file-sharing service.
- **Synthetic demo labels** — the built-in demos do not use real brands or product data.
- **Rule-profile mindset** — the UI makes context, rule references and review conditions visible.
- **Human authorisation** — a final legal interpretation or enforcement action is never made by the prototype alone.
- **Version-ready approach** — a production system can store rules with source links, effective dates, exceptions and authorised approval history.

---

## Prototype workflow

```text
Package image / Camera / QR phone transfer / Listing text
                ↓
 OCR + editable declaration text + image-quality signals
                ↓
 Structured field extraction + font/placement evidence proxy
                ↓
 Context-aware Legal Metrology rule checks
                ↓
 Score + evidence + human-review cues
                ↓
 PDF / editable DOC / JSON / repository / dashboard
```

---

## Demo scenarios

| Scenario | What it demonstrates |
|---|---|
| **Gap demo** | Missing address, tax-inclusive MRP wording, unit-sale-price cue and consumer-care details. |
| **Declaration demo** | A declaration-rich synthetic product label. |
| **Imported product** | Importer, country of origin and e-commerce context. |
| **Multipack case** | Context-aware unit-sale-price exception/review handling. |

---

## Technology stack

- **Frontend:** Vanilla HTML, CSS and JavaScript
- **Primary OCR integration:** Configurable FastAPI OCR backend deployed on Render
- **OCR fallback:** Tesseract.js loaded in-browser when the FastAPI backend is not connected
- **Rule engine:** Transparent regex / rule-profile logic in the browser
- **Visual audit:** OCR bounding boxes, image resolution and calibrated font-height proxy
- **Reports:** Local jsPDF PDF export, editable Word-compatible DOC, text, JSON and print view
- **Repository:** Browser-local searchable inspection history for the prototype
- **Access view:** Local Inspector / Supervisor / Admin demo mode
- **Deployment:** `server.py` serves the app plus same-origin, short-lived phone-transfer API; Vercel can use `api/ocr-config.js` to expose the public FastAPI base URL configured in `OCR_API_URL`.

---

## FastAPI OCR backend integration

metrikAI now has a configurable **OCR backend** control in the top bar.

1. Click **OCR backend: connect**.
2. Enter the real Render base URL, for example `https://metrix-1z5z.onrender.com` — **no trailing slash**.
3. Click **Test /health**. The backend must return a healthy status and Tesseract availability.
4. Click **Save & use backend**.
5. Select **Smart: FastAPI if connected** or **FastAPI OCR backend**, upload a real label image, then click **Run OCR**.

The integration sends a `multipart/form-data` request to:

```text
POST <BACKEND_URL>/ocr
field name: file
```

It consumes the backend response for OCR text, word boxes, parsed fields, confidence, compliance hints and the optional `annotated_image`. When supplied, the annotated image is shown directly in the preview with a **View original** toggle.

### Deployment configuration

- **Vercel:** Set `OCR_API_URL` in Project → Settings → Environment Variables, enable Production/Preview/Development, then redeploy. `api/ocr-config.js` exposes the public base URL to the static frontend.
- **Local server:** set the environment variable before starting `server.py`:

```bash
OCR_API_URL=https://metrix-1z5z.onrender.com python3 server.py
```

- **Static-only deployment:** edit `config.js` and set `window.METRIK_OCR_API_URL`.

The app keeps a 120-second timeout for Render cold starts and surfaces backend-reported missing / needs-review fields rather than inventing values. If a browser console reports CORS, the Render backend must allow the deployed frontend origin.

---

## Run the prototype

```bash
cd legal-metrology-prototype
python3 server.py
```

Open:

```text
http://localhost:4173
```

For mobile testing, open the same address from the preview environment or host the static folder on a network-accessible server.

---

## Project structure

```text
.
├── README.md
├── legal-metrology-prototype/
│   ├── index.html                # Desktop inspection workspace
│   ├── phone.html                # QR-linked, mobile camera uploader
│   ├── server.py                 # Same-origin temporary transfer API
│   ├── assets/
│   │   ├── demo-compliant.svg
│   │   ├── demo-violation.svg
│   │   └── vendor/
│   │       ├── qrcode.js          # Local QR generator
│   │       └── jspdf.umd.min.js   # Local PDF generator
│   ├── README.md
│   └── serve.sh
├── docs/
│   └── ARCHITECTURE.md             # Architecture and deployment framework
└── presentation/
    ├── metrikAI_SIH2026_Idea_Presentation.pptx
    └── README.md
```

---

## Architecture and deployment documentation

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the logical architecture, current prototype implementation, visual/font-size validation framework, role model, production security controls and recommended deployment pattern.

---

## SIH presentation

The visual-first SIH deck is here:

`presentation/metrikAI_SIH2026_Idea_Presentation.pptx`

It keeps the supplied SIH template, uses six slides, and prioritises diagrams, workflow visuals, stakeholder mapping, a prototype dashboard visual and concise captions over dense paragraphs.

---

## Official-source starting points

- Department of Consumer Affairs — Legal Metrology overview:  
  https://consumeraffairs.gov.in/pages/legal-metrology-overview
- Consolidated Legal Metrology (Packaged Commodities) Rules, 2011 with amendments:  
  https://consumeraffairs.gov.in/public/upload/admin/cmsfiles/whatsnews/Book_on_Legal_Metrology_Packaged_Commodities_Rules,2011_with_all_amendments_whatsnews.pdf
- 2026 country-of-origin e-commerce filter notification:  
  https://consumeraffairs.gov.in/public/upload/files/2026.02.13%20PCR%201st%20COO%20Filter%20on%20e-commerce%20websites_1771231030.pdf

---

## Important disclaimer

metrikAI is a **prototype for explainable pre-screening**. It does not replace the current official text of the Rules, product-category requirements, physical net-quantity verification, officer judgement or authorised legal action. Any production use should be validated with Legal Metrology authorities and maintained through a version-controlled rule-governance process.
