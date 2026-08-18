import streamlit as st
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. Konfiguration & Layout auf Full-Width
st.set_page_config(
    page_title="Global Multi-Asset Terminal",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }
    </style>
""", unsafe_allow_html=True)

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

if asset_class == "Kryptowährungen":
    market_list = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
    base_price = 64255.58
elif asset_class == "US-Märkte":
    market_list = ["S&P 500 (SPY)", "Nasdaq (QQQ)", "Apple (AAPL)", "Tesla (TSLA)", "NVIDIA (NVDA)"]
    base_price = 450.0
elif asset_class == "Deutsche Märkte (Xetra)":
    market_list = ["DAX Index", "SAP SE", "Siemens", "Allianz"]
    base_price = 18500.0
else:
    market_list = ["Gold (XAUUSD)", "Silver", "Crude Oil", "EUR/USD"]
    base_price = 2400.0

selected_market = st.sidebar.selectbox("🎯 Spezieller Markt:", market_list)

# Marktstatus-Logik
def get_market_status(m_type):
    if "Krypto" in asset_class:
        return "🟢 24/7 Geöffnet (Live)", "Open"
    now_hour = datetime.utcnow().hour
    if "Xetra" in asset_class and 7 <= now_hour < 16:
        return "🟢 Xetra Geöffnet", "Open"
    elif "US" in asset_class and 13 <= now_hour < 21:
        return "🟢 US-Börse Geöffnet", "Open"
    elif "Forex" in asset_class:
        return "🟢 Forex Aktiv", "Open"
    else:
        return "🔴 Markt Geschlossen", "Closed"

status_text, status_flag = get_market_status(asset_class)

# Session State Initialisierung
if "market_data" not in st.session_state or st.session_state.get("current_market") != selected_market:
    np.random.seed(sum(map(ord, selected_market)))
    timestamps = [datetime.now() - timedelta(minutes=i) for i in range(40, 0, -1)]
    
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

# 3. Haupt-UI Layout
st.title(f"Terminal // {selected_market}")
st.markdown(f"Kategorie: **{asset_class}** | Status: **{status_text}**")

col1, col2, col3 = st.columns(3)
col1.metric("Aktueller Preis", f"{current_price:,.2f}", f"{diff_percent:+.2f}%")
col2.metric("Marktstatus", status_text, status_flag)
col3.metric("Ausgewählter Asset", selected_market, "Aktiv")

st.divider()

# 4. Ansichten mit fehlerfreier Fragment-Logik
if "Chart" in view_mode:
    @st.fragment(run_every=1.0)
    def render_live_chart():
        tick_change = np.random.randn() * (base_price * 0.0002)
        data["closes"][-1] += tick_change
        data["highs"][-1] = max(data["highs"][-1], data["closes"][-1])
        data["lows"][-1] = min(data["lows"][-1], data["closes"][-1])
        
        cur_p = data["closes"][-1]
        p_diff = cur_p - data["opens"][0]
        p_pct = (p_diff / data["opens"][0]) * 100

        fig_candle = go.Figure(data=[go.Candlestick(
            x=data["times"],
            open=data["opens"],
            high=data["highs"],
            low=data["lows"],
            close=data["closes"]
        )])
        
        fig_candle.update_layout(
            template="plotly_dark",
            title=dict(
                text=f"Echtzeit-Kursverlauf ({selected_market})",
                font=dict(color="white", size=16)
            ),
            xaxis_rangeslider_visible=True,
            xaxis=dict(backgroundcolor="black", gridcolor="gray"),
            yaxis=dict(backgroundcolor="black", gridcolor="gray", side="right"), # Preis-Skala rechts
            autosize=True,
            height=650,
            margin=dict(l=20, r=20, b=20, t=50)
        )
        
        fig_candle.add_annotation(
            text=f"{selected_market}: ${cur_p:,.2f} ({p_pct:+.2f}%)",
            xref="paper", yref="paper",
            x=0.98, y=0.95,
            showarrow=False,
            font=dict(size=16, color="orange", family="Arial Black"),
            align="right",
            bgcolor="rgba(0,0,0,0.7)",
            bordercolor="gray",
            borderwidth=1
        )

        st.plotly_chart(
            fig_candle, 
            use_container_width=True, 
            config={'scrollZoom': True, 'displayModeBar': True},
            key="candlestick_chart_unique"
        )
        st.caption("ℹ️ TradingView-Style: Scrolle mit dem Mausrad zum Zoomen, verschiebe den Ausschnitt oder nutze den Range-Slider.")

    render_live_chart()

else:
    @st.fragment(run_every=0.3)
    def render_animated_3d():
        x = np.linspace(-3.0, 3.0, 35)
        y = np.linspace(-3.0, 3.0, 35)
        X, Y = np.meshgrid(x, y)
        
        # Animierte Volatilität, streng >= 0
        phase = datetime.now().timestamp() * 2
        R = np.sqrt(X**2 + Y**2)
        Z = 0.4 + 0.05 * (X**2 + Y**2) + 0.1 * np.cos(R - phase * 0.5)
        Z = np.maximum(Z, 0.01)
        
        fig_3d = go.Figure(data=[go.Surface(z=Z, x=X, y=Y, colorscale='Viridis')])
        fig_3d.update_layout(
            template="plotly_dark",
            title=dict(
                text=f"{selected_market} – 3D Surface Chart [ANIMIERT]",
                font=dict(color="white", size=16)
            ),
            autosize=True,
            height=650,
            margin=dict(l=10, r=10, b=10, t=50),
            scene=dict(
                xaxis_title='Strike Price',
                yaxis_title='Time',
                zaxis=dict(title='Volatility', backgroundcolor="black", gridcolor="gray", range=[0, 1.5]),
                xaxis=dict(backgroundcolor="black", gridcolor="gray"),
                yaxis=dict(backgroundcolor="black", gridcolor="gray")
            )
        )
        
        fig_3d.add_annotation(
            text=f"{selected_market}: ${current_price:,.2f}",
            xref="paper", yref="paper",
            x=0.02, y=0.92,
            showarrow=False,
            font=dict(size=18, color="orange", family="Arial Black")
        )
        
        st.plotly_chart(
            fig_3d, 
            use_container_width=True,
            config={'scrollZoom': True, 'displayModeBar': True},
            key="surface_3d_unique"
        )
        st.caption("ℹ️ Das 3D-Modell bewegt sich fließend, bleibt stabil im Layout und lässt sich frei mit der Maus drehen.")

    render_animated_3d()
