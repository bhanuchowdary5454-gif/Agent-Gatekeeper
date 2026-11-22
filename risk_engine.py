"""
AirGuard AI - Risk Assessment Engine (Module 7)
Multi-factor security risk evaluation, anomaly detection, and explainable scoring for AI agent actions.
"""

from typing import Dict, List, Tuple
from database import get_db_connection

class RiskEngine:
    @staticmethod
    def assess_risk(
        agent: dict,
        customer: dict,
        flight: dict,
        requested_permissions: list,
        granted_permissions: dict,
        total_amount: float,
        baggage_count: int = 0,
        seat_code: str = "14A"
    ) -> Tuple[int, str, List[Dict[str, any]], str]:
        """
        Evaluate composite risk for an AI agent's proposed airline action.

        Returns:
            (risk_score: int [0-100],
             risk_level: str ['LOW RISK', 'MEDIUM RISK', 'HIGH RISK'],
             factor_breakdown: list of dicts with factor, score, details,
             recommendation: str)
        """
        score = 0
        factors = []

        # --- 1. Agent Status & Baseline Evaluation ---
        if not agent:
            return 100, "HIGH RISK", [{"factor": "AGENT_UNKNOWN", "score": 100, "detail": "Agent does not exist in registry."}], "REJECT"

        status = agent.get("status", "ACTIVE")
        if status == "REVOKED":
            factors.append({
                "factor": "AGENT_REVOKED",
                "score": 100,
                "detail": "CRITICAL: Agent is REVOKED by customer or security administrator."
            })
            return 100, "HIGH RISK", factors, "REJECT"

        if status == "INACTIVE":
            score += 50
            factors.append({
                "factor": "AGENT_INACTIVE",
                "score": 50,
                "detail": "Agent is currently paused / inactive."
            })

        baseline = agent.get("risk_baseline", "LOW")
        if baseline == "MEDIUM":
            score += 10
            factors.append({
                "factor": "BASELINE_RISK_MEDIUM",
                "score": 10,
                "detail": "Agent has elevated historical risk profile."
            })
        elif baseline == "HIGH":
            score += 25
            factors.append({
                "factor": "BASELINE_RISK_HIGH",
                "score": 25,
                "detail": "Agent has high-risk developer or deployment baseline."
            })

        # --- 2. Permission Integrity Evaluation ---
        missing_perms = [p for p in requested_permissions if not granted_permissions.get(p, False)]
        if missing_perms:
            score += 35
            factors.append({
                "factor": "UNAUTHORIZED_PERMISSIONS",
                "score": 35,
                "detail": f"Agent requested unauthorized capabilities: {', '.join(missing_perms)}."
            })

        if "MAKE_PAYMENTS" in requested_permissions:
            score += 15
            factors.append({
                "factor": "FINANCIAL_EXECUTION_REQUESTED",
                "score": 15,
                "detail": "Agent requested direct automated payment authorization."
            })

        if "CANCEL_BOOKINGS" in requested_permissions or "MODIFY_BOOKINGS" in requested_permissions:
            score += 10
            factors.append({
                "factor": "MUTATION_PRIVILEGE_REQUESTED",
                "score": 10,
                "detail": "Agent requested reservation modification or cancellation privileges."
            })

        # --- 3. Financial & Budget Analysis ---
        if customer:
            max_txn_budget = customer.get("max_budget_per_transaction", 15000.0)
            daily_budget = customer.get("daily_budget_limit", 35000.0)

            if total_amount > max_txn_budget:
                excess_pct = round(((total_amount - max_txn_budget) / max_txn_budget) * 100, 1)
                score += 40
                factors.append({
                    "factor": "TRANSACTION_BUDGET_EXCEEDED",
                    "score": 40,
                    "detail": f"Total amount (₹{total_amount:,.2f}) exceeds customer's max transaction limit (₹{max_txn_budget:,.2f}) by {excess_pct}%."
                })
            elif total_amount > (0.85 * max_txn_budget):
                score += 15
                factors.append({
                    "factor": "APPROACHING_BUDGET_LIMIT",
                    "score": 15,
                    "detail": f"Total amount (₹{total_amount:,.2f}) consumes over 85% of transaction limit (₹{max_txn_budget:,.2f})."
                })

            if total_amount > 30000.0:
                score += 10
                factors.append({
                    "factor": "HIGH_VALUE_TRANSACTION",
                    "score": 10,
                    "detail": f"Absolute transaction value ₹{total_amount:,.2f} is classified as high-value ticket."
                })
        else:
            score += 30
            factors.append({
                "factor": "NO_CUSTOMER_PROFILE",
                "score": 30,
                "detail": "No associated customer profile found to verify financial bounds."
            })

        # --- 4. Anomaly & Behavioral Heuristics ---
        if baggage_count > 2:
            score += 15
            factors.append({
                "factor": "UNUSUAL_BAGGAGE_VOLUME",
                "score": 15,
                "detail": f"Requested baggage ({baggage_count} bags) exceeds standard single-passenger threshold."
            })

        if seat_code.startswith("2") or seat_code.startswith("1"):
            # Premium or first class seat selection
            if total_amount > 12000.0:
                score += 10
                factors.append({
                    "factor": "PREMIUM_SEAT_SURCHARGE",
                    "score": 10,
                    "detail": f"First/Business Class seat code '{seat_code}' selected."
                })

        # Check velocity anomaly (recent requests in last 24h)
        recent_requests_count = RiskEngine._get_recent_requests_count(agent.get("id"))
        if recent_requests_count >= 5:
            score += 20
            factors.append({
                "factor": "HIGH_TRANSACTION_VELOCITY",
                "score": 20,
                "detail": f"High booking activity: {recent_requests_count} booking requests submitted in the last 24 hours."
            })

        # Normalize score between 0 and 100
        score = min(100, max(0, score))

        # Classify Level
        if score <= 35:
            risk_level = "LOW RISK"
            recommendation = "APPROVE"
        elif score <= 70:
            risk_level = "MEDIUM RISK"
            recommendation = "VERIFY_OR_APPROVE"
        else:
            risk_level = "HIGH RISK"
            recommendation = "REQUIRE_HUMAN_APPROVAL_OR_REJECT"

        if not factors:
            factors.append({
                "factor": "CLEAN_SECURITY_PROFILE",
                "score": 0,
                "detail": "All security heuristics within nominal baseline parameters."
            })

        return score, risk_level, factors, recommendation

    @staticmethod
    def _get_recent_requests_count(agent_id: str) -> int:
        """Count requests submitted by this agent in the last 24 hours."""
        if not agent_id:
            return 0
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
            SELECT COUNT(*) FROM booking_requests
            WHERE agent_id = ? AND created_at >= datetime('now', '-1 day')
            """, (agent_id,))
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0
