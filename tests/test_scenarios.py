"""
AirGuard AI - Comprehensive Automated Test Suite
Verifies all 8 core security and authorization scenarios required by the project specifications.
"""

import os
import sys
import unittest

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, get_db_connection
from agent_manager import AgentManager
from flight_service import FlightService
from gatekeeper import GatekeeperEngine
from risk_engine import RiskEngine
from ai_agent import AITravelAgentOrchestrator, TravelQueryParser

class TestAirGuardGatekeeper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reset and seed clean test database
        init_db(force_reseed=True)

    def test_01_authorized_agent_booking(self):
        """Scenario 1: Authorized agent with valid permissions and budget books a flight."""
        # AGT-7001 is active, owned by Aditi Sharma (limit 20,000), has all permissions
        agent = AgentManager.authenticate_agent("AGT-7001", "agtok_deltaflyer_live_7a8b9c", "CUST-101")[3]
        self.assertIsNotNone(agent)

        decision = GatekeeperEngine.evaluate_request(
            agent_id="AGT-7001",
            auth_token="agtok_deltaflyer_live_7a8b9c",
            customer_id="CUST-101",
            flight_id="FL-101", # DL-101 base price 6200
            seat_code="14A",
            baggage_count=1, # 1200 -> total 7400
            requested_permissions=["SEARCH_FLIGHTS", "BOOK_FLIGHTS", "SELECT_SEATS", "PURCHASE_BAGGAGE", "MAKE_PAYMENTS"]
        )

        self.assertEqual(decision["status"], "APPROVED")
        self.assertEqual(decision["risk_level"], "LOW RISK")
        self.assertLessEqual(decision["risk_score"], 35)
        self.assertIsNotNone(decision["transaction_id"])
        print("\n[PASS] Scenario 1: Authorized Agent Booking Succeeded.")

    def test_02_unauthorized_agent_attempt(self):
        """Scenario 2: Unauthorized agent (invalid ID or token) attempting a booking."""
        # Non-existent agent ID
        decision = GatekeeperEngine.evaluate_request(
            agent_id="AGT-INVALID-999",
            auth_token="fake_token_xyz",
            customer_id="CUST-101",
            flight_id="FL-101",
            requested_permissions=["BOOK_FLIGHTS"]
        )

        self.assertEqual(decision["status"], "REJECTED")
        self.assertIn("Authentication gate failed", decision["decision_reason"])
        print("[PASS] Scenario 2: Unauthorized Agent Request Successfully Rejected.")

    def test_03_revoked_agent_attempt(self):
        """Scenario 3: Revoked agent attempting a booking (Must never be allowed)."""
        # AGT-7004 is pre-seeded as REVOKED
        decision = GatekeeperEngine.evaluate_request(
            agent_id="AGT-7004",
            auth_token="agtok_roguetravel_revoked_99",
            customer_id="CUST-104",
            flight_id="FL-101",
            requested_permissions=["BOOK_FLIGHTS", "MAKE_PAYMENTS"]
        )

        self.assertEqual(decision["status"], "REJECTED")
        self.assertEqual(decision["risk_score"], 100)
        self.assertIn("REVOKED", decision["decision_reason"])
        print("[PASS] Scenario 3: Revoked Agent Attempt Permanently Blocked.")

    def test_04_agent_exceeding_customer_budget(self):
        """Scenario 4: Agent attempting a transaction exceeding customer spending limit."""
        # CUST-103 (Priya Nair) has max budget per transaction of ₹12,000.
        # Flight FL-112 (First class base 7300 + suite seat 4500 + 3 bags 3600 = ₹15,400)
        decision = GatekeeperEngine.evaluate_request(
            agent_id="AGT-7003",
            auth_token="agtok_skybreeze_dev_1a2b3c",
            customer_id="CUST-103",
            flight_id="FL-112",
            seat_code="2A", # first class suite (+4500)
            baggage_count=3, # 3*1200 = 3600 -> total 7300+4500+3600 = 15,400 > 12,000
            requested_permissions=["SEARCH_FLIGHTS", "BOOK_FLIGHTS"]
        )

        self.assertIn(decision["status"], ["PENDING_HUMAN_APPROVAL", "REJECTED"])
        self.assertGreater(decision["risk_score"], 50)
        self.assertIn("exceeds", decision["decision_reason"].lower())
        print("[PASS] Scenario 4: Over-budget Booking Caught & Flagged/Rejected.")

    def test_05_agent_requesting_restricted_permissions(self):
        """Scenario 5: Agent requesting permissions that were not granted by customer."""
        # AGT-7002 does NOT have MAKE_PAYMENTS granted
        perms = AgentManager.get_agent_permissions("AGT-7002")
        self.assertFalse(perms.get("MAKE_PAYMENTS", False))

        decision = GatekeeperEngine.evaluate_request(
            agent_id="AGT-7002",
            auth_token="agtok_voyagebot_prod_4d5e6f",
            customer_id="CUST-102",
            flight_id="FL-105",
            requested_permissions=["BOOK_FLIGHTS", "MAKE_PAYMENTS"] # Requesting restricted payment
        )

        self.assertEqual(decision["status"], "REJECTED")
        self.assertIn("Permission denied", decision["decision_reason"])
        self.assertIn("MAKE_PAYMENTS", decision["decision_reason"])
        print("[PASS] Scenario 5: Restricted Permission Request Correctly Rejected.")

    def test_06_high_risk_transaction(self):
        """Scenario 6: High-risk transaction evaluation."""
        # High value ticket, multiple bags, ungranted permissions
        agent = AgentManager.get_all_agents()[0]
        customer = {"max_budget_per_transaction": 10000.0, "daily_budget_limit": 20000.0}
        flight = FlightService.get_flight_by_id("FL-112")

        score, level, factors, rec = RiskEngine.assess_risk(
            agent=agent,
            customer=customer,
            flight=flight,
            requested_permissions=["CANCEL_BOOKINGS", "MODIFY_BOOKINGS", "MAKE_PAYMENTS"],
            granted_permissions={"SEARCH_FLIGHTS": True},
            total_amount=28000.0,
            baggage_count=4,
            seat_code="2A"
        )

        self.assertEqual(level, "HIGH RISK")
        self.assertGreaterEqual(score, 70)
        print(f"[PASS] Scenario 6: High Risk Heuristics Successfully Triggered (Score: {score}/100, Level: {level}).")

    def test_07_human_approval_workflow(self):
        """Scenario 7: Request flagged for human approval is reviewed and approved."""
        # Create a pending request
        conn = get_db_connection()
        req_id = "REQ-TEST-HUMAN-001"
        conn.execute("""
        INSERT OR REPLACE INTO booking_requests (
            id, agent_id, customer_id, flight_id, seat_selected, baggage_count, total_amount,
            requested_permissions, status, risk_score, risk_level, decision_reason
        ) VALUES (?, 'AGT-7001', 'CUST-101', 'FL-101', '14A', 1, 7400.0, '["BOOK_FLIGHTS"]',
                 'PENDING_HUMAN_APPROVAL', 72, 'HIGH RISK', 'Escalated for test')
        """, (req_id,))
        conn.commit()
        conn.close()

        # Execute human approval
        res = GatekeeperEngine.resolve_human_approval(
            request_id=req_id,
            action="APPROVED",
            approval_comment="Approved after customer phone identity check",
            resolved_by="Security Supervisor"
        )

        self.assertEqual(res["status"], "APPROVED")
        self.assertIsNotNone(res["transaction_id"])

        # Verify DB updated
        conn = get_db_connection()
        row = conn.execute("SELECT status, approval_comment FROM booking_requests WHERE id = ?", (req_id,)).fetchone()
        conn.close()
        self.assertEqual(row["status"], "APPROVED")
        self.assertIn("Approved after customer phone identity check", row["approval_comment"])
        print("[PASS] Scenario 7: Human Approval Workflow Succeeded.")

    def test_08_successful_agent_revocation(self):
        """Scenario 8: Immediate deactivation, stripping permissions, and rejecting future requests."""
        # Register a temporary test agent
        new_ag = AgentManager.register_agent(
            name="TemporaryBot",
            customer_id="CUST-101",
            developer_org="TestOrg",
            initial_permissions=["SEARCH_FLIGHTS", "BOOK_FLIGHTS"]
        )
        test_agent_id = new_ag["id"]

        # Verify initial active status & permissions
        perms_before = AgentManager.get_agent_permissions(test_agent_id)
        self.assertTrue(perms_before["BOOK_FLIGHTS"])

        # Execute Revocation
        revoked = AgentManager.revoke_agent(
            agent_id=test_agent_id,
            reason="Compromised credentials detected during unit testing",
            revoked_by="Automated Security Engine"
        )
        self.assertTrue(revoked)

        # Verify agent is REVOKED
        agent_after = [a for a in AgentManager.get_all_agents() if a["id"] == test_agent_id][0]
        self.assertEqual(agent_after["status"], "REVOKED")

        # Verify all permissions are disabled (0 / False)
        perms_after = AgentManager.get_agent_permissions(test_agent_id)
        for p_key, is_granted in perms_after.items():
            self.assertFalse(is_granted, f"Permission {p_key} should be disabled after revocation")

        # Verify subsequent request is REJECTED
        decision = GatekeeperEngine.evaluate_request(
            agent_id=test_agent_id,
            auth_token=new_ag["auth_token"],
            customer_id="CUST-101",
            flight_id="FL-101",
            requested_permissions=["BOOK_FLIGHTS"]
        )
        self.assertEqual(decision["status"], "REJECTED")
        self.assertEqual(decision["risk_score"], 100)
        self.assertIn("REVOKED", decision["decision_reason"])
        print("[PASS] Scenario 8: Agent Revocation Verified End-to-End.")

if __name__ == "__main__":
    unittest.main()
