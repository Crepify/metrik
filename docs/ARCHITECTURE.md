# metrik — SIH26036 Architecture and Deployment Framework

## 1. Goal

metrik is an online verification and digital certification platform for weighing and measuring instruments. It supports instrument users, State LMOs, GATCs and State Admins through the lifecycle of application, allocation, field verification, QR certificate issue, validity monitoring and re-verification.

```text
Instrument User → Application → Scheduling → LMO/GATC Field Verification
→ Digital Certificate + QR → Validity Tracking → Expiry Alert → Re-verification
```

The system digitises workflow and evidence. It does not replace statutory verification by authorised LMOs/GATCs.

---

## 2. Prototype architecture

```text
[Instrument User Portal] [LMO Workspace] [GATC Workspace] [State Admin Dashboard]
                 ↓
[Browser Application]
  • Instrument photo/document upload
  • FastAPI OCR / browser OCR fallback
  • Verification application and field workflow
  • QR certificate presentation
  • Local registry and dashboard
                 ↓
[FastAPI OCR Service on Render]
  • /health pre-warm
  • /ocr multipart extraction
  • text, bounding boxes, parsed fields, compliance hints, annotated image
                 ↓
[Production data layer]
  PostgreSQL instrument records + applications + certificates + history + alerts
  Object storage for photographs and documents
```

---

## 3. Current prototype modules

| Module | Prototype behaviour |
|---|---|
| Instrument application | Captures photo, document reference, capacity, manufacturer, model, serial, owner, location and due dates |
| OCR | FastAPI `/ocr` with browser fallback; maps text to capacity/model/serial/manufacturer fields |
| Render protection | Client-side image downscale to max 1200px and JPEG quality 0.85 before OCR upload |
| Queue | Sorts expired/expiring and pending applications for verification scheduling |
| Allocation | Assigns application to LMO or GATC and records visit date |
| Field verification | Captures standard/observed value, seal status, condition and digital remarks |
| Certificate | Issues certificate ID, validity period and QR verification payload |
| Public verify page | Displays the certificate payload encoded in the QR for prototype demonstration |
| Registry | Stores local instrument records and verification history |
| Dashboard | Shows records, pending work, expiry alerts and overdue cases |

---

## 4. Production implementation requirements

### Data model

```text
Stakeholder
├── Instrument User
├── LMO
├── GATC
└── State Admin

Instrument
├── type, capacity, manufacturer, model, serial number
├── installation location and owner
├── evidence documents
└── validity status

Verification Application
├── verification / re-verification request
├── assigned LMO/GATC
├── scheduled visit
├── field observations
└── result

Certificate
├── certificate ID
├── issue / validity dates
├── QR signature
└── public verification state
```

### Security controls

- Server-side authentication and RBAC
- State/district scoped access controls
- Immutable audit log for applications, allocation, observations and certificate edits
- Server-generated certificate signature or HMAC/Ed25519 verification payload
- Object-storage access controls for photo/document evidence
- No client-side secret embedded in QR or frontend code

### Validity and alerts

- Store instrument-specific validity rules in a versioned policy table
- Calculate `next_due_date` from authorised verification date and applicable category
- Send configurable alerts at 30/15/7 days prior to due date
- Escalate expired certificates to the State Admin dashboard
- Validate exact validity periods against current Central and State rules before pilot

---

## 5. Deployment

### Frontend
- Static/Vercel web deployment
- `config.js` preconfigured with the Render OCR base URL
- `api/ocr-config.js` supports Vercel `OCR_API_URL` environment configuration

### OCR backend
- FastAPI service on Render
- `GET /health` for availability/Tesseract checks
- `POST /ocr` receives multipart field `file`
- Browser compresses large uploads before transmission due to low-CPU free-tier constraints

### Recommended production stack
- FastAPI service(s) with background verification/alert workers
- PostgreSQL for central registry
- S3-compatible object storage for evidence
- Redis/queue for expiry alerts and document jobs
- Transactional email/SMS provider for reminders
- Monitoring, backups and log retention

---

## 6. Pilot plan

1. Select one State/district and a small instrument category subset.
2. Configure approved verification checklist and validity policy table.
3. Import limited instrument registry data.
4. Conduct LMO/GATC field pilot with digital observations.
5. Issue QR certificates for pilot instruments.
6. Measure pendency, allocation time, expiry tracking and QR verification events.
7. Review legal, security and operational feedback before scale-up.
