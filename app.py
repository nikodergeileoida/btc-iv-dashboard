import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import pandas as pd

st.set_page_config(page_title="BTC Live IV Surface", layout="wide")
st.title("Bitcoin Implied Volatility Surface (Deribit Live)")

@st.cache_data(ttl=15)
def get_deribit_data():
    url = "https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option"
    try:
        res = requests.get(url).json()
        return res.get("result", [])
    except Exception:
        return []

raw_data = get_deribit_data()

if raw_data:
    parsed = []
    for item in raw_data:
        parts = item["instrument_name"].split("-")
        if len(parts) == 4 and item.get("mark_iv", 0) > 0:
            parsed.append({
                "expiry": parts[1],
                "strike": float(parts[2]),
                "iv": item["mark_iv"]
            })

    df = pd.DataFrame(parsed)
    if not df.empty:
        pivot = df.pivot_table(index="strike", columns="expiry", values="iv", aggfunc="mean").dropna()

        strikes = pivot.index.tolist()
        expiries = pivot.columns.tolist()
        z_values = pivot.values.tolist()

        # Flicker-free Plotly.js rendering via HTML component
        plotly_html = f"""
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <div id="plotly-surface" style="width:100%; height:750px;"></div>
        <script>
            var data = [{{
                x: {json.dumps(expiries)},
                y: {json.dumps(strikes)},
                z: {json.dumps(z_values)},
                type: 'surface',
                colorscale: 'Viridis'
            }}];

            var layout = {{
                autosize: true,
                scene: {{
                    xaxis: {{ title: 'Expiry' }},
                    yaxis: {{ title: 'Strike (USD)' }},
                    zaxis: {{ title: 'IV (%)' }}
                }},
                margin: {{ l: 0, r: 0, b: 0, t: 10 }}
            }};

            Plotly.react('plotly-surface', data, layout, {{responsive: true}});
        </script>
        """
        components.html(plotly_html, height=770)
else:
    st.warning("Lade Deribit-Marktdaten...")
