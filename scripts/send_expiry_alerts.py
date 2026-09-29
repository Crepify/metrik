"""Daily expiry-alert worker for Metrik SIH26036.

Default mode is safe demo logging. For production, replace send_message() with an
approved transactional email/SMS provider and run at 09:00 local time.

Cron example (server time configured to Asia/Kolkata):
  0 9 * * * cd /app && /usr/local/bin/python scripts/send_expiry_alerts.py
"""
from __future__ import annotations
import os
from datetime import date

try:
    import psycopg
except ImportError as exc:
    raise SystemExit("Install psycopg first: pip install 'psycopg[binary]'") from exc


def send_message(recipient: str, subject: str, body: str) -> None:
    """Demo delivery adapter. Replace with approved email/SMS provider in production."""
    mode = os.getenv("ALERT_MODE", "console")
    if mode == "console":
        print(f"[DEMO ALERT] to={recipient} | subject={subject} | {body}")
        return
    # Production integration point intentionally explicit rather than silently sending mail.
    raise RuntimeError("Configure a production email/SMS provider before using non-console alerts")


def main() -> None:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL is required")

    today = date.today()
    with psycopg.connect(dsn) as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                SELECT * FROM instruments
                WHERE next_due_date IS NOT NULL
                  AND next_due_date >= CURRENT_DATE
                  AND next_due_date <= CURRENT_DATE + INTERVAL '30 days'
                ORDER BY next_due_date
                """
            )
            expiring = cur.fetchall()
            cur.execute(
                """
                SELECT * FROM instruments
                WHERE next_due_date IS NOT NULL
                  AND next_due_date < CURRENT_DATE
                ORDER BY next_due_date
                """
            )
            overdue = cur.fetchall()

            alerts = [("expiry_30_days", item) for item in expiring] + [("overdue", item) for item in overdue]
            sent = 0
            for alert_type, item in alerts:
                recipient = item.get("owner_email") or item.get("owner_phone")
                if not recipient:
                    continue
                cur.execute(
                    """
                    INSERT INTO verification_alerts (instrument_id, alert_type, recipient, status, alert_date)
                    VALUES (%s, %s, %s, 'pending', %s)
                    ON CONFLICT (instrument_id, alert_type, alert_date) DO NOTHING
                    RETURNING id
                    """,
                    (item["id"], alert_type, recipient, today),
                )
                alert = cur.fetchone()
                if not alert:
                    continue
                if alert_type == "overdue":
                    subject = "Verification OVERDUE"
                    body = f"Instrument {item['serial_number']} has been overdue since {item['next_due_date']}. Please apply for re-verification."
                else:
                    subject = "Verification expiring soon"
                    body = f"Instrument {item['serial_number']} is due for re-verification on {item['next_due_date']}."
                try:
                    send_message(recipient, subject, body)
                    cur.execute("UPDATE verification_alerts SET status='sent', sent_at=NOW() WHERE id=%s", (alert["id"],))
                    sent += 1
                except Exception as error:
                    cur.execute("UPDATE verification_alerts SET status='failed' WHERE id=%s", (alert["id"],))
                    print(f"[ALERT FAILED] instrument={item['id']} error={error}")
        conn.commit()
    print(f"Expiry alert run complete: {sent} alerts sent/logged")


if __name__ == "__main__":
    main()
