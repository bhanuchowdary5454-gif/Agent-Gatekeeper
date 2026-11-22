"""
AirGuard AI - Page 8: Risk Monitoring & Assessment Lab (Module 7)
Real-time risk scoring analytics, multi-factor heuristic simulator, and anomaly tracking.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from risk_engine import RiskEngine
from agent_manager import AgentManager
from flight_service import FlightService, SEAT_OPTIONS
from database import get_db_connection, ALL_PERMISSIONS
from utils.helpers import render_delta_header, format_currency, render_risk_pill

def render_risk_monitoring_page():
    render_delta_header(
        title="Risk Assessment & Threat Modeling Engine",
        subtitle="Multi-factor scoring heuristic evaluating identity, permissions, budget anomalies and velocity",
        tag="RISK ENGINE"
    )

    tab_analytics, tab_simulator = st.tabs(["📊 Risk Analytics & Threat Radar", "🧪 Interactive Risk Simulator"])

    with tab_analytics:
        st.subheader("Fleet-wide Risk Threat Modeling")

        conn = get_db_connection()
        df_req = pd.read_sql_query("SELECT id, agent_id, customer_id, total_amount, risk_score, risk_level, status FROM booking_requests", conn)
        conn.close()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Risk Threshold Governance")
            st.markdown("""
            - 🟢 **LOW RISK (0 - 35):** Nominal behavioral baseline. All requested permissions granted. Well within spending limits. Automatic authorization.
            - 🟡 **MEDIUM RISK (36 - 70):** Approaching budget limit (>85%), or requesting sensitive mutation permissions (Modification/Cancellation). Conditional review.
            - 🔴 **HIGH RISK (71 - 100):** Budget exceeded, revoked or deactivated agent, unauthorized capability requests, or transaction velocity anomalies. Triggers human escalation or instant gatekeeper rejection.
            """)

        with col2:
            if not df_req.empty:
                fig_hist = px.histogram(
                    df_req,
                    x="risk_score",
                    nbins=10,
                    color="risk_level",
                    color_discrete_map={"LOW RISK": "#10B981", "MEDIUM RISK": "#F59E0B", "HIGH RISK": "#DC2626"},
                    title="Risk Score Frequency Distribution"
                )
                fig_hist.update_layout(margin=dict(t=30, b=20, l=20, r=20), xaxis_title="Risk Score (0-100)", yaxis_title="Request Count")
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("No transaction data available.")

    with tab_simulator:
        st.subheader("🧪 Live Gatekeeper Risk Simulator")
        st.write("Simulate any combination of Agent, Customer, Flight, and Requested Permissions to preview the Risk Engine's calculation.")

        agents = AgentManager.get_all_agents()
        flights = FlightService.search_flights()

        conn = get_db_connection()
        customers = [dict(r) for r in conn.execute("SELECT * FROM customers").fetchall()]
        conn.close()

        c_s1, c_s2 = st.columns(2)
        with c_s1:
            agent_map = {f"{a['name']} ({a['id']} - {a['status']})": a for a in agents}
            sim_agent_lbl = st.selectbox("Test Agent", list(agent_map.keys()))
            sim_agent = agent_map[sim_agent_lbl]

            cust_map = {f"{c['name']} (Limit: ₹{c['max_budget_per_transaction']:,.0f})": c for c in customers}
            sim_cust_lbl = st.selectbox("Customer Context", list(cust_map.keys()))
            sim_cust = cust_map[sim_cust_lbl]

        with c_s2:
            flight_map = {f"{f['flight_number']}: {f['source_city']} ➔ {f['dest_city']} (₹{f['base_price']:,.0f})": f for f in flights}
            sim_flight_lbl = st.selectbox("Flight Route", list(flight_map.keys()))
            sim_flight = flight_map[sim_flight_lbl]

            seat_map = {f"{s['code']} - {s['label']} (+₹{s['extra_cost']:,.0f})": s["code"] for s in SEAT_OPTIONS}
            sim_seat_lbl = st.selectbox("Seat Selection", list(seat_map.keys()))
            sim_seat_code = seat_map[sim_seat_lbl]

            sim_bags = st.slider("Additional Checked Bags", 0, 5, 1)

        st.markdown("**Simulated Requested Permissions:**")
        sim_req_perms = []
        perm_cols = st.columns(4)
        for idx, (pk, desc) in enumerate(ALL_PERMISSIONS):
            with perm_cols[idx % 4]:
                if st.checkbox(pk, value=pk in ["SEARCH_FLIGHTS", "BOOK_FLIGHTS", "SELECT_SEATS", "MAKE_PAYMENTS"], key=f"sim_lab_p_{pk}"):
                    sim_req_perms.append(pk)

        if st.button("⚡ Calculate Risk Score", type="primary"):
            sim_total = FlightService.calculate_total_cost(sim_flight["id"], sim_seat_code, sim_bags)
            granted_perms = AgentManager.get_agent_permissions(sim_agent["id"])

            score, level, factors, rec = RiskEngine.assess_risk(
                agent=sim_agent,
                customer=sim_cust,
                flight=sim_flight,
                requested_permissions=sim_req_perms,
                granted_permissions=granted_perms,
                total_amount=sim_total,
                baggage_count=sim_bags,
                seat_code=sim_seat_code
            )

            st.markdown("---")
            col_res1, col_res2, col_res3 = st.columns(3)
            with col_res1:
                st.metric("Computed Risk Score", f"{score}/100", delta=level, delta_color="inverse" if score > 35 else "normal")
            with col_res2:
                st.metric("Risk Classification", level)
            with col_res3:
                st.metric("Engine Recommendation", rec)

            st.markdown("#### Factor Breakdown & Diagnostic Signals:")
            for f in factors:
                pts_color = "#DC2626" if f["score"] >= 30 else ("#D97706" if f["score"] > 0 else "#10B981")
                st.markdown(f"""
                <div style="background: white; border: 1px solid #E2E8F0; border-left: 4px solid {pts_color}; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px;">
                    <b>{f['factor']}</b> <span style="color: {pts_color}; font-weight: 700;">(+{f['score']} pts)</span><br>
                    <span style="font-size: 0.85rem; color: #475569;">{f['detail']}</span>
                </div>
                """, unsafe_allow_html=True)
