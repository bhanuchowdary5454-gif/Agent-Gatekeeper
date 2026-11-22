"""
AirGuard AI - Page 3: Granular Permission Management (Module 4)
Fine-grained capability configuration and consent matrix for third-party airline AI agents.
"""

import streamlit as st
import pandas as pd
from agent_manager import AgentManager
from database import ALL_PERMISSIONS
from utils.helpers import render_delta_header

def render_permissions_page():
    render_delta_header(
        title="Granular Permission & Consent Management",
        subtitle="Principle of Least Privilege: Authorize or restrict individual operational capabilities per AI agent",
        tag="CONSENT CONTROL"
    )

    agents = AgentManager.get_all_agents()
    if not agents:
        st.warning("No registered agents found.")
        return

    agent_options = {f"{a['name']} ({a['id']} - {a['status']})": a["id"] for a in agents}
    selected_label = st.selectbox("Select Target AI Agent", list(agent_options.keys()))
    selected_agent_id = agent_options[selected_label]

    agent = next((a for a in agents if a["id"] == selected_agent_id), None)
    if not agent:
        return

    is_revoked = agent["status"] == "REVOKED"

    st.markdown(f"""
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px 18px; margin-bottom: 20px;">
        <span style="font-size: 0.9rem; color: #475569;">Configuring Permissions for:</span>
        <b style="color: #001A49; font-size: 1.1rem; margin-left: 5px;">{agent['name']}</b>
        <span style="margin-left: 10px; font-size: 0.85rem; color: #64748B;">Owner: {agent.get('customer_name') or agent['customer_id']} | Status: <b>{agent['status']}</b></span>
    </div>
    """, unsafe_allow_html=True)

    if is_revoked:
        st.error("🚨 This agent is REVOKED. All permissions have been permanently stripped and cannot be re-granted.")

    current_perms = AgentManager.get_agent_permissions(selected_agent_id)

    st.subheader("Granular Capability Access Matrix")
    st.write("Toggle individual permissions on or off. Changes take effect immediately at the Gatekeeper Policy Decision Point.")

    # Render permission cards with toggles
    for perm_key, desc in ALL_PERMISSIONS:
        is_currently_granted = current_perms.get(perm_key, False)

        c1, c2 = st.columns([4, 1])
        with c1:
            icon = "💳" if "PAY" in perm_key else ("✈️" if "BOOK" in perm_key or "SEARCH" in perm_key else ("💺" if "SEAT" in perm_key else ("🧳" if "BAGGAGE" in perm_key else "⚙️")))
            st.markdown(f"**{icon} `{perm_key}`**")
            st.caption(desc)

        with c2:
            new_val = st.toggle(
                "Granted" if is_currently_granted else "Revoked",
                value=is_currently_granted,
                key=f"toggle_{selected_agent_id}_{perm_key}",
                disabled=is_revoked
            )

            if new_val != is_currently_granted and not is_revoked:
                try:
                    AgentManager.update_agent_permission(selected_agent_id, perm_key, new_val)
                    st.success(f"Updated `{perm_key}` to {'GRANTED' if new_val else 'REVOKED'}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating permission: {e}")

        st.markdown("<hr style='margin: 6px 0; border-color: #F1F5F9;'>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Global Permission Overview Across Fleet")

    summary_rows = []
    for ag in agents:
        perms = AgentManager.get_agent_permissions(ag["id"])
        row = {"Agent": ag["name"], "ID": ag["id"], "Status": ag["status"]}
        for pk, _ in ALL_PERMISSIONS:
            row[pk] = "✅" if perms.get(pk, False) else "❌"
        summary_rows.append(row)

    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
