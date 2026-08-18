import streamlit as st
import plotly.graph_objects as go
import requests
import pandas as pd
import numpy as np
import socket
import time

# 1. Grundkonfiguration
st.set_page_config(page_title="Bitcoin (BTC) – TradingView & 3D Terminal", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        .stApp, div[data-testid="stAppViewContainer"] {
            background-color: #000000 !important;
            color: #FFFFFF !important;
            font-family: 'Segoe UI', sans-serif !important;
        }
        footer { visibility: hidden; }
        header[data-testid="stHeader"] { background-color: transparent !important; }

        [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarCollapseButton"] {
            color: #FF9900 !important;
            background-color: #111111 !important;
            border: 1px solid #FF9900 !important;
            border-radius: 4px !important;
            margin: 5px !important;
        }

        .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        
        .chart-header-title {
            font-size: 1.35rem;
            font-weight: 600;
            color: #FFFFFF;
            margin-bottom: 2px;
            font-family: monospace, sans-serif;
        }
        .btc-price-orange {
            font-size: 1.8rem;
            font-weight: 900;
            color: #FF9900;
            text-shadow: 0 0 10px rgba(255, 153, 0, 0.4);
            margin-bottom: 10px;
        }

        .paper-desk {
            background: #0d0e12;
            border: 1px solid #2a2e39;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 15px;
        }
        .pnl-positive { color: #089981; font-weight: bold; }
        .pnl-negative { color: #f23645; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. Session State für Paper Trading
if "paper_balance" not in st.session_state:
    st.session_state.paper_balance = 10000.0
if "btc_position" not in st.session_state:
    st.session_state.btc_position = 0.0
if "entry_price" not in st.session_state:
    st.session_state.entry_price = 0.0

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()

# 3. Sidebar Steuerleiste
st.sidebar.markdown("### ⚙️ Terminal Steuerleiste")
view_mode = st.sidebar.radio(
    "Ansicht wählen:", 
    ["TradingView Live Chart (Paper Trading)", "3D Volatility Surface (Real Math)"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⏱️ 3D-Chart Update-Intervall")
three_d_interval = st.sidebar.selectbox(
    "3D-Refresh alle:",
    ["30 Sekunden", "15 Sekunden", "5 Sekunden", "1 Sekunde"]
)

three_d_map = {
    "30 Sekunden": 30,
    "15 Sekunden": 15,
    "5 Sekunden": 5,
    "1 Sekunde": 1
}
vola_ttl = three_d_map.get(three_d_interval, 30)

st.sidebar.caption("⚡ *Kerzenchart aktualisiert IMMER jede 1 Sekunde live.*")

# Handy QR-Code
st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Mobile Sync")
target_url = f"http://{LOCAL_IP}:8501"
st.sidebar.caption(f"Netzwerk URL: `{target_url}`")
qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={target_url}&color=FF9900&bgcolor=000000"
st.sidebar.image(qr_api_url, caption="Mit Handy-Kamera scannen", width=150)


# 4. Live BTC Preis Abrufen (Jede Sekunde)
def get_btc_price():
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=1).json()
        return float(res["price"])
    except Exception:
        return 64255.58

current_price = get_btc_price()

# Header
st.markdown('<div class="chart-header-title">Bitcoin (BTC) – Live Terminal</div>', unsafe_allow_html=True)
st.markdown(f'<div class="btc-price-orange">BTC/USD: ${current_price:,.2f}</div>', unsafe_allow_html=True)


# 5. ANSICHT 1: TradingView Chart (Jede Sekunde Live) + Paper Trading
if view_mode == "TradingView Live Chart (Paper Trading)":
    
    unrealized_pnl = 0.0
    if st.session_state.btc_position > 0:
        unrealized_pnl = (current_price - st.session_state.entry_price) * st.session_state.btc_position
    
    pnl_class = "pnl-positive" if unrealized_pnl >= 0 else "pnl-negative"

    st.markdown(f"""
    <div class="paper-desk">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="color: #848e9c; font-size: 0.85rem;">Papiergeld Guthaben:</span><br>
                <strong style="font-size: 1.3rem; color: #FFFFFF;">${st.session_state.paper_balance:,.2f} USD</strong>
            </div>
            <div>
                <span style="color: #848e9c; font-size: 0.85rem;">Position:</span><br>
                <strong style="font-size: 1.3rem; color: #FF9900;">{st.session_state.btc_position:.4f} BTC</strong>
            </div>
            <div>
                <span style="color: #848e9c; font-size: 0.85rem;">Unrealisierter PnL:</span><br>
                <strong class="{pnl_class}" style="font-size: 1.3rem;">{unrealized_pnl:+.2f} USD</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_buy, col_sell, col_close = st.columns(3)
    with col_buy:
        if st.button("🟢 BUY 0.1 BTC (Market)", use_container_width=True):
            cost = current_price * 0.1
            if st.session_state.paper_balance >= cost:
                st.session_state.paper_balance -= cost
                st.session_state.btc_position += 0.1
                st.session_state.entry_price = current_price
                st.rerun()

    with col_sell:
        if st.button("🔴 SHORT / SELL 0.1 BTC", use_container_width=True):
            if st.session_state.btc_position >= 0.1:
                revenue = current_price * 0.1
                st.session_state.paper_balance += revenue
                st.session_state.btc_position -= 0.1
                st.rerun()

    with col_close:
        if st.button("❌ POSITION SCHLIESSEN", use_container_width=True):
            if st.session_state.btc_position > 0:
                revenue = current_price * st.session_state.btc_position
                st.session_state.paper_balance += revenue
                st.session_state.btc_position = 0.0
                st.session_state.entry_price = 0.0
                st.rerun()

    # Binance Kerzen (1s Update)
    try:
        res = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100", timeout=1).json()
        df = pd.DataFrame(res, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)

        # Letzte Kerze mit aktuellem Preis überschreiben für echten 1s Tick
        df.iloc[-1, df.columns.get_loc('close')] = current_price

        # EMA 9 & EMA 21
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()

        # Buy / Sell Signale
        df['buy_signal'] = (df['ema9'] > df['ema21']) & (df['ema9'].shift(1) <= df['ema21'].shift(1))
        df['sell_signal'] = (df['ema9'] < df['ema21']) & (df['ema9'].shift(1) >= df['ema21'].shift(1))

        fig = go.Figure()

        # Kerzenchart
        fig.add_trace(go.Candlestick(
            x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
            name="BTC/USDT",
            increasing_line_color='#089981', decreasing_line_color='#f23645'
        ))

        # EMAs
        fig.add_trace(go.Scatter(x=df['time'], y=df['ema9'], line=dict(color='#2962FF', width=1), name="EMA 9"))
        fig.add_trace(go.Scatter(x=df['time'], y=df['ema21'], line=dict(color='#FF6D00', width=1), name="EMA 21"))

        # BUY Signale
        buys = df[df['buy_signal']]
        fig.add_trace(go.Scatter(
            x=buys['time'], y=buys['low'] * 0.999,
            mode='markers+text',
            marker=dict(symbol='triangle-up', size=12, color='#089981'),
            text=["▲ BUY"] * len(buys), textposition="bottom center",
            name="Buy Signal"
        ))

        # SELL Signale
        sells = df[df['sell_signal']]
        fig.add_trace(go.Scatter(
            x=sells['time'], y=sells['high'] * 1.001,
            mode='markers+text',
            marker=dict(symbol='triangle-down', size=12, color='#f23645'),
            text=["▼ SELL"] * len(sells), textposition="top center",
            name="Sell Signal"
        ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#000000",
            plot_bgcolor="#000000",
            margin=dict(l=10, r=10, b=10, t=10),
            height=600,
            xaxis=dict(gridcolor="#1e222d", rangeslider=dict(visible=False)),
            yaxis=dict(gridcolor="#1e222d"),
            legend=dict(orientation="h", y=1.02, x=0)
        )

        # Scroll Zoom & Pan
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

    except Exception as e:
        st.error(f"Fehler beim Laden des Charts: {e}")


# 6. ANSICHT 2: 3D Volatilitätsfläche (Gesteuert über gewähltes Intervall)
elif view_mode == "3D Volatility Surface (Real Math)":
    
    @st.cache_data(ttl=vola_ttl)
    def generate_3d_data(price):
        strikes = np.linspace(30000, 100000, 50)
        expiries = np.linspace(7, 180, 50)
        K, T = np.meshgrid(strikes, expiries)
        moneyness = np.log(K / price)
        Z_IV = 0.45 + 0.35 * (moneyness ** 2) + 0.15 * (1.0 / np.sqrt(T / 30.0))
        return K, T, Z_IV * 100.0

    K, T, Z_IV_percent = generate_3d_data(current_price)

    image_colorscale = [
        [0.0, "#240046"],
        [0.25, "#5a007a"],
        [0.5, "#d93800"],
        [0.75, "#ff8c00"],
        [1.0, "#ffff00"]
    ]

    fig_3d = go.Figure(data=[go.Surface(
        x=K, y=T, z=Z_IV_percent,
        colorscale=image_colorscale,
        showscale=True,
        colorbar=dict(title="IV (%)", len=0.6),
        contours=dict(
            z=dict(show=True, usecolormap=False, color="rgba(0,0,0,0.3)", project=dict(z=True))
        ),
        lighting=dict(ambient=0.7, diffuse=0.9, fresnel=0.2, specular=0.6, roughness=0.3)
    )])

    fig_3d.update_layout(
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        margin=dict(l=0, r=0, b=0, t=0),
        height=650,
        scene=dict(
            xaxis=dict(title="Strike Price ($)", color="#FFFFFF", gridcolor="#FFFFFF", showbackground=True, backgroundcolor="rgb(80, 80, 80)"),
            yaxis=dict(title="Time to Expiry (Tage)", color="#FFFFFF", gridcolor="#FFFFFF", showbackground=True, backgroundcolor="rgb(80, 80, 80)"),
            zaxis=dict(title="Implied Volatility (%)", color="#FFFFFF", gridcolor="#FFFFFF", showbackground=True, backgroundcolor="rgb(80, 80, 80)", range=[0, max(Z_IV_percent.max(), 120)]),
            camera=dict(eye=dict(x=-1.5, y=-1.5, z=0.9)),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=0.75)
        )
    )

    st.plotly_chart(fig_3d, use_container_width=True)


# 7. Exakt 1-Sekunde Intervall für ständiges Kerzenchart-Redraw
time.sleep(1)
st.rerun()
