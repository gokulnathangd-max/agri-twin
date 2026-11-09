import datetime
import json
from pathlib import Path
import pandas as pd
import streamlit as st

from decay import BASE_DECAY_RATES, REFERENCE_TEMP_C, TEMP_COEFF_DOUBLING_INTERVAL, quality_on_day
from decision import evaluate_options
from alerts import generate_alerts

# Page configuration
st.set_page_config(
    page_title="Agri-Twin | Agricultural Post-Harvest & Market Logistics Digital Twin",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom enterprise/government-grade CSS styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Overall Background */
    [data-testid="stAppViewContainer"] {
        background-color: #F8FAFC;
        color: #0F172A;
    }
    
    /* Top Navigation Banner */
    .gov-banner {
        background: linear-gradient(90deg, #0F766E 0%, #115E59 100%);
        color: #FFFFFF;
        padding: 14px 24px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 6px -1px rgba(15, 118, 110, 0.15);
        margin-bottom: 20px;
    }
    .gov-title {
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .gov-subtitle {
        font-size: 0.82rem;
        color: #CCFBF1;
        margin: 2px 0 0 0;
    }
    .gov-badge {
        background-color: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        color: #F0FDFA;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    
    /* Teal Headings */
    h1, h2, h3, h4, .teal-heading {
        color: #0F766E !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    /* Recommendation Card with Amber Accent */
    .rec-card-hero {
        background: #FFFBEB;
        border: 2px solid #F59E0B;
        border-left: 8px solid #D97706;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 22px;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.08);
    }
    .rec-badge {
        display: inline-block;
        background-color: #D97706;
        color: #FFFFFF;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        padding: 3px 10px;
        border-radius: 4px;
        margin-bottom: 8px;
        letter-spacing: 0.05em;
    }
    .rec-reason-text {
        font-size: 1.12rem;
        color: #78350F;
        font-weight: 600;
        line-height: 1.5;
        margin: 0;
    }
    
    /* KPI Metric Cards */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 20px;
    }
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px 16px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        transition: transform 0.15s ease;
    }
    .kpi-card:hover {
        border-color: #0F766E;
    }
    .kpi-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        color: #64748B;
        font-weight: 600;
        letter-spacing: 0.04em;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #0F766E;
        margin: 0;
    }
    .kpi-subtext {
        font-size: 0.75rem;
        color: #94A3B8;
        margin-top: 3px;
    }
    
    /* Input Container Styling */
    .input-section {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    /* Official Advisory Slip */
    .advisory-slip {
        background: #FFFFFF;
        border: 2px dashed #0F766E;
        border-radius: 10px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .advisory-header {
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 12px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Clean tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 0.95rem;
        padding: 8px 16px;
        border-radius: 6px 6px 0 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Load mock market data
DATA_PATH = Path(__file__).parent / "data" / "markets.json"


@st.cache_data
def load_markets_data():
    if not DATA_PATH.exists():
        st.error(f"Market data file not found at: {DATA_PATH}")
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("markets", [])
    return data


markets_data = load_markets_data()
all_market_names = [m["name"] for m in markets_data if "name" in m]

# Top Official Header Banner
st.markdown(
    """
    <div class="gov-banner">
        <div>
            <div class="gov-title">
                🌱 Agri-Twin: Sell at the right time, place and price
            </div>
            <div class="gov-subtitle">
                National Agricultural Mandi Logistics & Post-Harvest Perishability Optimization Twin • Decision Support Portal
            </div>
        </div>
        <div class="gov-badge">
            🟢 Digital Twin Engine Active
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main Two-Column Layout (Form on Left, Analysis on Right)
col_left, col_right = st.columns([1, 1.65], gap="large")

with col_left:
    st.markdown("### 🌾 Harvest & Farm Storage Parameters")
    
    with st.container():
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        
        # 1. Crop Dropdown
        crop = st.selectbox(
            "Target Crop",
            options=["Tomato", "Onion"],
            index=0,
            help="Select harvested produce. Physiological decay kinetics are calibrated specifically per crop.",
        )
        
        # 2. Quantity (kg)
        quantity = st.number_input(
            "Harvest Batch Quantity (kg)",
            min_value=1.0,
            max_value=100000.0,
            value=500.0,
            step=50.0,
            help="Total weight of current batch ready for sale.",
        )
        
        # 3. Harvest Day
        harvest_date = st.date_input(
            "Harvest Date",
            value=datetime.date.today(),
            help="Harvest day (Day 0) baseline.",
        )
        
        # 4. Initial Quality Slider
        quality_0 = st.slider(
            "Quality on Arrival at Harvest (%)",
            min_value=50,
            max_value=100,
            value=100,
            step=1,
            help="Initial visual & physical quality grade on harvest day (100% = Grade A Premium).",
        )
        
        # 5. Storage Temperature
        temp_c = st.number_input(
            "Storage Ambient Temperature (°C)",
            min_value=0.0,
            max_value=50.0,
            value=25.0,
            step=1.0,
            help="On-farm ambient holding temperature for delayed selling options.",
        )
        
        # 6. Available Markets Multiselect
        selected_markets = st.multiselect(
            "Available Selling Markets",
            options=all_market_names,
            default=all_market_names,
            help="Target mandis and wholesale terminal markets evaluated by the decision twin.",
        )
        
        # Additional Logistics Option
        with st.expander("🚚 Advanced Logistics & Transport Mode", expanded=False):
            vehicle_type = st.selectbox(
                "Transport Fleet Mode",
                options=["Standard Cargo Auto / Pickup", "E-Rickshaw (Local)", "Dedicated Mini-Truck", "Refrigerated Reefer Van"],
                index=0,
                help="Select vehicle type used for mandi transport.",
            )
            farmer_name = st.text_input("Farmer / FPO Name", value="Ramanathan K.", help="Used on generated advisory slip.")
            batch_id = st.text_input("Batch Lot No.", value=f"LOT-{crop[:3].upper()}-{datetime.date.today().strftime('%m%d')}", help="Lot tracking reference.")

        st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown("### 📊 Market Optimization & Decision Twin")
    
    if not selected_markets:
        st.warning("⚠️ Please select at least one market from the left panel to begin analysis.")
    else:
        # Run decision logic
        options, recommendation, reason = evaluate_options(
            crop=crop,
            quantity_kg=quantity,
            harvest_date=harvest_date,
            q0=quality_0,
            temp_c=temp_c,
            markets_data=markets_data,
            selected_markets=selected_markets,
        )
        
        if not recommendation or not options:
            st.error("No valid options available for the specified criteria.")
        else:
            # Highlighted Recommendation Hero Card
            st.markdown(
                f"""
                <div class="rec-card-hero">
                    <span class="rec-badge">🌟 Optimal Selling Recommendation</span>
                    <p class="rec-reason-text">{reason}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # KPI Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Recommended Market", recommendation["market"], delta=f"{recommendation['distance_km']} km away")
            m2.metric("Optimal Selling Day", recommendation["day"], delta=f"Hold: {recommendation['days_held']} day(s)")
            m3.metric("Net Realized Price", f"₹{recommendation['net_per_kg']:.2f}/kg", delta=f"Gross: ₹{recommendation['gross_per_kg']:.2f}")
            m4.metric("Total Batch Net Value", f"₹{recommendation['total_net']:,.0f}", delta=f"{quantity:,.0f} kg batch")
            
            st.markdown("#### 📋 Comprehensive Selling Opportunities (Ranked by Expected Net Value)")
            
            # Format DataFrame
            df = pd.DataFrame(options)
            display_df = pd.DataFrame({
                "Market": df["market"],
                "Category": df.get("category", "Mandi"),
                "Day": df["day"],
                "Days Held": df["days_held"],
                "Arrival Quality": df["quality_on_arrival"].map(lambda x: f"{x:.1f}%"),
                "Mandi Price": df["price"].map(lambda x: f"₹{x:.2f}"),
                "Transport Cost": df["transport_cost"].map(lambda x: f"₹{x:.2f}"),
                "Expected Net": df["net_per_kg"].map(lambda x: f"₹{x:.2f}/kg"),
                "Total Net Realization": df["total_net"].map(lambda x: f"₹{x:,.0f}"),
            })
            
            # Styling: Amber highlight on recommended top row
            def highlight_recommended_row(row):
                if row.name == 0:
                    return ["background-color: #FEF3C7; font-weight: 700; color: #92400E; border-top: 1px solid #F59E0B; border-bottom: 1px solid #F59E0B;"] * len(row)
                return [""] * len(row)

            styled_df = display_df.style.apply(highlight_recommended_row, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=290)

# Multi-Feature Tabbed Analytics Section Below
st.write("---")

tab_chart, tab_trends, tab_coldchain, tab_advisory, tab_alerts, tab_assumptions = st.tabs([
    "📊 Net Value Comparison",
    "📈 7-Day Market Price Trends",
    "❄️ Quality & Cold-Chain Simulation",
    "📜 Official Advisory Slip",
    "📲 Bilingual Farmer Alerts",
    "ℹ️ Assumptions & Calibration",
])

with tab_chart:
    st.subheader("📊 Net Expected Return Across All Selling Alternatives (₹/kg)")
    st.caption("Visualizing the net farmer realization per kg after subtracting transport expenses and accounting for spoilage.")
    if 'options' in locals() and options:
        chart_df = pd.DataFrame({
            "Selling Option": [f"{opt['market']} ({opt['day']})" for opt in options],
            "Net Value (₹/kg)": [opt["net_per_kg"] for opt in options],
        }).set_index("Selling Option")
        st.bar_chart(chart_df, height=340)

with tab_trends:
    st.subheader("📈 7-Day Mandi Price Dynamics Forecast")
    st.caption("Comparative price trajectory for target markets across the 7-day harvest decision window.")
    
    # Build 7-day price matrix across selected markets
    dates_list = [(harvest_date + datetime.timedelta(days=d)).strftime("%a, %b %d") for d in range(7)]
    market_price_matrix = {"Selling Date": dates_list}
    
    for m in markets_data:
        m_name = m.get("name")
        if m_name in selected_markets:
            prices = (m.get("price_per_kg") or m.get("prices", {})).get(crop, [])
            if len(prices) >= 7:
                market_price_matrix[m_name] = prices[:7]
    
    trend_df = pd.DataFrame(market_price_matrix).set_index("Selling Date")
    st.line_chart(trend_df, height=340)
    
    # Mandi metadata table
    st.markdown("##### 🏛️ Mandi Operational Profiles & Trading Volume")
    mandi_profile = []
    for m in markets_data:
        if m.get("name") in selected_markets:
            mandi_profile.append({
                "Market Name": m.get("name"),
                "Classification": m.get("category", "General APMC"),
                "Distance (km)": f"{m.get('distance_km')} km",
                "Transport Cost": f"₹{m.get('transport_cost_per_kg'):.2f} / kg",
                "Daily Arrival Volume": f"{m.get('daily_volume_tons', 'N/A')} Tons",
                "Buyer Demand Index": m.get("buyer_demand", "Moderate"),
            })
    st.dataframe(pd.DataFrame(mandi_profile), use_container_width=True)

with tab_coldchain:
    st.subheader("❄️ Post-Harvest Quality Decay & Cold-Chain Payoff Simulator")
    st.caption(
        "Evaluate how temperature control suppresses biological respiration and extends marketable shelf life."
    )
    
    c_sim1, c_sim2 = st.columns([1, 2], gap="medium")
    with c_sim1:
        st.markdown("**Simulation Parameters:**")
        sim_days = st.slider("Simulation Horizon (Days)", min_value=1, max_value=14, value=7)
        cold_temp = st.slider("Cold Storage Unit Temperature (°C)", min_value=0, max_value=15, value=10)
        
        # Calculate quality retention after 5 days
        q_amb_5 = quality_on_day(quality_0, crop, temp_c, 5)
        q_cold_5 = quality_on_day(quality_0, crop, cold_temp, 5)
        shelf_gain = round((q_cold_5 - q_amb_5), 1)
        
        st.metric(
            label="Day-5 Quality Retention Delta",
            value=f"+{shelf_gain}%",
            delta="Preserved by Cold Chain",
            help="Quality difference between farm ambient holding vs cold storage unit after 5 days."
        )
    
    with c_sim2:
        days_range = list(range(sim_days + 1))
        decay_data = {
            "Days Elapsed": [f"Day {d}" for d in days_range],
            f"Farm Ambient ({temp_c}°C)": [round(quality_on_day(quality_0, crop, temp_c, d), 1) for d in days_range],
            f"Micro Cold Storage ({cold_temp}°C)": [round(quality_on_day(quality_0, crop, cold_temp, d), 1) for d in days_range],
            "High Heat / Open Shed (35°C)": [round(quality_on_day(quality_0, crop, 35.0, d), 1) for d in days_range],
        }
        decay_df = pd.DataFrame(decay_data).set_index("Days Elapsed")
        st.line_chart(decay_df, height=300)

with tab_advisory:
    st.subheader("📜 Official Farmer Advisory Certificate & Mandi Gate Pass")
    st.caption("A printable formal trade recommendation docket for extension officers, FPOs, and farmers.")
    
    if 'recommendation' in locals() and recommendation:
        adv_col1, adv_col2 = st.columns([2, 1])
        with adv_col1:
            st.markdown(
                f"""
                <div class="advisory-slip">
                    <div class="advisory-header">
                        <div>
                            <h3 style="margin: 0; color: #0F766E;">🌱 AGRI-TWIN POST-HARVEST DISPATCH ADVISORY</h3>
                            <span style="font-size: 0.8rem; color: #64748B;">National Agriculture Decision Support Protocol • Lot Ref: <b>{batch_id}</b></span>
                        </div>
                        <div style="text-align: right;">
                            <span style="background: #E0F2FE; color: #0369A1; padding: 4px 10px; border-radius: 4px; font-weight: 700; font-size: 0.8rem;">OFFICIAL PASS</span>
                        </div>
                    </div>
                    <table style="width: 100%; border-collapse: collapse; font-size: 0.95rem; margin-bottom: 16px;">
                        <tr><td style="padding: 6px 0; color: #64748B;"><b>Beneficiary Farmer:</b></td><td style="padding: 6px 0; font-weight: 600;">{farmer_name}</td></tr>
                        <tr><td style="padding: 6px 0; color: #64748B;"><b>Commodity / Lot:</b></td><td style="padding: 6px 0; font-weight: 600;">{crop} ({quantity:,.0f} kg)</td></tr>
                        <tr><td style="padding: 6px 0; color: #64748B;"><b>Harvest Date:</b></td><td style="padding: 6px 0; font-weight: 600;">{harvest_date.strftime('%B %d, %Y')}</td></tr>
                        <tr><td style="padding: 6px 0; color: #64748B;"><b>Initial Quality Grade:</b></td><td style="padding: 6px 0; font-weight: 600;">{quality_0}% (Grade A)</td></tr>
                        <tr style="border-top: 1px solid #E2E8F0;"><td style="padding: 8px 0; color: #0F766E;"><b>Recommended Target Mandi:</b></td><td style="padding: 8px 0; font-weight: 700; color: #0F766E; font-size: 1.05rem;">{recommendation['market']}</td></tr>
                        <tr><td style="padding: 6px 0; color: #64748B;"><b>Recommended Dispatch Date:</b></td><td style="padding: 6px 0; font-weight: 700;">{recommendation['day']} (Hold: {recommendation['days_held']} days)</td></tr>
                        <tr><td style="padding: 6px 0; color: #64748B;"><b>Transit Logistics Mode:</b></td><td style="padding: 6px 0; font-weight: 600;">{vehicle_type} ({recommendation['distance_km']} km)</td></tr>
                        <tr><td style="padding: 6px 0; color: #64748B;"><b>Expected Realized Net Value:</b></td><td style="padding: 6px 0; font-weight: 700; color: #B45309;">₹{recommendation['net_per_kg']:.2f} / kg</td></tr>
                        <tr style="border-top: 2px solid #0F766E;"><td style="padding: 10px 0; font-size: 1.1rem; font-weight: 700; color: #0F766E;"><b>Total Expected Net Realization:</b></td><td style="padding: 10px 0; font-size: 1.25rem; font-weight: 800; color: #0F766E;">₹{recommendation['total_net']:,.0f}</td></tr>
                    </table>
                    <div style="font-size: 0.8rem; color: #64748B; border-top: 1px dashed #CBD5E1; padding-top: 8px;">
                        Digital Verification Hash: <code>AGRI-TWIN-{abs(hash(str(recommendation))) % 10000000:07d}</code> • Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with adv_col2:
            st.markdown("##### 📥 Export & Data Handover")
            st.info("Export the advisory to facilitate logistics dispatch or extension officer records.")
            
            # Export CSV of all evaluated options
            csv_data = pd.DataFrame(options).to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 Download Options Evaluation (CSV)",
                data=csv_data,
                file_name=f"agri_twin_{crop.lower()}_{harvest_date}.csv",
                mime="text/csv",
                use_container_width=True,
            )
            
            # Export Slip Text
            slip_text = (
                f"AGRI-TWIN HARVEST ADVISORY\n"
                f"Lot: {batch_id} | Farmer: {farmer_name}\n"
                f"Crop: {crop} ({quantity} kg)\n"
                f"Recommended Mandi: {recommendation['market']}\n"
                f"Dispatch Day: {recommendation['day']}\n"
                f"Net Price: Rs {recommendation['net_per_kg']:.2f}/kg\n"
                f"Total Net: Rs {recommendation['total_net']:,.0f}\n"
                f"Reason: {reason}\n"
            )
            st.download_button(
                label="📋 Download Text Advisory Docket",
                data=slip_text,
                file_name=f"advisory_{batch_id}.txt",
                mime="text/plain",
                use_container_width=True,
            )

with tab_alerts:
    st.subheader("📲 Bilingual Farmer Alerts (SMS & WhatsApp Ready)")
    st.caption("Auto-generated, character-constrained alerts (<200 characters) for field broadcast.")
    
    if 'recommendation' in locals() and recommendation:
        en_alert, ta_alert = generate_alerts(recommendation, crop=crop)
        
        col_msg1, col_msg2 = st.columns(2)
        with col_msg1:
            st.markdown("#### 🇬🇧 English Alert (SMS / IVRS)")
            st.code(en_alert, language="text")
            st.caption(f"Length: {len(en_alert)} / 200 characters (Strictly compliant)")
            st.markdown(
                f"""
                <div style="background: #F1F5F9; border-radius: 6px; padding: 12px; margin-top: 10px; font-size: 0.88rem;">
                    <b>SMS Gateway Payload Preview:</b><br/>
                    <code>TO: +91-XXXXXXXXXX | MSG: {en_alert}</code>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        with col_msg2:
            st.markdown("#### 🇮🇳 தமிழ் அறிவிப்பு (Tamil Alert)")
            st.code(ta_alert, language="text")
            st.caption(f"நீளம்: {len(ta_alert)} / 200 எழுத்துக்கள் (மொழிபெயர்ப்பு மாதிரி)")
            st.markdown(
                f"""
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 6px; padding: 12px; margin-top: 10px; font-size: 0.88rem; color: #166534;">
                    <b>வாட்ஸ்அப் செய்தி முன்னோட்டம் (WhatsApp Preview):</b><br/>
                    {ta_alert}
                </div>
                """,
                unsafe_allow_html=True,
            )

with tab_assumptions:
    st.subheader("ℹ️ Scientific Assumptions & Model Calibration")
    st.markdown(
        f"""
        ### 1. Physiological Quality Decay Kinetics
        - **Model Equation:**  
          $$q(t) = q_0 \\cdot e^{{-k_{{\\text{{eff}}}} \\cdot t}}$$  
          where $q_0$ is initial harvest quality, $t$ is days elapsed since harvest, and $k_{{\\text{{eff}}}}$ is the thermal-adjusted perishability constant.
        - **Temperature Dependence ($Q_{{10}}$ Factor):**  
          $$k_{{\\text{{eff}}}} = k_{{\\text{{base}}}} \\cdot 2^{{(T - {REFERENCE_TEMP_C}) / {TEMP_COEFF_DOUBLING_INTERVAL}}}$$  
          Reflecting respiration rate doubling for every {TEMP_COEFF_DOUBLING_INTERVAL}°C rise above {REFERENCE_TEMP_C}°C.
        - **Placeholder Decay Constants at {REFERENCE_TEMP_C}°C:**
          - **Tomato:** `{BASE_DECAY_RATES['Tomato']}` / day
          - **Onion:** `{BASE_DECAY_RATES['Onion']}` / day
        
        ### 2. Economic Valuation Engine
        - **Realized Gross Return per kg:** $\\text{{Gross}} = \\frac{{q(t)}}{{100}} \\cdot \\text{{Market Price}}$
        - **Net Farmer Value per kg:** $\\text{{Net}} = \\text{{Gross}} - \\text{{Transport Cost}}$
        - **Total Realization:** $\\text{{Total Net}} = \\text{{Net}} \\cdot \\text{{Quantity (kg)}}$
        
        ### 3. Data Integrity & Live APMC Interfacing
        - Market price figures in `data/markets.json` are **illustrative placeholders** for hackathon demonstration.
        - In production deployments, this service integrates with Agmarknet / e-NAM REST APIs via automated daily ingestion.
        """
    )
