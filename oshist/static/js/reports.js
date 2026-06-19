(() => {
    "use strict";

    const readChartData = (id) => {
        const element = document.getElementById(id);
        return element ? JSON.parse(element.textContent) : null;
    };

    const yen = (value) => `${Number(value).toLocaleString("ja-JP")}円`;
    const accent = "#4a90d9";
    const accentLight = "rgba(74, 144, 217, 0.55)";

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: (context) => yen(context.raw),
                },
            },
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: (value) => yen(value),
                },
            },
        },
    };

    const monthly = readChartData("monthly-chart-data");
    const monthlyCanvas = document.getElementById("monthly-spending-chart");
    if (monthly && monthlyCanvas) {
        new Chart(monthlyCanvas, {
            type: "bar",
            data: {
                labels: monthly.labels,
                datasets: [{
                    data: monthly.amounts,
                    backgroundColor: accentLight,
                    borderColor: accent,
                    borderWidth: 1,
                }],
            },
            options: commonOptions,
        });
    }

    const createHorizontalChart = (canvasId, dataId) => {
        const chartData = readChartData(dataId);
        const canvas = document.getElementById(canvasId);
        if (!chartData || !canvas || chartData.labels.length === 0) {
            return;
        }
        new Chart(canvas, {
            type: "bar",
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.amounts,
                    backgroundColor: accentLight,
                    borderColor: accent,
                    borderWidth: 1,
                }],
            },
            options: {
                ...commonOptions,
                indexAxis: "y",
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => yen(value),
                        },
                    },
                },
            },
        });
    };

    createHorizontalChart("series-spending-chart", "series-chart-data");
    createHorizontalChart("category-spending-chart", "category-chart-data");
})();
