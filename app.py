import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import json
from datetime import datetime
import time
import requests

# 1. Konfiguration
st.set_page_config(
    page_title="Global Multi-Asset Terminal",
    page_icon="📈",
    layout="wide"
)

# 2. Sidebar Navigation & Live-Feed Control
st.sidebar.title("⚡ Terminal Control")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔄 Live-Feed Engine")
live_feed = st.sidebar.checkbox("⚡ Live-Feed aktiv (10s Tick)", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("### 👁️ Ansicht & Engine")
view_mode = st.sidebar.radio("Modus wählen:", [
    "📈 TradingView Live-Terminal", 
    "🕯️ Eigene Kerzen (Custom Python Engine)",
    "🧊 Quanten-Membran (Matt)", 
    "⚡ Beide nebeneinander (Split-View)"
])

# Standardwerte definieren
smoothing = 1
price_offset = 0.0

custom_mode = "Eigene Kerzen" in view_mode or "Split-View" in view_mode
if custom_mode:
    st.sidebar.markdown("### 🛠️ Kerzen-Manipulation")
    smoothing = st.sidebar.slider("Glättungs-Faktor (Smoothing)", 1, 5, 1)
    price_offset = st.sidebar.number_input("Preis-Offset ($)", value=0.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌍 Märkte")
asset_class = st.sidebar.selectbox(
    "Asset-Klasse:", 
    ["Kryptowährungen", "US-Märkte", "Deutsche Märkte (Xetra)", "Forex & Rohstoffe"]
)

# Ticker-Mapping
if asset_class == "Kryptowährungen":
    market_map = {
        "BTCUSDT": {"binance": "BTCUSDT", "yf": "BTC-USD"},
        "ETHUSDT": {"binance": "ETHUSDT", "yf": "ETH-USD"},
        "SOLUSDT": {"binance": "SOLUSDT", "yf": "SOL-USD"},
        "BNBUSDT": {"binance": "BNBUSDT", "yf": "BNB-USD"},
        "XRPUSDT": {"binance": "XRPUSDT", "yf": "XRP-USD"}
    }
elif asset_class == "US-Märkte":
    market_map = {
        "S&P 500 (SPY)": {"yf": "SPY"}, "Nasdaq (QQQ)": {"yf": "QQQ"}, 
        "Apple (AAPL)": {"yf": "AAPL"}, "Tesla (TSLA)": {"yf": "TSLA"}, "NVIDIA (NVDA)": {"yf": "NVIDIA"}
    }
elif asset_class == "Deutsche Märkte (Xetra)":
    market_map = {
        "DAX Index": {"yf": "^GDAXI"}, "SAP SE": {"yf": "SAP.DE"}, 
        "Siemens": {"yf": "SIE.DE"}, "Allianz": {"yf": "ALV.DE"}
    }
else:
    market_map = {
        "Gold (XAUUSD)": {"yf": "GC=F"}, "Silver": {"yf": "SI=F"}, 
        "Crude Oil": {"yf": "CL=F"}, "EUR/USD": {"yf": "EURUSD=X"}
    }

selected_market = st.sidebar.selectbox("🎯 Spezieller Markt:", list(market_map.keys()))
market_info = market_map[selected_market]

# 3. Robuste Datenbeschaffung
@st.cache_data(ttl=5)
def fetch_robust_market_data(asset_cls, info):
    df = pd.DataFrame()
    current_price = 100.0

    if asset_cls == "Kryptowährungen" and "binance" in info:
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={info['binance']}&interval=1m&limit=150"
            response = requests.get(url, timeout=3)
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data, columns=[
                    'Open_time', 'Open', 'High', 'Low', 'Close', 'Volume',
                    'Close_time', 'Quote_asset_volume', 'Number_of_trades',
                    'Taker_buy_base_asset_volume', 'Taker_buy_quote_asset_volume', 'Ignore'
                ])
                df['Open'] = df['Open'].astype(float)
                df['High'] = df['High'].astype(float)
                df['Low'] = df['Low'].astype(float)
                df['Close'] = df['Close'].astype(float)
                df['Open_time'] = pd.to_datetime(df['Open_time'], unit='ms')
                df.set_index('Open_time', inplace=True)
                current_price = df['Close'].iloc[-1]
                return df[['Open', 'High', 'Low', 'Close']], current_price
        except Exception:
            pass

    try:
        yf_symbol = info.get("yf", list(info.values())[0])
        t = yf.Ticker(yf_symbol)
        df = t.history(period="1d", interval="1m", auto_adjust=False)
        if df.empty:
            df = t.history(period="5d", interval="15m", auto_adjust=False)
        
        if not df.empty:
            current_price = t.history(period="1d", auto_adjust=False)['Close'].iloc[-1]
            return df[['Open', 'High', 'Low', 'Close']], current_price
    except Exception:
        pass

    return None, current_price

df_raw, base_price = fetch_robust_market_data(asset_class, market_info)

# Eigene Kerzen verarbeiten / manipulieren
if df_raw is not None and not df_raw.empty:
    df_data = df_raw.copy()
    if smoothing > 1:
        df_data['Open'] = df_data['Open'].rolling(window=smoothing).mean()
        df_data['High'] = df_data['High'].rolling(window=smoothing).max()
        df_data['Low'] = df_data['Low'].rolling(window=smoothing).min()
        df_data['Close'] = df_data['Close'].rolling(window=smoothing).mean()
        df_data.dropna(inplace=True)
    
    df_data['Open'] += price_offset
    df_data['High'] += price_offset
    df_data['Low'] += price_offset
    df_data['Close'] += price_offset
else:
    df_data = None

# Marktstatus-Logik
def get_market_status():
    if "Krypto" in asset_class or "Forex" in asset_class:
        return "🟢 24/7 Geöffnet (Live)", "Open"
    now_hour = datetime.utcnow().hour
    if "Xetra" in asset_class and 7 <= now_hour < 16:
        return "🟢 Xetra Geöffnet", "Open"
    elif "US" in asset_class and 13 <= now_hour < 21:
        return "🟢 US-Börse Geöffnet", "Open"
    else:
        return "🔴 Markt Geschlossen / Nachbörslich", "Closed"

status_text, status_flag = get_market_status()

# Haupt-Layout
display_symbol = market_info.get("yf", market_info.get("binance", ""))
st.title(f"Terminal // {selected_market} ({display_symbol})")
st.markdown(f"Kategorie: **{asset_class}** | Status: **{status_text}**")

col1, col2, col3 = st.columns(3)
col1.metric("Marktstatus", status_text, status_flag)
col2.metric("Aktueller Preis", f"${base_price:,.2f}", "Live")
col3.metric("Modus", view_mode, "Aktiv")

st.divider()

# Hilfsfunktion für TradingView Original-Widget
def get_tradingview_html(symbol_key):
    tv_symbol_map = {
        "BTCUSDT": "BINANCE:BTCUSDT", "ETHUSDT": "BINANCE:ETHUSDT", "SOLUSDT": "BINANCE:SOLUSDT",
        "BNBUSDT": "BINANCE:BNBUSDT", "XRPUSDT": "BINANCE:XRPUSDT", "SPY": "AMEX:SPY",
        "QQQ": "NASDAQ:QQQ", "AAPL": "NASDAQ:AAPL", "TSLA": "NASDAQ:TSLA", "NVIDIA": "NASDAQ:NVIDIA",
        "^GDAXI": "XETR:DAX", "SAP.DE": "XETR:SAP", "SIE.DE": "XETR:SIE", "ALV.DE": "XETR:ALV",
        "GC=F": "COMEX:GC1!", "SI=F": "NYMEX:SI1!", "CL=F": "NYMEX:CL1!", "EURUSD=X": "FX_IDC:EURUSD"
    }
    tv_symbol = tv_symbol_map.get(symbol_key, "BINANCE:BTCUSDT")
    return f"""
    <!DOCTYPE html>
    <html>
    <head><style>html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; background: #000; overflow: hidden; }} .tradingview-widget-container {{ width: 100%; height: 100%; }}</style></head>
    <body>
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget" style="height:100%;width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
          {{
            "autosize": true, "symbol": "{tv_symbol}", "interval": "D", "timezone": "Etc/UTC",
            "theme": "dark", "style": "1", "locale": "de", "enable_publishing": false,
            "hide_top_toolbar": false, "hide_legend": false, "save_image": false, "calendar": false, "support_host": "https://www.tradingview.com"
          }}
          </script>
        </div>
    </body>
    </html>
    """

# Funktion für persistente Custom-Kerzen mit echtem Fullscreen
def render_persistent_custom_candles(df, title_text):
    if df is None or df.empty:
        st.warning("Keine Kerzen-Daten verfügbar.")
        return
    
    x_data = [d.strftime('%Y-%m-%d %H:%M:%S') for d in df.index]
    open_data = df['Open'].tolist()
    high_data = df['High'].tolist()
    low_data = df['Low'].tolist()
    close_data = df['Close'].tolist()

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
            html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; background: #131722; overflow: hidden; }}
            #chart-container {{ width: 100%; height: 100%; position: relative; }}
            #chart-div {{ width: 100%; height: 550px; }}
            /* Im echten Vollbildmodus dehnt sich das Chart auf 100% aus */
            :-webkit-full-screen #chart-div {{ height: 100vh !important; }}
            :-moz-full-screen #chart-div {{ height: 100vh !important; }}
            :fullscreen #chart-div {{ height: 100vh !important; }}
            
            .controls-overlay {{
                position: absolute; top: 8px; left: 12px; z-index: 100;
            }}
            .fs-btn {{
                font-family: Arial, sans-serif; font-size: 11px; color: #fff;
                background: rgba(30,30,30,0.85); padding: 5px 8px; border: 1px solid #555; border-radius: 4px;
                cursor: pointer; transition: background 0.2s;
            }}
            .fs-btn:hover {{ background: rgba(50,50,50,1); border-color: #089981; }}
        </style>
    </head>
    <body>
        <div id="chart-container">
            <div class="controls-overlay">
                <button class="fs-btn" onclick="toggleFullscreen()">⛶ Fullscreen</button>
            </div>
            <div id="chart-div"></div>
        </div>
        <script>
            function toggleFullscreen() {{
                var elem = document.getElementById('chart-container');
                if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.mozFullScreenElement) {{
                    if (elem.requestFullscreen) {{
                        elem.requestFullscreen();
                    }} else if (elem.webkitRequestFullscreen) {{
                        elem.webkitRequestFullscreen();
                    }} else if (elem.mozRequestFullScreen) {{
                        elem.mozRequestFullScreen();
                    }}
                }} else {{
                    if (document.exitFullscreen) {{
                        document.exitFullscreen();
                    }} else if (document.webkitExitFullscreen) {{
                        document.webkitExitFullscreen();
                    }} else if (document.mozCancelFullScreen) {{
                        document.mozCancelFullScreen();
                    }}
                }}
            }}

            const trace = {{
                x: {json.dumps(x_data)},
                open: {json.dumps(open_data)},
                high: {json.dumps(high_data)},
                low: {json.dumps(low_data)},
                close: {json.dumps(close_data)},
                type: 'candlestick',
                increasing: {{ line: {{ color: '#089981' }}, fillcolor: '#089981' }},
                decreasing: {{ line: {{ color: '#F23645' }}, fillcolor: '#F23645' }}
            }};

            const layout = {{
                template: 'plotly_dark',
                paper_bgcolor: '#131722',
                plot_bgcolor: '#131722',
                margin: {{ l: 10, r: 50, t: 30, b: 10 }},
                xaxis: {{
                    rangeslider: {{ visible: false }},
                    gridcolor: '#1f293d',
                    showspikes: true, spikecolor: '#787b86', spikethickness: 1, spikedash: 'dot'
                }},
                yaxis: {{
                    side: 'right',
                    gridcolor: '#1f293d',
                    showspikes: true, spikecolor: '#787b86', spikethickness: 1, spikedash: 'dot'
                }},
                title: {{ text: {json.dumps(title_text)}, font: {{ size: 14, color: '#d1d4dc' }} }},
                dragmode: 'pan',
                hovermode: 'x unified'
            }};

            const config = {{
                scrollZoom: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                responsive: true
            }};

            const div = document.getElementById('chart-div');
            let existingLayout = div.layout;
            let currentZoom = null;
            if (existingLayout && existingLayout.xaxis && existingLayout.xaxis.range) {{
                currentZoom = {{
                    xaxis: existingLayout.xaxis.range,
                    yaxis: existingLayout.yaxis.range
                }};
            }}

            Plotly.newPlot(div, [trace], layout, config).then(function() {{
                if (currentZoom) {{
                    Plotly.relayout(div, {{
                        'xaxis.range': currentZoom.xaxis,
                        'yaxis.range': currentZoom.yaxis
                    }});
                }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=580)

# Hilfsfunktion für Quanten-Membran (3D) mit echtem Fullscreen
def get_quantum_html(market_name, price, vol_num):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
            html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; background: #000000; overflow: hidden; }}
            #chart-container {{ width: 100%; height: 100%; position: relative; }}
            #plotly-div {{ width: 100%; height: 550px; }}
            :-webkit-full-screen #plotly-div {{ height: 100vh !important; }}
            :-moz-full-screen #plotly-div {{ height: 100vh !important; }}
            :fullscreen #plotly-div {{ height: 100vh !important; }}

            .controls-overlay {{
                position: absolute; top: 8px; left: 12px; z-index: 100;
                display: flex; gap: 8px; align-items: center;
            }}
            .market-badge {{
                font-family: Arial Black, sans-serif; font-size: 11px; color: orange;
                background: rgba(0,0,0,0.9); padding: 4px 8px; border: 1px solid #333; border-radius: 4px;
            }}
            .fs-btn {{
                font-family: Arial, sans-serif; font-size: 11px; color: #fff;
                background: rgba(30,30,30,0.9); padding: 5px 8px; border: 1px solid #555; border-radius: 4px;
                cursor: pointer; transition: background 0.2s;
            }}
            .fs-btn:hover {{ background: rgba(50,50,50,1); border-color: orange; }}
        </style>
    </head>
    <body>
        <div id="chart-container">
            <div class="controls-overlay">
                <div class="market-badge">{market_name}: ${price}</div>
                <button class="fs-btn" onclick="toggleFullscreen()">⛶ Fullscreen</button>
            </div>
            <div id="plotly-div"></div>
        </div>
        <script>
            function toggleFullscreen() {{
                var elem = document.getElementById('chart-container');
                if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.mozFullScreenElement) {{
                    if (elem.requestFullscreen) {{
                        elem.requestFullscreen();
                    }} else if (elem.webkitRequestFullscreen) {{
                        elem.webkitRequestFullscreen();
                    }} else if (elem.mozRequestFullScreen) {{
                        elem.mozRequestFullScreen();
                    }}
                }} else {{
                    if (document.exitFullscreen) {{
                        document.exitFullscreen();
                    }} else if (document.webkitExitFullscreen) {{
                        document.webkitExitFullscreen();
                    }} else if (document.mozCancelFullScreen) {{
                        document.mozCancelFullScreen();
                    }}
                }}
            }}

            const n = 50;
            const vol = {vol_num};

            function getSurface(frame) {{
                let x = [], y = [], z = [];
                for (let i = 0; i < n; i++) {{
                    let rowX = [], rowY = [], rowZ = [];
                    let u = (i / (n - 1)) * 5 - 2.5;
                    for (let j = 0; j < n; j++) {{
                        let v = (j / (n - 1)) * 5 - 2.5;
                        let r = Math.sqrt(u*u + v*v);
                        let wave = Math.sin(r * 2 - frame) * Math.cos(u * 0.8 + frame * 0.4);
                        let pz = Math.abs(wave) * vol * 1.2 + 0.05; 
                        rowX.push(u); rowY.push(v); rowZ.push(pz);
                    }}
                    x.push(rowX); y.push(rowY); z.push(rowZ);
                }}
                return {{ x: x, y: y, z: z }};
            }}

            let initialData = getSurface(0);
            const data = [{{
                type: 'surface',
                x: initialData.x, y: initialData.y, z: initialData.z,
                colorscale: [[0, '#4b0082'], [0.3, '#9400d3'], [0.6, '#ff8c00'], [1, '#ffff00']],
                showscale: false,
                lighting: {{ ambient: 0.6, diffuse: 0.8, specular: 0.05, roughness: 0.95 }}
            }}];

            const layout = {{
                template: 'plotly_dark',
                paper_bgcolor: '#000000', plot_bgcolor: '#000000',
                autosize: true, margin: {{l: 0, r: 0, b: 0, t: 0}},
                scene: {{
                    bgcolor: '#000000',
                    xaxis: {{showgrid: true, zeroline: true, title: 'Strike', gridcolor: '#333', zerolinecolor: '#555'}},
                    yaxis: {{showgrid: true, zeroline: true, title: 'Time', gridcolor: '#333', zerolinecolor: '#555'}},
                    zaxis: {{showgrid: true, zeroline: true, title: 'Volatility', range: [0, 3.5], gridcolor: '#333', zerolinecolor: '#555'}},
                    camera: {{ eye: {{x: 1.6, y: -1.6, z: 1.2}} }}
                }}
            }};

            let plotDiv = document.getElementById('plotly-div');
            Plotly.newPlot(plotDiv, data, layout, {{responsive: true, scrollZoom: true}});

            let frame = 0;
            function animate() {{
                frame += 0.02;
                let currentData = getSurface(frame);
                Plotly.restyle(plotDiv, {{ x: [currentData.x], y: [currentData.y], z: [currentData.z] }}, [0]);
                requestAnimationFrame(animate);
            }}
            requestAnimationFrame(animate);
        </script>
    </body>
    </html>
    """

# Volatilitätsfaktor für 3D berechnen
if df_raw is not None and len(df_raw) > 1:
    try:
        volatility_factor = float((df_raw['High'].max() - df_raw['Low'].min()) / base_price * 50)
        volatility_factor = max(0.5, min(volatility_factor, 3.0))
    except Exception:
        volatility_factor = 1.0
else:
    volatility_factor = 1.0

# Ansichten Rendering
tv_map_key = market_info.get("binance", market_info.get("yf", "BTCUSDT"))

if "TradingView Live-Terminal" in view_mode:
    st.subheader(f"📈 TradingView Live-Terminal — {selected_market}")
    components.html(get_tradingview_html(tv_map_key), height=620, scrolling=False)

elif "Eigene Kerzen" in view_mode:
    st.subheader(f"🕯️ Eigene Kerzen (Custom Python Engine) — {selected_market}")
    render_persistent_custom_candles(df_data, f"Custom OHLC Stream — {selected_market}")

elif "Quanten-Membran" in view_mode:
    st.subheader(f"🧊 Quanten-Membran (Matt) — {selected_market}")
    html_content = get_quantum_html(selected_market, f"{base_price:,.2f}", volatility_factor)
    components.html(html_content, height=620)

else:  
    st.subheader(f"⚡ Dual Screen: Eigene Kerzen & Quanten-Membran — {selected_market}")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("**🕯️ Eigene Kerzen (Custom)**")
        render_persistent_custom_candles(df_data, f"Custom Stream — {selected_market}")
        
    with col_b:
        st.markdown("**🧊 Quanten-Membran (3D)**")
        html_content = get_quantum_html(selected_market, f"{base_price:,.2f}", volatility_factor)
        components.html(html_content, height=580)

# Live-Feed Loop
if live_feed:
    time.sleep(10)
    st.rerun()
