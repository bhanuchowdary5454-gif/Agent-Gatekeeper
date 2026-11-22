"""
AirGuard AI - Airline Flight Service & Simulator (Module 5)
Simulated flight inventory, search engine, pricing calculator, and Delta Air Lines schedule.
"""

from database import get_db_connection

CITIES = [
    "Delhi", "Mumbai", "Bengaluru", "Hyderabad",
    "Chennai", "Kolkata", "Pune", "Goa"
]

SEAT_OPTIONS = [
    {"code": "14A", "label": "Window - Economy", "tier": "Standard", "extra_cost": 0.0},
    {"code": "14B", "label": "Middle - Economy", "tier": "Standard", "extra_cost": 0.0},
    {"code": "14C", "label": "Aisle - Economy", "tier": "Preferred", "extra_cost": 500.0},
    {"code": "8A", "label": "Delta Comfort+ Extra Legroom Window", "tier": "Comfort+", "extra_cost": 1500.0},
    {"code": "8C", "label": "Delta Comfort+ Extra Legroom Aisle", "tier": "Comfort+", "extra_cost": 1500.0},
    {"code": "2A", "label": "First Class Recliner Suite", "tier": "First", "extra_cost": 4500.0},
]

BAGGAGE_FEE_PER_UNIT = 1200.0

class FlightService:
    @staticmethod
    def get_supported_cities():
        return CITIES

    @staticmethod
    def get_seat_options():
        return SEAT_OPTIONS

    @staticmethod
    def search_flights(source: str = None, destination: str = None,
                       cabin_class: str = None, max_price: float = None):
        """
        Search available simulated flights with optional filters.
        """
        conn = get_db_connection()
        query = "SELECT * FROM flights WHERE 1=1"
        params = []

        if source and source != "ALL":
            query += " AND LOWER(source_city) = LOWER(?)"
            params.append(source)

        if destination and destination != "ALL":
            query += " AND LOWER(dest_city) = LOWER(?)"
            params.append(destination)

        if cabin_class and cabin_class != "ALL":
            query += " AND LOWER(cabin_class) = LOWER(?)"
            params.append(cabin_class)

        if max_price and max_price > 0:
            query += " AND base_price <= ?"
            params.append(max_price)

        query += " ORDER BY base_price ASC"

        cursor = conn.cursor()
        cursor.execute(query, params)
        flights = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return flights

    @staticmethod
    def get_flight_by_id(flight_id: str):
        """Get flight details by primary ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM flights WHERE id = ?", (flight_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def calculate_total_cost(flight_id: str, seat_code: str = "14A", baggage_count: int = 0) -> float:
        """
        Compute total cost: base ticket price + seat selection surcharge + additional baggage fee.
        """
        flight = FlightService.get_flight_by_id(flight_id)
        if not flight:
            raise ValueError(f"Flight '{flight_id}' not found.")

        seat_cost = 0.0
        for opt in SEAT_OPTIONS:
            if opt["code"] == seat_code:
                seat_cost = opt["extra_cost"]
                break

        baggage_cost = max(0, baggage_count) * BAGGAGE_FEE_PER_UNIT
        return flight["base_price"] + seat_cost + baggage_cost
