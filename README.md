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

### 4. Explainable decision support

| Feature | What it does |
|---|---|
| **Compliance pre-screen score** | Combines missing declarations and context conditions into a transparent triage score. |
| **Rule-linked findings** | Every finding carries a reference label and a plain-language explanation. |
| **Pass / warning / gap / review states** | Avoids a simplistic compliant/non-compliant black-box result. |
| **Officer-ready case note** | Downloads a readable case summary with evidence text and findings. |
| **JSON export** | Exports structured declarations and rule-linked findings for later integration. |
| **Print view** | Provides a print-friendly findings view. |

### 5. Workflow and analytics screens

| Feature | What it does |
|---|---|
| **Review queue** | Demonstrates risk-based triage and sample case prioritisation. |
| **Rule library** | Makes the selected prototype rule baseline visible to reviewers. |
| **Field insights dashboard** | Demonstrates aggregate gap patterns and review-oriented metrics. |
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
Package image / Camera / Listing text
                ↓
      OCR + editable declaration text
                ↓
     Structured field extraction
                ↓
 Context-aware Legal Metrology rule checks
                ↓
 Score + evidence + human-review cues
                ↓
 Case note / JSON / queue / dashboard
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
- **OCR:** Tesseract.js loaded in-browser when available
- **Rule engine:** Transparent regex / rule-profile logic in the browser
- **Outputs:** Browser-generated text case note, JSON export and print view
- **Deployment:** Static web app; no backend required for the prototype

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
│   │   └── vendor/qrcode.js      # Local QR generator
│   ├── README.md
│   └── serve.sh
└── presentation/
    ├── metrikAI_SIH2026_Idea_Presentation.pptx
    └── README.md
```

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
