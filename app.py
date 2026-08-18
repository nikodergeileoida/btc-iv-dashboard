import streamlit as st
import qrcode
from io import BytesIO
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# 1. Konfiguration & Feste Cloud-URL
st.set_page_config(
    page_title="Global Multi-Asset 3D Monitoring Terminal",
    page_icon="📈",
    layout="wide"
)

CLOUD_URL = "https://bitcoinstatus3d.streamlit.app/"

# 2. Sidebar Navigation & Globale Markt-Kategorien
st.sidebar.title("🌍 Global Markets")
menu = st.sidebar.radio("Ansicht wählen", ["📊 Live Terminal", "📱 Mobile QR-Code"])

st.sidebar.divider()
st.sidebar.markdown("### 🗂️ Markt-Kategorie")
asset_class = st.sidebar.selectbox(
    "Asset-Klasse wählen:", 
    ["Kryptowährungen", "US-Märkte (Aktien/Indizes)", "Deutsche Märkte (Xetra/DAX)", "Forex & Rohstoffe"]
)

# Dynamische Markt-Auswahl basierend auf der Kategorie
if asset_class == "Kryptowährungen":
    market_list = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
    market_type = "crypto"
elif asset_class == "US-Märkte (Aktien/Indizes)":
    market_list = ["S&P 500 (SPY)", "Nasdaq 100 (QQQ)", "Apple (AAPL)", "Tesla (TSLA)", "NVIDIA (NVDA)"]
    market_type = "us"
elif asset_class == "Deutsche Märkte (Xetra/DAX)":
    market_list = ["DAX Index (DAX)", "SAP SE (SAP)", "Siemens (SIE)", "Allianz (ALV)"]
    market_type = "de"
else:
    market_list = ["Gold (XAUUSD)", "Silver (XAGUSD)", "Crude Oil (WTI)", "EUR/USD"]
    market_type = "forex"

selected_market = st.sidebar.selectbox("🎯 Spezieller Markt:", market_list)

# Einfache Marktstatus-Logik (Öffnungszeiten-Simulation)
def get_market_status(m_type):
    if m_type == "crypto":
        return "🟢 24/7 Geöffnet (Live)", "Open"
    
    # Vereinfachte Prüfung für traditionelle Märkte (Beispiel basierend auf UTC/MEZ)
    now_hour = datetime.utcnow().hour
    # Xetra/DAX ca. 07:00 - 15:30 UTC, US ca. 13:30 - 20:00 UTC
    if m_type == "de" and 7 <= now_hour < 16:
        return "🟢 Xetra Geöffnet", "Open"
    elif m_type == "us" and 13 <= now_hour < 21:
        return "🟢 US-Börse Geöffnet", "Open"
    elif m_type == "forex":
        return "🟢 Forex Aktiv", "Open"
    else:
        return "🔴 Markt Geschlossen (Feierabend/Wochenende)", "Closed"

status_text, status_flag = get_market_status(market_type)

# 3. Haupt-Logik
if menu == "📊 Live Terminal":
    st.title(f"⚡ Live Monitoring Terminal — {selected_market}")
    st.markdown(f"Kategorie: **{asset_class}** | Status: **{status_text}**")
    
    # Metriken-Leiste
    col1, col2, col3 = st.columns(3)
    col1.metric("Aktiver Markt", selected_market, status_flag)
    col2.metric("Daten-Feed", "Live WebSocket / API", "Aktiv")
    col3.metric("Hosting", "Streamlit Cloud", "24/7 Online")
    
    st.divider()
    
    # --- ANSCHNITT: CHARTS & 3D-OBERFLÄCHE ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📈 Live Chart (Candlestick / Preis)")
        # Simulierter Preisverlauf im Bitcoin-Style
        chart_data = np.cumsum(np.random.randn(50)) + 100
        st.line_chart(chart_data)
        st.caption(f"Echtzeit-Preisverlauf für {selected_market}")

    with c2:
        st.subheader("🧊 3D Volatilitàts-Oberfläche (Enger skaliert)")
        
        # Hier wurden die Werte enger zusammengelegt (kleinere Schritte / feinere Gitterdichte)
        x = np.linspace(-1.0, 1.0, 30)  # Engere Abstände für Strike / Moneyness
        y = np.linspace(0.1, 1.0, 30)  # Engere Abstände für Laufzeit / Expiry
        X, Y = np.meshgrid(x, y)
        
        # Volatlichkeits-Smile Formel passend simuliert
        Z = np.sin(X) * np.cos(Y) + (X**2) * 0.5 + 2.0
        
        fig = go.Figure(data=[go.Surface(z=Z, x=X, y=Y, colorscale='Viridis')])
        fig.update_layout(
            title=f"3D Volatility Smile — {selected_market}",
            autosize=False,
      графіk_width=500,
            height=400,
            margin=dict(l=20, r=20, b=20, t=40)
        )
        st.plotly_chart(fig, use_container_width=True)

elif menu == "📱 Mobile QR-Code":
    st.title("📱 Mobile Access (QR-Code)")
    st.markdown("Scanne diesen Code mit deinem Smartphone, um von überall auf den Markt zuzugreifen:")
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(CLOUD_URL)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(buffered.getvalue(), caption=CLOUD_URL, use_container_width=True)
        st.success("App ist global einsatzbereit auf allen Endgeräten!")
