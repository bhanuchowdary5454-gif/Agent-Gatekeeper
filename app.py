"""
AirGuard AI - Intelligent Airline Agent Gatekeeper
Case Study: Delta Air Lines (Academic Prototype)
Main Application Router and Executive Controller.
"""

import streamlit as st
import os
import sys

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database import init_db
from utils.helpers import inject_custom_css

# Page configuration
st.set_page_config(
    page_title="AirGuard AI – Delta Air Lines Agent Gatekeeper",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure database is initialized with tables and sample data
init_db()

# Inject Delta brand stylesheet
inject_custom_css()

# Import page modules
from pages.dashboard import render_dashboard_page
from pages.agents import render_agents_page
from pages.permissions import render_permissions_page
from pages.flights import render_flights_page
from pages.bookings import render_bookings_page
from pages.decisions import render_decisions_page
from pages.approvals import render_approvals_page
from pages.risk_monitoring import render_risk_monitoring_page
from pages.revoke import render_revoke_page
from pages.audit_logs import render_audit_logs_page

# Sidebar Branding & Navigation
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 12px 0 16px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 15px;">
        <div style="font-size: 2.2rem;">✈️ 🛡️</div>
        <div style="font-weight: 800; font-size: 1.25rem; color: #001A49; letter-spacing: -0.5px;">AirGuard AI</div>
        <div style="font-size: 0.75rem; color: #E01933; font-weight: 700; text-transform: uppercase; margin-top: 2px;">Delta Air Lines Gatekeeper</div>
        <div style="font-size: 0.7rem; color: #64748B; margin-top: 3px;">Agentic Cybersecurity Architecture</div>
    </div>
    """, unsafe_allow_html=True)

    nav_selection = st.radio(
        "Navigation Portal",
        [
            "1. Dashboard",
            "2. AI Agent Management",
            "3. Permissions",
            "4. Flight Search",
            "5. Booking Simulator",
            "6. Gatekeeper Decisions",
            "7. Human Approval",
            "8. Risk Monitoring",
            "9. Revoke Agent",
            "10. Audit Logs"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("""
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px; font-size: 0.75rem; color: #475569;">
        <div style="color: #10B981; font-weight: 700; margin-bottom: 4px;">● GATEKEEPER ENGINE ONLINE</div>
        <div><b>Protocol:</b> Zero-Trust PEP/PDP</div>
        <div><b>Database:</b> SQLite (Auto-Seeded)</div>
        <div><b>Case Study:</b> Delta Air Lines</div>
        <div style="margin-top: 6px; font-size: 0.7rem; color: #94A3B8;">Academic Research Prototype. Simulated Data Only.</div>
    </div>
    """, unsafe_allow_html=True)

# Route to selected page
if "1. Dashboard" in nav_selection:
    render_dashboard_page()
elif "2. AI Agent Management" in nav_selection:
    render_agents_page()
elif "3. Permissions" in nav_selection:
    render_permissions_page()
elif "4. Flight Search" in nav_selection:
    render_flights_page()
elif "5. Booking Simulator" in nav_selection:
    render_bookings_page()
elif "6. Gatekeeper Decisions" in nav_selection:
    render_decisions_page()
elif "7. Human Approval" in nav_selection:
    render_approvals_page()
elif "8. Risk Monitoring" in nav_selection:
    render_risk_monitoring_page()
elif "9. Revoke Agent" in nav_selection:
    render_revoke_page()
elif "10. Audit Logs" in nav_selection:
    render_audit_logs_page()
