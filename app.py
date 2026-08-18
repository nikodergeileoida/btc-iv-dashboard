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
view_mode = st.sidebar.radio("Ansicht wählen:", [
    "Live Kerzenchart (TradingView Native)", 
    "3D Volatility Surface (Kamera-Fix)"
])

html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <!-- TradingView Lightweight Charts Library -->
    <script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
    <!-- Plotly Library für 3D -->
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{ background-color: #050505; color: #ffffff; font-family: sans-serif; margin: 0; padding: 10px; }}
        .header {{ font-family: monospace; font-size: 1.2rem; color: #888888; }}
        .price {{ font-size: 2.2rem; font-weight: bold; color: #FF9900; margin-bottom: 10px; }}
        #chart {{ width: 100%; height: 680px; border-radius: 8px; overflow: hidden; }}
    </style>
</head>
<body>
    <div class="header">Bitcoin (BTC/USDT) Live Terminal</div>
    <div class="price" id="btc-price">Lade Live Feed...</div>
    <div id="chart"></div>

    <script>
        const viewMode = "{view_mode}";
        let currentPrice = 65000;
        let isUserInteracting = false;

        // Mouse Tracker: Verhindert 3D-Kamera-Resets während der Drehung
        const chartDiv = document.getElementById('chart');
        chartDiv.addEventListener('mousedown', () => {{ isUserInteracting = true; }});
        window.addEventListener('mouseup', () => {{ isUserInteracting = false; }});
        chartDiv.addEventListener('touchstart', () => {{ isUserInteracting = true; }});
        window.addEventListener('touchend', () => {{ isUserInteracting = false; }});

        // ----------------------------------------------------
        // 1. TRADINGVIEW NATIVE KANDLESTICK ENGINE
        // ----------------------------------------------------
        if (viewMode.includes("Kerzenchart")) {{
            const chart = LightweightCharts.createChart(chartDiv, {{
                layout: {{ backgroundColor: '#050505', textColor: '#DDD' }},
                grid: {{ vertLines: {{ color: '#151515' }}, horzLines: {{ color: '#151515' }} }},
                crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
                rightPriceScale: {{ borderColor: '#222', scaleMargins: {{ top: 0.1, bottom: 0.1 }} }},
                timeScale: {{ borderColor: '#222', timeVisible: true, secondsVisible: false }}
            }});

            const candleSeries = chart.addCandlestickSeries({{
                upColor: '#00FF88',
                downColor: '#FF0055',
                borderUpColor: '#00FF88',
                borderDownColor: '#FF0055',
                wickUpColor: '#00FF88',
                wickDownColor: '#FF0055',
            }});

            // Binance 1m Kerzen laden
            fetch("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=150")
                .then(res => res.json())
                .then(data => {{
                    let formatted = data.map(d => ({{
                        time: Math.floor(d[0] / 1000),
                        open: parseFloat(d[1]),
                        high: parseFloat(d[2]),
                        low: parseFloat(d[3]),
                        close: parseFloat(d[4])
                    }}));
                    candleSeries.setData(formatted);
                    currentPrice = formatted[formatted.length - 1].close;
                    document.getElementById('btc-price').innerText = "$" + currentPrice.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
                }});

            // Echter Binance WebSocket Stream (Zoom & Stretch bleiben voll erhalten!)
            const ws = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@kline_1m');
            ws.onmessage = (event) => {{
                let msg = JSON.parse(event.data);
                let k = msg.k;
                let candle = {{
                    time: Math.floor(k.t / 1000),
                    open: parseFloat(k.o),
                    high: parseFloat(k.h),
                    low: parseFloat(k.l),
                    close: parseFloat(k.c)
                }};
                candleSeries.update(candle);
                currentPrice = candle.close;
                document.getElementById('btc-price').innerText = "$" + currentPrice.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
            }};

        // ----------------------------------------------------
        // 2. FLACKERFREIER 3D CHART ENGINE
        // ----------------------------------------------------
        }} else {{
            let tOffset = 0;

            function generate3DData(price, offset) {{
                let strikes = [], expiries = [], zValues = [];
                for(let i=0; i<30; i++) strikes.push(price * (0.6 + i * 0.026));
                for(let j=0; j<30; j++) expiries.push(7 + j * 5.8);

                for(let j=0; j<30; j++) {{
                    let row = [];
                    let T = expiries[j];
                    for(let i=0; i<30; i++) {{
                        let K = strikes[i];
                        let moneyness = Math.log(K / price);
                        let wave = Math.sin(2 * Math.PI * (K / price) + offset) * 2.5;
                        let iv = (0.35 + 0.25 * Math.pow(moneyness, 2) + 0.08 * (1.0 / Math.sqrt(T / 30.0))) * 100.0 + wave;
                        row.push(iv);
                    }}
                    zValues.push(row);
                }}
                return {{ x: strikes, y: expiries, z: zValues }};
            }}

            // Startpreis holen
            fetch("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
                .then(res => res.json())
                .then(data => {{
                    currentPrice = parseFloat(data.price);
                    document.getElementById('btc-price').innerText = "$" + currentPrice.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
                    
                    let surf = generate3DData(currentPrice, 0);
                    let trace = {{
                        x: surf.x, y: surf.y, z: surf.z,
                        type: 'surface',
                        colorscale: [[0.0, '#0D0887'], [0.35, '#6A00A8'], [0.70, '#B12A90'], [1.0, '#FCA636']],
                        showscale: true
                    }};

                    let layout = {{
                        paper_bgcolor: '#050505',
                        plot_bgcolor: '#050505',
                        margin: {{ l: 0, r: 0, b: 0, t: 0 }},
                        uirevision: 'camera_lock_key', // Erhält die Kamera bei Updates
                        scene: {{
                            xaxis: {{ title: 'Strike ($)', gridcolor: '#333' }},
                            yaxis: {{ title: 'Days', gridcolor: '#333' }},
                            zaxis: {{ title: 'IV (%)', gridcolor: '#333' }},
                            camera: {{ eye: {{ x: -1.5, y: -1.5, z: 0.8 }} }}
                        }}
                    }};

                    Plotly.newPlot('chart', [trace], layout, {{ responsive: true, displayModeBar: false }});
                }});

            // Price WebSocket
            const ws = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@ticker');
            ws.onmessage = (event) => {{
                let msg = JSON.parse(event.data);
                currentPrice = parseFloat(msg.c);
                document.getElementById('btc-price').innerText = "$" + currentPrice.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
            }};

            // Live 3D Render-Loop (Pausiert automatisch, wenn du die Kamera mit der Maus drehst!)
            setInterval(() => {{
                if (isUserInteracting) return; // Wenn du die Maus gedrückt hältst -> KEIN Update!
                
                tOffset += 0.2;
                let surf = generate3DData(currentPrice, tOffset);
                Plotly.react('chart', [{{
                    x: surf.x, y: surf.y, z: surf.z,
                    type: 'surface',
                    colorscale: [[0.0, '#0D0887'], [0.35, '#6A00A8'], [0.70, '#B12A90'], [1.0, '#FCA636']],
                    showscale: true
                }}], {{
                    paper_bgcolor: '#050505',
                    plot_bgcolor: '#050505',
                    margin: {{ l: 0, r: 0, b: 0, t: 0 }},
                    uirevision: 'camera_lock_key',
                    scene: {{
                        xaxis: {{ title: 'Strike ($)', gridcolor: '#333' }},
                        yaxis: {{ title: 'Days', gridcolor: '#333' }},
                        zaxis: {{ title: 'IV (%)', gridcolor: '#333' }}
                    }}
                }}, {{ responsive: true, displayModeBar: false }});
            }}, 1000);
        }}
    </script>
</body>
</html>
"""

components.html(html_code, height=750)
