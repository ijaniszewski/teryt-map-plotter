const state = {
  map: null,
  layer: null,
  datasets: [],
  profile: null,
  pendingUploadId: null,
  source: "built-in",
  range: null,
  legend: null,
};

const sequentialColors = ["#f2e8c9", "#d7d98d", "#86b66b", "#2f8664", "#143f3a"];
const candidateColors = ["#2f80ed", "#eb5757"];
const defaultState = {
  source: "built-in",
  level: "powiaty",
  dataset: "built-in:poland/2025/presidential_elections/second_round/wyniki_gl_na_kandydatow_po_gminach_w_drugiej_turze_utf8.csv",
  mode: "winner_colors",
  metric: "turnout",
  a: "NAWROCKI Karol Tadeusz",
  b: "TRZASKOWSKI Rafał Kazimierz",
};

const els = {
  level: document.querySelector("#level"),
  sourceButtons: document.querySelectorAll("[data-source]"),
  builtInControls: document.querySelector("#built-in-controls"),
  uploadControls: document.querySelector("#upload-controls"),
  country: document.querySelector("#country"),
  year: document.querySelector("#year"),
  election: document.querySelector("#election"),
  round: document.querySelector("#round"),
  uploadedDataset: document.querySelector("#uploaded-dataset"),
  uploadedDatasetControl: document.querySelector("#uploaded-dataset-control"),
  strategyControl: document.querySelector("#strategy-control"),
  strategy: document.querySelector("#strategy"),
  valueMetric: document.querySelector("#value-metric"),
  valueMetricControl: document.querySelector("#value-metric-control"),
  candidateA: document.querySelector("#candidate-a"),
  candidateB: document.querySelector("#candidate-b"),
  headToHeadControl: document.querySelector("#head-to-head-control"),
  upload: document.querySelector("#upload"),
  dropZone: document.querySelector("#drop-zone"),
  legend: document.querySelector("#legend"),
  toast: document.querySelector("#toast"),
  statCount: document.querySelector("#stat-count"),
  statRange: document.querySelector("#stat-range"),
  statMean: document.querySelector("#stat-mean"),
  downloadPng: document.querySelector("#download-png"),
  copyLink: document.querySelector("#copy-link"),
};

function initMap() {
  state.map = L.map("map", {
    zoomControl: true,
    attributionControl: false,
    zoomSnap: 0.1,
    zoomDelta: 0.5,
    wheelPxPerZoomLevel: 90,
  }).setView([52.0, 19.1], 6);
}

async function loadDatasets(preferredId = null) {
  const data = await getJson("/api/datasets");
  state.datasets = data.datasets;
  restoreStateFromUrl();
  preferredId = preferredId || activeParams().get("dataset");
  if (preferredId?.startsWith("uploaded:") && !state.datasets.some((item) => item.id === preferredId)) {
    try {
      const profile = await getJson(`/api/datasets/${encodeURIComponent(preferredId)}`);
      state.datasets.push({
        id: profile.id,
        name: profile.name || "Uploaded CSV",
        source: "uploaded",
        facets: profile.facets,
      });
    } catch (_error) {
      showToast("Uploaded dataset link is unavailable on this server");
    }
  }
  if (preferredId) {
    state.source = preferredId.startsWith("uploaded:") ? "upload" : "built-in";
  }
  renderSourceControls();
  populateBuiltInFacets(preferredId);
  populateUploadedDatasets(preferredId);
  await loadProfile();
}

function renderSourceControls() {
  els.sourceButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.source === state.source);
  });
  els.builtInControls.hidden = state.source !== "built-in";
  els.uploadControls.hidden = state.source !== "upload";
}

function populateBuiltInFacets(preferredId = null) {
  populateFacet(els.country, uniqueFacet("country"), preferredId);
  populateDependentFacets(preferredId);
}

function populateDependentFacets(preferredId = null) {
  populateFacet(els.year, uniqueFacet("year", { country: els.country.value }), preferredId);
  populateFacet(els.election, uniqueFacet("election", { country: els.country.value, year: els.year.value }), preferredId);
  populateFacet(
    els.round,
    uniqueFacet("round", {
      country: els.country.value,
      year: els.year.value,
      election: els.election.value,
    }),
    preferredId,
  );
}

function populateUploadedDatasets(preferredId = null) {
  const uploads = state.datasets.filter((item) => item.source === "uploaded");
  els.uploadedDatasetControl.hidden = uploads.length === 0;
  els.uploadedDataset.innerHTML = uploads
    .map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)}</option>`)
    .join("");
  if (preferredId && uploads.some((item) => item.id === preferredId)) {
    els.uploadedDataset.value = preferredId;
  }
}

function populateFacet(select, values, preferredId = null) {
  const previous = select.value;
  select.innerHTML = values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join("");
  const preferred = preferredId ? state.datasets.find((item) => item.id === preferredId)?.facets : null;
  const preferredValue = preferred ? preferred[facetNameFor(select)] : null;
  if (preferredValue && values.includes(preferredValue)) {
    select.value = preferredValue;
  } else if (values.includes(previous)) {
    select.value = previous;
  }
}

function uniqueFacet(facet, filters = {}) {
  const values = state.datasets
    .filter((item) => item.source === "built-in")
    .filter((item) => Object.entries(filters).every(([key, value]) => !value || item.facets[key] === value))
    .map((item) => item.facets[facet])
    .filter(Boolean);
  return [...new Set(values)];
}

function selectedDataset() {
  if (state.source === "upload") {
    return state.datasets.find((item) => item.id === els.uploadedDataset.value);
  }
  return state.datasets.find((item) => (
    item.source === "built-in"
    && item.facets.country === els.country.value
    && item.facets.year === els.year.value
    && item.facets.election === els.election.value
    && item.facets.round === els.round.value
  ));
}

async function loadProfile() {
  const dataset = selectedDataset();
  if (!dataset) {
    state.profile = null;
    clearSelect(els.strategy);
    clearSelect(els.valueMetric);
    updateModeControls();
    await drawMap();
    return;
  }
  state.profile = await getJson(`/api/datasets/${encodeURIComponent(dataset.id)}`);
  populateStrategies();
  populateCandidates();
  populateValueMetrics();
  const isUploadProfile = state.source === "upload";
  if (isUploadProfile && state.profile.suggested_level) {
    els.level.value = state.profile.suggested_level;
  }
  if (isUploadProfile) {
    applyUploadDefaults();
    state.pendingUploadId = null;
  } else {
    applyUrlSelection();
  }
  updateModeControls();
  await drawMap();
}

function applyUploadDefaults() {
  if (state.profile?.preferred_mode === "custom_color" && [...els.strategy.options].some((option) => option.value === "uploaded_colors")) {
    els.strategy.value = "uploaded_colors";
    return;
  }
  if (state.profile?.preferred_mode === "uploaded_value" && [...els.strategy.options].some((option) => option.value === "value_scale")) {
    els.strategy.value = "value_scale";
    if ([...els.valueMetric.options].some((option) => option.value === "uploaded_value")) {
      els.valueMetric.value = "uploaded_value";
    }
  }
}

function populateStrategies() {
  const modes = state.profile?.modes.map((mode) => mode.id) || [];
  const strategies = [];
  if (modes.includes("head_to_head")) {
    strategies.push({ id: "winner_colors", label: "Winner colors" });
  }
  if (modes.some((mode) => ["candidate_share", "turnout", "uploaded_value"].includes(mode))) {
    strategies.push({ id: "value_scale", label: "Value scale" });
  }
  if (modes.includes("custom_color")) {
    strategies.push({ id: "uploaded_colors", label: "Uploaded colors" });
  }
  els.strategy.innerHTML = strategies
    .map((strategy) => `<option value="${escapeHtml(strategy.id)}">${escapeHtml(strategy.label)}</option>`)
    .join("");
}

function populateCandidates() {
  const candidates = state.profile?.candidates || [];
  const options = candidates
    .map((candidate) => `<option value="${escapeHtml(candidate)}">${escapeHtml(candidateLabel(candidate))}</option>`)
    .join("");
  els.candidateA.innerHTML = options;
  els.candidateB.innerHTML = options;
  if (candidates.length > 1) {
    els.candidateA.value = candidates[0];
    els.candidateB.value = candidates[1];
  }
}

function populateValueMetrics() {
  const modes = state.profile?.modes.map((mode) => mode.id) || [];
  const metrics = [];
  if (modes.includes("uploaded_value")) {
    metrics.push({ id: "uploaded_value", label: "Uploaded value" });
  }
  if (modes.includes("turnout")) {
    metrics.push({ id: "turnout", label: "Turnout" });
  }
  if (modes.includes("candidate_share")) {
    for (const candidate of state.profile.candidates) {
      metrics.push({ id: `candidate_share:${candidate}`, label: `${candidateLabel(candidate)} support` });
    }
  }
  els.valueMetric.innerHTML = metrics
    .map((metric) => `<option value="${escapeHtml(metric.id)}">${escapeHtml(metric.label)}</option>`)
    .join("");
}

function updateModeControls() {
  const hasStrategy = Boolean(els.strategy.value);
  els.strategyControl.hidden = !hasStrategy;
  els.headToHeadControl.hidden = els.strategy.value !== "winner_colors";
  els.valueMetricControl.hidden = els.strategy.value !== "value_scale";
}

async function drawMap() {
  const dataset = selectedDataset();
  const params = new URLSearchParams({ level: els.level.value });
  if (dataset && els.strategy.value) {
    params.set("dataset", dataset.id);
    if (els.strategy.value === "winner_colors") {
      params.set("mode", "head_to_head");
      params.set("candidate_a", els.candidateA.value);
      params.set("candidate_b", els.candidateB.value);
    } else if (els.strategy.value === "value_scale") {
      const [mode, candidate] = els.valueMetric.value.split(/:(.*)/s);
      params.set("mode", mode);
      if (candidate) {
        params.set("candidate", candidate);
      }
    } else if (els.strategy.value === "uploaded_colors") {
      params.set("mode", "custom_color");
    }
  }

  const payload = await getJson(`/api/map?${params.toString()}`);
  updateUrlState();
  const geojson = JSON.parse(payload.geojson);
  state.legend = payload.legend;
  updateStats(payload.stats);

  const values = geojson.features
    .map((feature) => feature.properties.value)
    .filter((value) => typeof value === "number");
  state.range = values.length ? [Math.min(...values), Math.max(...values)] : null;

  if (state.layer) {
    state.layer.remove();
  }
  state.layer = L.geoJSON(geojson, {
    style: styleFeature,
    onEachFeature: bindFeature,
  }).addTo(state.map);
  state.map.fitBounds(state.layer.getBounds(), { padding: [14, 14] });
  renderLegend();
}

function styleFeature(feature) {
  const value = feature.properties.value;
  return {
    color: "#2b342f",
    weight: feature.properties.has_value || feature.properties.color ? 0.45 : 0.35,
    opacity: 0.8,
    fillColor: colorFor(feature, value),
    fillOpacity: feature.properties.has_value || feature.properties.color ? 0.84 : 0.08,
  };
}

function bindFeature(feature, layer) {
  const props = feature.properties;
  const rows = [
    `<strong>${escapeHtml(props.display_name || props.name || props.teryt)}</strong>`,
    `TERYT: ${escapeHtml(props.teryt)}`,
  ];

  if (props.winner) {
    rows.push(`Winner: ${escapeHtml(candidateLabel(props.winner))}`);
    rows.push(`Margin: ${formatNumber(props.margin)} pp`);
    rows.push(`${escapeHtml(candidateLabel(props.candidate_a))}: ${formatNumber(props.share_a)}%`);
    rows.push(`${escapeHtml(candidateLabel(props.candidate_b))}: ${formatNumber(props.share_b)}%`);
  } else if (props.candidate) {
    rows.push(`${escapeHtml(candidateLabel(props.candidate))}: ${formatNumber(props.value)}%`);
  } else if (typeof props.value === "number") {
    rows.push(`Value: ${formatNumber(props.value)}`);
  } else {
    rows.push("No data");
  }

  layer.bindTooltip(rows.join("<br>"));
}

function colorFor(feature, value) {
  if (feature.properties.color) {
    return feature.properties.color;
  }
  if (typeof value !== "number" || !state.range) {
    return "#dbe2d8";
  }
  if (state.legend?.type === "diverging") {
    return value >= 0 ? candidateColors[0] : candidateColors[1];
  }
  const [min, max] = state.range;
  if (max === min) {
    return sequentialColors[2];
  }
  const idx = Math.max(0, Math.min(sequentialColors.length - 1, Math.floor(((value - min) / (max - min)) * sequentialColors.length)));
  return sequentialColors[idx];
}

function renderLegend() {
  if (!state.range && state.legend?.type !== "custom") {
    els.legend.innerHTML = "Boundaries only";
    return;
  }

  if (state.legend?.type === "diverging") {
    els.legend.innerHTML = `
      <strong>Winner colors</strong>
      <div class="legend-duo">
        <span style="background:${candidateColors[1]}"></span>
        <span style="background:${candidateColors[0]}"></span>
      </div>
      <div class="legend-row"><span>${escapeHtml(candidateLabel(state.legend.left))}</span><span>${escapeHtml(candidateLabel(state.legend.right))}</span></div>
    `;
    return;
  }

  if (state.legend?.type === "custom") {
    els.legend.innerHTML = "<strong>Uploaded colors</strong>";
    return;
  }

  const [min, max] = state.range;
  els.legend.innerHTML = `
    <strong>Value scale</strong>
    <div class="legend-scale">${sequentialColors.map((color) => `<span style="background:${color}"></span>`).join("")}</div>
    <div class="legend-row"><span>${formatNumber(min)}</span><span>${formatNumber(max)}</span></div>
  `;
}

function updateStats(stats) {
  if (!stats) {
    els.statCount.textContent = "-";
    els.statRange.textContent = "-";
    els.statMean.textContent = "-";
    return;
  }
  els.statCount.textContent = stats.count ?? "-";
  els.statRange.textContent = stats.min === null ? "-" : `${formatNumber(stats.min)}\u00a0-\u00a0${formatNumber(stats.max)}`;
  els.statMean.textContent = stats.mean === null ? "-" : formatNumber(stats.mean);
}

async function uploadCsv() {
  const file = els.upload.files[0];
  if (file) {
    await uploadFile(file);
  }
}

async function uploadFile(file) {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch("/api/uploads", { method: "POST", body });
  const data = await response.json();
  if (!response.ok) {
    showToast(data.error || "Could not upload this CSV");
    return;
  }
  state.source = "upload";
  state.datasets = state.datasets.filter((item) => item.id !== data.id);
  state.datasets.push({
    id: data.id,
    name: data.name || "Uploaded CSV",
    source: "uploaded",
    facets: data.facets,
  });
  state.pendingUploadId = data.id;
  renderSourceControls();
  populateUploadedDatasets(data.id);
  await loadProfile();
}

async function downloadPng() {
  const svg = document.querySelector(".leaflet-overlay-pane svg");
  if (!svg) {
    showToast("No map to export yet");
    return;
  }
  const bounds = svg.getBoundingClientRect();
  const clone = svg.cloneNode(true);
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("width", Math.ceil(bounds.width));
  clone.setAttribute("height", Math.ceil(bounds.height));
  const background = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  background.setAttribute("x", "0");
  background.setAttribute("y", "0");
  background.setAttribute("width", "100%");
  background.setAttribute("height", "100%");
  background.setAttribute("fill", "#e6ebe2");
  clone.insertBefore(background, clone.firstChild);

  const dataUrl = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(new XMLSerializer().serializeToString(clone))}`;
  const image = new Image();
  image.onload = () => {
    const canvas = document.createElement("canvas");
    canvas.width = Math.ceil(bounds.width);
    canvas.height = Math.ceil(bounds.height);
    const ctx = canvas.getContext("2d");
    ctx.drawImage(image, 0, 0);
    const link = document.createElement("a");
    link.download = "teryt-map.png";
    link.href = canvas.toDataURL("image/png");
    link.click();
  };
  image.src = dataUrl;
}

async function copyLink() {
  updateUrlState();
  await navigator.clipboard.writeText(window.location.href);
  showToast("Link copied");
}

async function getJson(url) {
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function showToast(message) {
  els.toast.textContent = message;
  els.toast.hidden = false;
  window.setTimeout(() => {
    els.toast.hidden = true;
  }, 5000);
}

function clearSelect(select) {
  select.innerHTML = "";
}

function facetNameFor(select) {
  return {
    country: "country",
    year: "year",
    election: "election",
    round: "round",
  }[select.id];
}

function formatNumber(value) {
  return Number(value).toLocaleString("en-US", { maximumFractionDigits: 2 });
}

function candidateLabel(name) {
  const upperWords = String(name || "").match(/[A-ZĄĆĘŁŃÓŚŹŻ]{2,}(?:-[A-ZĄĆĘŁŃÓŚŹŻ]{2,})?/g);
  return upperWords?.join(" ") || String(name || "");
}

function updateUrlState() {
  const dataset = selectedDataset();
  const params = new URLSearchParams();
  params.set("source", state.source);
  params.set("level", els.level.value);
  if (dataset) {
    params.set("dataset", dataset.id);
  }
  if (els.strategy.value) {
    params.set("mode", els.strategy.value);
  }
  if (els.valueMetric.value) {
    params.set("metric", els.valueMetric.value);
  }
  if (els.candidateA.value) {
    params.set("a", els.candidateA.value);
  }
  if (els.candidateB.value) {
    params.set("b", els.candidateB.value);
  }
  history.replaceState(null, "", `${window.location.pathname}?${params.toString()}`);
}

function restoreStateFromUrl() {
  const params = activeParams();
  if (params.get("source")) {
    state.source = params.get("source");
  }
  if (params.get("level")) {
    els.level.value = params.get("level");
  }
}

function applyUrlSelection() {
  const params = activeParams();
  const mode = params.get("mode");
  if (mode && [...els.strategy.options].some((option) => option.value === mode)) {
    els.strategy.value = mode;
  }
  const metric = params.get("metric");
  if (metric && [...els.valueMetric.options].some((option) => option.value === metric)) {
    els.valueMetric.value = metric;
  }
  const candidateA = params.get("a");
  if (candidateA && [...els.candidateA.options].some((option) => option.value === candidateA)) {
    els.candidateA.value = candidateA;
  }
  const candidateB = params.get("b");
  if (candidateB && [...els.candidateB.options].some((option) => option.value === candidateB)) {
    els.candidateB.value = candidateB;
  }
}

function activeParams() {
  const params = new URLSearchParams(window.location.search);
  if ([...params.keys()].length > 0) {
    return params;
  }
  return new URLSearchParams(defaultState);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#039;",
  })[char]);
}

els.level.addEventListener("change", drawMap);
els.sourceButtons.forEach((button) => {
  button.addEventListener("click", () => {
    state.source = button.dataset.source;
    renderSourceControls();
    loadProfile();
  });
});
els.country.addEventListener("change", () => {
  populateDependentFacets();
  loadProfile();
});
els.year.addEventListener("change", () => {
  populateDependentFacets();
  loadProfile();
});
els.election.addEventListener("change", () => {
  populateDependentFacets();
  loadProfile();
});
els.round.addEventListener("change", loadProfile);
els.uploadedDataset.addEventListener("change", loadProfile);
els.strategy.addEventListener("change", () => {
  updateModeControls();
  drawMap();
});
els.valueMetric.addEventListener("change", drawMap);
els.candidateA.addEventListener("change", drawMap);
els.candidateB.addEventListener("change", drawMap);
els.upload.addEventListener("change", uploadCsv);
els.downloadPng.addEventListener("click", downloadPng);
els.copyLink.addEventListener("click", copyLink);
els.dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  els.dropZone.classList.add("is-dragover");
});
els.dropZone.addEventListener("dragleave", () => {
  els.dropZone.classList.remove("is-dragover");
});
els.dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  els.dropZone.classList.remove("is-dragover");
  const file = event.dataTransfer.files[0];
  if (file) {
    uploadFile(file);
  }
});

initMap();
loadDatasets().catch((error) => showToast(error.message));
