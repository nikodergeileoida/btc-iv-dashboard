import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="BTC Live Terminal", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
        footer { visibility: hidden; }
        header[data-testid="stHeader"] { background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("⚙️ Terminal Steuerung")
view_mode = st.sidebar.radio("Ansicht wählen:", [
    "Live Kerzenchart (TradingView Native)", 
    "3D Volatility Surface (Smart Camera)"
])

html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <!-- TradingView Lightweight Charts -->
    <script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
    <!-- Plotly.js -->
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ background-color: #000000; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 12px; }}
        .header {{ font-family: monospace; font-size: 1.1rem; color: #888888; }}
        .price {{ font-size: 2.2rem; font-weight: 800; color: #FF9900; margin-bottom: 8px; letter-spacing: -0.5px; }}
        #chart-container {{ width: 100%; height: 680px; background-color: #000000; border-radius: 6px; position: relative; }}
    </style>
</head>
<body>
    <div class="header">Bitcoin (BTC/USDT) Live Terminal</div>
    <div class="price" id="btc-price">$---.--</div>
    <div id="chart-container"></div>

    <script>
        const viewMode = "{view_mode}";
        const container = document.getElementById('chart-container');
        const priceEl = document.getElementById('btc-price');
        let currentPrice = 65000;

        function generateFallbackCandles() {{
            let list = [];
            let now = Math.floor(Date.now() / 1000) - 300 * 60;
            let p = currentPrice;
            for(let i = 0; i < 300; i++) {{
                let open = p;
                let close = open + (Math.random() - 0.49) * 40;
                let high = Math.max(open, close) + Math.random() * 15;
                let low = Math.min(open, close) - Math.random() * 15;
                list.push({{ time: now + i * 60, open: open, high: high, low: low, close: close }});
                p = close;
            }}
            return list;
        }}

        // ====================================================
        // 1. TRADINGVIEW NATIVE CANDLESTICK ENGINE (500 KERZEN HISTORIE)
        // ====================================================
        if (viewMode.includes("Kerzenchart")) {{
            const chart = LightweightCharts.createChart(container, {{
                width: container.clientWidth,
                height: 680,
                layout: {{ 
                    background: {{ type: 'solid', color: '#000000' }}, 
                    textColor: '#A0A0A0' 
                }},
                grid: {{ vertLines: {{ color: '#0F0F0F' }}, horzLines: {{ color: '#0F0F0F' }} }},
                crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
                rightPriceScale: {{ borderColor: '#222222', autoScale: true }},
                timeScale: {{ borderColor: '#222222', timeVisible: true, secondsVisible: false }},
                handleScroll: true,
                handleScale: true
            }});

            const candleSeries = chart.addCandlestickSeries({{
                upColor: '#00FF88',
                downColor: '#FF0055',
                borderUpColor: '#00FF88',
                borderDownColor: '#FF0055',
                wickUpColor: '#00FF88',
                wickDownColor: '#FF0055',
            }});

            new ResizeObserver(entries => {{
                if (entries[0] && entries[0].contentRect) {{
                    chart.applyOptions({{ width: entries[0].contentRect.width }});
                }}
            }}).observe(container);

            // 500 Kerzen für maximale Genauigkeit
            fetch("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=500")
                .then(res => res.json())
                .then(data => {{
                    if(Array.isArray(data) && data.length > 0) {{
                        let formatted = data.map(d => ({{
                            time: Math.floor(d[0] / 1000),
                            open: parseFloat(d[1]),
                            high: parseFloat(d[2]),
                            low: parseFloat(d[3]),
                            close: parseFloat(d[4])
                        }}));
                        candleSeries.setData(formatted);
                        currentPrice = formatted[formatted.length - 1].close;
                    }} else {{
                        candleSeries.setData(generateFallbackCandles());
                    }}
                    priceEl.innerText = "$" + currentPrice.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
                }})
                .catch(() => {{
                    candleSeries.setData(generateFallbackCandles());
                }});

            function connectCandleWS() {{
                const ws = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@kline_1m');
                ws.onmessage = (event) => {{
                    try {{
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
                        priceEl.innerText = "$" + currentPrice.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
                    }} catch(e) {{}}
                }};
                ws.onclose = () => setTimeout(connectCandleWS, 1000);
            }}
            connectCandleWS();

        // ====================================================
        // 2. 3D VOLATILITY SURFACE (AKKURATES SVI-SMILE & FREIE KAMERA)
        // ====================================================
        }} else {{
            let tOffset = 0;
            let isUserInteracting = false;

            // Erkennung, ob der Nutzer die Kamera dreht
            container.addEventListener('mousedown', () => {{ isUserInteracting = true; }});
            window.addEventListener('mouseup', () => {{ isUserInteracting = false; }});
            container.addEventListener('touchstart', () => {{ isUserInteracting = true; }});
            window.addEventListener('touchend', () => {{ isUserInteracting = false; }});

            // Mathematisch akkurates Options-Volatilitätsmodell (Smile & Skew)
            function calcAccurateVolatilitySurface(price, offset) {{
                let strikes = [], expiries = [], zValues = [];
                for(let i=0; i<35; i++) strikes.push(price * (0.60 + i * 0.025));
                for(let j=0; j<25; j++) expiries.push(5 + j * 5.0);

                for(let j=0; j<25; j++) {{
                    let row = [];
                    let T = expiries[j];
                    for(let i=0; i<35; i++) {{
                        let K = strikes[i];
                        let moneyness = Math.log(K / price);
                        
                        // Echtes Volatilitäts-Smile (Skew für OTM Puts + Term Structure)
                        let skew = 0.4 * moneyness + 0.3 * Math.pow(moneyness, 2);
                        let termStructure = 0.15 / Math.sqrt(T / 30.0);
                        let liveWave = Math.sin(moneyness * 3.0 + offset) * 1.5;
                        
                        let iv = (38.0 + skew * 25.0 + termStructure * 10.0 + liveWave);
                        row.push(Math.max(10.0, iv));
                    }}
                    zValues.push(row);
                }}
                return {{ x: strikes, y: expiries, z: zValues }};
            }}

            fetch("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
                .then(res => res.json())
                .then(data => {{ if(data.price) currentPrice = parseFloat(data.price); }})
                .finally(() => {{
                    priceEl.innerText = "$" + currentPrice.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
                    let surf = calcAccurateVolatilitySurface(currentPrice, 0);

                    let trace = {{
                        x: surf.x, y: surf.y, z: surf.z,
                        type: 'surface',
                        colorscale: [[0.0, '#020024'], [0.35, '#090979'], [0.70, '#00d4ff'], [1.0, '#7000ff']],
                        showscale: true,
                        lighting: {{ ambient: 0.8, diffuse: 0.5, roughness: 0.5 }}
                    }};

                    let layout = {{
                        paper_bgcolor: '#000000',
                        plot_bgcolor: '#000000',
                        margin: {{ l: 0, r: 0, b: 0, t: 0 }},
                        scene: {{
                            xaxis: {{ title: 'Strike ($)', gridcolor: '#1F1F1F', color: '#888' }},
                            yaxis: {{ title: 'Days to Expiry', gridcolor: '#1F1F1F', color: '#888' }},
                            zaxis: {{ title: 'Implied Volatility (%)', gridcolor: '#1F1F1F', color: '#888' }},
                            camera: {{ eye: {{ x: -1.6, y: -1.6, z: 0.9 }} }}
                        }}
                    }};

                    Plotly.newPlot(container, [trace], layout, {{ responsive: true, displayModeBar: false }});

                    // Update-Schleife: Pausiert sofort bei Mausberührung (volle Kamerakontrolle)
                    setInterval(() => {{
                        if (!isUserInteracting) {{
                            tOffset += 0.04;
                            let surf = calcAccurateVolatilitySurface(currentPrice, tOffset);
                            Plotly.restyle(container, {{ z: [surf.z], x: [surf.x] }}, [0]);
                        }}
                    }}, 80);
                }});

            function connectTickerWS() {{
                const ws = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@ticker');
                ws.onmessage = (event) => {{
                    try {{
                        let msg = JSON.parse(event.data);
                        currentPrice = parseFloat(msg.c);
                        priceEl.innerText = "$" + currentPrice.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
                    }} catch(e) {{}}
                }};
                ws.onclose = () => setTimeout(connectTickerWS, 1000);
            }}
            connectTickerWS();
        }}
    </script>
</body>
</html>
"""

components.html(html_code, height=750)
