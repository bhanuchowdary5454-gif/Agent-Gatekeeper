"""
AirGuard AI - Page 5: Agentic AI Booking Simulator & Orchestrator
Interactive AI travel agent console executing natural language queries through the Gatekeeper.
"""

import streamlit as st
import json
from agent_manager import AgentManager
from ai_agent import AITravelAgentOrchestrator, TravelQueryParser
from flight_service import FlightService, SEAT_OPTIONS
from gatekeeper import GatekeeperEngine
from utils.helpers import render_delta_header, format_currency, render_status_pill, render_risk_pill

def render_bookings_page():
    render_delta_header(
        title="Agentic AI Booking Simulator & Gatekeeper Sandbox",
        subtitle="Test third-party autonomous AI travel agents interacting with Delta's Gatekeeper PDP/PEP",
        tag="AI SIMULATOR"
    )

    agents = AgentManager.get_all_agents()
    if not agents:
        st.warning("No agents registered.")
        return

    st.markdown("### 1. Select Calling AI Agent & Persona")
    c_ag, c_preset = st.columns([2, 2])

    with c_ag:
        agent_dict = {f"{a['name']} ({a['id']} - Status: {a['status']})": a for a in agents}
        selected_agent_label = st.selectbox("Executing AI Agent", list(agent_dict.keys()), index=0)
        selected_agent = agent_dict[selected_agent_label]

    # Quick test presets
    with c_preset:
        preset_choice = st.selectbox(
            "Quick Scenario Presets",
            [
                "Custom Query / Manual Entry",
                "Scenario A: Normal Authorized Flight Booking (Expected: APPROVED)",
                "Scenario B: Revoked Agent Attack Attempt (Expected: REJECTED)",
                "Scenario C: Excessive Budget Breach (Expected: REJECTED / ESCALATED)",
                "Scenario D: Missing 'MAKE_PAYMENTS' Permission (Expected: REJECTED)",
                "Scenario E: High Risk Anomaly (Multiple Bags + Premium Cabin)"
            ]
        )

    # Preset logic
    default_prompt = "Book a flight from Delhi to Mumbai tomorrow with window seat under 7500 rupees"
    preset_permissions = None

    if "Scenario A" in preset_choice:
        # Pick an active agent with all permissions (like AGT-7001)
        default_prompt = "Book a flight from Delhi to Mumbai with 1 extra baggage and window seat under 10000"
    elif "Scenario B" in preset_choice:
        # Prompt for revoked agent
        default_prompt = "Book a first class flight from Kolkata to Delhi immediately"
        # Find revoked agent
        for label, ag in agent_dict.items():
            if ag["status"] == "REVOKED":
                selected_agent = ag
                break
    elif "Scenario C" in preset_choice:
        # Huge budget violation for Priya Nair (budget 12,000)
        default_prompt = "Book a flight from Kolkata to Delhi with first class seat 2A and 3 bags under 50000"
    elif "Scenario D" in preset_choice:
        # Agent 7002 or agent lacking MAKE_PAYMENTS
        default_prompt = "Book a flight from Delhi to Bengaluru under 9000 rupees"
        preset_permissions = ["SEARCH_FLIGHTS", "BOOK_FLIGHTS", "SELECT_SEATS", "MAKE_PAYMENTS"]
    elif "Scenario E" in preset_choice:
        default_prompt = "Book a flight from Delhi to Goa with first class seat 2A and 4 extra luggage bags"

    st.markdown(f"""
    <div style="background: #F1F5F9; border-radius: 8px; padding: 10px 14px; margin-bottom: 15px; font-size: 0.85rem; color: #334155;">
        🤖 <b>Simulating Agent:</b> {selected_agent['name']} (<code>{selected_agent['id']}</code>) |
        Status: <b>{selected_agent['status']}</b> |
        Customer ID: <b>{selected_agent['customer_id']}</b> |
        Token: <code>{selected_agent['auth_token'][:18]}...</code>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 2. Customer Travel Prompt")
    user_prompt = st.text_area(
        "Natural Language Request from Customer to AI Agent:",
        value=default_prompt,
        height=75
    )

    with st.expander("⚙️ Advanced Agent Payload & Permission Overrides"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.write("**Simulated Requested Permissions:**")
            req_perms = []
            perm_keys = [
                "SEARCH_FLIGHTS", "VIEW_FLIGHT_DETAILS", "BOOK_FLIGHTS",
                "SELECT_SEATS", "PURCHASE_BAGGAGE", "MAKE_PAYMENTS"
            ]
            for pk in perm_keys:
                is_checked = True
                if preset_choice and "Scenario D" in preset_choice and pk == "MAKE_PAYMENTS":
                    is_checked = True # Requesting it even though agent may not have it
                if st.checkbox(pk, value=is_checked, key=f"sim_perm_{pk}"):
                    req_perms.append(pk)
        with col_p2:
            override_token = st.text_input("Auth Token (leave default for registered token)", value=selected_agent["auth_token"])

    # Run Button
    if st.button("🛫 Launch Autonomous Agent & Submit to Gatekeeper", type="primary", use_container_width=True):
        with st.spinner("Autonomous AI Travel Agent reasoning and dispatching to Gatekeeper..."):
            orchestrator = AITravelAgentOrchestrator(
                agent_id=selected_agent["id"],
                auth_token=override_token.strip(),
                customer_id=selected_agent["customer_id"]
            )

            result = orchestrator.execute_travel_request(
                user_instruction=user_prompt,
                requested_permissions=req_perms
            )

            # Display Gatekeeper Decision Card
            gk = result.get("gatekeeper_result")
            status = result["status"]

            st.markdown("---")
            st.markdown("## 🛡️ Gatekeeper Decision")

            if status == "APPROVED":
                st.success(f"### ✅ Gatekeeper Verdict: {status}")
            elif status == "PENDING_HUMAN_APPROVAL":
                st.warning(f"### ⏳ Gatekeeper Verdict: {status}")
            else:
                st.error(f"### 🚨 Gatekeeper Verdict: {status}")

            if gk:
                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1:
                    st.metric("Request ID", gk["request_id"])
                with col_d2:
                    st.metric("Composite Risk Score", f"{gk['risk_score']}/100", delta=gk['risk_level'], delta_color="inverse" if gk['risk_score'] > 35 else "normal")
                with col_d3:
                    st.metric("Total Transaction Value", format_currency(gk.get("total_amount", 0.0)))

                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; margin-top: 10px;">
                    <b>Explainable Decision Reason:</b><br>
                    <span style="color: #1E293B; font-size: 0.95rem;">{gk['decision_reason']}</span>
                </div>
                """, unsafe_allow_html=True)

                if gk.get("transaction_id"):
                    st.info(f"💳 **Executed Transaction ID:** `{gk['transaction_id']}` | Status: **SUCCESS**")

                if gk.get("risk_factors"):
                    with st.expander("🔎 Risk Factor Breakdown"):
                        for rf in gk["risk_factors"]:
                            st.write(f"- **{rf['factor']}** (+{rf['score']} pts): {rf['detail']}")

            # Step-by-Step Agentic Trace
            st.markdown("---")
            st.markdown("### 🧠 Autonomous Agent Execution & Reasoning Trace")
            st.write("Full audit trace of AI agent intent extraction, inventory tool calls, and Gatekeeper interaction:")

            for step in result["trace"]:
                st.markdown(f"""
                <div class="trace-step">
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #64748B;">
                        <span><b>Step {step['step']}: {step['action']}</b> (Tool: <code>{step['tool']}</code>)</span>
                        <span>{step['timestamp']}</span>
                    </div>
                    <div style="margin-top: 4px; font-size: 0.9rem; color: #1E293B;">
                        💭 <i>{step['thought']}</i>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                with st.expander(f"Inspect Step {step['step']} Payload ({step['action']})", expanded=False):
                    st.json(step["data"])
