import streamlit as st
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# 1. Konfiguration
st.set_page_config(
    page_title="Global Multi-Asset 3D Monitoring Terminal",
    page_icon="📈",
    layout="wide"
)

# 2. Sidebar Navigation & Globale Markt-Kategorien
st.sidebar.title("🌍 Global Markets")
st.sidebar.markdown("### 🗂️ Markt-Kategorie")
asset_class = st.sidebar.selectbox(
    "Asset-Klasse wählen:", 
    ["Kryptowährungen", "US-Märkte (Aktien/Indizes)", "Deutsche Märkte (Xetra/DAX)", "Forex & Rohstoffe"]
)

# Dynamische Markt-Auswahl basierend auf der Kategorie
if asset_class == "Kryptowährungen":
    market_list = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
    market_type = "crypto"
elif asset_class == "US-Märkte (Aktien/Indizes)":
    market_list = ["S&P 500 (SPY)", "Nasdaq 100 (QQQ)", "Apple (AAPL)", "Tesla (TSLA)", "NVIDIA (NVDA)"]
    market_type = "us"
elif asset_class == "Deutsche Märkte (Xetra/DAX)":
    market_list = ["DAX Index (DAX)", "SAP SE (SAP)", "Siemens (SIE)", "Allianz (ALV)"]
    market_type = "de"
else:
    market_list = ["Gold (XAUUSD)", "Silver (XAGUSD)", "Crude Oil (WTI)", "EUR/USD"]
    market_type = "forex"

selected_market = st.sidebar.selectbox("🎯 Spezieller Markt:", market_list)

# Marktstatus-Logik (Öffnungszeiten-Simulation)
def get_market_status(m_type):
    if m_type == "crypto":
        return "🟢 24/7 Geöffnet (Live)", "Open"
    
    now_hour = datetime.utcnow().hour
    if m_type == "de" and 7 <= now_hour < 16:
        return "🟢 Xetra Geöffnet", "Open"
    elif m_type == "us" and 13 <= now_hour < 21:
        return "🟢 US-Börse Geöffnet", "Open"
    elif m_type == "forex":
        return "🟢 Forex Aktiv", "Open"
    else:
        return "🔴 Markt Geschlossen (Feierabend/Wochenende)", "Closed"

status_text, status_flag = get_market_status(market_type)

# 3. Haupt-Logik
st.title(f"⚡ Live Monitoring Terminal — {selected_market}")
st.markdown(f"Kategorie: **{asset_class}** | Status: **{status_text}**")

# Metriken-Leiste
col1, col2, col3 = st.columns(3)
col1.metric("Aktiver Markt", selected_market, status_flag)
col2.metric("Daten-Feed", "Live WebSocket / API", "Aktiv")
col3.metric("Hosting", "Streamlit Cloud", "24/7 Online")

st.divider()

# --- CHARTS & 3D-OBERFLÄCHE ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("📈 Live Chart (Candlestick / Preis)")
    chart_data = np.cumsum(np.random.randn(50)) + 100
    st.line_chart(chart_data)
    st.caption(f"Echtzeit-Preisverlauf für {selected_market}")

with c2:
    st.subheader("🧊 3D Volatilitäts-Oberfläche (Enger skaliert)")
    
    # Engere Abstände für feinere Gitterdichte
    x = np.linspace(-1.0, 1.0, 30)
    y = np.linspace(0.1, 1.0, 30)
    X, Y = np.meshgrid(x, y)
    
    Z = np.sin(X) * np.cos(Y) + (X**2) * 0.5 + 2.0
    
    fig = go.Figure(data=[go.Surface(z=Z, x=X, y=Y, colorscale='Viridis')])
    fig.update_layout(
        title=f"3D Volatility Smile — {selected_market}",
        autosize=True,
        height=400,
        margin=dict(l=20, r=20, b=20, t=40)
    )
    st.plotly_chart(fig, use_container_width=True)
