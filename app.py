import datetime
import json
from pathlib import Path
import pandas as pd
import streamlit as st

from decay import BASE_DECAY_RATES, REFERENCE_TEMP_C, TEMP_COEFF_DOUBLING_INTERVAL
from decision import evaluate_options
from alerts import generate_alerts

# Set page configuration
st.set_page_config(
    page_title="Agri-Twin: Sell at the right time, place and price",
    page_icon="🌱",
    layout="wide",
)

# Custom clean professional styling: white background, teal headings, amber accents
st.markdown(
    """
    <style>
    /* Clean white background and typography */
    [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF;
        color: #1F2937;
    }
    
    /* Teal headings */
    h1, h2, h3, h4, .teal-heading {
        color: #0F766E !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Recommendation Card with amber highlight */
    .rec-card {
        background-color: #FFFBEB;
        border: 2px solid #F59E0B;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 20px;
    }
    .rec-card h3 {
        color: #B45309 !important;
        margin-top: 0;
        margin-bottom: 8px;
    }
    .rec-reason {
        font-size: 1.05rem;
        color: #78350F;
        line-height: 1.5;
        font-weight: 500;
    }
    
    /* Metrics block */
    div[data-testid="stMetricValue"] {
        color: #0F766E;
    }

    /* Subdued labels */
    .stSelectbox label, .stNumberInput label, .stSlider label, .stMultiSelect label, .stDateInput label {
        color: #374151;
        font-weight: 600;
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

# Header
st.title("Agri-Twin: Sell at the right time, place and price")
st.caption(
    "A digital twin decision engine helping smallholder farmers maximize harvest value "
    "by balancing market price dynamics, transport logistics, and post-harvest quality decay."
)

st.write("---")

# Main 2-column layout
col_left, col_right = st.columns([1, 1.6], gap="large")

with col_left:
    st.subheader("🌾 Harvest & Storage Inputs")
    
    # 1. Crop
    crop = st.selectbox(
        "Crop",
        options=["Tomato", "Onion"],
        index=0,
        help="Select crop type. Each crop has distinct post-harvest perishability characteristics."
    )
    
    # 2. Quantity (kg)
    quantity = st.number_input(
        "Quantity (kg)",
        min_value=1.0,
        max_value=100000.0,
        value=500.0,
        step=50.0,
        help="Total harvest weight in kilograms."
    )
    
    # 3. Harvest day
    harvest_date = st.date_input(
        "Harvest day",
        value=datetime.date.today(),
        help="Date when produce was harvested."
    )
    
    # 4. Quality on arrival at harvest
    quality_0 = st.slider(
        "Quality on arrival at harvest (%)",
        min_value=50,
        max_value=100,
        value=100,
        step=1,
        help="Visual and physical quality percentage at harvest (100% = optimal grade A)."
    )
    
    # 5. Storage temperature
    temp_c = st.number_input(
        "Storage temperature (°C)",
        min_value=0.0,
        max_value=50.0,
        value=25.0,
        step=1.0,
        help="Average on-farm storage ambient temperature used for holding produce."
    )
    
    # 6. Available markets
    selected_markets = st.multiselect(
        "Available markets",
        options=all_market_names,
        default=all_market_names,
        help="Select markets accessible for selling."
    )

with col_right:
    st.subheader("📊 Selling Opportunities & Recommendation")
    
    if not selected_markets:
        st.warning("Please select at least one market to evaluate selling options.")
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
            st.error("No valid options available for the selected parameters.")
        else:
            # Highlighted recommendation card
            st.markdown(
                f"""
                <div class="rec-card">
                    <h3>🏆 Recommended Action</h3>
                    <div class="rec-reason">{reason}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # Key metric highlights
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Recommended Market", recommendation["market"])
            m2.metric("Best Selling Day", recommendation["day"])
            m3.metric("Net Value / kg", f"₹{recommendation['net_per_kg']:.2f}")
            m4.metric("Total Net Earnings", f"₹{recommendation['total_net']:,.0f}")
            
            st.write("#### All Options (Ranked by Net Value)")
            
            # Format DataFrame for presentation
            df = pd.DataFrame(options)
            display_df = pd.DataFrame({
                "Market": df["market"],
                "Day": df["day"],
                "Days Held": df["days_held"],
                "Quality (%)": df["quality_on_arrival"].map(lambda x: f"{x:.1f}%"),
                "Price (₹/kg)": df["price"].map(lambda x: f"₹{x:.2f}"),
                "Transport (₹/kg)": df["transport_cost"].map(lambda x: f"₹{x:.2f}"),
                "Net (₹/kg)": df["net_per_kg"].map(lambda x: f"₹{x:.2f}"),
                "Total Net (₹)": df["total_net"].map(lambda x: f"₹{x:,.0f}"),
            })
            
            # Style the table: amber highlight on first row (the recommended option)
            def highlight_first_row(row):
                if row.name == 0:
                    return ["background-color: #FEF3C7; font-weight: bold; color: #92400E;"] * len(row)
                return [""] * len(row)

            styled_df = display_df.style.apply(highlight_first_row, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=280)

# Section below: Visual Bar Chart & Expanders
st.write("---")

if 'options' in locals() and options:
    st.subheader("📈 Net Value Comparison Across All Options (₹/kg)")
    
    chart_data = pd.DataFrame({
        "Option": [f"{opt['market']} ({opt['day']})" for opt in options],
        "Net Value (₹/kg)": [opt["net_per_kg"] for opt in options],
    }).set_index("Option")
    
    st.bar_chart(chart_data, height=320)
    
    # Expanders
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        with st.expander("📲 Show Alert Message (English & Tamil)", expanded=True):
            en_alert, ta_alert = generate_alerts(recommendation, crop=crop)
            
            st.markdown("**English Alert (SMS / WhatsApp):**")
            st.code(en_alert, language="text")
            st.caption(f"Character count: {len(en_alert)} / 200")
            
            st.markdown("**Tamil Alert (தமிழ் குறுஞ்செய்தி):**")
            st.code(ta_alert, language="text")
            st.caption(f"Character count: {len(ta_alert)} / 200 (Subject to native speaker review)")

    with col_exp2:
        with st.expander("ℹ️ Assumptions & Model Calibration", expanded=True):
            st.markdown(
                f"""
                - **Quality Decay Model:**
                  - Exponential decay formula: $q(t) = q_0 \\cdot e^{{-k_{{\\text{{eff}}}} \\cdot t}}$
                  - Temperature adjustment: $k_{{\\text{{eff}}}} = k \\cdot 2^{{(T - {REFERENCE_TEMP_C}) / {TEMP_COEFF_DOUBLING_INTERVAL}}}$
                  - Base decay constants at {REFERENCE_TEMP_C}°C:
                    - **Tomato:** `{BASE_DECAY_RATES['Tomato']}` / day
                    - **Onion:** `{BASE_DECAY_RATES['Onion']}` / day
                - **Mock Market Prices:**
                  - Market prices and transport figures in `data/markets.json` are **illustrative and fictional placeholders** for hackathon demonstration.
                  - In real production, plug in live AGMARKNET or APMC mandi API feeds.
                """
            )
