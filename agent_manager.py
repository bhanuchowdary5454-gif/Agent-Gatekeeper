"""
AirGuard AI - Agent Management Module (Modules 2, 3 & 9)
Registration, Token Authentication, Lifecycle Management, and Revocation.
"""

import uuid
import secrets
from datetime import datetime
from database import get_db_connection, ALL_PERMISSIONS
from audit_logger import AuditLogger

class AgentManager:
    @staticmethod
    def generate_agent_id() -> str:
        """Generate a structured unique Agent ID (e.g., AGT-8421)."""
        short_num = secrets.randbelow(9000) + 1000
        return f"AGT-{short_num}"

    @staticmethod
    def generate_token(agent_name: str) -> str:
        """Generate a simulated secure API bearer token."""
        clean_name = "".join(c for c in agent_name.lower() if c.isalnum())[:8]
        entropy = secrets.token_hex(8)
        return f"agtok_{clean_name}_{entropy}"

    @staticmethod
    def register_agent(name: str, customer_id: str, developer_org: str,
                       initial_permissions: list = None, risk_baseline: str = "LOW") -> dict:
        """
        Register a new AI Agent with auto-generated ID, bearer token, and default permissions.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check customer exists
        cursor.execute("SELECT id, name FROM customers WHERE id = ?", (customer_id,))
        cust = cursor.fetchone()
        if not cust:
            conn.close()
            raise ValueError(f"Customer with ID '{customer_id}' does not exist.")

        agent_id = AgentManager.generate_agent_id()
        # Ensure unique ID
        while True:
            cursor.execute("SELECT id FROM agents WHERE id = ?", (agent_id,))
            if not cursor.fetchone():
                break
            agent_id = AgentManager.generate_agent_id()

        auth_token = AgentManager.generate_token(name)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        INSERT INTO agents (id, name, customer_id, developer_org, auth_token, status, risk_baseline, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?)
        """, (agent_id, name, customer_id, developer_org, auth_token, risk_baseline, now, now))

        # Initialize permissions
        if initial_permissions is None:
            # Default to basic search, view and booking
            initial_permissions = ["SEARCH_FLIGHTS", "VIEW_FLIGHT_DETAILS", "BOOK_FLIGHTS"]

        for perm_key, _ in ALL_PERMISSIONS:
            granted = 1 if perm_key in initial_permissions else 0
            cursor.execute("""
            INSERT INTO permissions (agent_id, permission_key, is_granted, granted_at)
            VALUES (?, ?, ?, ?)
            """, (agent_id, perm_key, granted, now))

        conn.commit()
        conn.close()

        AuditLogger.log_event(
            event_type="AGENT_REGISTRATION",
            agent_id=agent_id,
            customer_id=customer_id,
            severity="INFO",
            action_details=f"AI Agent '{name}' ({agent_id}) registered by customer {cust['name']} ({customer_id}). Developer: {developer_org}."
        )

        return {
            "id": agent_id,
            "name": name,
            "customer_id": customer_id,
            "developer_org": developer_org,
            "auth_token": auth_token,
            "status": "ACTIVE",
            "risk_baseline": risk_baseline
        }

    @staticmethod
    def authenticate_agent(agent_id: str, auth_token: str, customer_id: str = None) -> tuple:
        """
        Authenticate an agent based on Agent ID, token, status, and customer association.
        Returns: (is_authenticated: bool, error_code: str, error_message: str, agent_dict: dict)
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT a.id, a.name, a.customer_id, a.developer_org, a.auth_token, a.status, a.risk_baseline,
               c.name as customer_name, c.max_budget_per_transaction, c.daily_budget_limit
        FROM agents a
        JOIN customers c ON a.customer_id = c.id
        WHERE a.id = ?
        """, (agent_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            AuditLogger.log_event(
                event_type="AUTH_FAILURE",
                agent_id=agent_id,
                severity="WARNING",
                action_details=f"Authentication rejected: Agent ID '{agent_id}' not found."
            )
            return False, "AGENT_NOT_FOUND", f"Agent '{agent_id}' does not exist in the airline registry.", None

        agent = dict(row)

        # 1. Revocation check - HIGHEST PRIORITY
        if agent["status"] == "REVOKED":
            AuditLogger.log_event(
                event_type="AUTH_FAILURE",
                agent_id=agent_id,
                customer_id=agent["customer_id"],
                severity="ALERT",
                action_details=f"SECURITY ALERT: Revoked agent '{agent['name']}' ({agent_id}) attempted authentication. Access strictly blocked."
            )
            return False, "AGENT_REVOKED", f"SECURITY ALERT: Agent '{agent['name']}' ({agent_id}) has been PERMANENTLY REVOKED.", agent

        # 2. Inactive check
        if agent["status"] == "INACTIVE":
            AuditLogger.log_event(
                event_type="AUTH_FAILURE",
                agent_id=agent_id,
                customer_id=agent["customer_id"],
                severity="WARNING",
                action_details=f"Authentication blocked: Agent '{agent['name']}' ({agent_id}) is currently INACTIVE."
            )
            return False, "AGENT_INACTIVE", f"Agent '{agent['name']}' ({agent_id}) is currently INACTIVE. Reactivate agent to proceed.", agent

        # 3. Token verification
        if agent["auth_token"] != auth_token:
            AuditLogger.log_event(
                event_type="AUTH_FAILURE",
                agent_id=agent_id,
                customer_id=agent["customer_id"],
                severity="WARNING",
                action_details=f"Token mismatch for agent '{agent['name']}' ({agent_id})."
            )
            return False, "INVALID_TOKEN", "Invalid authentication bearer token provided for this AI agent.", agent

        # 4. Customer authorization check
        if customer_id and agent["customer_id"] != customer_id:
            AuditLogger.log_event(
                event_type="AUTH_FAILURE",
                agent_id=agent_id,
                customer_id=customer_id,
                severity="ALERT",
                action_details=f"Identity fraud: Agent '{agent_id}' authorized for {agent['customer_id']} attempted action for customer {customer_id}."
            )
            return False, "CUSTOMER_MISMATCH", f"Agent '{agent_id}' is not authorized to act on behalf of customer '{customer_id}'.", agent

        AuditLogger.log_event(
            event_type="AUTH_SUCCESS",
            agent_id=agent_id,
            customer_id=agent["customer_id"],
            severity="INFO",
            action_details=f"Agent '{agent['name']}' ({agent_id}) authenticated successfully."
        )

        return True, "AUTH_SUCCESS", "Authentication successful.", agent

    @staticmethod
    def revoke_agent(agent_id: str, reason: str, revoked_by: str = "Customer") -> bool:
        """
        Module 9: Agent Revocation.
        - Immediately deactivates agent (status = 'REVOKED').
        - Disables all permissions.
        - Generates revocation record.
        - Logs CRITICAL audit entry.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, customer_id, status FROM agents WHERE id = ?", (agent_id,))
        agent = cursor.fetchone()
        if not agent:
            conn.close()
            raise ValueError(f"Agent '{agent_id}' not found.")

        prev_status = agent["status"]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Update agent status
        cursor.execute("""
        UPDATE agents
        SET status = 'REVOKED', updated_at = ?
        WHERE id = ?
        """, (now, agent_id))

        # 2. Disable all permissions
        cursor.execute("""
        UPDATE permissions
        SET is_granted = 0, revoked_at = ?
        WHERE agent_id = ?
        """, (now, agent_id))

        # 3. Create revocation record
        cursor.execute("""
        INSERT INTO revocation_records (agent_id, customer_id, reason, revoked_by, previous_status, revoked_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (agent_id, agent["customer_id"], reason, revoked_by, prev_status, now))

        conn.commit()
        conn.close()

        AuditLogger.log_event(
            event_type="AGENT_REVOCATION",
            agent_id=agent_id,
            customer_id=agent["customer_id"],
            severity="CRITICAL",
            action_details=f"AGENT REVOKED: '{agent['name']}' ({agent_id}) revoked by {revoked_by}. Reason: '{reason}'. All permissions stripped."
        )

        return True

    @staticmethod
    def toggle_agent_status(agent_id: str, new_status: str) -> bool:
        """Toggle status between ACTIVE and INACTIVE (cannot activate a REVOKED agent)."""
        if new_status not in ["ACTIVE", "INACTIVE"]:
            raise ValueError("Only 'ACTIVE' and 'INACTIVE' are permitted via toggle.")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, status, customer_id FROM agents WHERE id = ?", (agent_id,))
        agent = cursor.fetchone()
        if not agent:
            conn.close()
            raise ValueError(f"Agent '{agent_id}' not found.")

        if agent["status"] == "REVOKED":
            conn.close()
            raise ValueError("Cannot reactivate a REVOKED agent. A revoked agent must remain permanently disabled.")

        cursor.execute("UPDATE agents SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_status, agent_id))
        conn.commit()
        conn.close()

        AuditLogger.log_event(
            event_type="AGENT_STATUS_CHANGE",
            agent_id=agent_id,
            customer_id=agent["customer_id"],
            severity="INFO",
            action_details=f"Agent '{agent['name']}' ({agent_id}) status updated to {new_status}."
        )
        return True

    @staticmethod
    def get_all_agents():
        """Retrieve list of all agents with customer metadata."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT a.id, a.name, a.customer_id, a.developer_org, a.auth_token, a.status,
               a.risk_baseline, a.created_at, a.updated_at, c.name as customer_name
        FROM agents a
        LEFT JOIN customers c ON a.customer_id = c.id
        ORDER BY a.created_at DESC
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_agent_permissions(agent_id: str) -> dict:
        """Get granular permission status map for a given agent."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT permission_key, is_granted, granted_at, revoked_at
        FROM permissions
        WHERE agent_id = ?
        """, (agent_id,))
        rows = cursor.fetchall()
        conn.close()
        return {r["permission_key"]: bool(r["is_granted"]) for r in rows}

    @staticmethod
    def update_agent_permission(agent_id: str, permission_key: str, is_granted: bool) -> bool:
        """Grant or revoke a specific permission for an agent."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT status, customer_id FROM agents WHERE id = ?", (agent_id,))
        agent = cursor.fetchone()
        if not agent:
            conn.close()
            raise ValueError(f"Agent '{agent_id}' not found.")

        if agent["status"] == "REVOKED" and is_granted:
            conn.close()
            raise ValueError("Cannot grant permissions to a REVOKED agent.")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO permissions (agent_id, permission_key, is_granted, granted_at, revoked_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(agent_id, permission_key) DO UPDATE SET
            is_granted = excluded.is_granted,
            granted_at = CASE WHEN excluded.is_granted = 1 THEN excluded.granted_at ELSE granted_at END,
            revoked_at = CASE WHEN excluded.is_granted = 0 THEN excluded.revoked_at ELSE revoked_at END
        """, (agent_id, permission_key, 1 if is_granted else 0, now if is_granted else None, now if not is_granted else None))

        conn.commit()
        conn.close()

        AuditLogger.log_event(
            event_type="PERMISSION_CHANGED",
            agent_id=agent_id,
            customer_id=agent["customer_id"],
            severity="INFO",
            action_details=f"Permission '{permission_key}' set to {is_granted} for Agent {agent_id}."
        )
        return True

    @staticmethod
    def get_revocation_records():
        """Fetch all revocation ledger records."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT r.id, r.agent_id, r.customer_id, r.reason, r.revoked_by, r.previous_status, r.revoked_at,
               a.name as agent_name, c.name as customer_name
        FROM revocation_records r
        LEFT JOIN agents a ON r.agent_id = a.id
        LEFT JOIN customers c ON r.customer_id = c.id
        ORDER BY r.revoked_at DESC
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
