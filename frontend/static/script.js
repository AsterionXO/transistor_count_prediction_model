// --- 1. CHART INITIALIZATION ---
const ctx = document.getElementById('trendChart').getContext('2d');

const historicalData = [
    { x: 1971, y: 2300 }, { x: 1980, y: 29000 }, { x: 1990, y: 1200000 },
    { x: 2000, y: 42000000 }, { x: 2010, y: 2300000000 }, { x: 2020, y: 50000000000 }
];

const chart = new Chart(ctx, {
    type: 'scatter',
    data: {
        datasets: [
            {
                label: 'Historical Trend (Moore\'s Law)',
                data: historicalData,
                borderColor: '#444',
                backgroundColor: '#444',
                showLine: true,
                borderDash: [5, 5],
                pointRadius: 3
            },
            {
                label: 'Your Prediction (You Are Here)',
                data: [],
                backgroundColor: '#00bcd4',
                borderColor: '#fff',
                borderWidth: 2,
                pointRadius: 8,
                pointHoverRadius: 10
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { title: { display: true, text: 'Year', color: '#888' }, grid: { color: '#333' } },
            y: {
                type: 'logarithmic',
                title: { display: true, text: 'Transistor Count (Log Scale)', color: '#888' },
                grid: { color: '#333' }
            }
        },
        plugins: { legend: { labels: { color: '#fff' } } }
    }
});

// --- 2. FORM HANDLING ---
document.getElementById('predictForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const btn = document.getElementById('predictBtn');
    const originalText = btn.innerText;
    btn.innerText = "Calculating...";
    btn.disabled = true;

    const node = parseFloat(document.getElementById('node_size').value);
    if (node <= 0) {
        alert("Warning: Node size must be positive.");
    }

    const data = {
        year: document.getElementById('year').value,
        node_size: node,
        area: document.getElementById('area').value,
        trans_density: document.getElementById('trans_density').value,
        power_density: document.getElementById('power_density').value
    };

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if(result.status === 'success') {
            document.getElementById('result').classList.remove('hidden');
            document.getElementById('predictionValue').textContent = result.formatted_count;
            document.getElementById('confInterval').textContent = `${result.lower_bound} - ${result.upper_bound}`;
            document.getElementById('mooresComp').textContent = result.moores_comp;

            chart.data.datasets[1].data = [{ x: parseFloat(data.year), y: result.prediction_count }];
            chart.update();

            // Setup PDF Export Button
            document.getElementById('exportBtn').onclick = () => exportPDF(result, data);

            document.querySelector('.chart-section').scrollIntoView({ behavior: 'smooth' });
        } else {
            alert("Error: " + result.message);
        }

    } catch (error) {
        console.error(error);
        alert("Server Connection Failed");
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
});

// --- 3. PDF EXPORT FUNCTION ---
function exportPDF(result, inputs) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    doc.setFontSize(20);
    doc.setTextColor(0, 188, 212);
    doc.text("Transistor Count Prediction Report", 105, 20, null, null, "center");

    doc.setFontSize(10);
    doc.setTextColor(100);
    doc.text(`Generated on: ${new Date().toLocaleString()}`, 105, 30, null, null, "center");

    doc.setDrawColor(0);
    doc.line(20, 35, 190, 35);
    doc.setFontSize(14);
    doc.setTextColor(0);
    doc.text("Model Inputs:", 20, 45);

    doc.setFontSize(12);
    doc.setTextColor(60);
    let y = 55;
    const inputLabels = {
        year: "Target Year",
        node_size: "Node Size (nm)",
        area: "Die Area (mm2)",
        trans_density: "Transistor Density (tr/mm2)",
        power_density: "Power Density (W/cm2)"
    };

    for (const [key, value] of Object.entries(inputs)) {
        doc.text(`- ${inputLabels[key] || key}: ${value}`, 25, y);
        y += 8;
    }

    y += 10;
    doc.line(20, y, 190, y);
    y += 10;
    doc.setFontSize(14);
    doc.setTextColor(0);
    doc.text("Projection Results:", 20, y);

    y += 15;
    doc.setFontSize(16);
    doc.setTextColor(0, 150, 0);
    doc.text(`Predicted Count: ${result.formatted_count}`, 25, y);

    y += 10;
    doc.setFontSize(12);
    doc.setTextColor(60);
    doc.text(`Confidence Interval (20%): ${result.lower_bound} to ${result.upper_bound}`, 25, y);
    y += 8;
    doc.text(`Moore's Law Comparison: ${result.moores_comp}`, 25, y);
    y += 8;
    doc.text(`Log10 Value: ${result.prediction_log}`, 25, y);

    doc.setFontSize(10);
    doc.setTextColor(150);
    doc.text("Generated by Silicon Scaling Projector", 105, 280, null, null, "center");

    doc.save("prediction_report.pdf");
}

// --- 4. MODAL HANDLING SYSTEM ---
function toggleModal(modalId, show) {
    const modal = document.getElementById(modalId);
    if (show) {
        modal.style.display = "flex";
    } else {
        modal.style.display = "none";
    }
}

// Updated Button Listeners (Removed aboutBtn)
document.getElementById("creatorBtn").onclick = () => toggleModal("creatorModal", true);
document.getElementById("contactBtn").onclick = () => toggleModal("contactModal", true);

// Close Button Listeners
document.querySelectorAll('.close').forEach(closeBtn => {
    closeBtn.onclick = function() {
        const targetId = this.getAttribute('data-target');
        toggleModal(targetId, false);
    };
});

// Close on Outside Click
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = "none";
    }
};