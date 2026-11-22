"""
AirGuard AI - Audit Logger Module (Module 10)
Centralized, immutable security event logging for airline agent gatekeeping.
"""

from datetime import datetime
import pandas as pd
from database import get_db_connection

class AuditLogger:
    @staticmethod
    def log_event(event_type: str, agent_id: str = None, customer_id: str = None,
                  severity: str = "INFO", action_details: str = "",
                  ip_or_origin: str = "agent-runtime://gatekeeper-core"):
        """
        Record a tamper-evident audit log event into the database.
        """
        valid_severities = {"INFO", "WARNING", "CRITICAL", "ALERT"}
        if severity not in valid_severities:
            severity = "INFO"

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
            INSERT INTO audit_logs (event_type, agent_id, customer_id, severity, action_details, ip_or_origin, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (event_type, agent_id, customer_id, severity, action_details, ip_or_origin,
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
        except Exception as e:
            print(f"[AuditLogger Error] Failed to write audit log: {e}")
        finally:
            conn.close()

    @staticmethod
    def get_logs(limit: int = 100, event_type: str = None, severity: str = None,
                 agent_id: str = None, search_query: str = None) -> pd.DataFrame:
        """
        Retrieve audit logs with optional filtering and keyword search.
        """
        conn = get_db_connection()
        query = "SELECT id, timestamp, event_type, severity, agent_id, customer_id, action_details, ip_or_origin FROM audit_logs WHERE 1=1"
        params = []

        if event_type and event_type != "ALL":
            query += " AND event_type = ?"
            params.append(event_type)

        if severity and severity != "ALL":
            query += " AND severity = ?"
            params.append(severity)

        if agent_id and agent_id != "ALL":
            query += " AND agent_id = ?"
            params.append(agent_id)

        if search_query:
            query += " AND (action_details LIKE ? OR event_type LIKE ? OR agent_id LIKE ?)"
            wildcard = f"%{search_query}%"
            params.extend([wildcard, wildcard, wildcard])

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        try:
            df = pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            print(f"[AuditLogger Error] Query failed: {e}")
            df = pd.DataFrame()
        finally:
            conn.close()

        return df

    @staticmethod
    def get_recent_alerts(limit: int = 10):
        """Retrieve recent WARNING, CRITICAL and ALERT security events."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT timestamp, event_type, severity, agent_id, action_details
        FROM audit_logs
        WHERE severity IN ('WARNING', 'CRITICAL', 'ALERT')
        ORDER BY id DESC LIMIT ?
        """, (limit,))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows
