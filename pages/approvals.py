"""
AirGuard AI - Page 7: Human Approval Portal (Module 8)
Review queue for high-risk or budget-breaching AI agent requests requiring customer or admin authorization.
"""

import streamlit as st
import pandas as pd
from gatekeeper import GatekeeperEngine
from utils.helpers import render_delta_header, format_currency, render_risk_pill

def render_approvals_page():
    render_delta_header(
        title="Human-in-the-Loop Approval Queue",
        subtitle="Mandatory manual verification checkpoint for escalated AI agent airline transactions",
        tag="HUMAN OVERSIGHT"
    )

    pending_requests = GatekeeperEngine.get_all_booking_requests(status_filter="PENDING_HUMAN_APPROVAL")

    st.subheader(f"Pending Authorizations Queue ({len(pending_requests)})")

    if not pending_requests:
        st.success("✅ The human approval queue is clear. No AI agent transactions currently pending review.")
        return

    for req in pending_requests:
        with st.container():
            st.markdown(f"""
            <div style="background: white; border: 2px solid #F59E0B; border-radius: 10px; padding: 18px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(245, 158, 11, 0.15);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #FEF3C7; padding-bottom: 10px; margin-bottom: 12px;">
                    <div>
                        <span style="font-size: 1.1rem; font-weight: 700; color: #001A49;">{req['id']}</span>
                        <span style="margin-left: 10px; background: #FEF3C7; color: #92400E; font-weight: 700; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">PENDING REVIEW</span>
                    </div>
                    <div>
                        {render_risk_pill(req['risk_level'], req['risk_score'])}
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 12px;">
                    <div>
                        <div style="font-size: 0.75rem; color: #64748B;">CALLING AI AGENT</div>
                        <div style="font-weight: 600; color: #0F172A;">{req.get('agent_name') or req['agent_id']}</div>
                        <div style="font-size: 0.75rem; color: #94A3B8;">ID: {req['agent_id']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #64748B;">AFFECTED CUSTOMER</div>
                        <div style="font-weight: 600; color: #0F172A;">{req.get('customer_name') or req['customer_id']}</div>
                        <div style="font-size: 0.75rem; color: #94A3B8;">ID: {req['customer_id']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #64748B;">TRANSACTION AMOUNT</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #0067C5;">{format_currency(req['total_amount'])}</div>
                    </div>
                </div>
                <div style="background: #FFFBEB; border-left: 4px solid #F59E0B; padding: 10px 14px; border-radius: 4px; font-size: 0.85rem; color: #92400E; margin-bottom: 15px;">
                    <b>Trigger Reason:</b> {req['decision_reason']}
                </div>
                <div style="font-size: 0.85rem; color: #475569; margin-bottom: 12px;">
                    ✈️ <b>Flight Details:</b> {req.get('flight_number')} ({req.get('source_city')} ➔ {req.get('dest_city')}) | Seat: <b>{req.get('seat_selected')}</b> | Baggage: <b>{req.get('baggage_count')} bags</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.form(f"approval_form_{req['id']}"):
                col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
                with col_c1:
                    comment = st.text_input("Reviewer Comment / Justification", placeholder="e.g. Authorized by customer via phone call", key=f"comm_{req['id']}")
                with col_c2:
                    reviewer = st.selectbox("Reviewer Identity", ["Customer", "Security Admin", "Airline Supervisor"], key=f"rev_{req['id']}")
                with col_c3:
                    st.write("") # spacing
                    st.write("")
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        approve_btn = st.form_submit_button("✓ Approve", type="primary", use_container_width=True)
                    with col_b2:
                        reject_btn = st.form_submit_button("✕ Reject", use_container_width=True)

                if approve_btn:
                    try:
                        res = GatekeeperEngine.resolve_human_approval(
                            request_id=req["id"],
                            action="APPROVED",
                            approval_comment=comment.strip() or "Approved via human verification portal",
                            resolved_by=reviewer
                        )
                        st.success(f"Request {req['id']} successfully APPROVED! Executed transaction: {res.get('transaction_id')}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Approval failed: {e}")

                if reject_btn:
                    try:
                        res = GatekeeperEngine.resolve_human_approval(
                            request_id=req["id"],
                            action="REJECTED",
                            approval_comment=comment.strip() or "Rejected by human reviewer",
                            resolved_by=reviewer
                        )
                        st.warning(f"Request {req['id']} has been REJECTED.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Rejection failed: {e}")

            st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
