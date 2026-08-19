<script>
            const res = 70; 
            const vol = {volatility_factor};

            function getRiemannGrid(frame) {
                let x = [], y = [], z = [];
                for (let i = 0; i < res; i++) {
                    let rowX = [], rowY = [], rowZ = [];
                    let u = (i / (res - 1)) * Math.PI * 4 - Math.PI * 2;
                    for (let j = 0; j < res; j++) {
                        let v = (j / (res - 1)) * Math.PI * 2;
                        
                        let r = Math.sin(u * 1.5) * Math.cos(v * 1.5) * 2.0;
                        let px = u * 0.8 + Math.sin(v + frame * 0.3) * vol * 0.5;
                        let py = v * 0.8 + Math.cos(u + frame * 0.3) * vol * 0.5;
                        let pz = Math.sin(u * v - frame * 0.5) * (1.5 + 0.5 * Math.cos(u)) * vol;

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

            let initialData = getRiemannGrid(0);

            const data = [{
                type: 'surface',
                x: initialData.x,
                y: initialData.y,
                z: initialData.z,
                colorscale: 'YlGnBu',
                showscale: false,
                lighting: { ambient: 0.2, diffuse: 0.9, specular: 0.9, roughness: 0.1 }
            }];

            const layout = {
                template: 'plotly_dark',
                paper_bgcolor: '#000000',
                plot_bgcolor: '#000000',
                autosize: true,
                margin: {l: 0, r: 0, b: 0, t: 0},
                scene: {
                    bgcolor: '#000000',
                    xaxis: {showgrid: false, zeroline: false, showticklabels: false, title: ''},
                    yaxis: {showgrid: false, zeroline: false, showticklabels: false, title: ''},
                    zaxis: {showgrid: false, zeroline: false, showticklabels: false, title: '', range: [-4, 4]},
                    camera: { eye: {x: 2.2, y: -2.2, z: 1.6} }
                }
            };

            let plotDiv = document.getElementById('plotly-div');
            Plotly.newPlot(plotDiv, data, layout, {responsive: true, scrollZoom: true, displayModeBar: true});

            function zoomIn() {
                let cam = plotDiv._fullLayout.scene.camera;
                let newEye = { x: cam.eye.x * 0.75, y: cam.eye.y * 0.75, z: cam.eye.z * 0.75 };
                Plotly.relayout(plotDiv, {'scene.camera.eye': newEye});
            }

            function zoomOut() {
                let cam = plotDiv._fullLayout.scene.camera;
                let newEye = { x: cam.eye.x * 1.25, y: cam.eye.y * 1.25, z: cam.eye.z * 1.25 };
                Plotly.relayout(plotDiv, {'scene.camera.eye': newEye});
            }

            let isInteracting = false;
            plotDiv.addEventListener('mousedown', () => { isInteracting = true; });
            window.addEventListener('mouseup', () => { isInteracting = false; });

            let frame = 0;
            function runAnimation() {
                if (!isInteracting) {
                    // Angepasster Frame-Zuwachs für 120 FPS
                    frame += 0.01; 
                    let currentData = getRiemannGrid(frame);
                    Plotly.restyle(plotDiv, {
                        x: [currentData.x],
                        y: [currentData.y],
                        z: [currentData.z]
                    }, [0]);
                }
                // 8ms Intervall für ~120 FPS
                setTimeout(runAnimation, 8);
            }

            setTimeout(runAnimation, 8);
        </script>
