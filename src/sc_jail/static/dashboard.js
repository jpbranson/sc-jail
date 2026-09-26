// Charts are rendered on the server at the width the page gives them. Each chart is
// requested once that width is known, and every later version is decoded off screen
// before it replaces the visible one, so a chart never shows at the wrong size or blanks.
const REFRESH_MS = 60000;

function chartWidth(plot) {
  return Math.max(360, Math.min(1800, Math.floor(plot.parentElement.clientWidth)));
}

// The server renders in 60-pixel width steps; requesting the step keeps URLs cacheable.
function widthStep(width) {
  return Math.max(360, Math.min(1800, Math.floor(width / 60) * 60));
}

function decoded(image) {
  if (image.decode) return image.decode();
  return new Promise((resolve, reject) => {
    image.onload = resolve;
    image.onerror = reject;
  });
}

function prepareChart(plot) {
  let step = 0;
  let version = plot.dataset.version;
  let generation = 0;
  const notice = document.createElement("p");
  notice.className = "chart-retry notice";
  notice.hidden = true;
  notice.setAttribute("role", "status");
  notice.append("Chart could not load. ");
  const retry = document.createElement("button");
  retry.type = "button";
  retry.textContent = "Retry chart";
  retry.setAttribute("aria-label", "Retry " + plot.dataset.kind.replace(/-/g, " ") + " chart");
  notice.append(retry);
  plot.parentElement.after(notice);

  function load({ force = false, changed = false } = {}) {
    const nextStep = widthStep(chartWidth(plot));
    if (!force && !changed && nextStep === step) {
      // Same rendered width: the shown chart only needs to follow its frame.
      if (plot.classList.contains("is-loaded")) plot.style.width = chartWidth(plot) + "px";
      return;
    }
    step = nextStep;
    const current = ++generation;
    const url = "/chart/" + plot.dataset.kind + ".svg?days=" + plot.dataset.days +
      "&width=" + nextStep + "&v=" + encodeURIComponent(version);
    let attempt = 0;
    notice.hidden = true;

    function requestChart() {
      if (current !== generation) return;
      const image = new Image();
      let settled = false;
      const timeout = setTimeout(() => finish(false), 15000);
      function finish(loaded) {
        if (settled) return;
        settled = true;
        clearTimeout(timeout);
        if (current !== generation) return;
        if (loaded) {
          // One step: the previous chart stays visible until this one is ready to paint.
          plot.style.width = chartWidth(plot) + "px";
          plot.src = image.src;
          plot.classList.add("is-loaded");
          notice.hidden = true;
        } else if (attempt < 2) {
          attempt += 1;
          setTimeout(requestChart, attempt * 1000);
        } else {
          notice.hidden = false;
        }
      }
      // Bypass a cached failure when retrying, including a manual retry.
      image.src = url + (attempt || force ? "&retry=" + Date.now() + "-" + attempt : "");
      decoded(image).then(() => finish(true), () => finish(false));
    }
    requestChart();
  }

  retry.addEventListener("click", () => load({ force: true }));
  return {
    kind: plot.dataset.kind,
    load,
    update(nextVersion) {
      if (!nextVersion || nextVersion === version) return;
      version = nextVersion;
      load({ changed: true });
    },
  };
}

const charts = Array.from(document.querySelectorAll("img.plot-live"), prepareChart);
charts.forEach((chart) => chart.load());
let resizeTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => charts.forEach((chart) => chart.load()), 250);
});

// Refresh in place: only regions whose markup changed are replaced, and charts update
// only when the server reports a new chart version.
const FOCUSABLE = "a, button, summary, select, input, [tabindex]";

function carryOpenDetails(from, to) {
  const open = Array.from(from.querySelectorAll("details"), (details) => details.open);
  to.querySelectorAll("details").forEach((details, index) => {
    if (open[index]) details.open = true;
  });
}

function replaceRegion(region, replacement) {
  const focusable = Array.from(region.querySelectorAll(FOCUSABLE));
  const focused = focusable.indexOf(document.activeElement);
  const fresh = document.importNode(replacement, true);
  region.replaceWith(fresh);
  if (focused >= 0) {
    const target = fresh.querySelectorAll(FOCUSABLE)[focused];
    if (target) target.focus({ preventScroll: true });
  }
}

let lastRefresh = Date.now();
let refreshing = false;

async function refresh() {
  if (refreshing || document.hidden) return;
  refreshing = true;
  lastRefresh = Date.now();
  try {
    const response = await fetch(location.href, { cache: "no-store" });
    if (!response.ok) return;
    const next = new DOMParser().parseFromString(await response.text(), "text/html");
    const regions = Array.from(document.querySelectorAll("[data-refresh]"));
    const incoming = new Map(
      Array.from(next.querySelectorAll("[data-refresh]"), (region) => [region.dataset.refresh, region])
    );
    const sameLayout = next.body.dataset.assets === document.body.dataset.assets &&
      regions.length === incoming.size &&
      regions.every((region) => incoming.has(region.dataset.refresh));
    if (!sameLayout) {
      // A deployment changed the page itself; load it once in full.
      location.reload();
      return;
    }
    for (const region of regions) {
      const replacement = incoming.get(region.dataset.refresh);
      carryOpenDetails(region, replacement);
      if (!region.isEqualNode(replacement)) replaceRegion(region, replacement);
    }
    next.querySelectorAll("img.plot-live").forEach((image) => {
      const chart = charts.find((candidate) => candidate.kind === image.dataset.kind);
      if (chart) chart.update(image.dataset.version);
    });
  } catch (error) {
    // Keep showing the current page when the network or server is unavailable.
  } finally {
    refreshing = false;
  }
}

setInterval(refresh, REFRESH_MS);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden && Date.now() - lastRefresh >= REFRESH_MS) refresh();
});

// The optional font must never delay layout or chart initialization.
const font = document.createElement("link");
font.rel = "stylesheet";
font.href = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap";
document.head.append(font);
