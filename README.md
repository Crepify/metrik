# metrik

> **Online verification, digital certification and validity lifecycle management for weighing and measuring instruments.**

**Smart India Hackathon 2026**  
**Problem Statement:** SIH26036 — Development of an Online Verification System for Weighing and Measuring Instruments  
**Ministry:** Consumer Affairs, Food & Public Distribution  
**Department:** Department of Consumer Affairs (DoCA)  
**Theme:** Miscellaneous  
**Team:** 404 ERROR FOUND

---

## What metrik does

metrik digitises the lifecycle of verification and re-verification for weighing and measuring instruments used in transaction or protection.

```text
Instrument User Application
        ↓
LMO / GATC Allocation & Scheduling
        ↓
Mobile Field Verification + Digital Observations
        ↓
QR-enabled Digital Certificate
        ↓
Validity Tracking + Expiry Alert + Re-verification
```

The platform is decision-support and workflow-management software. Statutory verification and final approval remain with authorised Legal Metrology Officers (LMOs) and Government Approved Test Centres (GATCs).

---

## Current prototype features

### Instrument user workflow

- Online application for verification or re-verification
- Instrument photo upload, drag/drop and mobile camera support
- QR phone-to-PC instrument photo transfer
- Specification document / prior certificate attachment
- Instrument type, capacity/range, manufacturer, model and serial-number capture
- Installation site, district/PIN, owner and contact capture
- Last verification and next due-date fields
- OCR-assisted extraction from instrument photographs and serial plates

### FastAPI OCR integration

- Configured Render OCR backend: `https://metrix-1z5z.onrender.com`
- Backend health pre-warm via `/health`
- `POST /ocr` multipart upload using required field name `file`
- OCR text, word boxes, parsed fields, confidence and annotated-image handling
- Extracted field mapping for capacity, manufacturer, model and serial number
- Browser Tesseract fallback in Smart mode
- Client-side Render protection:
  - Large images / PNG files are resized to max **1200 px**
  - Optimized JPEG upload at quality **0.85**
  - Small non-PNG files under 300 KB are not re-encoded
  - Original evidence photo remains attached locally
- 120-second Render cold-start timeout and clear network/CORS/timeout messages

### Verification workflow

- Priority verification queue
- Expired and expiring instruments prioritised first
- LMO/GATC assignment workflow
- Visit scheduling date
- Mobile field-verification form
- Standard test value and observed instrument value recording
- Seal/stamp observation
- Instrument condition and field remarks
- Configurable validity period
- Digital verification result: verified / failed / needs review

### Digital certificate and public verification

- QR-enabled certificate ID generation
- Certificate issue date and validity date
- Certificate PDF export
- Certificate JSON export
- Public read-only QR verification page: `verify.html`
- Demo public verification via QR payload
- Production roadmap for server-signed QR payload and central certificate lookup

### Registry, dashboard and reports

- Searchable instrument registry and verification history
- Local prototype evidence repository
- Verification status badges: valid / expiring soon / expired / pending
- State dashboard for total records, pendency, expiry alerts and overdue instruments
- Application PDF export
- Editable Word-compatible DOC export
- JSON export
- QR certificate PDF export

### Role-based workflow demo

- Instrument User
- LMO
- GATC
- State Admin

The prototype role selector demonstrates workflow separation. Production deployment requires server-side authentication, role-based authorisation, audit trails and a central database.

### Demo seed data

- `data/demo-instruments.js` and `data/demo-instruments.json` contain **27 realistic India-specific instrument records**
- Distribution: **12 valid**, **5 expiring soon**, **5 overdue**, **5 pending verification**
- `database/schema.sql` contains PostgreSQL tables and indexes for instruments, certificates and alerts
- `scripts/seed_instruments.py` seeds PostgreSQL idempotently using `DATABASE_URL`
- `scripts/send_expiry_alerts.py` is a daily 9 AM alert-worker template; default mode logs demo alerts to console until an approved SMS/email provider is configured

---

## Run locally

```bash
cd legal-metrology-prototype
python3 server.py
```

Open:

```text
http://localhost:4173
```

For local FastAPI OCR configuration:

```bash
OCR_API_URL=https://metrix-1z5z.onrender.com python3 server.py
```

For Vercel deployment, `config.js` is preconfigured. The optional Vercel serverless endpoint `api/ocr-config.js` reads `OCR_API_URL` from environment variables after redeployment.

---

## Key SIH26036 requirement mapping

| SIH26036 requirement | metrik module |
|---|---|
| Stakeholder registration | Instrument User / LMO / GATC / State Admin role workflow |
| Verification/re-verification application | Online instrument application form |
| Scheduling and allocation | Priority queue, LMO/GATC assignment and visit date |
| Digital observations | Field-verification form with evidence and readings |
| QR digital certificate | Certificate ID, QR payload and public verification view |
| Validity tracking | Next due date, valid/expiring/expired status |
| Expiry reminders | Expiry-alert dashboard workflow; notification service is production roadmap |
| Dashboard and pendency | State verification dashboard and priority queue |
| Mobile field support | Phone camera, QR transfer and responsive field form |
| Search/retrieval | Instrument registry and certificate history |

---

## Regulatory references

- SIH26036 official problem statement: https://sih2026.vuce.in/ps/SIH26036
- Legal Metrology Act, 2009 — verification and stamping context
- Legal Metrology (General) Rules, 2011 — instrument specifications and verification procedures
- Department of Consumer Affairs Legal Metrology overview: https://consumeraffairs.gov.in/pages/legal-metrology-overview

> Validate instrument-specific verification periods, fees, certificate formats and checklists against the latest consolidated Central and State legal-metrology rules before deployment.

---

## Production roadmap

1. PostgreSQL central instrument/certificate repository
2. Secure SSO / MFA and server-side RBAC
3. Immutable audit log and certificate-signing service
4. SMS/email renewal reminders
5. Server-side QR authenticity endpoint
6. State/district workload allocation algorithm
7. Object storage for photographs/documents
8. Offline field sync for low-connectivity areas

---

## Disclaimer

This SIH prototype is a workflow and digital-certification solution. It does not replace statutory verification, testing, stamping or final decision-making by authorised LMOs or GATCs.
