async function submitPlot(formId, endpoint, containerId) {
    const form = document.getElementById(formId);
    const container = document.getElementById(containerId);

    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        container.innerHTML = `
            <div class="loading-box">
                <div class="spinner"></div>
                <div>Chargement de la visualisation...</div>
            </div>
        `;

        const formData = new FormData(form);

        try {
            const response = await fetch(endpoint, {
                method: "POST",
                body: formData
            });

            const result = await response.json();

            if (result.plot_type === "plotly") {
                container.innerHTML = "";
                Plotly.purge(container);
                await Plotly.newPlot(container, result.figure.data, result.figure.layout, {
                 responsive: true,
                 displayModeBar: false
                });
                setTimeout(() => {
                    Plotly.Plots.resize(container);
                }, 100);
}
            else if (result.plot_type === "matplotlib") {
                Plotly.purge(container);
                container.innerHTML = `
                    <img
                        src="data:image/png;base64,${result.image_base64}"
                        alt="Plot"
                    >
                `;
            } else {
                container.innerHTML = `<p>Erreur : ${result.message || "Impossible d'afficher la figure."}</p>`;
            }
        } catch (error) {
            console.error(error);
            container.innerHTML = `<p>Erreur lors du chargement du graphique.</p>`;
        }
    });
}

submitPlot("form-france-map", "/plot/france-map", "plot-france-map");
submitPlot("form-region-time-series", "/plot/region-time-series", "plot-region-time-series");
submitPlot("form-monthly-comparison", "/plot/monthly-comparison", "plot-monthly-comparison");
submitPlot("form-seasonality-boxplot", "/plot/seasonality-boxplot", "plot-seasonality-boxplot");
submitPlot("form-waterways-flood", "/plot/waterways-flood", "plot-waterways-flood");