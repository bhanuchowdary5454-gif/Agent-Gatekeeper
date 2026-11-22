"""
AirGuard AI - Database Engine
SQLite schema definition, connection management, and automatic initial seed data.
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
DB_PATH = os.path.join(DB_DIR, "airguard.db")

ALL_PERMISSIONS = [
    ("SEARCH_FLIGHTS", "Search and query flight availability"),
    ("VIEW_FLIGHT_DETAILS", "View detailed flight schedules, aircraft specs and seat maps"),
    ("BOOK_FLIGHTS", "Initiate flight ticket booking requests"),
    ("SELECT_SEATS", "Select standard or premium seats for reservations"),
    ("PURCHASE_BAGGAGE", "Purchase extra check-in and carry-on baggage allowance"),
    ("CANCEL_BOOKINGS", "Cancel existing confirmed flight reservations"),
    ("MODIFY_BOOKINGS", "Modify travel dates, times, or passenger preferences"),
    ("MAKE_PAYMENTS", "Authorize automated payments and wallet debits")
]

def get_db_connection():
    """Establish and return a connection to the SQLite database with row factory."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    return conn

def init_db(force_reseed=False):
    """
    Initialize all database tables and seed sample data if not already present.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Customers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        skymiles_tier TEXT NOT NULL DEFAULT 'Silver Medallion',
        max_budget_per_transaction REAL NOT NULL DEFAULT 15000.0,
        daily_budget_limit REAL NOT NULL DEFAULT 35000.0,
        currency TEXT NOT NULL DEFAULT 'INR',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Agents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        developer_org TEXT NOT NULL,
        auth_token TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('ACTIVE', 'INACTIVE', 'REVOKED')),
        risk_baseline TEXT NOT NULL DEFAULT 'LOW',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Permissions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        permission_key TEXT NOT NULL,
        is_granted INTEGER NOT NULL DEFAULT 1,
        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        revoked_at TIMESTAMP,
        UNIQUE(agent_id, permission_key)
    );
    """)

    # 4. Flights Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS flights (
        id TEXT PRIMARY KEY,
        flight_number TEXT NOT NULL,
        airline_name TEXT NOT NULL,
        source_city TEXT NOT NULL,
        dest_city TEXT NOT NULL,
        departure_time TEXT NOT NULL,
        arrival_time TEXT NOT NULL,
        duration TEXT NOT NULL,
        base_price REAL NOT NULL,
        available_seats INTEGER NOT NULL,
        cabin_class TEXT NOT NULL DEFAULT 'Economy',
        aircraft_type TEXT NOT NULL DEFAULT 'Airbus A321neo',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Booking Requests Table (Supports recording rogue agent attempts for audit)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS booking_requests (
        id TEXT PRIMARY KEY,
        agent_id TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        flight_id TEXT NOT NULL,
        seat_selected TEXT,
        baggage_count INTEGER DEFAULT 0,
        total_amount REAL NOT NULL,
        requested_permissions TEXT NOT NULL, -- JSON array of strings
        status TEXT NOT NULL CHECK(status IN ('APPROVED', 'REJECTED', 'PENDING_HUMAN_APPROVAL', 'CANCELLED')),
        risk_score INTEGER NOT NULL DEFAULT 0,
        risk_level TEXT NOT NULL CHECK(risk_level IN ('LOW RISK', 'MEDIUM RISK', 'HIGH RISK')),
        decision_reason TEXT NOT NULL,
        approval_comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP
    );
    """)

    # 6. Transactions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        booking_request_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'INR',
        status TEXT NOT NULL CHECK(status IN ('SUCCESS', 'BLOCKED', 'PENDING', 'REFUNDED')),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 7. Revocation Records Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS revocation_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        revoked_by TEXT NOT NULL DEFAULT 'Customer',
        previous_status TEXT NOT NULL,
        revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 8. Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        agent_id TEXT,
        customer_id TEXT,
        severity TEXT NOT NULL CHECK(severity IN ('INFO', 'WARNING', 'CRITICAL', 'ALERT')),
        action_details TEXT NOT NULL,
        ip_or_origin TEXT DEFAULT 'agent-runtime://secure-channel',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()

    # Check if seed data exists
    cursor.execute("SELECT COUNT(*) FROM customers")
    cust_count = cursor.fetchone()[0]

    if cust_count == 0 or force_reseed:
        seed_sample_data(conn)

    conn.close()

def seed_sample_data(conn):
    """Seed comprehensive initial sample data for Delta Air Lines prototype."""
    cursor = conn.cursor()
    # Temporarily disable foreign keys during seed cleanup to prevent cascade replacement locks
    cursor.execute("PRAGMA foreign_keys = OFF;")

    # Clean existing tables in proper order
    cursor.execute("DELETE FROM audit_logs;")
    cursor.execute("DELETE FROM transactions;")
    cursor.execute("DELETE FROM booking_requests;")
    cursor.execute("DELETE FROM revocation_records;")
    cursor.execute("DELETE FROM permissions;")
    cursor.execute("DELETE FROM agents;")
    cursor.execute("DELETE FROM flights;")
    cursor.execute("DELETE FROM customers;")

    # 1. Seed Customers
    customers = [
        ("CUST-101", "Aditi Sharma", "aditi.sharma@example.com", "+91-9811223344", "Gold Medallion", 20000.0, 45000.0, "INR"),
        ("CUST-102", "Rahul Verma", "rahul.verma@example.com", "+91-9822334455", "Platinum Medallion", 35000.0, 75000.0, "INR"),
        ("CUST-103", "Priya Nair", "priya.nair@example.com", "+91-9833445566", "Silver Medallion", 12000.0, 25000.0, "INR"),
        ("CUST-104", "Vikram Malhotra", "vikram.m@example.com", "+91-9844556677", "Diamond Medallion", 80000.0, 160000.0, "INR"),
    ]
    cursor.executemany("""
    INSERT INTO customers (id, name, email, phone, skymiles_tier, max_budget_per_transaction, daily_budget_limit, currency)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, customers)

    # 2. Seed Agents
    agents = [
        ("AGT-7001", "DeltaFlyer Copilot", "CUST-101", "Delta AI Innovation Lab", "agtok_deltaflyer_live_7a8b9c", "ACTIVE", "LOW"),
        ("AGT-7002", "VoyageBot Pro", "CUST-102", "Expedia Agentic Ecosystem", "agtok_voyagebot_prod_4d5e6f", "ACTIVE", "LOW"),
        ("AGT-7003", "SkyBreeze Assistant", "CUST-103", "Personal Traveler GPT", "agtok_skybreeze_dev_1a2b3c", "ACTIVE", "MEDIUM"),
        ("AGT-7004", "RogueTraveler AI", "CUST-104", "ShadowAutomate Systems", "agtok_roguetravel_revoked_99", "REVOKED", "HIGH"),
        ("AGT-7005", "AirConcierge Enterprise", "CUST-104", "Global Corporate Travel", "agtok_airconcierge_8899aa", "INACTIVE", "LOW"),
    ]
    cursor.executemany("""
    INSERT OR REPLACE INTO agents (id, name, customer_id, developer_org, auth_token, status, risk_baseline)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, agents)

    # 3. Seed Permissions
    # Agent 7001: Has all 8 permissions
    for perm_key, _ in ALL_PERMISSIONS:
        cursor.execute("""
        INSERT OR REPLACE INTO permissions (agent_id, permission_key, is_granted)
        VALUES ('AGT-7001', ?, 1)
        """, (perm_key,))

    # Agent 7002: Has 6 permissions (No MAKE_PAYMENTS, No CANCEL_BOOKINGS)
    for perm_key, _ in ALL_PERMISSIONS:
        granted = 1 if perm_key not in ["MAKE_PAYMENTS", "CANCEL_BOOKINGS"] else 0
        cursor.execute("""
        INSERT OR REPLACE INTO permissions (agent_id, permission_key, is_granted)
        VALUES ('AGT-7002', ?, ?)
        """, (perm_key, granted))

    # Agent 7003: Read-only & Booking (No Payments, No Seat, No Baggage)
    for perm_key, _ in ALL_PERMISSIONS:
        granted = 1 if perm_key in ["SEARCH_FLIGHTS", "VIEW_FLIGHT_DETAILS", "BOOK_FLIGHTS"] else 0
        cursor.execute("""
        INSERT OR REPLACE INTO permissions (agent_id, permission_key, is_granted)
        VALUES ('AGT-7003', ?, ?)
        """, (perm_key, granted))

    # Agent 7004: Revoked agent - all permissions disabled (0)
    for perm_key, _ in ALL_PERMISSIONS:
        cursor.execute("""
        INSERT OR REPLACE INTO permissions (agent_id, permission_key, is_granted, revoked_at)
        VALUES ('AGT-7004', ?, 0, CURRENT_TIMESTAMP)
        """, (perm_key,))

    # Agent 7005: Inactive agent - basic search granted
    for perm_key, _ in ALL_PERMISSIONS:
        granted = 1 if perm_key in ["SEARCH_FLIGHTS", "VIEW_FLIGHT_DETAILS"] else 0
        cursor.execute("""
        INSERT OR REPLACE INTO permissions (agent_id, permission_key, is_granted)
        VALUES ('AGT-7005', ?, ?)
        """, (perm_key, granted))

    # 4. Seed Flights (Connecting Delhi, Mumbai, Bengaluru, Hyderabad, Chennai, Kolkata, Pune, Goa)
    flights = [
        ("FL-101", "DL-101", "Delta Air Lines / SkyTeam", "Delhi", "Mumbai", "06:00", "08:15", "2h 15m", 6200.0, 48, "Economy", "Airbus A321neo"),
        ("FL-102", "DL-102", "Delta Air Lines / SkyTeam", "Mumbai", "Delhi", "09:30", "11:45", "2h 15m", 5900.0, 36, "Economy", "Boeing 737-900ER"),
        ("FL-103", "DL-204", "Delta Air Lines / SkyTeam", "Delhi", "Bengaluru", "07:15", "10:05", "2h 50m", 7400.0, 24, "Comfort+", "Airbus A350-900"),
        ("FL-104", "DL-205", "Delta Air Lines / SkyTeam", "Bengaluru", "Delhi", "11:30", "14:20", "2h 50m", 7100.0, 52, "Economy", "Airbus A321neo"),
        ("FL-105", "DL-308", "Delta Air Lines / SkyTeam", "Bengaluru", "Mumbai", "15:00", "16:40", "1h 40m", 4800.0, 60, "Economy", "Boeing 737-800"),
        ("FL-106", "DL-309", "Delta Air Lines / SkyTeam", "Mumbai", "Bengaluru", "18:00", "19:40", "1h 40m", 5100.0, 18, "Comfort+", "Airbus A321neo"),
        ("FL-107", "DL-412", "Delta Air Lines / SkyTeam", "Delhi", "Goa", "10:20", "13:00", "2h 40m", 8200.0, 12, "Economy", "Boeing 757-200"),
        ("FL-108", "DL-413", "Delta Air Lines / SkyTeam", "Goa", "Mumbai", "14:15", "15:35", "1h 20m", 4200.0, 45, "Economy", "Airbus A320"),
        ("FL-109", "DL-515", "Delta Air Lines / SkyTeam", "Hyderabad", "Delhi", "08:45", "11:05", "2h 20m", 6600.0, 30, "Economy", "Airbus A321neo"),
        ("FL-110", "DL-516", "Delta Air Lines / SkyTeam", "Delhi", "Hyderabad", "16:30", "18:50", "2h 20m", 6800.0, 22, "Comfort+", "Boeing 737-900ER"),
        ("FL-111", "DL-620", "Delta Air Lines / SkyTeam", "Chennai", "Kolkata", "11:00", "13:20", "2h 20m", 6100.0, 38, "Economy", "Airbus A321neo"),
        ("FL-112", "DL-621", "Delta Air Lines / SkyTeam", "Kolkata", "Delhi", "17:15", "19:45", "2h 30m", 7300.0, 15, "First Class", "Boeing 767-300ER"),
        ("FL-113", "DL-730", "Delta Air Lines / SkyTeam", "Pune", "Delhi", "07:00", "09:15", "2h 15m", 5800.0, 28, "Economy", "Airbus A321neo"),
        ("FL-114", "DL-731", "Delta Air Lines / SkyTeam", "Mumbai", "Chennai", "13:45", "15:45", "2h 00m", 5400.0, 40, "Economy", "Boeing 737-800"),
        ("FL-115", "DL-840", "Delta Air Lines / SkyTeam", "Bengaluru", "Goa", "12:10", "13:25", "1h 15m", 3900.0, 35, "Economy", "Airbus A320"),
        ("FL-116", "DL-841", "Delta Air Lines / SkyTeam", "Hyderabad", "Bengaluru", "19:10", "20:25", "1h 15m", 4100.0, 50, "Economy", "Airbus A320"),
    ]
    cursor.executemany("""
    INSERT OR REPLACE INTO flights (id, flight_number, airline_name, source_city, dest_city, departure_time, arrival_time, duration, base_price, available_seats, cabin_class, aircraft_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, flights)

    # 5. Seed Revocation Record
    cursor.execute("""
    INSERT OR REPLACE INTO revocation_records (id, agent_id, customer_id, reason, revoked_by, previous_status)
    VALUES (1, 'AGT-7004', 'CUST-104', 'Repeated unauthorized high-value booking attempts detected', 'Security Admin', 'ACTIVE')
    """)

    # 6. Seed Historical Booking Requests
    requests = [
        (
            "REQ-2026-001", "AGT-7001", "CUST-101", "FL-101", "14A", 1, 7400.0,
            json.dumps(["SEARCH_FLIGHTS", "BOOK_FLIGHTS", "SELECT_SEATS", "PURCHASE_BAGGAGE", "MAKE_PAYMENTS"]),
            "APPROVED", 15, "LOW RISK", "All security checks passed. Agent verified, budget approved, valid permissions.",
            "Auto-approved by Gatekeeper", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            "REQ-2026-002", "AGT-7002", "CUST-102", "FL-103", "3B", 2, 9800.0,
            json.dumps(["SEARCH_FLIGHTS", "BOOK_FLIGHTS", "SELECT_SEATS", "PURCHASE_BAGGAGE", "MAKE_PAYMENTS"]),
            "REJECTED", 65, "MEDIUM RISK", "Permission denied: Agent 'AGT-7002' lacks 'MAKE_PAYMENTS' privilege.",
            None, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            "REQ-2026-003", "AGT-7004", "CUST-104", "FL-112", "1A", 3, 24500.0,
            json.dumps(["BOOK_FLIGHTS", "MAKE_PAYMENTS"]),
            "REJECTED", 100, "HIGH RISK", "Security Violation: Agent 'AGT-7004' is REVOKED. Zero access permitted.",
            None, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            "REQ-2026-004", "AGT-7003", "CUST-103", "FL-107", "8C", 2, 14200.0,
            json.dumps(["BOOK_FLIGHTS", "SELECT_SEATS", "PURCHASE_BAGGAGE", "MAKE_PAYMENTS"]),
            "PENDING_HUMAN_APPROVAL", 78, "HIGH RISK", "Risk Threshold Exceeded: Transaction (₹14,200) exceeds customer transaction limit (₹12,000).",
            None, None
        ),
    ]
    cursor.executemany("""
    INSERT OR REPLACE INTO booking_requests (
        id, agent_id, customer_id, flight_id, seat_selected, baggage_count, total_amount,
        requested_permissions, status, risk_score, risk_level, decision_reason, approval_comment, resolved_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, requests)

    # 7. Seed Transactions
    cursor.execute("""
    INSERT OR REPLACE INTO transactions (id, booking_request_id, agent_id, customer_id, amount, currency, status)
    VALUES ('TXN-90111', 'REQ-2026-001', 'AGT-7001', 'CUST-101', 7400.0, 'INR', 'SUCCESS')
    """)
    cursor.execute("""
    INSERT OR REPLACE INTO transactions (id, booking_request_id, agent_id, customer_id, amount, currency, status)
    VALUES ('TXN-90112', 'REQ-2026-002', 'AGT-7002', 'CUST-102', 9800.0, 'INR', 'BLOCKED')
    """)

    # 8. Seed Audit Logs
    logs = [
        ("AGENT_REGISTRATION", "AGT-7001", "CUST-101", "INFO", "Agent 'DeltaFlyer Copilot' successfully registered by Customer Aditi Sharma"),
        ("PERMISSION_CHANGED", "AGT-7001", "CUST-101", "INFO", "Granted all 8 permissions to Agent AGT-7001"),
        ("AUTH_SUCCESS", "AGT-7001", "CUST-101", "INFO", "Agent token authentication successful for session DL-SESSION-81"),
        ("BOOKING_REQUEST", "AGT-7001", "CUST-101", "INFO", "Booking request REQ-2026-001 submitted for Flight DL-101 (DEL -> BOM)"),
        ("GATEKEEPER_DECISION", "AGT-7001", "CUST-101", "INFO", "Decision APPROVED for REQ-2026-001 (Risk Score: 15, LOW RISK)"),
        ("AUTH_FAILURE", "AGT-7004", "CUST-104", "ALERT", "Attempted transaction by REVOKED agent 'AGT-7004'. Immediately blocked."),
        ("RISK_ALERT", "AGT-7003", "CUST-103", "WARNING", "High risk detected on REQ-2026-004: Transaction ₹14,200 > Customer Limit ₹12,000"),
        ("AGENT_REVOCATION", "AGT-7004", "CUST-104", "CRITICAL", "Emergency revocation triggered for Agent AGT-7004 by Security Admin"),
    ]
    cursor.executemany("""
    INSERT INTO audit_logs (event_type, agent_id, customer_id, severity, action_details)
    VALUES (?, ?, ?, ?, ?)
    """, logs)

    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.commit()

if __name__ == "__main__":
    init_db(force_reseed=True)
    print("AirGuard AI Database initialized and seeded successfully.")
