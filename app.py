import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="BTC Live Terminal", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        .stApp { background-color: #050505 !important; color: #FFFFFF !important; }
        footer { visibility: hidden; }
        header[data-testid="stHeader"] { background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("⚙️ Terminal Steuerung")
view_mode = st.sidebar.radio("Ansicht wählen:", ["Live Kerzenchart (TradingView Style)", "3D Volatility Surface (Ultra Live)"])

# HTML/JS Client-Side Engine (Kein Server-Rerender, Null Flackern, Echter Sekunden-Live-Feed)
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{ background-color: #050505; color: #ffffff; font-family: sans-serif; margin: 0; padding: 10px; }}
        .header {{ font-family: monospace; font-size: 1.2rem; color: #888888; }}
        .price {{ font-size: 2.2rem; font-weight: bold; color: #FF9900; margin-bottom: 10px; }}
        #chart {{ width: 100%; height: 680px; }}
    </style>
</head>
<body>
    <div class="header">Bitcoin (BTC/USDT) Live Terminal</div>
    <div class="price" id="btc-price">Lade Live-Feed...</div>
    <div id="chart"></div>

    <script>
        const viewMode = "{view_mode}";
        let currentPrice = 65000;
        let candleData = {{ x: [], open: [], high: [], low: [], close: [] }};
        let is3DInitialized = false;

        // 1. Initial-Daten von Binance holen
        async function initData() {{
            try {{
                let res = await fetch("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100");
                let data = await res.json();
                
                data.forEach(d => {{
                    candleData.x.push(new Date(d[0]));
                    candleData.open.push(parseFloat(d[1]));
                    candleData.high.push(parseFloat(d[2]));
                    candleData.low.push(parseFloat(d[3]));
                    candleData.close.push(parseFloat(d[4]));
                }});
                
                currentPrice = candleData.close[candleData.close.length - 1];
                document.getElementById('btc-price').innerText = "$" + currentPrice.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
                
                if (viewMode.includes("Kerzenchart")) {{
                    renderCandlestick();
                }} else {{
                    render3D();
                }}
            }} catch(e) {{
                console.error("Binance Fetch Error", e);
            }}
        }}

        // 2. TRADINGVIEW KERZENCHART RENDERN
        function renderCandlestick() {{
            let trace = {{
                x: candleData.x,
                open: candleData.open,
                high: candleData.high,
                low: candleData.low,
                close: candleData.close,
                type: 'candlestick',
                increasing: {{ line: {{ color: '#00FF88' }}, fillcolor: '#00FF88' }},
                decreasing: {{ line: {{ color: '#FF0055' }}, fillcolor: '#FF0055' }}
            }};

            let layout = {{
                paper_bgcolor: '#050505',
                plot_bgcolor: '#050505',
                margin: {{ l: 20, r: 50, b: 30, t: 10 }},
                xaxis: {{ gridcolor: '#151515', rangeslider: {{ visible: false }} }},
                yaxis: {{ gridcolor: '#151515', side: 'right' }},
                uirevision: 'true'
            }};

            Plotly.newPlot('chart', [trace], layout, {{ responsive: true, displayModeBar: false }});
        }}

        // 3. FLACKERFREIER 3D CHART RENDERN
        function generate3DSurface(price, tOffset) {{
            let strikes = [], expiries = [], zValues = [];
            for(let i=0; i<30; i++) strikes.push(price * (0.6 + i * 0.026));
            for(let j=0; j<30; j++) expiries.push(7 + j * 5.8);

            for(let j=0; j<30; j++) {{
                let row = [];
                let T = expiries[j];
                for(let i=0; i<30; i++) {{
                    let K = strikes[i];
                    let moneyness = Math.log(K / price);
                    let wave = Math.sin(2 * Math.PI * (K / price) + tOffset) * 2.5;
                    let iv = (0.35 + 0.25 * Math.pow(moneyness, 2) + 0.08 * (1.0 / Math.sqrt(T / 30.0))) * 100.0 + wave;
                    row.push(iv);
                }}
                zValues.push(row);
            }}

            return {{ x: strikes, y: expiries, z: zValues }};
        }}

        function render3D() {{
            let surface = generate3DSurface(currentPrice, 0);

            let trace = {{
                x: surface.x,
                y: surface.y,
                z: surface.z,
                type: 'surface',
                colorscale: [
                    [0.0, '#0D0887'],
                    [0.35, '#6A00A8'],
                    [0.70, '#B12A90'],
                    [1.0, '#FCA636']
                ],
                showscale: true
            }};

            let layout = {{
                paper_bgcolor: '#050505',
                plot_bgcolor: '#050505',
                margin: {{ l: 0, r: 0, b: 0, t: 0 }},
                uirevision: '3d_camera_lock', // Kamera-Fixierung beim Drehen
                scene: {{
                    xaxis: {{ title: 'Strike ($)', gridcolor: '#333333' }},
                    yaxis: {{ title: 'Days to Expiry', gridcolor: '#333333' }},
                    zaxis: {{ title: 'IV (%)', gridcolor: '#333333' }},
                    camera: {{ eye: {{ x: -1.5, y: -1.5, z: 0.8 }} }}
                }}
            }};

            Plotly.newPlot('chart', [trace], layout, {{ responsive: true, displayModeBar: false }});
            is3DInitialized = true;
        }}

        // 4. LIVE WEBSOCKET & SEKUNDEN-UPDATE (Direct-Stream von Binance)
        const ws = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@ticker');
        let tCount = 0;

        ws.onmessage = (event) => {{
            let data = JSON.parse(event.data);
            currentPrice = parseFloat(data.c);
            
            document.getElementById('btc-price').innerText = "$" + currentPrice.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});

            let len = candleData.close.length;
            if (len > 0) {{
                // NUR DIE ERSTE/NEUESTE KERZE REAGIERT UND BEWEGT SICH!
                candleData.close[len - 1] = currentPrice;
                if (currentPrice > candleData.high[len - 1]) candleData.high[len - 1] = currentPrice;
                if (currentPrice < candleData.low[len - 1]) candleData.low[len - 1] = currentPrice;
            }}

            // Updates direkt im Browser ausführen (Ohne Python Rerender -> KEIN Flackern!)
            if (viewMode.includes("Kerzenchart")) {{
                Plotly.update('chart', {{
                    close: [candleData.close],
                    high: [candleData.high],
                    low: [candleData.low]
                }}, {{}}, [0]);
            }} else if (is3DInitialized) {{
                tCount += 0.2;
                let surface = generate3DSurface(currentPrice, tCount);
                Plotly.update('chart', {{
                    z: [surface.z],
                    x: [surface.x]
                }}, {{}}, [0]);
            }}
        }};

        initData();
    </script>
</body>
</html>
"""

components.html(html_code, height=750)
