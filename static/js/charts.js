/* ==========================================
   MEDI-MIND CDSS - CHART VISUALIZATION ENGINE
   ========================================== */

let benchmarkChartInstance = null;
let clusterChartInstance = null;

function renderBenchmarkChart(benchmarkData) {
    const ctx = document.getElementById('benchmarkChart');
    if (!ctx) return;

    const labels = Object.keys(benchmarkData);
    const accuracies = labels.map(k => benchmarkData[k].accuracy);
    const precisions = labels.map(k => benchmarkData[k].precision);
    const recalls = labels.map(k => benchmarkData[k].recall);
    const f1Scores = labels.map(k => benchmarkData[k].f1_score);

    if (benchmarkChartInstance) {
        benchmarkChartInstance.destroy();
    }

    benchmarkChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Accuracy (%)',
                    data: accuracies,
                    backgroundColor: 'rgba(6, 182, 212, 0.7)',
                    borderColor: '#06b6d4',
                    borderWidth: 1
                },
                {
                    label: 'Precision (%)',
                    data: precisions,
                    backgroundColor: 'rgba(13, 148, 136, 0.7)',
                    borderColor: '#0d9488',
                    borderWidth: 1
                },
                {
                    label: 'Recall (%)',
                    data: recalls,
                    backgroundColor: 'rgba(59, 130, 246, 0.7)',
                    borderColor: '#3b82f6',
                    borderWidth: 1
                },
                {
                    label: 'F1-Score (%)',
                    data: f1Scores,
                    backgroundColor: 'rgba(16, 185, 129, 0.7)',
                    borderColor: '#10b981',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                }
            },
            plugins: {
                legend: { labels: { color: '#f8fafc' } }
            }
        }
    });
}

function renderClusterScatterChart(clusterData) {
    const ctx = document.getElementById('clusterChart');
    if (!ctx) return;

    const points = clusterData.points || [];
    const colors = ['#06b6d4', '#f59e0b', '#ef4444', '#10b981'];
    const clusterNames = [
        "Cluster 0: Low Risk",
        "Cluster 1: Metabolic Risk",
        "Cluster 2: Cardiovascular Alert",
        "Cluster 3: Elderly Comorbidity"
    ];

    const datasets = [0, 1, 2, 3].map(k => {
        const clusterPts = points.filter(p => p.cluster === k);
        return {
            label: clusterNames[k],
            data: clusterPts.map(p => ({ x: p.x, y: p.y, patientName: p.name, age: p.age, bmi: p.bmi, bp: p.bp })),
            backgroundColor: colors[k],
            pointRadius: 6,
            pointHoverRadius: 9
        };
    });

    if (clusterChartInstance) {
        clusterChartInstance.destroy();
    }

    clusterChartInstance = new Chart(ctx, {
        type: 'scatter',
        data: { datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'PCA Dimension 1', color: '#94a3b8' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    title: { display: true, text: 'PCA Dimension 2', color: '#94a3b8' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                }
            },
            plugins: {
                legend: { labels: { color: '#f8fafc' } },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const raw = context.raw;
                            return `${raw.patientName} (Age: ${raw.age}, BMI: ${raw.bmi}, BP: ${raw.bp})`;
                        }
                    }
                }
            }
        }
    });
}

let trajectoryChartInstance = null;

function renderTrajectoryChart(years, baselineData, optimizedData) {
    const ctx = document.getElementById('trajectoryChart');
    if (!ctx) return;

    const labels = years.map(y => `Year ${y}`);

    if (trajectoryChartInstance) {
        trajectoryChartInstance.destroy();
    }

    trajectoryChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Baseline Trajectory (Compounding Risk)',
                    data: baselineData,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2.5,
                    borderDash: [5, 5],
                    pointBackgroundColor: '#ef4444',
                    pointRadius: 4,
                    fill: false,
                    tension: 0.3
                },
                {
                    label: 'Prescriptive Target Trajectory (With Lifestyle Intervention)',
                    data: optimizedData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    borderWidth: 3,
                    pointBackgroundColor: '#10b981',
                    pointRadius: 4,
                    fill: true,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    title: { display: true, text: 'Cumulative Event Risk (%)', color: '#94a3b8' },
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { 
                        color: '#94a3b8',
                        callback: function(value) { return value + '%'; }
                    }
                },
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                }
            },
            plugins: {
                legend: { 
                    labels: { color: '#f8fafc', font: { size: 11 } },
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y}% risk`;
                        }
                    }
                }
            }
        }
    });
}

