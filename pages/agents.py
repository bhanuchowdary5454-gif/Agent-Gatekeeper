"""
AirGuard AI - Page 2: AI Agent Management (Module 2)
Register new third-party AI agents, bind to customer accounts, and control operational status.
"""

import streamlit as st
import pandas as pd
from agent_manager import AgentManager
from database import get_db_connection, ALL_PERMISSIONS
from utils.helpers import render_delta_header, render_status_pill

def render_agents_page():
    render_delta_header(
        title="AI Agent Registry & Lifecycle Management",
        subtitle="Provision third-party travel bots, generate cryptographic tokens, and manage authorization status",
        tag="AGENT REGISTRY"
    )

    tab_list, tab_register = st.tabs(["📋 Registered Agents", "➕ Register New Agent"])

    with tab_register:
        st.subheader("Register a New Third-Party AI Travel Agent")
        st.write("Register an external personal assistant or enterprise booking agent authorized to interface with Delta Air Lines.")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, skymiles_tier FROM customers")
        customers = cursor.fetchall()
        conn.close()

        customer_options = {f"{c['name']} ({c['id']} - {c['skymiles_tier']})": c["id"] for c in customers}

        with st.form("register_agent_form"):
            col1, col2 = st.columns(2)
            with col1:
                agent_name = st.text_input("AI Agent Name", placeholder="e.g., SkyAssistant Pro")
                developer_org = st.text_input("Developer Organization", placeholder="e.g., Expedia Agent Ecosystem or Personal Bot")
                risk_baseline = st.selectbox("Risk Baseline Assessment", ["LOW", "MEDIUM", "HIGH"], index=0)

            with col2:
                selected_cust_label = st.selectbox("Associated Customer (Owner)", list(customer_options.keys()))
                customer_id = customer_options[selected_cust_label]

                st.write("**Initial Permissions Bundle:**")
                initial_perms = []
                for perm_key, desc in ALL_PERMISSIONS:
                    # Default search & book to checked
                    default_val = perm_key in ["SEARCH_FLIGHTS", "VIEW_FLIGHT_DETAILS", "BOOK_FLIGHTS"]
                    if st.checkbox(f"{perm_key} ({desc})", value=default_val, key=f"init_perm_{perm_key}"):
                        initial_perms.append(perm_key)

            submitted = st.form_submit_button("🚀 Register & Issue Bearer Token", use_container_width=True)

            if submitted:
                if not agent_name.strip():
                    st.error("Agent Name is required.")
                elif not developer_org.strip():
                    st.error("Developer Organization is required.")
                else:
                    try:
                        new_agent = AgentManager.register_agent(
                            name=agent_name.strip(),
                            customer_id=customer_id,
                            developer_org=developer_org.strip(),
                            initial_permissions=initial_perms,
                            risk_baseline=risk_baseline
                        )
                        st.success(f"Agent '{new_agent['name']}' successfully registered with ID **{new_agent['id']}**!")
                        st.info(f"🔑 **Generated Bearer Token:** `{new_agent['auth_token']}`\n\n*(Store securely. This token is required for all Gatekeeper authorizations.)*")
                    except Exception as e:
                        st.error(f"Registration failed: {e}")

    with tab_list:
        st.subheader("Active & Registered Agent Roster")
        agents = AgentManager.get_all_agents()

        if not agents:
            st.info("No agents registered yet.")
            return

        for ag in agents:
            status = ag["status"]
            status_color = "#10B981" if status == "ACTIVE" else ("#DC2626" if status == "REVOKED" else "#64748B")

            with st.container():
                st.markdown(f"""
                <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-bottom: 12px; border-left: 5px solid {status_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin: 0; color: #001A49;">{ag['name']} <span style="font-size: 0.8rem; color: #64748B;">({ag['id']})</span></h4>
                            <p style="margin: 4px 0 0 0; font-size: 0.85rem; color: #475569;">
                                Owner: <b>{ag.get('customer_name') or ag['customer_id']}</b> | Developer: <i>{ag['developer_org']}</i> | Baseline: <b>{ag['risk_baseline']}</b>
                            </p>
                        </div>
                        <div style="text-align: right;">
                            {render_status_pill(status)}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_token, col_btn = st.columns([3, 1])
                with col_token:
                    st.code(f"Token: {ag['auth_token']}", language="bash")
                with col_btn:
                    if status == "ACTIVE":
                        if st.button("⏸️ Deactivate", key=f"deact_{ag['id']}", use_container_width=True):
                            AgentManager.toggle_agent_status(ag["id"], "INACTIVE")
                            st.rerun()
                    elif status == "INACTIVE":
                        if st.button("▶️ Activate", key=f"act_{ag['id']}", use_container_width=True):
                            AgentManager.toggle_agent_status(ag["id"], "ACTIVE")
                            st.rerun()
                    else:
                        st.markdown("<span style='color: #DC2626; font-size: 0.85rem; font-weight: 600;'>PERMANENTLY REVOKED</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)
