"""
AirGuard AI - Page 1: Admin Dashboard (Module 1)
Executive airline security metrics, interactive Plotly visualizations, and live alert feed.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from gatekeeper import GatekeeperEngine
from audit_logger import AuditLogger
from utils.helpers import render_delta_header, render_status_pill, render_risk_pill

def render_dashboard_page():
    render_delta_header(
        title="Security & Authorization Operations Center",
        subtitle="Real-time surveillance of third-party AI travel agent requests on Delta Air Lines infrastructure",
        tag="ADMIN DASHBOARD"
    )

    metrics = GatekeeperEngine.get_dashboard_metrics()

    # KPI Rows (Row 1: Agent & Gatekeeper Stats)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(label="Total AI Agents", value=metrics["total_agents"], help="Registered third-party AI agents")
    with c2:
        st.metric(label="Active Agents", value=metrics["active_agents"], delta=f"{metrics['active_agents']} operational")
    with c3:
        st.metric(label="Revoked Agents", value=metrics["revoked_agents"], delta="High Security" if metrics["revoked_agents"] > 0 else "Normal", delta_color="inverse")
    with c4:
        st.metric(label="Security Alerts", value=metrics["security_alerts"], delta="Audit Warnings", delta_color="inverse")

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    # KPI Row 2: Transaction & Authorization Metrics
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.metric(label="Booking Requests", value=metrics["total_requests"], help="All gatekeeper evaluations")
    with c6:
        st.metric(label="Approved Requests", value=metrics["approved_requests"], delta=f"{(metrics['approved_requests']/max(1, metrics['total_requests'])*100):.0f}% pass rate")
    with c7:
        st.metric(label="Rejected Requests", value=metrics["rejected_requests"], delta="Enforced", delta_color="inverse")
    with c8:
        st.metric(label="Pending Approvals", value=metrics["pending_approvals"], delta="Requires Human Review" if metrics["pending_approvals"] > 0 else "Clear", delta_color="off")

    st.markdown("---")

    # Interactive Visualizations
    col_chart1, col_chart2 = st.columns(2)

    # Fetch all booking requests for plotting
    requests = GatekeeperEngine.get_all_booking_requests()
    df_req = pd.DataFrame(requests)

    with col_chart1:
        st.subheader("📊 Gatekeeper Authorization Outcomes")
        if not df_req.empty and "status" in df_req.columns:
            status_counts = df_req["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]

            # Delta-inspired color palette
            color_map = {
                "APPROVED": "#10B981",
                "REJECTED": "#EF4444",
                "PENDING_HUMAN_APPROVAL": "#F59E0B",
                "CANCELLED": "#94A3B8"
            }

            fig_donut = px.pie(
                status_counts,
                values="Count",
                names="Status",
                hole=0.55,
                color="Status",
                color_discrete_map=color_map
            )
            fig_donut.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No transaction data available yet.")

    with col_chart2:
        st.subheader("🛡️ Risk Severity Distribution")
        if not df_req.empty and "risk_level" in df_req.columns:
            risk_counts = df_req["risk_level"].value_counts().reset_index()
            risk_counts.columns = ["Risk Level", "Count"]

            risk_colors = {
                "LOW RISK": "#10B981",
                "MEDIUM RISK": "#F59E0B",
                "HIGH RISK": "#DC2626"
            }

            fig_bar = px.bar(
                risk_counts,
                x="Risk Level",
                y="Count",
                color="Risk Level",
                color_discrete_map=risk_colors,
                text="Count"
            )
            fig_bar.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False,
                xaxis_title="",
                yaxis_title="Total Transactions"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No risk profile data available.")

    # Second row of charts: Financial Route Distribution & Risk vs Amount Scatter
    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        st.subheader("✈️ Route Activity & Booking Volume")
        if not df_req.empty and "source_city" in df_req.columns:
            df_req["Route"] = df_req["source_city"] + " ➔ " + df_req["dest_city"]
            route_agg = df_req.groupby("Route").agg(
                Bookings=("id", "count"),
                Total_Value=("total_amount", "sum")
            ).reset_index().sort_values(by="Bookings", ascending=False).head(6)

            fig_route = px.bar(
                route_agg,
                x="Route",
                y="Bookings",
                color="Total_Value",
                color_continuous_scale="Blues",
                text="Bookings",
                labels={"Total_Value": "Total (₹)"}
            )
            fig_route.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_route, use_container_width=True)
        else:
            st.info("No route data recorded.")

    with col_chart4:
        st.subheader("🎯 Risk Score vs Transaction Value")
        if not df_req.empty and "risk_score" in df_req.columns:
            fig_scatter = px.scatter(
                df_req,
                x="total_amount",
                y="risk_score",
                color="status",
                size=[12]*len(df_req),
                hover_data=["id", "agent_name", "flight_number"],
                color_discrete_map={"APPROVED": "#10B981", "REJECTED": "#EF4444", "PENDING_HUMAN_APPROVAL": "#F59E0B"},
                labels={"total_amount": "Transaction Amount (₹)", "risk_score": "Risk Score (0-100)"}
            )
            fig_scatter.add_hline(y=70, line_dash="dash", line_color="#DC2626", annotation_text="High Risk Threshold (70)")
            fig_scatter.add_hline(y=35, line_dash="dot", line_color="#F59E0B", annotation_text="Medium Risk Threshold (35)")
            fig_scatter.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("No transaction scatter data.")

    st.markdown("---")

    # Recent Security Alerts Stream
    st.subheader("🚨 Live Security & Authorization Alerts Feed")
    alerts = AuditLogger.get_recent_alerts(limit=5)
    if alerts:
        for alert in alerts:
            sev = alert["severity"]
            badge_color = "#DC2626" if sev in ["CRITICAL", "ALERT"] else "#D97706"
            st.markdown(f"""
            <div style="background: #FFFFFF; border-left: 4px solid {badge_color}; border-radius: 6px; padding: 12px 16px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; color: {badge_color}; font-size: 0.85rem;">[{alert['severity']}] {alert['event_type']}</span>
                    <span style="color: #64748B; font-size: 0.75rem;">{alert['timestamp']}</span>
                </div>
                <div style="margin-top: 4px; color: #1E293B; font-size: 0.9rem;">{alert['action_details']}</div>
                <div style="margin-top: 4px; color: #64748B; font-size: 0.75rem;">Agent Ref: <code>{alert.get('agent_id') or 'SYSTEM'}</code></div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No critical security alerts currently reported.")
