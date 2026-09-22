function prepareChart(plot) {
  let width = 0;
  let version = 0;
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

  function load(force = false) {
    const nextWidth = Math.max(360, Math.min(1800, Math.floor(plot.parentElement.clientWidth)));
    if (!force && nextWidth === width) return;
    width = nextWidth;
    const currentVersion = ++version;
    const url = "/chart/" + plot.dataset.kind + ".svg?days=" + plot.dataset.days + "&width=" + width;
    let attempt = 0;
    notice.hidden = true;

    function requestChart() {
      if (currentVersion !== version) return;
      const image = new Image();
      let settled = false;
      const timeout = setTimeout(() => finish(false), 15000);
      function finish(loaded) {
        if (settled) return;
        settled = true;
        clearTimeout(timeout);
        image.onload = image.onerror = null;
        if (currentVersion !== version) return;
        if (loaded) {
          // Keep the previous/fallback chart visible until its replacement loads.
          plot.style.width = nextWidth + "px";
          plot.src = image.src;
          notice.hidden = true;
        } else if (attempt < 2) {
          attempt += 1;
          setTimeout(requestChart, attempt * 1000);
        } else {
          notice.hidden = false;
        }
      }
      image.onload = () => finish(true);
      image.onerror = () => finish(false);
      // Bypass a cached failure when retrying, including a manual retry.
      image.src = url + (attempt || force ? "&retry=" + Date.now() + "-" + attempt : "");
    }
    requestChart();
  }

  retry.addEventListener("click", () => load(true));
  return load;
}

const charts = Array.from(document.querySelectorAll("img.plot"), prepareChart);
function loadCharts() {
  charts.forEach((load) => load());
}
loadCharts();
let resizeTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(loadCharts, 250);
});

// The optional font must never delay layout or chart initialization.
const font = document.createElement("link");
font.rel = "stylesheet";
font.href = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap";
document.head.append(font);

setTimeout(() => { if (!document.hidden) location.reload(); }, 60000);
document.addEventListener("visibilitychange", () => { if (!document.hidden) location.reload(); });
