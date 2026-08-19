else:
    st.subheader(f"🧊 Catenoid-Helicoid-Morph (Gekoppelt an {selected_market})")
    
    if df_data is not None and len(df_data) > 1:
        volatility_factor = float((df_data['High'].max() - df_data['Low'].min()) / base_price * 50)
        volatility_factor = max(0.5, min(volatility_factor, 3.5))
    else:
        volatility_factor = 1.0

    # Wir nutzen wieder den .replace() Trick, um JavaScript-Syntaxfehler zu vermeiden
    raw_surface_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
            body { margin: 0; background: #000000; overflow: hidden; }
            #plotly-div { width: 100%; height: 580px; }
        </style>
    </head>
    <body>
        <div id="plotly-div"></div>
        <script>
            const res = 80;
            const vol = VOL_PLACEHOLDER_NUM;

            function getMorph(frame) {
                let x = [], y = [], z = [];
                // Morphing-Parameter zwischen Catenoid und Helicoid
                let morph = Math.sin(frame * 0.2) * 0.5 + 0.5; 
                
                for (let i = 0; i < res; i++) {
                    let rowX = [], rowY = [], rowZ = [];
                    let u = (i / (res - 1)) * 4 - 2;
                    for (let j = 0; j < res; j++) {
                        let v = (j / (res - 1)) * Math.PI * 2;
                        
                        // Minimalflächen-Parametrisierung
                        let r = 1 + 0.2 * Math.sin(u * 2 + frame);
                        let px = Math.cosh(u * morph) * Math.cos(v);
                        let py = Math.cosh(u * morph) * Math.sin(v);
                        let pz = u * (1 - morph) + Math.sin(u * 3 + frame) * vol * 0.3;

                        rowX.push(px);
                        rowY.push(py);
                        rowZ.push(pz);
                    }
                    x.push(rowX);
                    y.push(rowY);
                    z.push(rowZ);
                }
                return { x: x, y: y, z: z };
            }

            let initialData = getMorph(0);
            const data = [{
                type: 'surface',
                x: initialData.x, y: initialData.y, z: initialData.z,
                colorscale: [[0, '#00ffcc'], [0.5, '#000000'], [1, '#ff0055']],
                showscale: false,
                opacity: 0.9
            }];

            const layout = {
                template: 'plotly_dark',
                paper_bgcolor: '#000000',
                margin: {l: 0, r: 0, b: 0, t: 0},
                scene: {
                    xaxis: {visible: false}, yaxis: {visible: false}, zaxis: {visible: false},
                    camera: { eye: {x: 1.8, y: 1.8, z: 1.2} }
                }
            };

            let plotDiv = document.getElementById('plotly-div');
            Plotly.newPlot(plotDiv, data, layout, {responsive: true});

            let frame = 0;
            function runAnimation() {
                frame += 0.05;
                let currentData = getMorph(frame);
                Plotly.restyle(plotDiv, {x: [currentData.x], y: [currentData.y], z: [currentData.z]}, [0]);
                setTimeout(runAnimation, 16);
            }
            runAnimation();
        </script>
    </body>
    </html>
    """.replace("VOL_PLACEHOLDER_NUM", str(volatility_factor))

    components.html(raw_surface_html, height=600)
    st.caption("ℹ️ **Catenoid-Helicoid-Morph:** Eine fließende Minimalfläche, die durch den Live-Volatilitäts-Faktor ({volatility_factor:.2f}) ihre Struktur permanent transformiert.")
