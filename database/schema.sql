-- Metrik SIH26036 production data model (PostgreSQL)
CREATE TABLE IF NOT EXISTS instruments (
  id VARCHAR(32) PRIMARY KEY,
  instrument_type VARCHAR(32) NOT NULL CHECK (instrument_type IN ('weighing','measuring')),
  capacity VARCHAR(120) NOT NULL,
  manufacturer VARCHAR(180),
  model_number VARCHAR(120),
  serial_number VARCHAR(160) NOT NULL UNIQUE,
  installation_location VARCHAR(220),
  installation_address TEXT,
  owner_name VARCHAR(180) NOT NULL,
  owner_email VARCHAR(180),
  owner_phone VARCHAR(32),
  last_verification_date DATE,
  next_due_date DATE,
  validity_period_months INTEGER NOT NULL DEFAULT 12,
  verification_status VARCHAR(32) NOT NULL DEFAULT 'pending',
  assigned_lmo_id VARCHAR(64),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_instruments_due_date ON instruments(next_due_date);
CREATE INDEX IF NOT EXISTS idx_instruments_serial ON instruments(serial_number);
CREATE INDEX IF NOT EXISTS idx_instruments_status ON instruments(verification_status);
CREATE INDEX IF NOT EXISTS idx_instruments_assigned_lmo ON instruments(assigned_lmo_id);

CREATE TABLE IF NOT EXISTS verification_certificates (
  certificate_id VARCHAR(48) PRIMARY KEY,
  instrument_id VARCHAR(32) NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
  verification_date DATE NOT NULL,
  valid_until DATE NOT NULL,
  verified_by VARCHAR(120) NOT NULL,
  qr_payload TEXT NOT NULL,
  certificate_status VARCHAR(24) NOT NULL DEFAULT 'valid',
  issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS verification_alerts (
  id BIGSERIAL PRIMARY KEY,
  instrument_id VARCHAR(32) NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
  alert_type VARCHAR(32) NOT NULL CHECK (alert_type IN ('expiry_30_days','overdue')),
  recipient VARCHAR(180),
  sent_at TIMESTAMPTZ,
  status VARCHAR(24) NOT NULL DEFAULT 'pending',
  alert_date DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(instrument_id, alert_type, alert_date)
);
