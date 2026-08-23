# metrikAI — Software Architecture & Deployment Framework

## 1. Objective

metrikAI is an evidence-led inspection workflow for packaged commodities. It receives a label photo, product image or e-commerce listing; extracts declarations; applies a versioned Legal Metrology rule profile; produces explainable findings; and maintains inspection history for authorised review.

The design intentionally separates **automated pre-screening** from **final legal determination**.

---

## 2. Logical architecture

```text
┌────────────────────────────────────────────────────────────────┐
│  Capture channels                                               │
│  PC upload • mobile camera • QR phone transfer • listing text   │
└──────────────────────────────┬─────────────────────────────────┘
                               ↓
┌────────────────────────────────────────────────────────────────┐
│  Image / OCR / visual-quality layer                             │
│  OCR text • confidence • bounding boxes • resolution • proxy    │
│  font-height • declaration-location evidence                    │
└──────────────────────────────┬─────────────────────────────────┘
                               ↓
┌────────────────────────────────────────────────────────────────┐
│  Declaration extraction layer                                   │
│  Entity • address • commodity • quantity • MRP • date • care    │
│  importer • country of origin • listing context                 │
└──────────────────────────────┬─────────────────────────────────┘
                               ↓
┌────────────────────────────────────────────────────────────────┐
│  Versioned rule engine                                          │
│  Rule applicability • exceptions • severity • evidence links    │
│  Rules 3 / 6 / 6(10A) / 6(11) / 7 / 9 / 10 / 11–13 baseline    │
└──────────────────────────────┬─────────────────────────────────┘
                               ↓
┌────────────────────────────────────────────────────────────────┐
│  Officer workflow                                               │
│  Pre-screen score • review queue • repository • PDF/DOC/JSON    │
│  dashboard • audit trail • role-aware access                    │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Prototype implementation

| Layer | Current prototype implementation |
|---|---|
| Desktop UI | Responsive Vanilla HTML/CSS/JavaScript web application |
| Mobile capture | `capture="environment"` file inputs and a QR-linked mobile uploader |
| PC-to-phone transfer | Same-origin `server.py` API with random 15-minute transfer sessions |
| QR generation | Local vendored QR generator; no QR cloud service |
| OCR | Tesseract.js in the browser when available; extraction text remains editable |
| Visual-quality evidence | Image dimensions, OCR confidence, word bounding boxes and calibrated text-height proxy |
| Rule checks | Transparent client-side rule functions with individual status and evidence details |
| Repository | Browser-local inspection repository with search, retrieve and delete controls |
| Reports | PDF, editable Word-compatible DOC, text, print and JSON exports |
| Access demonstration | Local Inspector / Supervisor / Admin role view |

### Prototype data flow

1. A user captures or uploads an image.
2. The browser optionally runs OCR and returns text, confidence and word geometry.
3. The user can correct the text before analysis.
4. The rule engine evaluates declarations and context.
5. A pre-screen score, visual audit and rule-linked findings are rendered.
6. A real user scan is stored in the local repository and can be re-opened/exported.

---

## 4. Visual/readability and placement framework

A photograph alone does not always provide a legally reliable physical font measurement. metrikAI therefore uses a layered approach:

1. **Image-quality gate** — image dimensions and OCR confidence flag weak captures.
2. **OCR geometry** — word bounding boxes identify where detected declaration anchors occur.
3. **Calibrated text-height proxy** — the officer enters label width in millimetres and the current rule-profile threshold; the application estimates text height from image pixels.
4. **Human physical verification** — the app explicitly routes principal display panel, contrast, lettering, physical font size and package dimensions to authorised review.

This avoids making an unsupported automated enforcement decision from uncalibrated image pixels.

---

## 5. Production architecture recommendation

```text
Web / Mobile PWA
      ↓ HTTPS
API Gateway + Identity Provider (OIDC / SSO / MFA)
      ↓
Application services
├── OCR / Vision service
├── Rule-profile service
├── Report generation service
├── Inspection / repository service
├── Notification / workflow service
└── Audit-log service
      ↓
Data services
├── PostgreSQL / government-approved RDBMS
├── Object storage for original photographs and attachments
├── Search index for products, reports and entities
└── Immutable audit archive / SIEM integration
```

### Recommended production controls

- Government-approved identity provider, MFA and single sign-on.
- Role-based permissions: Inspector, Supervisor, Legal Reviewer, Administrator and Audit-only.
- Server-side rule-profile versioning with effective dates, exceptions and source references.
- Encrypted object storage for original evidence photographs.
- Database retention policy, audit log and chain-of-custody metadata.
- API rate limiting, malware/image validation and file-size limits.
- State/department tenancy or access segmentation where required.
- Offline-first PWA cache for field capture with delayed secure sync.
- Monitoring, backups, disaster recovery and accessibility testing.

---

## 6. Role model

| Role | Prototype behaviour | Production authorisation target |
|---|---|---|
| Inspector | Capture, edit OCR, analyze, create case, export own case | Create/update inspection, attach evidence, submit for review |
| Supervisor | Repository and dashboard access | Review/assign cases, approve corrections, monitor teams |
| Legal Reviewer | Modelled in governance flow | Validate rule applicability and enforcement recommendation |
| Administrator | Rule-library access in prototype role view | Manage users, rules, retention and integrations |
| Audit-only | Architecture target | Read-only access to immutable audit trail |

The prototype role selector demonstrates workflow separation only; it is **not a secure authentication system**. Production deployment must use OIDC/SSO, backend authorisation and server-side audit logging.

---

## 7. Report and evidence outputs

Each report should contain:

- Case ID, timestamps, user/role and applicable rule-profile version.
- Original attachment reference and image metadata.
- Extracted declarations and OCR confidence.
- Visual audit measurements and calibration inputs.
- Rule-linked findings, severity, evidence text and officer notes.
- Compliance score / triage status.
- Report export in PDF, editable document format and machine-readable JSON.

---

## 8. Current limitations and validation path

The current prototype does not replace commodity-specific law, physical net-quantity testing, legal opinion or final enforcement authority. The recommended validation path is:

1. Create an authorised, consolidated rule matrix.
2. Collect a representative labelled-image dataset across categories, scripts, materials and lighting conditions.
3. Calibrate visual/font proxy logic against physical measurement samples.
4. Pilot with enforcement officers and record false alerts / missed alerts.
5. Add secure authentication, central repository, audit trail and approved hosting.
6. Conduct legal, security, accessibility and privacy review before deployment.
