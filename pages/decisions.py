"""
AirGuard AI - Page 6: Gatekeeper Decisions Ledger (Module 6)
Comprehensive record and explainability ledger of all Gatekeeper Policy decisions.
"""

import streamlit as st
import pandas as pd
from gatekeeper import GatekeeperEngine
from utils.helpers import render_delta_header, format_currency, render_status_pill, render_risk_pill

def render_decisions_page():
    render_delta_header(
        title="Gatekeeper Policy Enforcement Ledger",
        subtitle="Transparent audit of all PDP evaluations, permission checks, budget enforcements and verdicts",
        tag="DECISION LOG"
    )

    c1, c2 = st.columns([2, 2])
    with c1:
        filter_status = st.selectbox("Filter by Verdict", ["ALL", "APPROVED", "REJECTED", "PENDING_HUMAN_APPROVAL"])
    with c2:
        search_query = st.text_input("Search Request ID, Agent, or Route", placeholder="e.g., REQ-2026 or DEL")

    requests = GatekeeperEngine.get_all_booking_requests(status_filter=filter_status)

    if search_query:
        sq = search_query.lower()
        requests = [r for r in requests if sq in r["id"].lower() or sq in (r.get("agent_name") or "").lower() or sq in (r.get("source_city") or "").lower() or sq in (r.get("dest_city") or "").lower()]

    st.write(f"Displaying **{len(requests)}** Gatekeeper records:")

    if not requests:
        st.info("No gatekeeper records matching the criteria.")
        return

    for r in requests:
        with st.container():
            st.markdown(f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #F8FAFC; padding-bottom: 8px; margin-bottom: 10px;">
                    <div>
                        <span style="font-weight: 700; color: #001A49; font-size: 1.05rem;">{r['id']}</span>
                        <span style="margin-left: 10px; font-size: 0.85rem; color: #64748B;">Agent: <b>{r.get('agent_name') or r['agent_id']}</b></span>
                        <span style="margin-left: 10px; font-size: 0.85rem; color: #64748B;">Customer: <b>{r.get('customer_name') or r['customer_id']}</b></span>
                    </div>
                    <div>
                        {render_status_pill(r['status'])}
                        <span style="margin-left: 8px;">{render_risk_pill(r['risk_level'], r['risk_score'])}</span>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 0.95rem; font-weight: 600; color: #1E293B;">
                            ✈️ {r.get('flight_number', 'N/A')} ({r.get('source_city', 'N/A')} ➔ {r.get('dest_city', 'N/A')})
                        </div>
                        <div style="font-size: 0.8rem; color: #64748B; margin-top: 2px;">
                            Seat: <b>{r.get('seat_selected') or 'Standard'}</b> | Baggage: <b>{r.get('baggage_count', 0)} pcs</b>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.15rem; font-weight: 700; color: #0067C5;">{format_currency(r['total_amount'])}</div>
                        <div style="font-size: 0.75rem; color: #64748B;">{r['created_at']}</div>
                    </div>
                </div>
                <div style="margin-top: 10px; background: #F8FAFC; border-radius: 6px; padding: 10px; font-size: 0.85rem; color: #334155;">
                    <b>Policy Decision Reason:</b> {r['decision_reason']}
                    {f"<br><span style='color: #0067C5;'><b>Approval Note:</b> {r['approval_comment']}</span>" if r.get('approval_comment') else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)
