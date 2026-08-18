import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta

# 1. Konfiguration
st.set_page_config(
    page_title="Global Multi-Asset Terminal",
    page_icon="📈",
    layout="wide"
)

# 2. Sidebar Navigation & Markt-Auswahl
st.sidebar.title("⚡ Terminal Control")

st.sidebar.markdown("---")
st.sidebar.markdown("### 👁️ Ansicht")
view_mode = st.sidebar.radio("Modus wählen:", ["📊 Chart (1s Live)", "🧊 3D Surface (High-Speed)"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌍 Märkte")
asset_class = st.sidebar.selectbox(
    "Asset-Klasse:", 
    ["Kryptowährungen", "US-Märkte", "Deutsche Märkte (Xetra)", "Forex & Rohstoffe"]
)

# Dynamische Marktauswahl
if asset_class == "Kryptowährungen":
    market_list = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
    market_type = "crypto"
elif asset_class == "US-Märkte":
    market_list = ["S&P 500 (SPY)", "Nasdaq (QQQ)", "Apple (AAPL)", "Tesla (TSLA)", "NVIDIA (NVDA)"]
    market_type = "us"
elif asset_class == "Deutsche Märkte (Xetra)":
    market_list = ["DAX Index", "SAP SE", "Siemens", "Allianz"]
    market_type = "de"
else:
    market_list = ["Gold (XAUUSD)", "Silver", "Crude Oil", "EUR/USD"]
    market_type = "forex"

selected_market = st.sidebar.selectbox("🎯 Spezieller Markt:", market_list)

# Marktstatus-Logik
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
        return "🔴 Markt Geschlossen", "Closed"

status_text, status_flag = get_market_status(market_type)

# 3. Haupt-Logik
st.title(f"Terminal // {selected_market}")
st.markdown(f"Kategorie: **{asset_class}** | Status: **{status_text}**")

col1, col2, col3 = st.columns(3)
col1.metric("Aktiver Markt", selected_market, status_flag)
col2.metric("Feed-Modus", view_mode, "Aktiv")
col3.metric("Cloud-Status", "24/7 Online", "Verbunden")

st.divider()

# Ansichten-Umschaltung
if "Chart" in view_mode:
    st.subheader(f"📈 Live Candlestick Chart — {selected_market} (Update: 1 Sekunde)")
    chart_placeholder = st.empty()
    
    # Session State für fortlaufende Candlestick-Daten (OHLC)
    if "df_candles" not in st.session_state or st.session_state.get("last_market_c") != selected_market:
        np.random.seed(42)
        timestamps = [datetime.now() - timedelta(seconds=i) for i in range(30, 0, -1)]
        
        opens, highs, lows, closes = [], [], [], []
        curr = 100.0
        for t in timestamps:
            o = curr
            c = o + np.random.randn() * 0.8
            h = max(o, c) + abs(np.random.randn() * 0.5)
            l = min(o, c) - abs(np.random.randn() * 0.5)
            opens.append(o)
            highs.append(h)
            lows.append(l)
            closes.append(c)
            curr = c
            
        st.session_state.df_candles = {
            "times": timestamps,
            "opens": opens,
            "highs": highs,
            "lows": lows,
            "closes": closes
        }
        st.session_state.last_market_c = selected_market

    # Neuen Kerzendatenpunkt im Sekundentakt anhängen
    data = st.session_state.df_candles
    last_close = data["closes"][-1]
    new_open = last_close
    new_close = new_open + np.random.randn() * 0.8
    new_high = max(new_open, new_close) + abs(np.random.randn() * 0.4)
    new_low = min(new_open, new_close) - abs(np.random.randn() * 0.4)
    new_time = datetime.now()

    data["times"].append(new_time)
    data["opens"].append(new_open)
    data["highs"].append(new_high)
    data["lows"].append(new_low)
    data["closes"].append(new_close)

    if len(data["times"]) > 40:
        data["times"].pop(0)
        data["opens"].pop(0)
        data["highs"].pop(0)
        data["lows"].pop(0)
        data["closes"].pop(0)

    fig_candle = go.Figure(data=[go.Candlestick(
        x=data["times"],
        open=data["opens"],
        high=data["highs"],
        low=data["lows"],
        close=data["closes"]
    )])
    fig_candle.update_layout(
        title=f"Live Candlestick — {selected_market}",
        xaxis_rangeslider_visible=False,
        height=500,
        margin=dict(l=20, r=20, b=20, t=40)
    )
    chart_placeholder.plotly_chart(fig_candle, use_container_width=True)
    
    # Exakt jede Sekunde neu laden
    time.sleep(1.0)
    st.rerun()

else:
    st.subheader(f"🧊 3D Volatilitäts-Oberfläche — {selected_market} (Hochfrequenz)")
    plot_placeholder = st.empty()
    
    # Sehr enge Gitterdichte für kompakten Look
    x = np.linspace(-1.0, 1.0, 35)
    y = np.linspace(0.1, 1.0, 35)
    X, Y = np.meshgrid(x, y)
    
    # Dynamische Animation im Millisekundenbereich
    phase = time.time() * 6
    Z = np.sin(X + phase * 0.1) * np.cos(Y) + (X**2) * 0.5 + 2.0
    
    fig = go.Figure(data=[go.Surface(z=Z, x=X, y=Y, colorscale='Viridis')])
    fig.update_layout(
        title=f"3D Volatility Smile — {selected_market}",
        autosize=True,
        height=520,
        margin=dict(l=10, r=10, b=10, t=30)
    )
    plot_placeholder.plotly_chart(fig, use_container_width=True)
    
    # Update im Millisekunden-Bereich
    time.sleep(0.05)
    st.rerun()
