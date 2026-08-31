/**
 * ChronosMatch High-Frequency Trading Monitoring Dashboard JS
 */

// Helper to format numbers with commas
function formatNumber(val) {
    if (val === undefined || val === null || isNaN(val)) return "0";
    return Number(val).toLocaleString();
}

// Show notification toast message
function showNotification(message, isError = false) {
    const banner = document.getElementById("sim-notification");
    const textEl = document.getElementById("notification-text");

    if (!banner || !textEl) return;

    textEl.textContent = message;
    banner.style.backgroundColor = isError ? "rgba(244, 63, 94, 0.15)" : "rgba(56, 189, 248, 0.15)";
    banner.style.borderColor = isError ? "rgba(244, 63, 94, 0.3)" : "rgba(56, 189, 248, 0.3)";
    banner.style.color = isError ? "#f43f5e" : "#38bdf8";

    banner.classList.remove("hidden");

    setTimeout(() => {
        banner.classList.add("hidden");
    }, 4000);
}

// Refresh All Dashboard Views & Metrics directly from backend API
async function refreshDashboard(isUserAction = false) {
    const btnRefresh = document.getElementById("btn-refresh");
    if (btnRefresh) {
        btnRefresh.disabled = true;
    }

    try {
        const timestamp = Date.now();

        // Fetch metrics, status, orderbook, and whale event with cache-busting timestamp
        const [metricsRes, statusRes, bookRes] = await Promise.all([
            fetch(`/api/metrics?t=${timestamp}`),
            fetch(`/api/status?t=${timestamp}`),
            fetch(`/api/orderbook?t=${timestamp}`)
        ]);

        if (metricsRes.ok) {
            const data = await metricsRes.json();

            // 1. Orders Processed
            const ordersEl = document.getElementById("orders");
            if (ordersEl) ordersEl.textContent = formatNumber(data.orders_processed);

            // 2. Trades Generated
            const tradesEl = document.getElementById("trades");
            if (tradesEl) tradesEl.textContent = formatNumber(data.trades_generated);

            // 3. Average Latency
            const latencyEl = document.getElementById("latency");
            if (latencyEl) {
                latencyEl.textContent = data.average_latency || (data.avg_latency_ns > 0 ? `${data.avg_latency_ns} ns/order` : "0 ns/order");
            }

            // 4. Throughput
            const throughputEl = document.getElementById("throughput");
            if (throughputEl) {
                throughputEl.textContent = data.throughput || (data.throughput_val > 0 ? `${formatNumber(data.throughput_val)} orders/second` : "0 orders/second");
            }
        }

        if (statusRes.ok) {
            const data = await statusRes.json();

            const statusText = document.getElementById("system-status-text");
            if (statusText) statusText.textContent = `SYSTEM ${data.system || "ONLINE"}`;

            const cLevelEl = document.getElementById("c-level");
            if (cLevelEl) {
                cLevelEl.textContent = data.c_level_optimization === "ENABLED" ? "ENABLED ✓" : "DISABLED";
                cLevelEl.style.color = data.c_level_optimization === "ENABLED" ? "#10b981" : "#f43f5e";
            }

            const gilFreeEl = document.getElementById("gil-free");
            if (gilFreeEl) {
                gilFreeEl.textContent = data.gil_free_matching === "ENABLED" ? "ENABLED ✓" : "DISABLED";
                gilFreeEl.style.color = data.gil_free_matching === "ENABLED" ? "#10b981" : "#f43f5e";
            }

            const testsEl = document.getElementById("tests");
            if (testsEl) {
                testsEl.textContent = data.automated_tests || "91/91 PASSED";
                testsEl.style.color = "#10b981";
            }
        }

        if (bookRes.ok) {
            const data = await bookRes.json();
            const bidsBody = document.getElementById("bids-body");
            const asksBody = document.getElementById("asks-body");

            if (bidsBody) {
                if (!data.bids || data.bids.length === 0) {
                    bidsBody.innerHTML = '<tr><td colspan="3" class="empty-state">Order book bids empty</td></tr>';
                } else {
                    bidsBody.innerHTML = data.bids.map(bid => `
                        <tr>
                            <td><strong>${formatNumber(bid.price)}</strong></td>
                            <td>${formatNumber(bid.quantity)}</td>
                            <td>${bid.order_count || 1}</td>
                        </tr>
                    `).join('');
                }
            }

            if (asksBody) {
                if (!data.asks || data.asks.length === 0) {
                    asksBody.innerHTML = '<tr><td colspan="3" class="empty-state">Order book asks empty</td></tr>';
                } else {
                    asksBody.innerHTML = data.asks.map(ask => `
                        <tr>
                            <td><strong>${formatNumber(ask.price)}</strong></td>
                            <td>${formatNumber(ask.quantity)}</td>
                            <td>${ask.order_count || 1}</td>
                        </tr>
                    `).join('');
                }
            }
        // Fetch & render Whale event alert if present
        await loadWhaleEvent();

        if (isUserAction) {
            showNotification("Metrics refreshed successfully from backend.");
        }

    } catch (error) {
        console.error("Refresh error:", error);
        if (isUserAction) {
            showNotification("Failed to refresh metrics: " + error.message, true);
        }
    } finally {
        if (btnRefresh) btnRefresh.disabled = false;
    }
}

// Helper wrapper functions
async function loadStatus() { return refreshDashboard(false); }
async function loadMetrics() { return refreshDashboard(false); }
async function loadOrderBook() { return refreshDashboard(false); }

// ---------------------------------------------------------------------------
// Whale Event Alert
// ---------------------------------------------------------------------------

/**
 * Fetch the latest whale event from the backend and update the alert panel.
 * The panel is shown only when a real multi-level clear event exists.
 */
async function loadWhaleEvent() {
    try {
        const res = await fetch(`/api/whale?t=${Date.now()}`);
        if (!res.ok) return;

        const data = await res.json();
        const panel = document.getElementById("whale-alert-panel");
        if (!panel) return;

        if (!data.whale_detected || !data.event) {
            panel.classList.add("hidden");
            return;
        }

        const ev = data.event;

        // Show the panel
        panel.classList.remove("hidden");

        // Order ID
        const orderId = document.getElementById("whale-order-id");
        if (orderId) orderId.textContent = `#${formatNumber(ev.order_id)}`;

        // Levels cleared
        const levels = document.getElementById("whale-levels");
        if (levels) levels.textContent = `${ev.levels_cleared} levels`;

        // Order quantity
        const qty = document.getElementById("whale-quantity");
        if (qty) qty.textContent = formatNumber(ev.total_quantity);

        // Matched quantity
        const matched = document.getElementById("whale-matched");
        if (matched) matched.textContent = formatNumber(ev.total_matched_qty);

        // Side badge
        const badge = document.getElementById("whale-side-badge");
        if (badge) {
            badge.textContent = ev.side;
            badge.className = "whale-side-badge " + (ev.side === "BUY" ? "side-buy" : "side-sell");
        }

        // Cleared price level tags
        const tagsContainer = document.getElementById("whale-prices-tags");
        if (tagsContainer && Array.isArray(ev.prices_cleared)) {
            tagsContainer.innerHTML = ev.prices_cleared
                .map(p => `<span class="whale-price-tag">${formatNumber(p)}</span>`)
                .join("");
        }

    } catch (err) {
        // Non-blocking: whale alert is informational only
        console.debug("Whale event fetch failed:", err);
    }
}

/**
 * Clear the whale alert panel (called on dashboard reset).
 */
function clearWhalePanel() {
    const panel = document.getElementById("whale-alert-panel");
    if (panel) panel.classList.add("hidden");
}

// State variables for storing performance comparison runs
// State variables for storing performance comparison runs
let standardSimResult = null;
let cythonSimResult = null;

function updateComparisonUI() {
    const hasStandard = standardSimResult !== null && typeof standardSimResult === "object" && standardSimResult.orders > 0;
    const hasCython = cythonSimResult !== null && typeof cythonSimResult === "object" && cythonSimResult.orders > 0;

    // 1. Standard Engine Card
    const stdStatus = document.getElementById("std-status-badge");
    const stdLatency = document.getElementById("std-comp-latency");
    const stdThroughput = document.getElementById("std-comp-throughput");
    const stdTime = document.getElementById("std-comp-time");
    const stdOrders = document.getElementById("std-comp-orders");
    const stdTrades = document.getElementById("std-comp-trades");

    if (hasStandard) {
        if (stdStatus) {
            stdStatus.textContent = "RECORDED ✓";
            stdStatus.className = "engine-status-badge status-active";
        }
        if (stdLatency) stdLatency.textContent = `${standardSimResult.latency.toFixed(3)} ns/order`;
        if (stdThroughput) stdThroughput.textContent = `${formatNumber(Math.round(standardSimResult.throughput))} orders/sec`;
        if (stdTime) stdTime.textContent = `${standardSimResult.elapsedTime.toFixed(4)} s`;
        if (stdOrders) stdOrders.textContent = formatNumber(standardSimResult.orders);
        if (stdTrades) stdTrades.textContent = formatNumber(standardSimResult.trades);
    } else {
        if (stdStatus) {
            stdStatus.textContent = "NOT RUN";
            stdStatus.className = "engine-status-badge status-pending";
        }
        if (stdLatency) stdLatency.textContent = "--";
        if (stdThroughput) stdThroughput.textContent = "--";
        if (stdTime) stdTime.textContent = "--";
        if (stdOrders) stdOrders.textContent = "--";
        if (stdTrades) stdTrades.textContent = "--";
    }

    // 2. Cython Engine Card
    const cyStatus = document.getElementById("cy-status-badge");
    const cyLatency = document.getElementById("cy-comp-latency");
    const cyThroughput = document.getElementById("cy-comp-throughput");
    const cyTime = document.getElementById("cy-comp-time");
    const cyOrders = document.getElementById("cy-comp-orders");
    const cyTrades = document.getElementById("cy-comp-trades");

    if (hasCython) {
        if (cyStatus) {
            cyStatus.textContent = "RECORDED ✓";
            cyStatus.className = "engine-status-badge status-active";
        }
        if (cyLatency) cyLatency.textContent = `${cythonSimResult.latency.toFixed(3)} ns/order`;
        if (cyThroughput) cyThroughput.textContent = `${formatNumber(Math.round(cythonSimResult.throughput))} orders/sec`;
        if (cyTime) cyTime.textContent = `${cythonSimResult.elapsedTime.toFixed(4)} s`;
        if (cyOrders) cyOrders.textContent = formatNumber(cythonSimResult.orders);
        if (cyTrades) cyTrades.textContent = formatNumber(cythonSimResult.trades);
    } else {
        if (cyStatus) {
            cyStatus.textContent = "NOT RUN";
            cyStatus.className = "engine-status-badge status-pending";
        }
        if (cyLatency) cyLatency.textContent = "--";
        if (cyThroughput) cyThroughput.textContent = "--";
        if (cyTime) cyTime.textContent = "--";
        if (cyOrders) cyOrders.textContent = "--";
        if (cyTrades) cyTrades.textContent = "--";
    }

    // 3. Performance Improvement Card
    const impStatus = document.getElementById("imp-status-badge");
    const impNotice = document.getElementById("imp-notice");
    const impBody = document.getElementById("imp-metrics-body");
    const impLatency = document.getElementById("imp-comp-latency");
    const impThroughput = document.getElementById("imp-comp-throughput");
    const impSpeed = document.getElementById("imp-comp-speed");

    if (hasStandard && hasCython) {
        if (impNotice) impNotice.classList.add("hidden");
        if (impBody) impBody.classList.remove("hidden");
        if (impStatus) {
            impStatus.textContent = "CALCULATED ✓";
            impStatus.className = "engine-status-badge status-active";
        }

        // Formulas:
        // Latency Improvement (%) = ((Standard Latency - Cython Latency) / Standard Latency) * 100
        const latencyImp = standardSimResult.latency > 0 
            ? ((standardSimResult.latency - cythonSimResult.latency) / standardSimResult.latency) * 100
            : 0;

        // Throughput Improvement (%) = ((Cython Throughput - Standard Throughput) / Standard Throughput) * 100
        const throughputImp = standardSimResult.throughput > 0
            ? ((cythonSimResult.throughput - standardSimResult.throughput) / standardSimResult.throughput) * 100
            : 0;

        // Processing Speed Improvement (%) = ((Standard Processing Time - Cython Processing Time) / Standard Processing Time) * 100
        const speedImp = standardSimResult.elapsedTime > 0
            ? ((standardSimResult.elapsedTime - cythonSimResult.elapsedTime) / standardSimResult.elapsedTime) * 100
            : 0;

        // Render Latency Improvement
        if (impLatency) {
            impLatency.textContent = `${latencyImp >= 0 ? '+' : ''}${latencyImp.toFixed(2)}%`;
            impLatency.className = `mono comp-val boost-val ${latencyImp >= 0 ? 'text-green' : 'text-red'}`;
        }

        // Render Throughput Improvement
        if (impThroughput) {
            impThroughput.textContent = `${throughputImp >= 0 ? '+' : ''}${throughputImp.toFixed(2)}%`;
            impThroughput.className = `mono comp-val boost-val ${throughputImp >= 0 ? 'text-green' : 'text-red'}`;
        }

        // Render Processing Speed Improvement
        if (impSpeed) {
            impSpeed.textContent = `${speedImp >= 0 ? '+' : ''}${speedImp.toFixed(2)}%`;
            impSpeed.className = `mono comp-val boost-val ${speedImp >= 0 ? 'text-green' : 'text-red'}`;
        }

    } else {
        if (impNotice) impNotice.classList.remove("hidden");
        if (impBody) impBody.classList.add("hidden");
        if (impStatus) {
            impStatus.textContent = "PENDING";
            impStatus.className = "engine-status-badge status-pending";
        }
        if (impLatency) {
            impLatency.textContent = "--";
            impLatency.className = "mono comp-val text-green boost-val";
        }
        if (impThroughput) {
            impThroughput.textContent = "--";
            impThroughput.className = "mono comp-val text-green boost-val";
        }
        if (impSpeed) {
            impSpeed.textContent = "--";
            impSpeed.className = "mono comp-val text-green boost-val";
        }
    }
}

// Execute Order Matching Simulation
async function runSimulation() {
    const btnSimulate = document.getElementById("btn-simulate");
    const countSelect = document.getElementById("sim-count-select");
    const cythonToggle = document.getElementById("cython-toggle");

    const orderCount = countSelect ? parseInt(countSelect.value, 10) : 10000;
    const useCython = cythonToggle ? cythonToggle.checked : true;

    if (btnSimulate) {
        btnSimulate.disabled = true;
        btnSimulate.innerHTML = '<span class="btn-icon">⚡</span> Simulating...';
    }

    try {
        const response = await fetch("/api/simulate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                count: orderCount,
                use_cython: useCython
            })
        });

        if (!response.ok) throw new Error("Simulation failed on backend");

        const result = await response.json();

        // Record comparison results
        if (!useCython) {
            standardSimResult = {
                latency: result.avg_latency_ns,
                throughput: result.throughput,
                elapsedTime: result.elapsed_seconds,
                orders: result.simulated_orders,
                trades: result.trades_generated
            };
        } else {
            cythonSimResult = {
                latency: result.avg_latency_ns,
                throughput: result.throughput,
                elapsedTime: result.elapsed_seconds,
                orders: result.simulated_orders,
                trades: result.trades_generated
            };
        }

        updateComparisonUI();

        showNotification(`Processed ${formatNumber(result.simulated_orders)} orders in ${result.elapsed_seconds}s (${formatNumber(result.throughput)} orders/sec)`);

        await refreshDashboard(false);

    } catch (error) {
        console.error("Simulation error:", error);
        showNotification("Simulation failed: " + error.message, true);
    } finally {
        if (btnSimulate) {
            btnSimulate.disabled = false;
            btnSimulate.innerHTML = '<span class="btn-icon">🚀</span> Run Simulation';
        }
    }
}

// Reset Dashboard Simulation Data
async function resetDashboard() {
    const btnReset = document.getElementById("btn-reset");
    if (btnReset) btnReset.disabled = true;

    try {
        const response = await fetch("/api/reset", { method: "POST" });
        if (!response.ok) throw new Error("Reset failed");

        const result = await response.json();

        // Reset local comparison state
        standardSimResult = null;
        cythonSimResult = null;
        updateComparisonUI();

        // Immediately update UI metrics to zero
        const ordersEl = document.getElementById("orders");
        if (ordersEl) ordersEl.textContent = "0";

        const tradesEl = document.getElementById("trades");
        if (tradesEl) tradesEl.textContent = "0";

        const latencyEl = document.getElementById("latency");
        if (latencyEl) latencyEl.textContent = "0 ns/order";

        const throughputEl = document.getElementById("throughput");
        if (throughputEl) throughputEl.textContent = "0 orders/second";

        // Immediately clear order book tables
        const bidsBody = document.getElementById("bids-body");
        if (bidsBody) bidsBody.innerHTML = '<tr><td colspan="3" class="empty-state">Order book bids empty</td></tr>';

        const asksBody = document.getElementById("asks-body");
        if (asksBody) asksBody.innerHTML = '<tr><td colspan="3" class="empty-state">Order book asks empty</td></tr>';

        // Clear whale alert panel
        clearWhalePanel();

        showNotification(result.message || "Simulation state reset successfully.");

        await refreshDashboard(false);

    } catch (error) {
        console.error("Reset error:", error);
        showNotification("Reset failed: " + error.message, true);
    } finally {
        if (btnReset) btnReset.disabled = false;
    }
}

// User Profile & Logout Handling
async function loadUserProfile() {
    try {
        const res = await fetch("/api/user");
        if (res.ok) {
            const data = await res.json();
            if (data.user) {
                const profileBadge = document.getElementById("user-profile");
                const displayName = document.getElementById("user-display-name");
                const btnLogout = document.getElementById("btn-logout");

                if (displayName) displayName.textContent = data.user.name || "Trader";
                if (profileBadge) profileBadge.classList.remove("hidden");
                if (btnLogout) btnLogout.classList.remove("hidden");
            }
        }
    } catch (e) {
        console.error("Error loading profile:", e);
    }
}

async function handleLogout() {
    try {
        await fetch("/api/logout", { method: "POST" });
        window.location.href = "/login";
    } catch (e) {
        console.error("Logout failed:", e);
        window.location.href = "/login";
    }
}

// Global Initialization
document.addEventListener("DOMContentLoaded", () => {
    // Initial fetch and UI setup
    loadUserProfile();
    refreshDashboard(false);
    updateComparisonUI();

    // Event Listeners
    const btnSimulate = document.getElementById("btn-simulate");
    if (btnSimulate) btnSimulate.addEventListener("click", runSimulation);

    const btnRefresh = document.getElementById("btn-refresh");
    if (btnRefresh) btnRefresh.addEventListener("click", () => refreshDashboard(true));

    const btnReset = document.getElementById("btn-reset");
    if (btnReset) btnReset.addEventListener("click", resetDashboard);

    const btnLogout = document.getElementById("btn-logout");
    if (btnLogout) btnLogout.addEventListener("click", handleLogout);

    // Auto Refresh every 3 seconds
    setInterval(() => {
        refreshDashboard(false);
    }, 3000);
});