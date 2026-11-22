"""
AirGuard AI - Gatekeeper Engine (Module 6)
The Core Policy Enforcement Point (PEP) and Policy Decision Point (PDP)
for third-party AI travel agent requests on Delta Air Lines.
"""

import json
import secrets
from datetime import datetime
from database import get_db_connection
from agent_manager import AgentManager
from risk_engine import RiskEngine
from audit_logger import AuditLogger
from flight_service import FlightService

class GatekeeperEngine:
    @staticmethod
    def evaluate_request(
        agent_id: str,
        auth_token: str,
        customer_id: str,
        flight_id: str,
        seat_code: str = "14A",
        baggage_count: int = 0,
        requested_permissions: list = None
    ) -> dict:
        """
        Execute the 9-step Gatekeeper authorization workflow:
        1. Receive AI agent request.
        2. Verify agent identity.
        3. Check whether agent is active.
        4. Verify customer consent.
        5. Check requested permission.
        6. Check transaction budget.
        7. Perform risk assessment.
        8. Make authorization decision (APPROVED / REJECTED / PENDING HUMAN APPROVAL).
        9. Record decision in audit logs and persistent database.
        """
        if requested_permissions is None:
            requested_permissions = ["SEARCH_FLIGHTS", "BOOK_FLIGHTS", "SELECT_SEATS"]

        req_id = f"REQ-{datetime.now().strftime('%Y%m%d')}-{secrets.randbelow(9000)+1000}"

        # Fetch flight details
        flight = FlightService.get_flight_by_id(flight_id)
        if not flight:
            reason = f"Flight ID '{flight_id}' does not exist in Delta Air Lines schedule."
            GatekeeperEngine._record_request(
                req_id, agent_id, customer_id, flight_id, seat_code, baggage_count,
                0.0, requested_permissions, "REJECTED", 90, "HIGH RISK", reason
            )
            AuditLogger.log_event("GATEKEEPER_DECISION", agent_id, customer_id, "WARNING",
                                  f"Request {req_id} REJECTED: {reason}")
            return {
                "request_id": req_id,
                "status": "REJECTED",
                "risk_score": 90,
                "risk_level": "HIGH RISK",
                "decision_reason": reason,
                "transaction_id": None
            }

        # Calculate total cost
        total_amount = FlightService.calculate_total_cost(flight_id, seat_code, baggage_count)

        # Step 2, 3, 4: Verify agent identity, status, token and customer consent
        is_auth, auth_code, auth_msg, agent = AgentManager.authenticate_agent(agent_id, auth_token, customer_id)

        # If agent is revoked -> STRICT IMMEDIATE REJECTION
        if auth_code == "AGENT_REVOKED":
            reason = f"SECURITY PROTOCOL ENFORCED: Agent '{agent_id}' is PERMANENTLY REVOKED. All airline gateway access is terminated."
            GatekeeperEngine._record_request(
                req_id, agent_id, customer_id, flight_id, seat_code, baggage_count,
                total_amount, requested_permissions, "REJECTED", 100, "HIGH RISK", reason
            )
            AuditLogger.log_event("GATEKEEPER_DECISION", agent_id, customer_id, "ALERT",
                                  f"Request {req_id} REJECTED: {reason}")
            return {
                "request_id": req_id,
                "status": "REJECTED",
                "risk_score": 100,
                "risk_level": "HIGH RISK",
                "decision_reason": reason,
                "transaction_id": None
            }

        if not is_auth:
            reason = f"Authentication gate failed: {auth_msg} (Code: {auth_code})"
            GatekeeperEngine._record_request(
                req_id, agent_id, customer_id, flight_id, seat_code, baggage_count,
                total_amount, requested_permissions, "REJECTED", 85, "HIGH RISK", reason
            )
            AuditLogger.log_event("GATEKEEPER_DECISION", agent_id, customer_id, "WARNING",
                                  f"Request {req_id} REJECTED: {reason}")
            return {
                "request_id": req_id,
                "status": "REJECTED",
                "risk_score": 85,
                "risk_level": "HIGH RISK",
                "decision_reason": reason,
                "transaction_id": None
            }

        # Fetch Customer record
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        customer_row = cursor.fetchone()
        conn.close()
        customer = dict(customer_row) if customer_row else None

        # Step 5: Check requested permissions against granted permissions
        granted_permissions = AgentManager.get_agent_permissions(agent_id)
        missing_permissions = [p for p in requested_permissions if not granted_permissions.get(p, False)]

        if missing_permissions:
            reason = f"Permission denied: Agent '{agent['name']}' lacks customer authorization for {', '.join(missing_permissions)}."
            GatekeeperEngine._record_request(
                req_id, agent_id, customer_id, flight_id, seat_code, baggage_count,
                total_amount, requested_permissions, "REJECTED", 65, "MEDIUM RISK", reason
            )
            AuditLogger.log_event("GATEKEEPER_DECISION", agent_id, customer_id, "WARNING",
                                  f"Request {req_id} REJECTED: {reason}")
            return {
                "request_id": req_id,
                "status": "REJECTED",
                "risk_score": 65,
                "risk_level": "MEDIUM RISK",
                "decision_reason": reason,
                "transaction_id": None
            }

        # Step 6: Check transaction budget
        max_budget = customer.get("max_budget_per_transaction", 15000.0) if customer else 15000.0
        budget_exceeded = total_amount > max_budget

        # Step 7: Perform comprehensive risk assessment
        risk_score, risk_level, factors, recommendation = RiskEngine.assess_risk(
            agent=agent,
            customer=customer,
            flight=flight,
            requested_permissions=requested_permissions,
            granted_permissions=granted_permissions,
            total_amount=total_amount,
            baggage_count=baggage_count,
            seat_code=seat_code
        )

        # Step 8: Make Authorization Decision
        # Rules:
        # A. If budget exceeded:
        #    If amount exceeds by more than 50% -> REJECT
        #    If amount exceeds within 50% -> PENDING_HUMAN_APPROVAL
        # B. If risk == HIGH RISK -> PENDING_HUMAN_APPROVAL (or REJECT if critical)
        # C. If risk == MEDIUM RISK:
        #    If financial payment requested and near budget -> PENDING_HUMAN_APPROVAL
        #    Else APPROVED
        # D. If risk == LOW RISK -> APPROVED

        decision = "APPROVED"
        decision_reason = "All security checks passed. Agent verified, budget approved, valid permissions."

        if budget_exceeded:
            excess_ratio = total_amount / max_budget
            if excess_ratio > 1.6:
                decision = "REJECTED"
                decision_reason = f"Transaction amount (₹{total_amount:,.2f}) critically exceeds customer spending limit (₹{max_budget:,.2f}) by {(excess_ratio-1)*100:.0f}%."
            else:
                decision = "PENDING_HUMAN_APPROVAL"
                decision_reason = f"Budget Alert: Transaction (₹{total_amount:,.2f}) exceeds customer spending limit (₹{max_budget:,.2f}). Escalated to customer for review."
        elif risk_level == "HIGH RISK":
            decision = "PENDING_HUMAN_APPROVAL"
            decision_reason = f"High Risk Detected (Score {risk_score}/100): " + "; ".join([f["detail"] for f in factors[:2]])
        elif risk_level == "MEDIUM RISK" and "MAKE_PAYMENTS" in requested_permissions and total_amount > (0.85 * max_budget):
            decision = "PENDING_HUMAN_APPROVAL"
            decision_reason = f"Elevated Risk (Score {risk_score}/100): Transaction consumes >85% of budget with financial payment permission. Human verification requested."
        else:
            decision = "APPROVED"
            decision_reason = f"Authorized: Risk score {risk_score}/100 ({risk_level}). Identity, consent, permissions, and budget validated."

        # Step 9: Record decision in database and audit logs
        GatekeeperEngine._record_request(
            req_id, agent_id, customer_id, flight_id, seat_code, baggage_count,
            total_amount, requested_permissions, decision, risk_score, risk_level, decision_reason
        )

        txn_id = None
        if decision == "APPROVED":
            txn_id = GatekeeperEngine._create_transaction(req_id, agent_id, customer_id, total_amount, "SUCCESS")
            # Decrement seat inventory
            GatekeeperEngine._decrement_flight_seats(flight_id)
            AuditLogger.log_event("GATEKEEPER_DECISION", agent_id, customer_id, "INFO",
                                  f"Request {req_id} APPROVED. Transaction {txn_id} executed for ₹{total_amount:,.2f}.")
        elif decision == "PENDING_HUMAN_APPROVAL":
            AuditLogger.log_event("RISK_ALERT", agent_id, customer_id, "WARNING",
                                  f"Request {req_id} flagged for HUMAN APPROVAL: {decision_reason}")
        else:
            # REJECTED
            GatekeeperEngine._create_transaction(req_id, agent_id, customer_id, total_amount, "BLOCKED")
            AuditLogger.log_event("GATEKEEPER_DECISION", agent_id, customer_id, "WARNING",
                                  f"Request {req_id} REJECTED: {decision_reason}")

        return {
            "request_id": req_id,
            "status": decision,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "decision_reason": decision_reason,
            "risk_factors": factors,
            "total_amount": total_amount,
            "flight_number": flight["flight_number"],
            "source": flight["source_city"],
            "destination": flight["dest_city"],
            "transaction_id": txn_id
        }

    @staticmethod
    def resolve_human_approval(request_id: str, action: str, approval_comment: str = "", resolved_by: str = "Customer") -> dict:
        """
        Module 8: Human Approval.
        Process human administrator or customer override: 'APPROVED' or 'REJECTED'.
        """
        if action not in ["APPROVED", "REJECTED"]:
            raise ValueError("Action must be 'APPROVED' or 'REJECTED'.")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM booking_requests WHERE id = ?", (request_id,))
        req_row = cursor.fetchone()

        if not req_row:
            conn.close()
            raise ValueError(f"Booking request '{request_id}' not found.")

        req = dict(req_row)
        if req["status"] != "PENDING_HUMAN_APPROVAL":
            conn.close()
            raise ValueError(f"Request '{request_id}' is in status '{req['status']}', not pending approval.")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_status = action
        reason_update = f"{req['decision_reason']} | Human review by {resolved_by}: {action}. Comment: '{approval_comment}'"

        cursor.execute("""
        UPDATE booking_requests
        SET status = ?, approval_comment = ?, decision_reason = ?, resolved_at = ?
        WHERE id = ?
        """, (new_status, approval_comment, reason_update, now, request_id))
        conn.commit()

        txn_id = None
        if action == "APPROVED":
            txn_id = GatekeeperEngine._create_transaction(request_id, req["agent_id"], req["customer_id"], req["total_amount"], "SUCCESS")
            GatekeeperEngine._decrement_flight_seats(req["flight_id"])
            AuditLogger.log_event("HUMAN_APPROVAL", req["agent_id"], req["customer_id"], "INFO",
                                  f"Request {request_id} manually APPROVED by {resolved_by}. Txn: {txn_id}. Comment: {approval_comment}")
        else:
            GatekeeperEngine._create_transaction(request_id, req["agent_id"], req["customer_id"], req["total_amount"], "BLOCKED")
            AuditLogger.log_event("HUMAN_APPROVAL", req["agent_id"], req["customer_id"], "WARNING",
                                  f"Request {request_id} manually REJECTED by {resolved_by}. Comment: {approval_comment}")

        conn.close()
        return {
            "request_id": request_id,
            "status": new_status,
            "resolved_by": resolved_by,
            "approval_comment": approval_comment,
            "transaction_id": txn_id
        }

    @staticmethod
    def _record_request(req_id, agent_id, customer_id, flight_id, seat, baggage,
                        amount, requested_permissions, status, risk_score, risk_level, reason):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
            INSERT INTO booking_requests (
                id, agent_id, customer_id, flight_id, seat_selected, baggage_count,
                total_amount, requested_permissions, status, risk_score, risk_level,
                decision_reason, created_at, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                req_id, agent_id, customer_id, flight_id, seat, baggage,
                amount, json.dumps(requested_permissions), status, risk_score, risk_level,
                reason, now, now if status != "PENDING_HUMAN_APPROVAL" else None
            ))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _create_transaction(booking_request_id, agent_id, customer_id, amount, status):
        txn_id = f"TXN-{secrets.randbelow(90000)+10000}"
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO transactions (id, booking_request_id, agent_id, customer_id, amount, currency, status, timestamp)
            VALUES (?, ?, ?, ?, ?, 'INR', ?, ?)
            """, (txn_id, booking_request_id, agent_id, customer_id, amount, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
        finally:
            conn.close()
        return txn_id

    @staticmethod
    def _decrement_flight_seats(flight_id):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE flights
            SET available_seats = MAX(0, available_seats - 1)
            WHERE id = ?
            """, (flight_id,))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_dashboard_metrics():
        """Retrieve aggregated KPI counts for Admin Dashboard."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM agents")
        total_agents = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM agents WHERE status = 'ACTIVE'")
        active_agents = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM agents WHERE status = 'REVOKED'")
        revoked_agents = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM booking_requests")
        total_requests = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM booking_requests WHERE status = 'APPROVED'")
        approved_requests = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM booking_requests WHERE status = 'REJECTED'")
        rejected_requests = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM booking_requests WHERE status = 'PENDING_HUMAN_APPROVAL'")
        pending_approvals = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE severity IN ('WARNING', 'CRITICAL', 'ALERT')")
        security_alerts = cursor.fetchone()[0]

        conn.close()

        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "revoked_agents": revoked_agents,
            "total_requests": total_requests,
            "approved_requests": approved_requests,
            "rejected_requests": rejected_requests,
            "pending_approvals": pending_approvals,
            "security_alerts": security_alerts
        }

    @staticmethod
    def get_all_booking_requests(status_filter: str = None):
        """Fetch all booking requests with customer, agent and flight metadata."""
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
        SELECT r.*, a.name as agent_name, c.name as customer_name,
               f.flight_number, f.source_city, f.dest_city, f.airline_name
        FROM booking_requests r
        LEFT JOIN agents a ON r.agent_id = a.id
        LEFT JOIN customers c ON r.customer_id = c.id
        LEFT JOIN flights f ON r.flight_id = f.id
        WHERE 1=1
        """
        params = []
        if status_filter and status_filter != "ALL":
            query += " AND r.status = ?"
            params.append(status_filter)

        query += " ORDER BY r.created_at DESC"
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
