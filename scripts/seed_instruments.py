"""Seed SIH26036 Metrik demo instruments into PostgreSQL.

Usage:
  pip install 'psycopg[binary]'
  DATABASE_URL=postgresql://user:password@host:5432/metrik python scripts/seed_instruments.py

The script is idempotent: repeated runs update demo records by instrument id.
"""
from __future__ import annotations
import json
import os
from pathlib import Path

try:
    import psycopg
except ImportError as exc:
    raise SystemExit("Install psycopg first: pip install 'psycopg[binary]'") from exc

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "database" / "schema.sql"
DATA = ROOT / "data" / "demo-instruments.json"

SQL = """
INSERT INTO instruments (
  id, instrument_type, capacity, manufacturer, model_number, serial_number,
  installation_location, installation_address, owner_name, owner_email, owner_phone,
  last_verification_date, next_due_date, validity_period_months,
  verification_status, assigned_lmo_id, created_at
) VALUES (
  %(id)s, %(instrument_type)s, %(capacity)s, %(manufacturer)s, %(model_number)s,
  %(serial_number)s, %(installation_location)s, %(installation_address)s,
  %(owner_name)s, %(owner_email)s, %(owner_phone)s,
  %(last_verification_date)s, %(next_due_date)s, %(validity_period_months)s,
  %(verification_status)s, %(assigned_lmo_id)s, %(created_at)s
)
ON CONFLICT (id) DO UPDATE SET
  instrument_type = EXCLUDED.instrument_type,
  capacity = EXCLUDED.capacity,
  manufacturer = EXCLUDED.manufacturer,
  model_number = EXCLUDED.model_number,
  serial_number = EXCLUDED.serial_number,
  installation_location = EXCLUDED.installation_location,
  installation_address = EXCLUDED.installation_address,
  owner_name = EXCLUDED.owner_name,
  owner_email = EXCLUDED.owner_email,
  owner_phone = EXCLUDED.owner_phone,
  last_verification_date = EXCLUDED.last_verification_date,
  next_due_date = EXCLUDED.next_due_date,
  validity_period_months = EXCLUDED.validity_period_months,
  verification_status = EXCLUDED.verification_status,
  assigned_lmo_id = EXCLUDED.assigned_lmo_id,
  created_at = EXCLUDED.created_at,
  updated_at = NOW();
"""

def main() -> None:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL is required")
    instruments = json.loads(DATA.read_text(encoding="utf-8"))
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA.read_text(encoding="utf-8"))
            cur.executemany(SQL, instruments)
        conn.commit()
    summary = {}
    for item in instruments:
        summary[item["verification_status"]] = summary.get(item["verification_status"], 0) + 1
    print(f"Seeded {len(instruments)} instruments: {summary}")

if __name__ == "__main__":
    main()
