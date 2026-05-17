function getCacheId() {
  const fromWindow = window.__UPGRADE_CACHE_ID__;
  if (fromWindow) return fromWindow;
  const params = new URLSearchParams(window.location.search);
  return params.get("cache") || sessionStorage.getItem("allocatorExportCacheId") || "";
}

async function downloadTierReport(tier, button) {
  const cacheId = getCacheId();
  if (!cacheId) {
    alert(
      "Export session not found. Please return to the allocator, calculate results, and export your free report again."
    );
    return;
  }

  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = "Generating…";

  try {
    const response = await fetch("/export-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tier, cache_id: cacheId }),
    });

    if (!response.ok) {
      const text = await response.text();
      alert(text || "Report export failed.");
      return;
    }

    const names = {
      options: "retirement_options_report.pdf",
    };

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = names[tier] || "retirement_report.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    console.error(err);
    alert(`Report export failed:\n\n${err.message}`);
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const cacheId = getCacheId();
  const status = document.getElementById("upgrade-status");
  if (!cacheId && status) {
    status.textContent =
      "Export session not found. Return to the allocator and export your free report to unlock upgrade options.";
  }

  document.querySelectorAll("[data-tier]").forEach((button) => {
    button.addEventListener("click", () => {
      downloadTierReport(button.getAttribute("data-tier"), button);
    });
  });
});
