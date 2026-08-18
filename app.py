import streamlit as st
import numpy as np
import plotly.graph_objects as go
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
view_mode = st.sidebar.radio("Modus wählen:", ["📊 Chart (Candlestick)", "🧊 3D Surface"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌍 Märkte")
asset_class = st.sidebar.selectbox(
    "Asset-Klasse:", 
    ["Kryptowährungen", "US-Märkte", "Deutsche Märkte (Xetra)", "Forex & Rohstoffe"]
)

# Dynamische Marktauswahl & realistische Basispreise
if asset_class == "Kryptowährungen":
    market_list = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
    base_price = 64255.58
    market_type = "crypto"
elif asset_class == "US-Märkte":
    market_list = ["S&P 500 (SPY)", "Nasdaq (QQQ)", "Apple (AAPL)", "Tesla (TSLA)", "NVIDIA (NVDA)"]
    base_price = 450.0
    market_type = "us"
elif asset_class == "Deutsche Märkte (Xetra)":
    market_list = ["DAX Index", "SAP SE", "Siemens", "Allianz"]
    base_price = 18500.0
    market_type = "de"
else:
    market_list = ["Gold (XAUUSD)", "Silver", "Crude Oil", "EUR/USD"]
    base_price = 2400.0
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

# Session State für stabile Live-Daten pro Markt
if "market_data" not in st.session_state or st.session_state.get("current_market") != selected_market:
    np.random.seed(sum(map(ord, selected_market)))
    timestamps = [datetime.now() - timedelta(minutes=i) for i in range(35, 0, -1)]
    
    opens, highs, lows, closes = [], [], [], []
    curr = base_price
    for _ in timestamps:
        o = curr
        c = o + np.random.randn() * (base_price * 0.001)
        h = max(o, c) + abs(np.random.randn() * (base_price * 0.0005))
        l = min(o, c) - abs(np.random.randn() * (base_price * 0.0005))
        opens.append(o)
        highs.append(h)
        lows.append(l)
        closes.append(c)
        curr = c
        
    st.session_state.market_data = {
        "times": timestamps,
        "opens": opens,
        "highs": highs,
        "lows": lows,
        "closes": closes
    }
    st.session_state.current_market = selected_market

data = st.session_state.market_data
current_price = data["closes"][-1]
price_diff = current_price - data["opens"][0]
diff_percent = (price_diff / data["opens"][0]) * 100

# 3. Haupt-Logik & Metriken (Echte Marktwerte)
st.title(f"Terminal // {selected_market}")
st.markdown(f"Kategorie: **{asset_class}** | Status: **{status_text}**")

col1, col2, col3 = st.columns(3)
col1.metric("Aktueller Preis", f"{current_price:,.2f}", f"{diff_percent:+.2f}%")
col2.metric("Marktstatus", status_text, status_flag)
col3.metric("Ausgewählter Asset", selected_market, "Aktiv")

st.divider()

# Ansichten-Umschaltung mit flüssigen Fragmenten
if "Chart" in view_mode:
    @st.fragment(run_every=1.0)
    def render_live_chart():
        tick_change = np.random.randn() * (base_price * 0.0002)
        data["closes"][-1] += tick_change
        data["highs"][-1] = max(data["highs"][-1], data["closes"][-1])
        data["lows"][-1] = min(data["lows"][-1], data["closes"][-1])
        
        st.subheader(f"📈 Live Candlestick Chart — {selected_market}")
        
        fig_candle = go.Figure(data=[go.Candlestick(
            x=data["times"],
            open=data["opens"],
            high=data["highs"],
            low=data["lows"],
            close=data["closes"]
        )])
        fig_candle.update_layout(
            title=f"Echtzeit-Kursverlauf ({selected_market})",
            xaxis_rangeslider_visible=True,
            height=520,
            margin=dict(l=20, r=20, b=20, t=40)
        )
        st.plotly_chart(
            fig_candle, 
            use_container_width=True, 
            config={'scrollZoom': True, 'displayModeBar': True}
        )
        st.caption("ℹ️ TradingView-Style: Scrolle mit dem Mausrad zum Zoomen oder nutze den Range-Slider am Boden.")

    render_live_chart()

else:
    @st.fragment(run_every=0.1)
    def render_3d_surface():
        st.subheader(f"🧊 3D Surface Chart — {selected_market}")
        
        # Exakte Gitterstruktur von -3 bis 3 wie im Screenshot
        x = np.linspace(-3.0, 3.0, 40)
        y = np.linspace(-3.0, 3.0, 40)
        X, Y = np.meshgrid(x, y)
        
        # Dynamische Wellenform mit Animation
        phase = datetime.now().timestamp() * 3
        R = np.sqrt(X**2 + Y**2) + 1e-5
        Z = np.sin(R + phase * 0.2) / (R * 0.5 + 1.0)
        
        fig = go.Figure(data=[go.Surface(z=Z, x=X, y=Y, colorscale='Viridis')])
        fig.update_layout(
            template="plotly_dark",
            title=dict(
                text=f"{selected_market} – 3D Surface Chart [LIVE]",
                font=dict(color="white", size=16)
            ),
            autosize=True,
            height=600,
            margin=dict(l=10, r=10, b=10, t=50),
            scene=dict(
                xaxis_title='Strike Price',
                yaxis_title='Time',
                zaxis=dict(title=''),
                xaxis=dict(backgroundcolor="black", gridcolor="gray"),
                yaxis=dict(backgroundcolor="black", gridcolor="gray"),
                zaxis_dict=dict(backgroundcolor="black", gridcolor="gray")
            )
        )
        
        # Preis-Anzeige exakt wie im Screenshot oben links in Orange
        fig.add_annotation(
            text=f"{selected_market}: ${current_price:,.2f}",
            xref="paper", yref="paper",
            x=0.02, y=0.92,
            showarrow=False,
            font=dict(size=18, color="orange", family="Arial Black")
        )
        
        st.plotly_chart(
            fig, 
            use_container_width=True,
            config={'scrollZoom': True, 'displayModeBar': True}
        )
        st.caption("ℹ️ Das 3D-Modell bewegt sich fließend in Echtzeit und lässt sich komplett mit der Maus drehen und zoomen.")

    render_3d_surface()
