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
def get_market_status():
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

status_text, status_flag = get_market_status()

# Session State für stabile Kursdaten
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

# 3. Haupt-Layout
st.title(f"Terminal // {selected_market}")
st.markdown(f"Kategorie: **{asset_class}** | Status: **{status_text}**")

col1, col2, col3 = st.columns(3)
col1.metric("Aktueller Preis", f"{current_price:,.2f}", f"{diff_percent:+.2f}%")
col2.metric("Marktstatus", status_text, status_flag)
col3.metric("Ausgewählter Asset", selected_market, "Aktiv")

st.divider()

# 4. Ansichten
if "Chart" in view_mode:
    st.subheader(f"📈 Candlestick Chart — {selected_market}")
    
    fig_candle = go.Figure(data=[go.Candlestick(
        x=data["times"],
        open=data["opens"],
        high=data["highs"],
        low=data["lows"],
        close=data["closes"]
    )])
    
    fig_candle.update_layout(
        template="plotly_dark",
        title=f"Echtzeit-Kursverlauf ({selected_market})",
        xaxis_rangeslider_visible=True,
        dragmode='pan',  # Exakt wie TradingView: Ziehen verschiebt den Chart, kein Zoom-Kasten!
        height=600,
        margin=dict(l=20, r=50, b=20, t=50)
    )
    
    fig_candle.update_yaxes(side="right", tickformat=",.2f", fixedrange=False)
    fig_candle.update_xaxes(fixedrange=False)
    
    fig_candle.add_annotation(
        text=f"{selected_market}: ${current_price:,.2f} ({diff_percent:+.2f}%)",
        xref="paper", yref="paper",
        x=0.98, y=0.95,
        showarrow=False,
        font=dict(size=16, color="orange", family="Arial Black"),
        bgcolor="rgba(0,0,0,0.8)",
        bordercolor="gray",
        borderwidth=1
    )

    st.plotly_chart(
        fig_candle, 
        use_container_width=True, 
        config={'scrollZoom': True, 'displayModeBar': True},
        key="candlestick_final_v2"
    )
    st.caption("ℹ️ **TradingView-Modus:** Klicken & Ziehen verschiebt den Chart. Mausrad zoomt. Ziehe direkt an den Skalenzahlen zum Stretchen.")

else:
    st.subheader(f"🧊 3D Volatility Surface — {selected_market}")
    
    # Generierung von Client-Side Frames für flüssige, flackerfreie Bewegung
    x = np.linspace(-3.0, 3.0, 30)
    y = np.linspace(-3.0, 3.0, 30)
    X, Y = np.meshgrid(x, y)
    
    frames = []
    num_frames = 25
    for i in range(num_frames):
        phase = i * (2 * np.pi / num_frames)
        R = np.sqrt(X**2 + Y**2)
        Z = 0.5 + 0.1 * (X**2 + Y**2) + 0.15 * np.cos(R - phase)
        Z = np.maximum(Z, 0.05)
        frames.append(go.Frame(data=[go.Surface(z=Z, x=X, y=Y)], name=f"f{i}"))

    R0 = np.sqrt(X**2 + Y**2)
    Z0 = 0.5 + 0.1 * (X**2 + Y**2) + 0.15 * np.cos(R0)
    Z0 = np.maximum(Z0, 0.05)

    fig_3d = go.Figure(
        data=[go.Surface(z=Z0, x=X, y=Y, colorscale='Viridis')],
        frames=frames
    )
    
    fig_3d.update_layout(
        template="plotly_dark",
        height=600,
        margin=dict(l=10, r=10, b=10, t=30),
        updatemenus=[{
            "type": "buttons",
            "showactive": False,
            "x": 0.05,
            "y": 1.12,
            "buttons": [{
                "label": "▶ Animation starten",
                "method": "animate",
                "args": [
                    None,
                    {
                        "frame": {"duration": 60, "redraw": True},
                        "fromcurrent": True,
                        "mode": "immediate",
                        "transition": {"duration": 60, "easing": "linear"},
                        "loop": True
                    }
                ]
            }, {
                "label": "⏸ Pause",
                "method": "animate",
                "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]
            }]
        }],
        scene=dict(
            xaxis_title='Strike Price',
            yaxis_title='Time',
            zaxis_title='Volatility',
            zaxis=dict(range=[0, 1.5], backgroundcolor="black", gridcolor="gray"),
            xaxis=dict(backgroundcolor="black", gridcolor="gray"),
            yaxis=dict(backgroundcolor="black", gridcolor="gray"),
            camera=dict(eye=dict(x=1.5, y=-1.5, z=1.2))
        )
    )
    
    fig_3d.add_annotation(
        text=f"{selected_market}: ${current_price:,.2f} ({diff_percent:+.2f}%)",
        xref="paper", yref="paper",
        x=0.02, y=0.92,
        showarrow=False,
        font=dict(size=18, color="orange", family="Arial Black")
    )
    
    st.plotly_chart(
        fig_3d, 
        use_container_width=True,
        config={'scrollZoom': True, 'displayModeBar': True},
        key="surface_3d_final_v2"
    )
    st.caption("ℹ️ **3D-Modell:** Klicke einmal auf **▶ Animation starten**, damit sich die Oberfläche permanent und flackerfrei bewegt. Du kannst die Ansicht währenddessen jederzeit mit der Maus frei drehen und zoomen!")
