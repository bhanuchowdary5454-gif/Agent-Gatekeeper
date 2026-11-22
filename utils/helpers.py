"""
AirGuard AI - UI Helpers and Delta Air Lines Styling Components
"""

import streamlit as st

DELTA_CSS = """
<style>
    /* Delta Air Lines Brand Colors */
    :root {
        --delta-navy: #001A49;
        --delta-red: #E01933;
        --delta-sky: #0067C5;
        --delta-light: #F4F7FC;
        --delta-card-border: #E2E8F0;
    }

    /* Top Banner Styling */
    .delta-banner {
        background: linear-gradient(135deg, #001A49 0%, #002B7A 50%, #003F9E 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 14px rgba(0, 26, 73, 0.2);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .delta-banner h1 {
        color: #FFFFFF !important;
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .delta-banner p {
        color: #CAD7F0 !important;
        margin: 0.3rem 0 0 0;
        font-size: 0.95rem;
    }
    .delta-badge-red {
        background-color: #E01933;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
        text-transform: uppercase;
    }

    /* KPI Cards */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        border-top: 4px solid #0067C5;
        transition: transform 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-title {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.4rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-subtitle {
        font-size: 0.75rem;
        color: #94A3B8;
        margin-top: 0.2rem;
    }

    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-approved { background-color: #DCFCE7; color: #166534; border: 1px solid #86EFAC; }
    .badge-rejected { background-color: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }
    .badge-pending { background-color: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
    .badge-revoked { background-color: #7F1D1D; color: #FFFFFF; border: 1px solid #991B1B; }
    .badge-active { background-color: #E0F2FE; color: #075985; border: 1px solid #7DD3FC; }
    .badge-inactive { background-color: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }

    /* Risk Badges */
    .risk-low { background-color: #DCFCE7; color: #15803D; font-weight: 700; padding: 2px 8px; border-radius: 4px; }
    .risk-medium { background-color: #FEF3C7; color: #B45309; font-weight: 700; padding: 2px 8px; border-radius: 4px; }
    .risk-high { background-color: #FEE2E2; color: #B91C1C; font-weight: 700; padding: 2px 8px; border-radius: 4px; }

    /* Trace timeline card */
    .trace-step {
        border-left: 3px solid #0067C5;
        padding-left: 1rem;
        margin-bottom: 1rem;
        position: relative;
    }
</style>
"""

def inject_custom_css():
    """Inject Delta brand styles into Streamlit page."""
    st.markdown(DELTA_CSS, unsafe_allow_html=True)

def render_delta_header(title: str, subtitle: str, tag: str = "SECURITY GATEKEEPER"):
    """Render a unified top banner across all pages."""
    st.markdown(f"""
    <div class="delta-banner">
        <div>
            <h1>✈️ {title}</h1>
            <p>{subtitle}</p>
        </div>
        <div style="text-align: right;">
            <span class="delta-badge-red">{tag}</span>
            <div style="font-size: 0.75rem; color: #CAD7F0; margin-top: 5px;">Delta Air Lines · AI Trust Framework</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_metric_card(title: str, value: any, subtitle: str = "", border_color: str = "#0067C5"):
    """Render a clean custom HTML metric card."""
    st.markdown(f"""
    <div class="metric-card" style="border-top-color: {border_color};">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def format_currency(amount: float) -> str:
    """Format currency in INR standard format."""
    return f"₹{amount:,.2f}"

def render_status_pill(status: str) -> str:
    status_lower = status.lower()
    if "approve" in status_lower:
        return f'<span class="status-badge badge-approved">✓ {status}</span>'
    elif "pending" in status_lower:
        return f'<span class="status-badge badge-pending">⏳ {status}</span>'
    elif "revok" in status_lower:
        return f'<span class="status-badge badge-revoked">🚫 {status}</span>'
    elif "active" in status_lower:
        return f'<span class="status-badge badge-active">● {status}</span>'
    elif "inactive" in status_lower:
        return f'<span class="status-badge badge-inactive">○ {status}</span>'
    else:
        return f'<span class="status-badge badge-rejected">✕ {status}</span>'

def render_risk_pill(risk_level: str, score: int = None) -> str:
    score_txt = f" ({score}/100)" if score is not None else ""
    if "low" in risk_level.lower():
        return f'<span class="risk-low">🛡️ {risk_level}{score_txt}</span>'
    elif "medium" in risk_level.lower():
        return f'<span class="risk-medium">⚠️ {risk_level}{score_txt}</span>'
    else:
        return f'<span class="risk-high">🚨 {risk_level}{score_txt}</span>'
