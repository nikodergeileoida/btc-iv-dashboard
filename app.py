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

    # Geändert: 100% Breite und Höhe auf 850px maximiert
    tv_widget_html = f"""
    <div class="tradingview-widget-container" style="height:850px;width:100%">
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
    """
    
    # Streamlit Frame ebenfalls auf 880px erhöht
    components.html(tv_widget_html, height=880, scrolling=False)
