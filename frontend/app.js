const DEFAULT_API_BASE = "http://127.0.0.1:8000";
const accounts = {
  farmer: "farmer@agriplace.demo",
  buyer: "buyer@agriplace.demo",
  transporter: "transporter@agriplace.demo",
  admin: "admin@agriplace.demo",
};

const state = {
  apiBase: localStorage.getItem("agriplace-api-base") || DEFAULT_API_BASE,
  role: "farmer",
  lang: "hi",
  token: null,
  user: null,
};

const app = document.querySelector("#app");
const connectionStatus = document.querySelector("#connectionStatus");
const apiDialog = document.querySelector("#apiDialog");
const apiBaseInput = document.querySelector("#apiBaseInput");

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", "\"": "&quot;",
  }[char]));
}

function money(value) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value || 0);
}

function number(value) {
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 1 }).format(value || 0);
}

function datePlus(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

function titleCase(value) {
  return String(value || "").toLowerCase().replace(/(^|_)([a-z])/g, (_, prefix, letter) => `${prefix ? " " : ""}${letter.toUpperCase()}`);
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`${state.apiBase}${path}`, { ...options, headers });
  const payload = await response.json().catch(() => null);
  if (!response.ok || !payload?.success) throw new Error(payload?.error || `Request failed (${response.status})`);
  return payload.data;
}

function toast(message, type = "success") {
  const item = document.createElement("div");
  item.className = `toast ${type === "error" ? "error" : ""}`;
  item.textContent = message;
  document.querySelector("#toastRegion").append(item);
  window.setTimeout(() => item.remove(), 4200);
}

function setConnection(online, label) {
  connectionStatus.className = `connection ${online ? "online" : "offline"}`;
  connectionStatus.innerHTML = `<b></b>${escapeHtml(label)}`;
}

function setLoading(label = "Loading farm trade workspace") {
  app.innerHTML = `<section class="loading-screen"><div class="loading-mark"><span></span><span></span><span></span></div><p>${escapeHtml(label)}</p></section>`;
}

function errorPanel(error) {
  app.innerHTML = `<section class="panel" style="max-width:620px;margin:10vh auto"><span class="status alert">Connection needed</span><h1 class="page-title" style="margin-top:14px">AgriPlace could not reach its local API.</h1><p class="page-subtitle">${escapeHtml(error.message)}</p><div style="margin-top:18px"><button class="primary-button" id="retryConnection" type="button">Retry connection</button></div></section>`;
  document.querySelector("#retryConnection").addEventListener("click", boot);
}

function activateRoleTab() {
  document.querySelectorAll(".role-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.role === state.role);
  });
}

async function loginForRole(role) {
  const data = await api("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email: accounts[role], password: "AgriPlace@123" }),
  });
  state.token = data.access_token;
  state.user = data.user;
}

async function renderCurrentRole() {
  activateRoleTab();
  setLoading(`Loading ${state.role} workspace`);
  try {
    if (!state.token) await loginForRole(state.role);
    if (state.role === "farmer") return renderFarmer();
    if (state.role === "buyer") return renderBuyer();
    if (state.role === "transporter") return renderTransporter();
    return renderAdmin();
  } catch (error) {
    setConnection(false, "API unavailable");
    errorPanel(error);
  }
}

async function switchRole(role) {
  if (state.role === role && state.token) return renderCurrentRole();
  state.role = role;
  state.token = null;
  state.user = null;
  return renderCurrentRole();
}

function pageHeader(title, subtitle, tools = "") {
  return `<header class="page-header"><div><h1 class="page-title">${title}</h1><p class="page-subtitle">${subtitle}</p></div><div class="header-tools">${tools}</div></header>`;
}

function kpi(label, value, meta, variant = "") {
  return `<article class="kpi ${variant}"><span class="kpi-label">${escapeHtml(label)}</span><strong class="kpi-value">${value}</strong><span class="kpi-meta">${escapeHtml(meta)}</span></article>`;
}

function listingRow(listing, showFarmer = false) {
  const farmer = showFarmer ? `<p class="listing-detail">${escapeHtml(listing.farmer.name)} · ${escapeHtml(listing.location.district)}</p>` : `<p class="listing-detail">${number(listing.quantity_kg)} kg · ${escapeHtml(listing.grade)}</p>`;
  return `<article class="listing-card"><div class="produce-visual" aria-hidden="true"></div><div><h3 class="listing-title">${escapeHtml(listing.crop.name)} <span class="status">${escapeHtml(listing.grade)}</span></h3>${farmer}</div><div class="listing-price">${money(listing.expected_price_per_kg)}<small>per kg</small></div></article>`;
}

function orderRow(order) {
  const payment = order.payment || {};
  return `<article class="listing-card"><div class="produce-visual" aria-hidden="true"></div><div><h3 class="listing-title">${escapeHtml(order.order_number)} <span class="status hold">${escapeHtml(payment.status || order.payment_status)}</span></h3><p class="listing-detail">${number(order.total_quantity_kg)} kg tomato · ${order.items.length} seller${order.items.length === 1 ? "" : "s"}</p></div><div class="listing-price">${money(order.total_value)}<small>protected value</small></div></article>`;
}

async function renderFarmer() {
  const home = await api(`/farmer/home?lang=${state.lang}`);
  const firstOrder = home.orders[0];
  const firstListing = home.active_listings[0];
  const market = home.market_price;
  const held = firstOrder?.payment?.held_amount || 0;
  const paymentLabel = state.lang === "hi" ? "सुरक्षित भुगतान" : "Payment protection";
  app.innerHTML = `${pageHeader(
    escapeHtml(home.text.greeting),
    state.lang === "hi" ? "अपने खेत से सीधे खरीदार तक" : "Move your crop directly from farm to buyer.",
    `<div class="segmented" aria-label="Language"><button data-lang="hi" class="${state.lang === "hi" ? "active" : ""}" type="button">हिंदी</button><button data-lang="en" class="${state.lang === "en" ? "active" : ""}" type="button">EN</button></div><button class="primary-button" id="scrollToSell" type="button">${escapeHtml(home.text.sell_button)}</button>`,
  )}
  <section class="kpi-grid">
    ${kpi(home.text.market_label, `${money(market.range_per_kg[0])}-${money(market.range_per_kg[1])}`, "Nashik mandi · daily sample", "saffron")}
    ${kpi(home.text.earning_label, money(home.expected_earnings), `${home.active_listings.length} active crop lot${home.active_listings.length === 1 ? "" : "s"}`)}
    ${kpi(paymentLabel, money(held), firstOrder ? `${firstOrder.order_number} is held` : "No protected order", "sky")}
    ${kpi(state.lang === "hi" ? "अगली पिकअप" : "Next pickup", firstListing ? firstListing.available_date.slice(5) : "-", firstListing ? `${number(firstListing.quantity_kg)} kg ${firstListing.crop.name}` : "Publish a crop lot", "tomato")}
  </section>
  <section class="dashboard-grid">
    <div class="stack">
      <article class="panel">
        <div class="panel-header"><div><h2>${escapeHtml(home.text.market_label)}</h2><p class="panel-note">Nashik, Maharashtra</p></div><span class="data-tag">SYNTHETIC SAMPLE</span></div>
        <div class="price-summary"><div><span class="kpi-label">Modal range</span><div class="price-amount">${money(market.range_per_kg[0])} - ${money(market.range_per_kg[1])}<small>/ kg</small></div><p class="panel-note">Grade and arrival-adjusted estimate</p></div><div class="price-bars" aria-label="Five day price signal"><span></span><span></span><span></span><span></span><span></span></div></div>
        <div class="breakdown"><div class="breakdown-row"><span>Recent modal price</span><strong>${money(25.8)} / kg</strong></div><div class="breakdown-row"><span>Grade A adjustment</span><strong>+${money(1.55)} / kg</strong></div><div class="breakdown-row total"><span>Suggested list price</span><strong>${money(27.35)} / kg</strong></div></div>
      </article>
      <article class="panel" id="sellPanel">
        <div class="panel-header"><div><h2>${escapeHtml(home.text.sell_button)}</h2><p class="panel-note">Tomato lot with transparent sale estimate</p></div><span class="data-tag">FARMER FLOW</span></div>
        <form id="listingForm" class="form-grid">
          <div class="field"><label for="listingQty">Quantity (kg)</label><input id="listingQty" min="1" value="500" type="number" required /></div>
          <div class="field"><label for="listingGrade">Quality</label><select id="listingGrade"><option value="Grade A">Grade A</option><option value="Grade B">Grade B</option><option value="Grade C">Grade C</option></select></div>
          <div class="field"><label for="listingDate">Available on</label><input id="listingDate" value="${datePlus(1)}" type="date" required /></div>
          <button class="primary-button form-action" type="submit">Get estimate</button>
        </form>
        <div class="estimate-line" id="saleEstimate"><span>Enter a quantity to calculate a price range.</span><strong>Voice capture ready</strong></div>
      </article>
      <article class="panel"><div class="panel-header"><div><h2>My crop lots</h2><p class="panel-note">Available quantities and published prices</p></div></div><div class="listings">${home.active_listings.length ? home.active_listings.map((listing) => listingRow(listing)).join("") : `<div class="empty">No crop lots yet.</div>`}</div></article>
    </div>
    <div class="stack">
      <article class="panel"><div class="panel-header"><div><h2>Protected sale</h2><p class="panel-note">Release follows buyer confirmation</p></div></div>${firstOrder ? `${orderRow(firstOrder)}<div class="breakdown" style="margin-top:14px"><div class="breakdown-row"><span>Payment held</span><strong>${money(firstOrder.payment.held_amount)}</strong></div><div class="breakdown-row"><span>Release trigger</span><strong>Delivery proof</strong></div></div>` : `<div class="empty">Your next confirmed sale will appear here.</div>`}</article>
      <article class="panel"><div class="panel-header"><div><h2>Price and crop alerts</h2><p class="panel-note">Actionable signals, not guarantees</p></div></div><div class="alert-list">${home.alerts.length ? home.alerts.map((alert) => `<article class="alert-item ${alert.severity === "critical" ? "red" : ""}"><h3 class="alert-title">${escapeHtml(alert.title)}</h3><p class="alert-text">${escapeHtml(alert.message)}</p></article>`).join("") : `<div class="empty">No alerts right now.</div>`}</div></article>
    </div>
  </section>`;

  document.querySelectorAll("[data-lang]").forEach((button) => button.addEventListener("click", () => {
    state.lang = button.dataset.lang;
    renderCurrentRole();
  }));
  document.querySelector("#scrollToSell").addEventListener("click", () => document.querySelector("#sellPanel").scrollIntoView({ behavior: "smooth", block: "start" }));
  document.querySelector("#listingForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const estimateLine = document.querySelector("#saleEstimate");
    estimateLine.innerHTML = "<span>Calculating current estimate...</span>";
    try {
      const quantity = Number(document.querySelector("#listingQty").value);
      const estimate = await api("/farmer/sale-estimate", { method: "POST", body: JSON.stringify({ crop: "Tomato", quantity_kg: quantity, grade: document.querySelector("#listingGrade").value, available_date: document.querySelector("#listingDate").value }) });
      estimateLine.innerHTML = `<span>Expected farmer realization: <strong>${money(estimate.estimated_net)}</strong></span><strong>${money(estimate.recommended_listing_price_per_kg)} / kg</strong>`;
      toast("Sale estimate is ready.");
    } catch (error) { estimateLine.innerHTML = `<span>${escapeHtml(error.message)}</span>`; toast(error.message, "error"); }
  });
}

async function renderBuyer() {
  const [marketplace, orders, requirements] = await Promise.all([api("/buyer/marketplace"), api("/buyer/orders"), api("/buyer/requirements")]);
  app.innerHTML = `${pageHeader("Buyer marketplace", "Source verified crop lots, then aggregate the right quantity.", `<button class="primary-button" id="openRequirement" type="button">Create requirement</button>`)}
  <section class="kpi-grid">
    ${kpi("Verified crop lots", String(marketplace.listings.length), "Farmer and FPO supplied")}
    ${kpi("Protected orders", String(orders.length), orders[0]?.payment?.status === "HELD" ? "Funds held for confirmation" : "Payment status tracked", "sky")}
    ${kpi("Open requirements", String(requirements.filter((item) => item.status !== "ORDERED").length), "Matching is explainable", "saffron")}
    ${kpi("Current order", orders[0] ? number(orders[0].total_quantity_kg) + " kg" : "-", orders[0] ? orders[0].order_number : "No active order", "tomato")}
  </section>
  <section class="marketplace">
    <aside class="panel filter-panel"><div class="panel-header"><div><h2>Find produce</h2><p class="panel-note">Filter live listings</p></div></div><div class="filter-list"><label>Crop<select id="cropFilter"><option value="all">All crops</option><option value="tomato">Tomato</option></select></label><label>Quality<select id="gradeFilter"><option value="all">All grades</option><option value="Grade A">Grade A</option><option value="Grade B">Grade B</option></select></label><label>Minimum quantity<input id="qtyFilter" type="number" min="0" placeholder="kg" /></label></div></aside>
    <div class="stack"><article class="panel"><div class="panel-header"><div><h2>Available lots</h2><p class="panel-note">Price, quality, location and seller trust are visible before matching.</p></div><span class="data-tag">MARKETPLACE</span></div><div class="market-cards" id="marketCards">${marketplace.listings.map(marketCard).join("")}</div></article>
    <article class="panel"><div class="panel-header"><div><h2>Protected orders</h2><p class="panel-note">Funds move only after delivery proof.</p></div></div><div class="listings">${orders.length ? orders.map(orderRow).join("") : `<div class="empty">No protected orders.</div>`}</div></article></div>
  </section>
  <section class="panel" id="requirementPanel" style="margin-top:18px" hidden><div class="panel-header"><div><h2>New tomato requirement</h2><p class="panel-note">Set the quantity, deadline and maximum price.</p></div></div><form id="requirementForm" class="form-grid"><div class="field"><label>Quantity (kg)<input id="requirementQty" type="number" min="100" value="1000" required /></label></div><div class="field"><label>Quality<select id="requirementGrade"><option value="Grade A">Grade A</option><option value="Grade B">Grade B</option></select></label></div><div class="field"><label>Needed by<input id="neededBy" type="date" value="${datePlus(3)}" required /></label></div><div class="field"><label>Maximum price / kg<input id="maxPrice" type="number" min="1" value="30" required /></label></div><button class="primary-button form-action" type="submit">Find matches</button></form><div class="estimate-line" id="matchResult"><span>Match results will explain price, distance, quality, timing and reliability.</span></div></section>`;

  document.querySelector("#openRequirement").addEventListener("click", () => { const panel = document.querySelector("#requirementPanel"); panel.hidden = false; panel.scrollIntoView({ behavior: "smooth", block: "start" }); });
  document.querySelector("#requirementForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const result = document.querySelector("#matchResult");
    result.innerHTML = "<span>Comparing availability, quality, distance, price and reliability...</span>";
    try {
      const response = await api("/buyer/requirements", { method: "POST", body: JSON.stringify({ crop: "Tomato", required_quantity_kg: Number(document.querySelector("#requirementQty").value), grade: document.querySelector("#requirementGrade").value, needed_by: document.querySelector("#neededBy").value, max_price_per_kg: Number(document.querySelector("#maxPrice").value) }) });
      const total = response.matches.matched_quantity_kg || 0;
      const matchedSellerCount = response.matches.matches?.length || 0;
      result.innerHTML = `<span>${number(total)} kg selected across ${matchedSellerCount} seller${matchedSellerCount === 1 ? "" : "s"}.</span><strong>${response.matches.is_fully_matched ? "Fulfillable" : "More supply needed"}</strong>`;
      toast("Matching result updated.");
    } catch (error) { result.innerHTML = `<span>${escapeHtml(error.message)}</span>`; toast(error.message, "error"); }
  });
  const filter = () => {
    const crop = document.querySelector("#cropFilter").value;
    const grade = document.querySelector("#gradeFilter").value;
    const qty = Number(document.querySelector("#qtyFilter").value || 0);
    const filtered = marketplace.listings.filter((listing) => (crop === "all" || listing.crop.name.toLowerCase() === crop) && (grade === "all" || listing.grade === grade) && listing.quantity_kg >= qty);
    document.querySelector("#marketCards").innerHTML = filtered.length ? filtered.map(marketCard).join("") : `<div class="empty">No crop lots match these filters.</div>`;
  };
  ["#cropFilter", "#gradeFilter", "#qtyFilter"].forEach((selector) => document.querySelector(selector).addEventListener("input", filter));
}

function marketCard(listing) {
  return `<article class="market-card"><div class="produce-visual" aria-hidden="true"></div><div class="market-card-info"><h3>${escapeHtml(listing.crop.name)} <span class="status">${escapeHtml(listing.grade)}</span></h3><p>${escapeHtml(listing.farmer.name)} · ${escapeHtml(listing.location.district)}</p><p>${number(listing.quantity_kg)} kg · Available ${escapeHtml(listing.available_date.slice(5))}</p><div class="market-card-footer"><strong>${money(listing.expected_price_per_kg)} / kg</strong><span class="status ${listing.status === "AVAILABLE" ? "" : "hold"}">${escapeHtml(titleCase(listing.status))}</span></div></div></article>`;
}

function routeMap(route, fallbackStops = []) {
  const stops = route?.routes?.flatMap((item) => item.stops || []) || fallbackStops.map((stop) => ({ ...stop, label: stop.location.label, latitude: stop.location.latitude, longitude: stop.location.longitude }));
  if (!stops.length) return `<div class="empty">A route will appear when the transporter accepts a trip.</div>`;
  const lats = stops.map((stop) => stop.latitude); const lons = stops.map((stop) => stop.longitude);
  const minLat = Math.min(...lats); const maxLat = Math.max(...lats); const minLon = Math.min(...lons); const maxLon = Math.max(...lons);
  const point = (stop) => ({ x: 12 + ((stop.longitude - minLon) / (maxLon - minLon || 1)) * 76, y: 14 + (1 - ((stop.latitude - minLat) / (maxLat - minLat || 1))) * 68 });
  const points = stops.map(point);
  const lines = points.slice(0, -1).map((start, index) => {
    const end = points[index + 1]; const dx = end.x - start.x; const dy = end.y - start.y; const length = Math.sqrt(dx ** 2 + dy ** 2); const angle = Math.atan2(dy, dx) * 180 / Math.PI;
    return `<i class="route-line" style="left:${start.x}%;top:${start.y}%;width:${length}%;transform:rotate(${angle}deg)"></i>`;
  }).join("");
  const markers = stops.map((stop, index) => `<i class="route-stop ${String(stop.stop_type || "").toLowerCase()}" style="left:${points[index].x}%;top:${points[index].y}%"></i><span class="route-label" style="left:${points[index].x}%;top:${points[index].y}%">${escapeHtml(stop.label)}</span>`).join("");
  return `<div class="route-map">${lines}${markers}</div><div class="route-legend"><span><i class="depot"></i> Depot</span><span><i></i> Pickup</span><span><i class="buyer"></i> Buyer</span><span>Derived coordinates</span></div>`;
}

async function renderTransporter() {
  const [active, available] = await Promise.all([api("/transporter/active"), api("/transporter/trips/available")]);
  const delivery = active || available[0] || null;
  const route = delivery?.route;
  app.innerHTML = `${pageHeader("Transporter control", "Pool pickups, confirm proof, and keep every movement traceable.", `<button class="secondary-button" id="refreshTrips" type="button">Refresh trips</button>`)}
  <section class="kpi-grid">
    ${kpi("Available trips", String(available.length), "Pooled route requests", "saffron")}
    ${kpi("Current cargo", delivery ? `${number(delivery.cargo_kg)} kg` : "0 kg", delivery ? titleCase(delivery.status) : "No active trip")}
    ${kpi("Route distance", delivery?.estimated_distance_km ? `${number(delivery.estimated_distance_km)} km` : "Pending", "Optimized with OR-Tools", "sky")}
    ${kpi("Estimated earning", delivery?.estimated_earnings ? money(delivery.estimated_earnings) : "Pending", "Distance-based prototype", "tomato")}
  </section>
  <section class="dashboard-grid"><div class="stack"><article class="panel"><div class="panel-header"><div><h2>Route plan</h2><p class="panel-note">Nashik pickup cluster to Mumbai buyer warehouse</p></div><span class="data-tag">DERIVED ROUTE</span></div>${routeMap(route, delivery?.stops || [])}${delivery?.route ? `<div class="route-metrics"><div><span>Original</span><strong>${number(route.original_distance_km)} km</strong></div><div><span>Optimized</span><strong>${number(route.optimized_distance_km)} km</strong></div><div><span>Saved</span><strong>${number(route.saved_distance_km)} km</strong></div></div>` : ""}</article>
  <article class="panel"><div class="panel-header"><div><h2>Pickup confirmation</h2><p class="panel-note">Quantity, grade and proof are part of the delivery record.</p></div></div>${delivery ? `<div class="trip-list">${delivery.stops.filter((stop) => stop.type === "PICKUP").map((stop) => `<article class="trip-row"><div><h3>${escapeHtml(stop.location.label)}</h3><p>${number(stop.planned_quantity_kg)} kg planned · ${escapeHtml(stop.status)}</p></div><button class="secondary-button pickup-button" data-stop="${stop.id}" data-qty="${stop.planned_quantity_kg}" ${delivery.status === "REQUESTED" ? "disabled" : ""} type="button">Confirm pickup</button></article>`).join("")}</div>` : `<div class="empty">Accept a trip to begin pickup confirmation.</div>`}</article></div>
  <div class="stack"><article class="panel"><div class="panel-header"><div><h2>Trip requests</h2><p class="panel-note">Only eligible transporter accounts can accept.</p></div></div><div class="trip-list">${available.length ? available.map((trip) => `<article class="trip-row"><div><h3>${escapeHtml(trip.order_number)}</h3><p>${number(trip.cargo_kg)} kg · ${trip.stops.length - 1} pickup stops</p></div><button class="primary-button accept-trip" data-delivery="${trip.id}" type="button">Accept trip</button></article>`).join("") : `<div class="empty">No unassigned trips.</div>`}</div></article>
  <article class="panel"><div class="panel-header"><div><h2>Proof trail</h2><p class="panel-note">Pickup and delivery records support protected payment release.</p></div></div><div class="breakdown"><div class="breakdown-row"><span>Pickup evidence</span><strong>${delivery?.status === "REQUESTED" ? "Awaiting acceptance" : "Required"}</strong></div><div class="breakdown-row"><span>Incident route</span><strong>Available</strong></div><div class="breakdown-row"><span>Buyer confirmation</span><strong>Release trigger</strong></div></div></article></div></section>`;
  document.querySelector("#refreshTrips").addEventListener("click", renderCurrentRole);
  document.querySelectorAll(".accept-trip").forEach((button) => button.addEventListener("click", async () => {
    try { await api(`/transporter/trips/${button.dataset.delivery}/accept`, { method: "POST", body: "{}" }); toast("Trip accepted and route optimized."); renderCurrentRole(); } catch (error) { toast(error.message, "error"); }
  }));
  document.querySelectorAll(".pickup-button").forEach((button) => button.addEventListener("click", async () => {
    if (!delivery) return;
    try { await api(`/transporter/deliveries/${delivery.id}/pickup`, { method: "POST", body: JSON.stringify({ stop_id: button.dataset.stop, actual_quantity_kg: Number(button.dataset.qty), grade: "Grade A", notes: "Demo pickup confirmation" }) }); toast("Pickup evidence recorded."); renderCurrentRole(); } catch (error) { toast(error.message, "error"); }
  }));
}

async function renderAdmin() {
  const [dashboard, weights, audit] = await Promise.all([api("/admin/dashboard"), api("/admin/matching-weights"), api("/admin/audit-logs")]);
  const kpis = dashboard.kpis;
  const priceRange = dashboard.ai_dashboard.price_forecast.predicted_range_per_kg || { min: 0, max: 0 };
  const priceForecast = (Number(priceRange.min) + Number(priceRange.max)) / 2;
  const demandLevel = dashboard.ai_dashboard.demand_forecast.demand_level || "UNKNOWN";
  app.innerHTML = `${pageHeader("Admin oversight", "Monitor trade health, matching fairness, routing, and exceptions.", `<button class="primary-button" id="saveWeights" type="button">Save matching weights</button>`)}
  <section class="kpi-grid">${kpi("Farmers", String(kpis.total_farmers), "Registered accounts")}${kpi("Active orders", String(kpis.active_orders), `${number(kpis.total_produce_kg)} kg in system`, "saffron")}${kpi("Transaction value", money(kpis.total_transaction_value), "Prototype order value", "sky")}${kpi("Route saving", `${number(kpis.route_savings_km)} km`, "Optimized pooled route", "tomato")}</section>
  <section class="dashboard-grid"><div class="stack"><article class="panel"><div class="panel-header"><div><h2>Explainable matching weights</h2><p class="panel-note">Every buyer-seller recommendation shows its score components.</p></div><span class="data-tag">ADMIN CONTROL</span></div><div class="weight-list" id="weightList">${Object.entries(weights).map(([key, value]) => `<label class="weight-row"><span>${escapeHtml(titleCase(key))}</span><input data-weight="${key}" min="0" max="100" value="${Math.round(value * 100)}" type="range" /><output>${Math.round(value * 100)}%</output></label>`).join("")}</div></article>
  <article class="panel"><div class="panel-header"><div><h2>AI signals</h2><p class="panel-note">Forecasts guide, but do not automatically decide trade outcomes.</p></div></div><div class="admin-kpis"><div class="admin-kpi"><span>Price forecast</span><strong>${money(priceForecast)} / kg</strong></div><div class="admin-kpi"><span>Demand signal</span><strong>${escapeHtml(demandLevel)}</strong></div><div class="admin-kpi"><span>Glut alerts</span><strong>${dashboard.ai_dashboard.glut_alerts.length}</strong></div></div></article></div>
  <div class="stack"><article class="panel"><div class="panel-header"><div><h2>System health</h2><p class="panel-note">Service-level status for the prototype.</p></div></div><div class="breakdown">${Object.entries(dashboard.system_health).map(([key, value]) => `<div class="breakdown-row"><span>${escapeHtml(titleCase(key))}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}</div></article>
  <article class="panel"><div class="panel-header"><div><h2>Audit trail</h2><p class="panel-note">Recent protected actions</p></div></div><div class="audit-list">${audit.slice(0, 7).map((entry) => `<article class="audit-row"><div><strong>${escapeHtml(entry.action)}</strong><p>${escapeHtml(entry.entity_type)} · ${escapeHtml(entry.entity_id || "system")}</p></div><time>${escapeHtml(new Date(entry.created_at).toLocaleString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }))}</time></article>`).join("") || `<div class="empty">No audit events yet.</div>`}</div></article></div></section>`;
  document.querySelectorAll("[data-weight]").forEach((input) => input.addEventListener("input", () => { input.parentElement.querySelector("output").value = `${input.value}%`; }));
  document.querySelector("#saveWeights").addEventListener("click", async () => {
    const values = Object.fromEntries([...document.querySelectorAll("[data-weight]")].map((input) => [input.dataset.weight, Number(input.value)]));
    try { await api("/admin/matching-weights", { method: "POST", body: JSON.stringify(values) }); toast("Matching weights updated."); renderCurrentRole(); } catch (error) { toast(error.message, "error"); }
  });
}

async function boot() {
  setLoading("Checking AgriPlace API");
  try {
    await api("/health");
    setConnection(true, "API connected");
    await switchRole(state.role);
  } catch (error) {
    setConnection(false, "API unavailable");
    errorPanel(error);
  }
}

document.querySelectorAll(".role-tab").forEach((button) => button.addEventListener("click", () => switchRole(button.dataset.role)));
document.querySelector("#refreshData").addEventListener("click", renderCurrentRole);
document.querySelector("#apiSettings").addEventListener("click", () => { apiBaseInput.value = state.apiBase; apiDialog.showModal(); });
document.querySelector("#apiForm").addEventListener("submit", (event) => {
  if (event.submitter?.value !== "default") return;
  const value = apiBaseInput.value.trim().replace(/\/$/, "");
  state.apiBase = value;
  state.token = null;
  localStorage.setItem("agriplace-api-base", value);
  window.setTimeout(boot, 0);
});
document.querySelector("#userMenu").addEventListener("click", () => toast(state.user ? `Signed in as ${state.user.name}.` : "Demo account is selected by workspace."));

boot();
