"""
AirGuard AI - Page 4: Flight Search & Airline Inventory (Module 5)
Simulated Delta Air Lines flight schedules, route explorer, and pricing lookup.
"""

import streamlit as st
import pandas as pd
from flight_service import FlightService
from utils.helpers import render_delta_header, format_currency

def render_flights_page():
    render_delta_header(
        title="Delta Air Lines Schedule & Inventory Explorer",
        subtitle="Simulated domestic routes connecting Delhi, Mumbai, Bengaluru, Hyderabad, Chennai, Kolkata, Pune and Goa",
        tag="SIMULATED INVENTORY"
    )

    cities = FlightService.get_supported_cities()

    # Search Filter Bar
    with st.expander("🔍 Search & Filter Flights", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            source = st.selectbox("Origin City", ["ALL"] + cities, index=0)
        with c2:
            destination = st.selectbox("Destination City", ["ALL"] + cities, index=0)
        with c3:
            cabin = st.selectbox("Cabin Class", ["ALL", "Economy", "Comfort+", "First Class"], index=0)
        with c4:
            max_price = st.number_input("Max Base Price (₹)", min_value=0, max_value=50000, value=0, step=1000, help="0 means no price limit")

    flights = FlightService.search_flights(
        source=None if source == "ALL" else source,
        destination=None if destination == "ALL" else destination,
        cabin_class=None if cabin == "ALL" else cabin,
        max_price=None if max_price == 0 else max_price
    )

    st.write(f"Showing **{len(flights)}** flights matching query:")

    if not flights:
        st.warning("No flights found matching the selected criteria. Try adjusting your filters.")
        return

    # Render Flight Cards
    for fl in flights:
        with st.container():
            st.markdown(f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 18px; margin-bottom: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #F1F5F9; padding-bottom: 10px; margin-bottom: 12px;">
                    <div>
                        <span style="background: #001A49; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.8rem;">{fl['flight_number']}</span>
                        <span style="margin-left: 8px; color: #64748B; font-size: 0.85rem;">{fl['airline_name']} · {fl['aircraft_type']}</span>
                    </div>
                    <div>
                        <span style="font-size: 1.25rem; font-weight: 700; color: #0067C5;">{format_currency(fl['base_price'])}</span>
                        <span style="font-size: 0.75rem; color: #64748B;"> / seat</span>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="font-size: 1.2rem; font-weight: 700; color: #0F172A;">{fl['departure_time']}</div>
                        <div style="font-size: 0.9rem; font-weight: 600; color: #334155;">{fl['source_city']}</div>
                    </div>
                    <div style="flex: 1; text-align: center;">
                        <div style="font-size: 0.8rem; color: #64748B;">⏱️ {fl['duration']}</div>
                        <div style="height: 2px; background: #CBD5E1; margin: 4px 15px; position: relative;">
                            <span style="position: absolute; top: -6px; right: 45%; color: #0067C5; font-size: 0.8rem;">✈️</span>
                        </div>
                        <div style="font-size: 0.75rem; color: #10B981; font-weight: 600;">Direct Non-Stop</div>
                    </div>
                    <div style="flex: 1; text-align: right;">
                        <div style="font-size: 1.2rem; font-weight: 700; color: #0F172A;">{fl['arrival_time']}</div>
                        <div style="font-size: 0.9rem; font-weight: 600; color: #334155;">{fl['dest_city']}</div>
                    </div>
                </div>
                <div style="margin-top: 12px; display: flex; justify-content: space-between; font-size: 0.8rem; color: #64748B;">
                    <span>Cabin: <b>{fl['cabin_class']}</b></span>
                    <span>Available Seats: <b style="color: {'#10B981' if fl['available_seats'] > 10 else '#DC2626'};">{fl['available_seats']} left</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
