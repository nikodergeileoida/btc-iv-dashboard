import streamlit as st
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

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

# Live-Tick: Simuliert echte Marktbewegung bei jedem Loop
tick_change = np.random.randn() * (base_price * 0.0004)
data["closes"][-1] += tick_change
data["highs"][-1] = max(data["highs"][-1], data["closes"][-1])
data["lows"][-1] = min(data["lows"][-1], data["closes"][-1])

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

# 4. Ansichten mit nativem Plotly für absolute Kamerafreiheit und Live-Refresh
if "Chart" in view_mode:
    st.subheader(f"📈 Candlestick Chart — {selected_market}")

    fig_candle = go.Figure(data=[go.Candlestick(
        x=list(data["times"]),
        open=list(data["opens"]),
        high=list(data["highs"]),
        low=list(data["lows"]),
        close=list(data["closes"])
    )])
    
    fig_candle.update_layout(
        template="plotly_dark",
        title=f"Echtzeit-Kursverlauf ({selected_market})",
        xaxis_rangeslider_visible=True,
        dragmode='pan',  # Nur Verschieben, kein Zoom-Kasten!
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
        config={
            'scrollZoom': True, 
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['zoom2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
        },
        key="candlestick_native_live"
    )
    st.caption("ℹ️ **Live-Feed Aktiv:** Der Chart aktualisiert sich sekündlich über den Auto-Loop.")

else:
    st.subheader(f"🧊 3D Volatility Surface — {selected_market}")

    # Generierung der 3D-Oberfläche mit asymmetrischem Smile & Skew
    n = 35
    x = np.linspace(-3, 3, n)
    y = np.linspace(-3, 3, n)
    X, Y = np.meshgrid(x, y)
    
    # Dynamischer Animations-Offset basierend auf der Zeit für flüssige Live-Wellen
    t_anim = time.time() * 2.0
    skew = 0.3 * X
    smile = 0.28 * (X**2) + 0.18 * (Y**2)
    wave = 0.4 * np.sin(X * 0.9 - t_anim) * np.cos(Y * 0.7 + t_anim)
    Z = np.maximum(0.2, 1.4 + smile - skew + wave)

    fig_3d = go.Figure(data=[go.Surface(
        z=Z, x=X, y=Y,
        colorscale='Viridis'
    )])

    fig_3d.update_layout(
        template="plotly_dark",
        paper_bgcolor='#000000',
        plot_bgcolor='#000000',
        autosize=True,
        height=600,
        margin=dict(l=0, r=0, b=0, t=0),
        # uirevision erzwingt, dass die Benutzer-Kameradrehung bei jedem Live-Update NICHT zurückgesetzt wird!
        uirevision="true",
        scene=dict(
            bgcolor='#000000',
            xaxis=dict(title='Strike Price (Skew)', backgroundcolor='#000000', gridcolor='#222', zerolinecolor='#444'),
            yaxis=dict(title='Time to Maturity', backgroundcolor='#000000', gridcolor='#222', zerolinecolor='#444'),
            zaxis=dict(title='Implied Volatility', range=[0.2, 3.2], backgroundcolor='#000000', gridcolor='#222', zerolinecolor='#444')
        )
    )

    st.plotly_chart(
        fig_3d, 
        use_container_width=True,
        config={'scrollZoom': True, 'displayModeBar': True},
        key="surface_3d_native_live"
    )
    st.caption("ℹ️ **Tiefschwarzes 3D-Modell:** Die Kamera bleibt komplett frei drehbar und zoombar. Kurse und Wellen laufen live im Sekundentakt.")

# Erzwingt den Live-Feed im Sekundentakt ohne manuelles Refresh
time.sleep(0.4)
st.rerun()
