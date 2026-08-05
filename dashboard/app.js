// Configuration
const API_BASE_URL = 'https://lqlt6vvduh.execute-api.us-east-1.amazonaws.com/dev/analytics';

// Chart instances
let revenueChartInstance = null;
let productsChartInstance = null;

// Chart.js defaults for dark theme
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';

async function fetchSummary() {
    try {
        const response = await fetch(`${API_BASE_URL}/summary`);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        
        document.getElementById('api-health').textContent = 'Live (Connected)';
        document.getElementById('api-health').style.color = '#10b981';
        
        updateDashboard(data);
    } catch (error) {
        console.error('Error fetching data:', error);
        document.getElementById('api-health').textContent = 'Disconnected';
        document.getElementById('api-health').style.color = '#ef4444';
        document.querySelector('.status-indicator').style.backgroundColor = '#ef4444';
        document.querySelector('.status-indicator').style.boxShadow = '0 0 10px #ef4444';
    }
}

function updateDashboard(data) {
    // 1. Update KPIs
    const totalRev = data.revenue.total_revenue || 0;
    document.getElementById('kpi-revenue').textContent = `$${totalRev.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    
    // Calculate total events processed from top products
    let totalEvents = 0;
    if (data.top_products && data.top_products.length > 0) {
        data.top_products.forEach(p => {
            totalEvents += (p.views + p.purchases);
        });
    }
    document.getElementById('kpi-events').textContent = totalEvents > 0 ? totalEvents + '+' : '0';

    // 2. Update Revenue Chart
    if (data.revenue && data.revenue.timeline) {
        const labels = data.revenue.timeline.map(item => item.time);
        const values = data.revenue.timeline.map(item => item.revenue);
        
        const revCtx = document.getElementById('revenueChart').getContext('2d');
        
        if (revenueChartInstance) revenueChartInstance.destroy();
        
        const gradient = revCtx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.5)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

        revenueChartInstance = new Chart(revCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Revenue ($)',
                    data: values,
                    borderColor: '#3b82f6',
                    backgroundColor: gradient,
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#1e293b',
                    pointBorderColor: '#3b82f6',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    // 3. Update Products Chart
    if (data.top_products && data.top_products.length > 0) {
        // Filter out 'unknown' for the chart to make it cleaner, or keep it. Let's keep top 5 named.
        const namedProducts = data.top_products.filter(p => p.product_id !== 'unknown').slice(0, 5);
        const labels = namedProducts.map(p => p.product_id);
        const scores = namedProducts.map(p => p.score);
        
        const prodCtx = document.getElementById('productsChart').getContext('2d');
        
        if (productsChartInstance) productsChartInstance.destroy();
        
        productsChartInstance = new Chart(prodCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Activity Score',
                    data: scores,
                    backgroundColor: '#8b5cf6',
                    borderRadius: 6,
                    barThickness: 30
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    // 4. Update Table
    if (data.top_products) {
        const tbody = document.querySelector('#productsTable tbody');
        tbody.innerHTML = '';
        
        data.top_products.slice(0, 8).forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${p.product_id}</strong></td>
                <td>${p.views}</td>
                <td>${p.purchases}</td>
                <td><span style="color: #10b981; font-weight: 600;">${p.score}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }
}

// Initialize
fetchSummary();
// Refresh every 10 seconds to simulate real-time
setInterval(fetchSummary, 10000);
