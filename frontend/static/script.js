async function loadMetrics() {

    const response = await fetch("/api/metrics");

    const data = await response.json();

    document.getElementById("orders").innerText =
        data.orders_processed.toLocaleString();

    document.getElementById("trades").innerText =
        data.trades_generated.toLocaleString();

    document.getElementById("latency").innerText =
        data.avg_latency_ns + " ns";

    document.getElementById("throughput").innerText =
        (data.throughput / 1000000).toFixed(2) + " M/sec";

    document.getElementById("cython").innerText =
        data.cython_enabled ? "ENABLED ✓" : "DISABLED";

    document.getElementById("gil").innerText =
        data.gil_free ? "ENABLED ✓" : "DISABLED";

    document.getElementById("tests").innerText =
        data.tests_passed + " / 48 PASSED";
}


async function loadOrderBook() {

    const response = await fetch("/api/orderbook");

    const data = await response.json();

    const bids = document.getElementById("bids");

    const asks = document.getElementById("asks");

    bids.innerHTML = "";
    asks.innerHTML = "";

    data.bids.forEach(order => {

        bids.innerHTML += `
            <tr>
                <td>${order.price}</td>
                <td>${order.quantity}</td>
            </tr>
        `;

    });


    data.asks.forEach(order => {

        asks.innerHTML += `
            <tr>
                <td>${order.price}</td>
                <td>${order.quantity}</td>
            </tr>
        `;

    });

}


async function loadDashboard() {

    try {

        await loadMetrics();

        await loadOrderBook();

    }

    catch (error) {

        console.error(
            "Dashboard loading error:",
            error
        );

    }

}


loadDashboard();

setInterval(
    loadDashboard,
    3000
);
async function loadDashboard() {
    try {
        const response = await fetch("/api/status");
        const data = await response.json();

        document.getElementById("orders").textContent =
            data.orders_processed.toLocaleString();

        document.getElementById("trades").textContent =
            data.trades_generated.toLocaleString();

        document.getElementById("latency").textContent =
            data.average_latency;

        document.getElementById("throughput").textContent =
            data.throughput;

        document.getElementById("c-level").textContent =
            data.c_level_optimization;

        document.getElementById("gil-free").textContent =
            data.gil_free_matching;

        document.getElementById("tests").textContent =
            data.automated_tests;

    } catch (error) {
        console.error("Dashboard data loading failed:", error);
    }
}

loadDashboard();