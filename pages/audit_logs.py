"""
AirGuard AI - Page 10: Audit Logs & Security Forensics (Module 10)
Searchable, filterable, and immutable audit logging for all airline gatekeeper transactions.
"""

import streamlit as st
import pandas as pd
from audit_logger import AuditLogger
from agent_manager import AgentManager
from utils.helpers import render_delta_header

EVENT_TYPES = [
    "ALL", "AGENT_REGISTRATION", "AUTH_SUCCESS", "AUTH_FAILURE",
    "PERMISSION_CHANGED", "BOOKING_REQUEST", "GATEKEEPER_DECISION",
    "HUMAN_APPROVAL", "AGENT_REVOCATION", "RISK_ALERT", "AGENT_STATUS_CHANGE"
]

SEVERITIES = ["ALL", "INFO", "WARNING", "CRITICAL", "ALERT"]

def render_audit_logs_page():
    render_delta_header(
        title="Central Audit Logging & Forensic Trail",
        subtitle="Immutable transaction ledger and compliance monitoring for airline cybersecurity governance",
        tag="AUDIT & COMPLIANCE"
    )

    # Filter Controls
    with st.expander("🔍 Filter & Query Audit Trail", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            sel_event = st.selectbox("Event Type", EVENT_TYPES, index=0)
        with c2:
            sel_sev = st.selectbox("Severity Level", SEVERITIES, index=0)
        with c3:
            agents = AgentManager.get_all_agents()
            agent_ids = ["ALL"] + [a["id"] for a in agents]
            sel_agent = st.selectbox("Agent Filter", agent_ids, index=0)
        with c4:
            search_txt = st.text_input("Keyword Search", placeholder="e.g. revoked, token, budget")

    df_logs = AuditLogger.get_logs(
        limit=200,
        event_type=sel_event,
        severity=sel_sev,
        agent_id=sel_agent,
        search_query=search_txt
    )

    st.write(f"Displaying **{len(df_logs)}** log records:")

    if df_logs.empty:
        st.info("No audit log entries found matching criteria.")
        return

    # Export to CSV
    csv_data = df_logs.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Audit Trail (CSV)",
        data=csv_data,
        file_name="airguard_audit_trail.csv",
        mime="text/csv"
    )

    # Render formatted table
    for _, row in df_logs.iterrows():
        sev = row["severity"]
        sev_color = "#10B981" if sev == "INFO" else ("#F59E0B" if sev == "WARNING" else "#DC2626")

        st.markdown(f"""
        <div style="background: white; border: 1px solid #E2E8F0; border-left: 4px solid {sev_color}; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem;">
                <div>
                    <span style="font-weight: 700; color: {sev_color};">[{row['severity']}] {row['event_type']}</span>
                    <span style="margin-left: 10px; color: #64748B;">Agent: <code>{row['agent_id'] or 'N/A'}</code></span>
                    <span style="margin-left: 10px; color: #64748B;">Customer: <code>{row['customer_id'] or 'N/A'}</code></span>
                </div>
                <div style="color: #94A3B8;">{row['timestamp']}</div>
            </div>
            <div style="margin-top: 5px; font-size: 0.85rem; color: #1E293B;">
                {row['action_details']}
            </div>
            <div style="margin-top: 3px; font-size: 0.75rem; color: #94A3B8;">
                Origin: <code>{row['ip_or_origin']}</code> | Record #{row['id']}
            </div>
        </div>
        """, unsafe_allow_html=True)
