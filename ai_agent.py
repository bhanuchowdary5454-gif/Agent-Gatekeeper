"""
AirGuard AI - Agentic AI Travel Agent Orchestrator
Autonomous travel agent with NLP intent parsing, tool execution, and Gatekeeper-mediated transaction lifecycle.
"""

import re
import json
from datetime import datetime, timedelta
from flight_service import FlightService, SEAT_OPTIONS
from gatekeeper import GatekeeperEngine
from agent_manager import AgentManager

class TravelQueryParser:
    """
    Robust local deterministic parser for natural language flight booking queries.
    Fallback engine ensuring 100% offline functionality without mandatory LLM keys.
    """
    @staticmethod
    def parse_query(prompt: str, default_budget: float = 20000.0) -> dict:
        prompt_lower = prompt.lower()
        cities = FlightService.get_supported_cities()

        source = None
        destination = None

        # Detect Source ("from X")
        from_match = re.search(r"from\s+([a-zA-Z]+)", prompt, re.IGNORECASE)
        if from_match:
            candidate = from_match.group(1).capitalize()
            for c in cities:
                if c.lower() == candidate.lower():
                    source = c
                    break

        # Detect Destination ("to Y")
        to_match = re.search(r"to\s+([a-zA-Z]+)", prompt, re.IGNORECASE)
        if to_match:
            candidate = to_match.group(1).capitalize()
            for c in cities:
                if c.lower() == candidate.lower():
                    destination = c
                    break

        # Fallback city scan if 'from/to' keywords were omitted
        if not source or not destination:
            found_cities = []
            for c in cities:
                if c.lower() in prompt_lower:
                    found_cities.append(c)
            if len(found_cities) >= 2:
                if not source:
                    source = found_cities[0]
                if not destination:
                    destination = found_cities[1]
            elif len(found_cities) == 1:
                if not source:
                    source = found_cities[0]
                else:
                    destination = found_cities[0]

        # Extract Budget / Price constraint ("under 8000", "budget 15000", "< 10000")
        budget = default_budget
        budget_match = re.search(r"(?:under|below|max|budget|within|less than|up to|inr|rs\.?|₹)\s*(\d{3,6})", prompt, re.IGNORECASE)
        if budget_match:
            budget = float(budget_match.group(1))

        # Extract Seat preference
        seat_code = "14A" # Default standard window
        if "first" in prompt_lower or "business" in prompt_lower or "suite" in prompt_lower:
            seat_code = "2A"
        elif "comfort" in prompt_lower or "extra legroom" in prompt_lower:
            if "aisle" in prompt_lower:
                seat_code = "8C"
            else:
                seat_code = "8A"
        elif "aisle" in prompt_lower:
            seat_code = "14C"
        elif "middle" in prompt_lower:
            seat_code = "14B"

        # Extract Baggage count
        baggage_count = 0
        bag_match = re.search(r"(\d+)\s*(?:bag|bags|baggage|luggage|suitcase)", prompt_lower)
        if bag_match:
            baggage_count = int(bag_match.group(1))
        elif "extra bag" in prompt_lower or "extra baggage" in prompt_lower:
            baggage_count = 1

        # Extract Cabin Class
        cabin_class = "Economy"
        if "first" in prompt_lower:
            cabin_class = "First Class"
        elif "comfort" in prompt_lower:
            cabin_class = "Comfort+"

        # Travel Date (e.g., 2026-11-25 or "tomorrow" or default)
        date_match = re.search(r"\b(202\d-\d{2}-\d{2})\b", prompt)
        if date_match:
            travel_date = date_match.group(1)
        elif "tomorrow" in prompt_lower:
            travel_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            travel_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

        return {
            "source": source or "Delhi",
            "destination": destination or "Mumbai",
            "travel_date": travel_date,
            "max_budget": budget,
            "cabin_class": cabin_class,
            "seat_code": seat_code,
            "baggage_count": baggage_count,
            "raw_prompt": prompt
        }


class AITravelAgentOrchestrator:
    """
    Autonomous Travel Agent Orchestrator interacting through the Gatekeeper PEP/PDP.
    Guaranteed: The agent cannot bypass Gatekeeper security rules.
    """
    def __init__(self, agent_id: str, auth_token: str, customer_id: str):
        self.agent_id = agent_id
        self.auth_token = auth_token
        self.customer_id = customer_id
        self.execution_trace = []

    def _log_trace(self, step_num: int, action: str, thought: str, tool_used: str, data: dict):
        self.execution_trace.append({
            "step": step_num,
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "action": action,
            "thought": thought,
            "tool": tool_used,
            "data": data
        })

    def execute_travel_request(self, user_instruction: str, requested_permissions: list = None) -> dict:
        """
        Execute full autonomous agent pipeline:
        1. Understand request & extract parameters
        2. Query flight database tool
        3. Select best matching flight
        4. Package booking payload
        5. Submit to Gatekeeper
        6. Act according to Gatekeeper decision
        """
        self.execution_trace = []

        if requested_permissions is None:
            # By default, travel agent needs full set to complete a real booking
            requested_permissions = [
                "SEARCH_FLIGHTS", "VIEW_FLIGHT_DETAILS", "BOOK_FLIGHTS",
                "SELECT_SEATS", "PURCHASE_BAGGAGE", "MAKE_PAYMENTS"
            ]

        # STEP 1: Understand & Parse
        self._log_trace(
            step_num=1,
            action="NLU_INTENT_EXTRACTION",
            thought="Parsing customer natural language travel intent and extracting routing, budget, and baggage constraints.",
            tool_used="TravelQueryParser.parse_query",
            data={"instruction": user_instruction}
        )

        parsed_plan = TravelQueryParser.parse_query(user_instruction)
        self._log_trace(
            step_num=2,
            action="PLAN_FORMULATION",
            thought=f"Extracted Plan: Route {parsed_plan['source']} -> {parsed_plan['destination']} on {parsed_plan['travel_date']}. Budget: ₹{parsed_plan['max_budget']:,.2f}.",
            tool_used="InternalReasoningEngine",
            data=parsed_plan
        )

        # STEP 2: Tool Call - Search Flights
        self._log_trace(
            step_num=3,
            action="TOOL_CALL_SEARCH_FLIGHTS",
            thought=f"Querying Delta flight inventory for route {parsed_plan['source']} to {parsed_plan['destination']}.",
            tool_used="FlightService.search_flights",
            data={"source": parsed_plan["source"], "dest": parsed_plan["destination"]}
        )

        flights = FlightService.search_flights(
            source=parsed_plan["source"],
            destination=parsed_plan["destination"]
        )

        if not flights:
            # Relax search filter or check reverse
            self._log_trace(
                step_num=4,
                action="TOOL_CALL_FALLBACK_SEARCH",
                thought="No direct flights found on exact origin-destination pair. Searching all available departures from source city.",
                tool_used="FlightService.search_flights",
                data={"source": parsed_plan["source"]}
            )
            flights = FlightService.search_flights(source=parsed_plan["source"])

        if not flights:
            self._log_trace(
                step_num=5,
                action="AGENT_HALT",
                thought="No scheduled flights found matching the source hub. Halting execution.",
                tool_used="None",
                data={"status": "NO_FLIGHTS_AVAILABLE"}
            )
            return {
                "success": False,
                "status": "NO_FLIGHTS_FOUND",
                "message": f"No flights found from {parsed_plan['source']} to {parsed_plan['destination']}.",
                "trace": self.execution_trace,
                "gatekeeper_result": None
            }

        # STEP 3: Select Best Flight
        selected_flight = flights[0] # Best price match
        self._log_trace(
            step_num=6,
            action="FLIGHT_SELECTION",
            thought=f"Selected best available flight {selected_flight['flight_number']} ({selected_flight['source_city']} -> {selected_flight['dest_city']}) at base price ₹{selected_flight['base_price']:,.2f}.",
            tool_used="FlightRankingOptimizer",
            data=selected_flight
        )

        # STEP 4: Calculate & Formulate Booking Request
        total_estimate = FlightService.calculate_total_cost(
            flight_id=selected_flight["id"],
            seat_code=parsed_plan["seat_code"],
            baggage_count=parsed_plan["baggage_count"]
        )

        self._log_trace(
            step_num=7,
            action="FORMULATE_GATEKEEPER_PAYLOAD",
            thought=f"Synthesized booking payload. Total computed cost ₹{total_estimate:,.2f}. Requesting authorization from AirGuard Gatekeeper.",
            tool_used="PayloadBuilder",
            data={
                "flight_id": selected_flight["id"],
                "seat_code": parsed_plan["seat_code"],
                "baggage_count": parsed_plan["baggage_count"],
                "total_cost": total_estimate,
                "permissions": requested_permissions
            }
        )

        # STEP 5: Gatekeeper Policy Enforcement Point (PEP) Submission
        self._log_trace(
            step_num=8,
            action="GATEKEEPER_AUTHORIZATION_DISPATCH",
            thought="Transmitting cryptographic bearer token and structured booking payload to Gatekeeper PDP.",
            tool_used="GatekeeperEngine.evaluate_request",
            data={"agent_id": self.agent_id, "customer_id": self.customer_id}
        )

        gatekeeper_decision = GatekeeperEngine.evaluate_request(
            agent_id=self.agent_id,
            auth_token=self.auth_token,
            customer_id=self.customer_id,
            flight_id=selected_flight["id"],
            seat_code=parsed_plan["seat_code"],
            baggage_count=parsed_plan["baggage_count"],
            requested_permissions=requested_permissions
        )

        decision_status = gatekeeper_decision["status"]

        # STEP 6: Handle Gatekeeper Decision
        if decision_status == "APPROVED":
            self._log_trace(
                step_num=9,
                action="GATEKEEPER_APPROVED",
                thought=f"Gatekeeper APPROVED booking (Risk Score: {gatekeeper_decision['risk_score']}). Transaction {gatekeeper_decision.get('transaction_id')} executed successfully. Generating reservation itinerary.",
                tool_used="ReservationIssuer",
                data=gatekeeper_decision
            )
            return {
                "success": True,
                "status": "APPROVED",
                "message": f"Flight {selected_flight['flight_number']} successfully booked! Transaction ID: {gatekeeper_decision.get('transaction_id')}.",
                "flight": selected_flight,
                "booking_details": {
                    "request_id": gatekeeper_decision["request_id"],
                    "seat": parsed_plan["seat_code"],
                    "baggage": parsed_plan["baggage_count"],
                    "total_amount": gatekeeper_decision["total_amount"],
                    "transaction_id": gatekeeper_decision.get("transaction_id")
                },
                "gatekeeper_result": gatekeeper_decision,
                "trace": self.execution_trace
            }
        elif decision_status == "PENDING_HUMAN_APPROVAL":
            self._log_trace(
                step_num=9,
                action="GATEKEEPER_ESCALATED",
                thought=f"Gatekeeper flagged request for HUMAN APPROVAL (Risk Score: {gatekeeper_decision['risk_score']}). Reason: {gatekeeper_decision['decision_reason']}. Halting transaction until customer or admin review.",
                tool_used="ApprovalQueueNotifier",
                data=gatekeeper_decision
            )
            return {
                "success": False,
                "status": "PENDING_HUMAN_APPROVAL",
                "message": f"Booking request {gatekeeper_decision['request_id']} has been placed in PENDING HUMAN APPROVAL queue.",
                "flight": selected_flight,
                "gatekeeper_result": gatekeeper_decision,
                "trace": self.execution_trace
            }
        else:
            # REJECTED
            self._log_trace(
                step_num=9,
                action="GATEKEEPER_REJECTED",
                thought=f"Gatekeeper REJECTED request (Risk Score: {gatekeeper_decision['risk_score']}). Reason: {gatekeeper_decision['decision_reason']}. Halting workflow immediately.",
                tool_used="SecurityEnforcement",
                data=gatekeeper_decision
            )
            return {
                "success": False,
                "status": "REJECTED",
                "message": f"Gatekeeper blocked this booking: {gatekeeper_decision['decision_reason']}",
                "flight": selected_flight,
                "gatekeeper_result": gatekeeper_decision,
                "trace": self.execution_trace
            }
