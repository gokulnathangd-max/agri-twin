# 🌱 Agri-Twin: Harvest Selling Decision Support System

> **Hackathon Prototype**: A decision engine helping smallholder farmers decide when and where to sell harvested produce to achieve maximum net value before quality deteriorates.

---

## 🎯 Goal

Smallholder farmers often face a tough dilemma right after harvest:
1. **Sell immediately** at the local village mandi at prevailing low spot prices.
2. **Hold produce** and transport it to a higher-paying town or city market on a later day, bearing storage quality decay and transport expenses.

**Agri-Twin** evaluates realistic multi-day and multi-market selling options, models post-harvest perishability under on-farm storage temperatures, subtracts logistics costs, and recommends the optimal market and selling day with clear, plain-language reasoning and SMS-ready bilingual alerts.

---

## 🏗️ Project Structure

```text
agri-twin/
├── app.py              # Streamlit web UI (inputs, comparison table, chart, alerts)
├── decay.py            # Post-harvest quality decay model & temperature scaling
├── decision.py         # Multi-market multi-day net value decision engine
├── alerts.py           # Bilingual SMS/notification generator (English & Tamil)
├── data/
│   └── markets.json    # Illustrative mock market prices and transport costs
├── tests/
│   ├── test_decay.py   # Unit tests for decay dynamics and temperature factors
│   ├── test_decision.py# Unit tests for recommendation ranking and edge cases
│   └── test_alerts.py  # Unit tests for message character limits (<200 chars)
├── requirements.txt    # Project dependencies
└── README.md           # Documentation and guide
```

---

## 🚀 Setup & Installation

### 1. Create and Activate Virtual Environment
```bash
# On Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell):
python -m venv venv
venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 💻 How to Run

### Run the Web Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### Run the Test Suite
```bash
pytest
```
Or for detailed output:
```bash
pytest -v
```

---

## 🔬 What is Simulated

This hackathon prototype uses three primary simulated components:

1. **Mock Market Prices (`data/markets.json`)**:
   - Includes 3 illustrative markets:
     - **Village Market** (2 km, ₹0.5/kg transport)
     - **Town Market** (25 km, ₹2.0/kg transport)
     - **City Market** (60 km, ₹4.5/kg transport)
   - Prices across 7 consecutive days are synthetic estimates reflecting typical regional spreads (e.g. Tomato between ₹18–₹30/kg, Onion between ₹24–₹32/kg).

2. **Quality Decay Model (`decay.py`)**:
   - Produce degrades exponentially:  
     $$q(t) = q_0 \cdot \exp(-k_{\text{eff}} \cdot t)$$
   - Base decay rates at reference temperature $25^\circ\text{C}$:
     - Tomato: $k = 0.08\text{ day}^{-1}$
     - Onion: $k = 0.03\text{ day}^{-1}$
   - Temperature coefficient ($Q_{10}$ approximation):  
     $$k_{\text{eff}} = k_{\text{base}} \cdot 2^{(T - 25) / 10}$$
   - When produce is held longer or stored at higher temperatures, quality degrades faster, reducing realized gross revenue:
     $$\text{Gross} = \frac{q(t)}{100} \cdot \text{Price}$$
     $$\text{Net/kg} = \text{Gross} - \text{Transport Cost/kg}$$

3. **Tamil Alert Template (`alerts.py`)**:
   - Fixed format string with Tamil crop and weekday names:
     `"Agri-Twin: {crop} பயிரை {day} அன்று {market} சந்தையில் விற்கவும். நிகர விலை: ₹{net_per_kg}/கிலோ (மொத்தம் ₹{total_net})."`
   - Strictly designed to remain under 200 characters for SMS / WhatsApp transmission.
   - *Note: Translations are placeholders and must be verified by a native Tamil speaker prior to field deployment.*

---

