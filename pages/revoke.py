"""
AirGuard AI - Page 9: Agent Revocation & Kill-Switch (Module 9)
Emergency decommissioning portal, instant capability stripping, and revocation ledger.
"""

import streamlit as st
import pandas as pd
from agent_manager import AgentManager
from utils.helpers import render_delta_header, render_status_pill

def render_revoke_page():
    render_delta_header(
        title="Emergency Agent Revocation & Decommissioning",
        subtitle="Zero-Trust Kill Switch: Permanently sever an AI agent's access to Delta Air Lines services",
        tag="SECURITY KILL-SWITCH"
    )

    tab_revoke, tab_ledger = st.tabs(["🛑 Emergency Revoke Action", "📜 Revocation Ledger"])

    with tab_revoke:
        st.subheader("Revoke an Active or Compromised AI Agent")
        st.warning("""
        **WARNING:** Revocation is an irreversible security action.
        - The agent status is immediately set to **REVOKED**.
        - All granular permissions are permanently disabled.
        - Subsequent Gatekeeper authentication attempts are immediately rejected and logged as critical alerts.
        """)

        agents = AgentManager.get_all_agents()
        non_revoked_agents = [a for a in agents if a["status"] != "REVOKED"]

        if not non_revoked_agents:
            st.info("No active or suspendable agents available to revoke.")
        else:
            agent_dict = {f"{a['name']} ({a['id']} - Owner: {a.get('customer_name') or a['customer_id']})": a for a in non_revoked_agents}
            selected_label = st.selectbox("Select Agent to Revoke", list(agent_dict.keys()))
            target_agent = agent_dict[selected_label]

            with st.form("revoke_agent_form"):
                reason = st.text_area("Justification / Revocation Reason", placeholder="e.g. Unusual high-value transaction patterns detected by customer, or API key compromise.", height=100)
                revoked_by = st.selectbox("Revoked By", ["Customer (Owner)", "Security Operations Center", "Airline Fraud Detection Engine", "Corporate Compliance Admin"])
                confirm_check = st.checkbox("I confirm that I want to PERMANENTLY revoke this AI agent's credentials.")

                submit_revoke = st.form_submit_button("🚨 Execute Immediate Revocation", type="primary", use_container_width=True)

                if submit_revoke:
                    if not confirm_check:
                        st.error("Please check the confirmation box to execute revocation.")
                    elif not reason.strip():
                        st.error("Please provide a valid justification for this revocation.")
                    else:
                        try:
                            AgentManager.revoke_agent(
                                agent_id=target_agent["id"],
                                reason=reason.strip(),
                                revoked_by=revoked_by
                            )
                            st.success(f"Agent '{target_agent['name']}' ({target_agent['id']}) has been PERMANENTLY REVOKED.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Revocation failed: {e}")

    with tab_ledger:
        st.subheader("Official Revocation Ledger")
        st.write("Permanent record of all revoked AI agents, justifications, and administrative oversight.")

        records = AgentManager.get_revocation_records()
        if not records:
            st.info("No revocation records found.")
        else:
            for rec in records:
                st.markdown(f"""
                <div style="background: white; border: 1px solid #FCA5A5; border-left: 5px solid #DC2626; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #FEE2E2; padding-bottom: 8px; margin-bottom: 10px;">
                        <div>
                            <span style="font-weight: 700; color: #991B1B; font-size: 1.05rem;">{rec.get('agent_name') or rec['agent_id']} ({rec['agent_id']})</span>
                            <span style="margin-left: 10px; font-size: 0.85rem; color: #64748B;">Customer: <b>{rec.get('customer_name') or rec['customer_id']}</b></span>
                        </div>
                        <div>
                            <span style="background: #FEE2E2; color: #991B1B; font-weight: 700; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem;">REVOKED</span>
                        </div>
                    </div>
                    <div style="font-size: 0.9rem; color: #1E293B; margin-bottom: 8px;">
                        <b>Revocation Justification:</b> {rec['reason']}
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #64748B;">
                        <span>Enforced By: <b>{rec['revoked_by']}</b></span>
                        <span>Previous Status: <code>{rec['previous_status']}</code></span>
                        <span>Timestamp: {rec['revoked_at']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
