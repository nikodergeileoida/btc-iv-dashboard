if "TradingView" in view_mode:
    st.subheader(f"📈 TradingView Live-Terminal — {selected_market}")

    tv_symbol_map = {
        "BTC-USD": "BINANCE:BTCUSDT",
        "ETH-USD": "BINANCE:ETHUSDT",
        "SOL-USD": "BINANCE:SOLUSDT",
        "BNB-USD": "BINANCE:BNBUSDT",
        "XRP-USD": "BINANCE:XRPUSDT",
        "SPY": "AMEX:SPY",
        "QQQ": "NASDAQ:QQQ",
        "AAPL": "NASDAQ:AAPL",
        "TSLA": "NASDAQ:TSLA",
        "NVIDIA": "NASDAQ:NVDA",
        "^GDAXI": "XETR:DAX",
        "SAP.DE": "XETR:SAP",
        "SIE.DE": "XETR:SIE",
        "ALV.DE": "XETR:ALV",
        "GC=F": "COMEX:GC1!",
        "SI=F": "NYMEX:SI1!",
        "CL=F": "NYMEX:CL1!",
        "EURUSD=X": "FX_IDC:EURUSD"
    }
    
    tv_symbol = tv_symbol_map.get(ticker_symbol, "BINANCE:BTCUSDT")

    # HTML Container nutzt nun die volle verfügbare Ansichtsfenster-Höhe (100vh)
    tv_widget_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; background: #000; overflow: hidden; }}
            .tradingview-widget-container {{ width: 100%; height: 100vh; }}
        </style>
    </head>
    <body>
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget" style="height:100%;width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
          {{
            "autosize": true,
            "symbol": "{tv_symbol}",
            "interval": "D",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "de",
            "enable_publishing": false,
            "hide_top_toolbar": false,
            "hide_legend": false,
            "save_image": false,
            "calendar": false,
            "support_host": "https://www.tradingview.com"
          }}
          </script>
        </div>
    </body>
    </html>
    """
    
    # Streamlit-Komponente auf 900 Pixel maximiert, damit der Platz komplett eingenommen wird
    components.html(tv_widget_html, height=900, scrolling=False)
