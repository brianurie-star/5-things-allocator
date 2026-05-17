let chartRefs = {};
let entryChartRefs = {};
let accordionChartRefs = {};
let lastPayload = null;
let lastResults = null;
let balanceSheetMode = "partial";

Chart.register(ChartDataLabels);

/**
 * App pie chart design (data entry Investment Profile + all results pies).
 * Single implementation: makePie() + basePieOptions() only — do not fork per screen.
 * - Square plot: maintainAspectRatio + aspectRatio 1 (see .pie-chart-host in styles.css).
 * - Outside labels: datalabels anchor/align "end" + offset. layout.padding MUST be equal on all sides so chartArea stays centered (asymmetric padding + this plugin skewed chartArea and clipped arcs).
 * - Radius: PIE_RADIUS_PCT vs PIE_RADIUS_LARGE_LABEL_PCT (profile-style % pies use "large").
 */
const PIE_ASPECT_RATIO = 1;
const PIE_RADIUS_PCT = "76%";
const PIE_RADIUS_LARGE_LABEL_PCT = "68%";
/** Same pixel gutter on top/right/bottom/left — room for outside labels without shifting the pie arc */
const PIE_OUTSIDE_LABEL_GUTTER = { default: 54, largeLabels: 58 };
const PIE_DATALABEL_OFFSET = { default: 16, largeLabels: 18 };
/** PDF/PNG: square host width (px) for consistent export bitmaps */
const PIE_EXPORT_SNAPSHOT_SIDE_PX = 400;
const PIE_TITLE_FONT = { size: 16, weight: "600" };
const PIE_DATALABEL_FONT = {
  family: "Inter, Segoe UI, Helvetica, Arial, sans-serif",
  size: 12,
  weight: "600",
  lineHeight: 1.35
};

const percentFields = [
  "guaranteed_income_allocation",
  "guaranteed_withdrawal_rate",
  "unprotected_withdrawal_rate",
  "inflation",
  "tax_rate"
];

function currency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  }).format(Math.round(Number(value || 0)));
}

function percent(value) {
  return `${Math.round(Number(value || 0))}%`;
}

function toRatio(field, value) {
  return percentFields.includes(field) ? Number(value || 0) / 100 : Number(value || 0);
}

function fromRatio(field, value) {
  return percentFields.includes(field) ? Math.round(Number(value || 0) * 100) : (value ?? "");
}

function getEl(id) {
  return document.getElementById(id);
}

function getValue(id) {
  const el = getEl(id);
  return el ? el.value : "";
}

function getPortfolioProfiles(prefix = "") {
  const gv = (id) => Number(getValue(prefix + id) || 0);

  return {
    aggressive: {
      label: "Aggressive",
      equity: gv("aggressive_equity") / 100,
      mean: gv("aggressive_mean"),
      stdev: gv("aggressive_stdev")
    },
    growth: {
      label: "Growth",
      equity: gv("growth_equity") / 100,
      mean: gv("growth_mean"),
      stdev: gv("growth_stdev")
    },
    growthIncome: {
      label: "Growth With Income",
      equity: gv("growthIncome_equity") / 100,
      mean: gv("growthIncome_mean"),
      stdev: gv("growthIncome_stdev")
    },
    intermediate: {
      label: "Intermediate Growth",
      equity: gv("intermediate_equity") / 100,
      mean: gv("intermediate_mean"),
      stdev: gv("intermediate_stdev")
    }
  };
}

function getPayload() {
  return {
    client_name: getValue("client_name"),
    report_date: getValue("report_date"),
    his_age: getValue("his_age"),
    her_age: getValue("her_age"),
    his_social_security: getValue("his_social_security"),
    her_social_security: getValue("her_social_security"),
    his_pension: getValue("his_pension"),
    her_pension: getValue("her_pension"),
    his_other_income: getValue("his_other_income"),
    her_other_income: getValue("her_other_income"),
    monthly_living_expenses: getValue("monthly_living_expenses"),
    retirement_assets: getValue("retirement_assets"),
    non_retirement_assets: getValue("non_retirement_assets"),
    home_value: getValue("home_value"),
    mortgage_balance: getValue("mortgage_balance"),
    guaranteed_income_allocation: toRatio("guaranteed_income_allocation", getValue("guaranteed_income_allocation")),
    risk_profile: getValue("risk_profile"),
    guaranteed_withdrawal_rate: toRatio("guaranteed_withdrawal_rate", getValue("guaranteed_withdrawal_rate")),
    unprotected_withdrawal_rate: toRatio("unprotected_withdrawal_rate", getValue("unprotected_withdrawal_rate")),
    inflation: toRatio("inflation", getValue("inflation")),
    his_life_expectancy: getValue("his_life_expectancy"),
    her_life_expectancy: getValue("her_life_expectancy"),
    tax_rate: toRatio("tax_rate", getValue("tax_rate")),
    life_insurance_protection: getValue("life_insurance_protection"),
    ltc_insurance_protection: getValue("ltc_insurance_protection"),
    auto_insurance_protection: getValue("auto_insurance_protection"),
    home_insurance_protection: getValue("home_insurance_protection"),
    umbrella_insurance_protection: getValue("umbrella_insurance_protection"),
    life_insurance_monthly_cost: getValue("life_insurance_monthly_cost"),
    ltc_insurance_monthly_cost: getValue("ltc_insurance_monthly_cost"),
    auto_insurance_monthly_cost: getValue("auto_insurance_monthly_cost"),
    home_insurance_monthly_cost: getValue("home_insurance_monthly_cost"),
    umbrella_insurance_monthly_cost: getValue("umbrella_insurance_monthly_cost"),
    monthly_ltc_cost: getValue("monthly_ltc_cost"),
    ltc_years: getValue("ltc_years"),
    lawsuit_award: getValue("lawsuit_award"),

    aggressive_equity: getValue("aggressive_equity"),
    aggressive_mean: getValue("aggressive_mean"),
    aggressive_stdev: getValue("aggressive_stdev"),

    growth_equity: getValue("growth_equity"),
    growth_mean: getValue("growth_mean"),
    growth_stdev: getValue("growth_stdev"),

    growthIncome_equity: getValue("growthIncome_equity"),
    growthIncome_mean: getValue("growthIncome_mean"),
    growthIncome_stdev: getValue("growthIncome_stdev"),

    intermediate_equity: getValue("intermediate_equity"),
    intermediate_mean: getValue("intermediate_mean"),
    intermediate_stdev: getValue("intermediate_stdev")
  };
}

function syncAccordion(payload) {
  Object.keys(payload).forEach((key) => {
    const el = getEl(`edit_${key}`);
    if (!el) return;
    el.value = percentFields.includes(key) ? fromRatio(key, payload[key]) : payload[key];
  });
  syncAccordionRiskPreview();
}

function pullAccordion() {
  const keys = [
    "client_name", "report_date", "his_age", "her_age",
    "his_social_security", "her_social_security",
    "his_pension", "her_pension",
    "his_other_income", "her_other_income",
    "monthly_living_expenses",
    "retirement_assets", "non_retirement_assets",
    "home_value", "mortgage_balance",
    "guaranteed_income_allocation", "risk_profile",
    "guaranteed_withdrawal_rate", "unprotected_withdrawal_rate",
    "inflation", "his_life_expectancy", "her_life_expectancy",
    "tax_rate",
    "life_insurance_protection", "ltc_insurance_protection",
    "auto_insurance_protection", "home_insurance_protection",
    "umbrella_insurance_protection",
    "life_insurance_monthly_cost", "ltc_insurance_monthly_cost",
    "auto_insurance_monthly_cost", "home_insurance_monthly_cost",
    "umbrella_insurance_monthly_cost",
    "monthly_ltc_cost", "ltc_years", "lawsuit_award",
    "aggressive_equity", "aggressive_mean", "aggressive_stdev",
    "growth_equity", "growth_mean", "growth_stdev",
    "growthIncome_equity", "growthIncome_mean", "growthIncome_stdev",
    "intermediate_equity", "intermediate_mean", "intermediate_stdev"
  ];

  const payload = {};
  keys.forEach((key) => {
    const el = getEl(`edit_${key}`);
    if (!el) return;
    payload[key] = percentFields.includes(key) ? Number(el.value || 0) / 100 : el.value;
  });
  return payload;
}

function showEntry() {
  getEl("results-screen")?.classList.add("hidden");
  getEl("entry-screen")?.classList.remove("hidden");
}

function openTab(name, btn) {
  document.querySelectorAll(".tab-content").forEach((el) => el.classList.remove("active"));
  document.querySelectorAll(".tab").forEach((el) => el.classList.remove("active"));
  getEl(name)?.classList.add("active");
  btn?.classList.add("active");
}

function destroyMap(map) {
  Object.values(map).forEach((chart) => {
    try { chart.destroy(); } catch (e) { console.error(e); }
  });
  Object.keys(map).forEach((key) => delete map[key]);
}

/** Matches report.py nice_axis_max — explicit bar scale so ticks match bar heights. */
function niceAxisMaxForChart(value) {
  if (value === null || value <= 0 || Number.isNaN(value)) return 1;
  const exp = 10 ** Math.floor(Math.log10(value));
  const step = value / exp <= 10 ? exp : exp * 2;
  return Math.ceil(value / step) * step * 1.02;
}

function resizeAllCharts(map) {
  Object.values(map).forEach((chart) => {
    try {
      chart.resize();
      chart.update("none");
    } catch (e) {
      console.error("Chart resize failed:", e);
    }
  });
}

function stopAllChartAnimations(map) {
  Object.values(map).forEach((chart) => {
    try {
      if (typeof chart.stop === "function") chart.stop();
      chart.update("none");
    } catch (e) {
      console.error("Chart stop failed:", e);
    }
  });
}

/**
 * Before pie PNG export, pin #results-screen .pie-chart-host to a fixed square (same order of
 * width as the 3-col Investment Strategy column). Restores previous host style via snapshot.
 */
function snapPieHostsForExport(sidePx) {
  const hosts = document.querySelectorAll("#results-screen .pie-chart-host");
  const snapshots = [];

  hosts.forEach((host) => {
    const canvas = host.querySelector("canvas");
    if (!canvas?.id) return;
    const ch = chartRefs[canvas.id];
    if (!ch || ch.config?.type !== "pie") return;

    snapshots.push({
      host,
      prevStyle: host.getAttribute("style")
    });

    host.style.boxSizing = "border-box";
    host.style.width = `${sidePx}px`;
    host.style.height = `${sidePx}px`;
    host.style.minWidth = `${sidePx}px`;
    host.style.minHeight = `${sidePx}px`;
    host.style.maxWidth = `${sidePx}px`;
    host.style.aspectRatio = "unset";
    host.style.flex = "0 0 auto";
    host.style.alignSelf = "center";
    host.style.marginLeft = "auto";
    host.style.marginRight = "auto";
  });

  return function restorePieHostSnapshots() {
    snapshots.forEach(({ host, prevStyle }) => {
      if (prevStyle === null || prevStyle === "") host.removeAttribute("style");
      else host.setAttribute("style", prevStyle);
    });
  };
}

/** Match Investment Strategy column width (profile/allocation hosts) so every pie PNG shares that geometry before PDF capture. */
function resolvePieExportSidePx() {
  const refCanvas = getEl("profileChart") || getEl("allocationChart");
  const host = refCanvas?.closest?.(".pie-chart-host");
  if (host) {
    const w = Math.round(host.getBoundingClientRect().width);
    if (Number.isFinite(w) && w >= 240 && w <= 680) {
      return w;
    }
  }
  return PIE_EXPORT_SNAPSHOT_SIDE_PX;
}

function basePieOptions(title, largeLabels = false, isPercent = false) {
  const gutter = largeLabels ? PIE_OUTSIDE_LABEL_GUTTER.largeLabels : PIE_OUTSIDE_LABEL_GUTTER.default;
  const labelOffset = largeLabels ? PIE_DATALABEL_OFFSET.largeLabels : PIE_DATALABEL_OFFSET.default;

  return {
    responsive: true,
    maintainAspectRatio: true,
    aspectRatio: PIE_ASPECT_RATIO,
    // Export can capture partial sweep states when pie animation is active.
    animation: { duration: 0 },
    layout: {
      padding: {
        top: gutter,
        right: gutter,
        bottom: gutter,
        left: gutter
      }
    },
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        text: title,
        padding: { top: 0, bottom: 14 },
        font: PIE_TITLE_FONT
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            return isPercent
              ? `${context.label}: ${percent(context.raw)}`
              : `${context.label}: ${currency(context.raw)}`;
          }
        }
      },
      datalabels: {
        color: "#333",
        anchor: "end",
        align: "end",
        offset: labelOffset,
        clamp: false,
        clip: false,
        textAlign: "center",
        padding: { top: 2, right: 4, bottom: 2, left: 4 },
        display: function (context) {
          const v = Number(context.dataset.data[context.dataIndex] ?? 0);
          if (isPercent) return Math.abs(v) > 0.05;
          return Math.abs(v) >= 0.01;
        },
        formatter: function (value, context) {
          const label = context.chart.data.labels[context.dataIndex];
          return isPercent
            ? `${label}\n${percent(value)}`
            : `${label}\n${currency(value)}`;
        },
        font: PIE_DATALABEL_FONT
      }
    }
  };
}

function makePie(map, id, labels, data, title, largeLabels = false, colors = null, isPercent = false) {
  const canvas = getEl(id);
  if (!canvas) return;

  map[id] = new Chart(canvas, {
    type: "pie",
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors || ["#ed7d31", "#70ad47", "#c00000", "#ffc000", "#5b9bd5", "#a5a5a5"],
        borderColor: "#ffffff",
        borderWidth: 2,
        radius: largeLabels ? PIE_RADIUS_LARGE_LABEL_PCT : PIE_RADIUS_PCT
      }]
    },
    options: basePieOptions(title, largeLabels, isPercent)
  });
}

function makeAnnualCoverageChart(id, labels, data, title) {
  const canvas = getEl(id);
  if (!canvas) return;

  const nums = data.map((v) => Number(v || 0));
  const diff = Number(nums[2] || 0);
  const posMax = Math.max(0, ...nums);
  const negMin = Math.min(0, ...nums);
  let yMin = 0;
  let yMax = niceAxisMaxForChart(posMax);
  if (negMin < 0) {
    yMin = -niceAxisMaxForChart(-negMin);
  }

  chartRefs[id] = new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        data: nums,
        backgroundColor: [
          "#70ad47",
          "#ed7d31",
          diff >= 0 ? "#00b050" : "#c00000"
        ]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 0 },
      layout: { padding: { top: 18, right: 18, bottom: 10, left: 18 } },
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: title,
          padding: { bottom: 18 },
          font: { size: 16, weight: "600" }
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              return currency(context.raw);
            }
          }
        },
        datalabels: {
          anchor: "end",
          align: function (context) {
            return Number(context.raw || 0) >= 0 ? "end" : "start";
          },
          formatter: function (value, context) {
            return `${context.chart.data.labels[context.dataIndex]}\n${currency(value)}`;
          },
          color: "#333",
          font: { size: 11, weight: "600" }
        }
      },
      scales: {
        x: {
          grid: { display: false }
        },
        y: {
          min: yMin,
          max: yMax,
          ticks: {
            callback: function (value) {
              return currency(value);
            }
          },
          grid: { color: "rgba(15, 23, 42, 0.08)" }
        }
      }
    }
  });
}

function makeOutcomeRangeChart(map, id, mean, low98, high98, low68, high68, title = "Sample Range of Investment Outcomes") {
  const canvas = getEl(id);
  if (!canvas) return;

  map[id] = new Chart(canvas, {
    type: "bar",
    data: {
      labels: ["98% of the Time", "68% of the Time"],
      datasets: [
        {
          label: "Downside",
          data: [[low98, mean], [low68, mean]],
          backgroundColor: "#c00000",
          barThickness: 28,
          categoryPercentage: 0.7,
          barPercentage: 0.95
        },
        {
          label: "Upside",
          data: [[mean, high98], [mean, high68]],
          backgroundColor: "#00b050",
          barThickness: 28,
          categoryPercentage: 0.7,
          barPercentage: 0.95
        }
      ]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 18, right: 18, bottom: 10, left: 18 } },
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: title,
          padding: { bottom: 18 },
          font: { size: 16, weight: "600" }
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const raw = context.raw;
              return `${context.dataset.label}: ${percent(raw[0])} to ${percent(raw[1])}`;
            }
          }
        },
        datalabels: {
          color: function (context) {
            return context.dataset.label === "Downside" ? "#ffffff" : "#003300";
          },
          formatter: function (value, context) {
            return context.dataset.label === "Downside" ? percent(value[0]) : percent(value[1]);
          },
          anchor: "center",
          align: "center",
          font: { size: 11, weight: "700" }
        }
      },
      scales: {
        x: {
          ticks: {
            callback: function (value) {
              return `${value}%`;
            }
          },
          grid: { color: "rgba(15, 23, 42, 0.08)" }
        },
        y: {
          grid: { display: false }
        }
      }
    }
  });
}

function makeSelfInsuranceChart(id, earlyDeath, ltc, lawsuit) {
  const canvas = getEl(id);
  if (!canvas) return;

  const vals = [earlyDeath, ltc, lawsuit].map((v) => Number(v || 0));
  const yMax = niceAxisMaxForChart(Math.max(0, ...vals, 1));

  chartRefs[id] = new Chart(canvas, {
    type: "bar",
    data: {
      labels: ["Early Death", "Long-Term Care", "Lawsuit"],
      datasets: [{
        data: vals,
        backgroundColor: ["#5b9bd5", "#ed7d31", "#c00000"]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 0 },
      layout: { padding: { top: 18, right: 18, bottom: 10, left: 18 } },
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: "Self-Insurance Need by Risk",
          padding: { bottom: 18 },
          font: { size: 16, weight: "600" }
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              return currency(context.raw);
            }
          }
        },
        datalabels: {
          anchor: "end",
          align: "end",
          formatter: function (value, context) {
            return `${context.chart.data.labels[context.dataIndex]}\n${currency(value)}`;
          },
          color: "#333",
          font: { size: 11, weight: "600" }
        }
      },
      scales: {
        x: {
          grid: { display: false }
        },
        y: {
          min: 0,
          max: yMax,
          ticks: {
            callback: function (value) {
              return currency(value);
            }
          },
          grid: { color: "rgba(15, 23, 42, 0.08)" }
        }
      }
    }
  });
}

function updateBalanceSheetSelectorUI() {
  const partialBtn = getEl("balanceSheetPartial");
  const fullBtn = getEl("balanceSheetFull");

  if (partialBtn) {
    const isActive = balanceSheetMode === "partial";
    partialBtn.classList.toggle("is-active", isActive);
    partialBtn.setAttribute("aria-pressed", isActive ? "true" : "false");
  }

  if (fullBtn) {
    const isActive = balanceSheetMode === "full";
    fullBtn.classList.toggle("is-active", isActive);
    fullBtn.setAttribute("aria-pressed", isActive ? "true" : "false");
  }
}

function setBalanceSheetMode(mode) {
  if (mode !== "partial" && mode !== "full") return;
  if (balanceSheetMode === mode) return;

  balanceSheetMode = mode;
  updateBalanceSheetSelectorUI();

  if (lastPayload && lastResults) {
    const payloadWithMode = { ...lastPayload, balance_sheet_mode: balanceSheetMode };
    fetch("/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payloadWithMode)
    })
      .then((response) => response.json())
      .then((results) => {
        lastPayload = payloadWithMode;
        lastResults = results;
        renderResults(payloadWithMode, results);
      })
      .catch((err) => console.error(err));
  }
}

function renderProfilePreview(map, profileChartId, outcomesChartId, riskProfile, prefix = "") {
  const profiles = getPortfolioProfiles(prefix);
  const profile = profiles[riskProfile] || profiles.growth;

  const stockPct = Math.round((profile.equity || 0) * 100);
  const bondPct = 100 - stockPct;

  makePie(
    map,
    profileChartId,
    ["Stock", "Bond/Alternative"],
    [stockPct, bondPct],
    `Investment Profile (${profile.label})`,
    true,
    ["#ed7d31", "#ffc000"],
    true
  );

  makeOutcomeRangeChart(
    map,
    outcomesChartId,
    Number(profile.mean || 0),
    Number(profile.mean || 0) - (2 * Number(profile.stdev || 0)),
    Number(profile.mean || 0) + (2 * Number(profile.stdev || 0)),
    Number(profile.mean || 0) - Number(profile.stdev || 0),
    Number(profile.mean || 0) + Number(profile.stdev || 0)
  );
}

function renderEntryProfilePreview() {
  destroyMap(entryChartRefs);
  const riskProfile = getValue("risk_profile") || "growth";
  renderProfilePreview(entryChartRefs, "entryProfileChart", "entryOutcomesChart", riskProfile, "");
}

function syncAccordionRiskPreview() {
  destroyMap(accordionChartRefs);
  const riskProfile = getValue("edit_risk_profile") || "growth";
  renderProfilePreview(accordionChartRefs, "accordionProfileChart", "accordionOutcomesChart", riskProfile, "edit_");
}

function resizeAccordionProfileCharts() {
  Object.values(accordionChartRefs).forEach((chart) => {
    if (chart && typeof chart.resize === "function") {
      chart.resize();
    }
  });
}

function renderResults(payload, results) {
  destroyMap(chartRefs);

  const basicLivingExpenses = Number(payload.monthly_living_expenses || 0);
  const protectedIncomeAnnual = Number(results.protected_monthly_income || 0) * 12;
  const basicExpensesAnnual = basicLivingExpenses * 12;
  const coverageDifference = protectedIncomeAnnual - basicExpensesAnnual;
  const ltcYears = Math.round(Number(payload.ltc_years || 0));

  const lawsuitIncomeAtRisk =
    (Number(payload.his_other_income || 0) + Number(payload.her_other_income || 0)) * 12;

  const displayedMonthlyIncome =
    balanceSheetMode === "full"
      ? Number(results.full_balance_sheet_monthly_income || 0)
      : Number(results.monthly_income || 0);

  const totalAnnualIncome = displayedMonthlyIncome * 12;
  const protectedIncomeRest = Math.max(totalAnnualIncome - lawsuitIncomeAtRisk, 0);

  const clientTitle = getEl("client-title");
  const kpiIncome = getEl("kpi-income");
  const kpiExpenses = getEl("kpi-expenses");
  const kpiAssets = getEl("kpi-assets");
  const kpiHomeEquity = getEl("kpi-home-equity");
  const selfInsuranceTotal = getEl("selfInsuranceTotal");

  if (clientTitle) clientTitle.textContent = `${payload.client_name || "Client"} • ${results.profile_label || ""}`;
  if (kpiIncome) kpiIncome.textContent = currency(displayedMonthlyIncome);
  if (kpiExpenses) kpiExpenses.textContent = currency(results.monthly_expenses);
  if (kpiAssets) kpiAssets.textContent = currency(results.investable_assets);
  if (kpiHomeEquity) kpiHomeEquity.textContent = currency(results.available_home_equity);
  if (selfInsuranceTotal) selfInsuranceTotal.textContent = currency(results.self_insurance_total);

  makePie(
    chartRefs,
    "cashFlowChart",
    ["Basic Living Expense", "Protection", "Estimated Taxes", "Extras"],
    [
      basicLivingExpenses,
      results.total_protection_monthly_cost,
      results.estimated_taxes_monthly,
      results.extras_monthly
    ],
    "Monthly Expenses",
    true,
    ["#ed7d31", "#5b9bd5", "#70ad47", "#c00000"]
  );

  makeAnnualCoverageChart(
    "expenseCoverageChart",
    ["Protected Income", "Basic Expenses", "Difference"],
    [protectedIncomeAnnual, basicExpensesAnnual, coverageDifference],
    "Annual Coverage"
  );

  const totalUnprotected = results.stock_assets + results.bond_assets;

  makePie(
    chartRefs,
    "profileChart",
    ["Stock", "Bond/Alternative"],
    totalUnprotected > 0
      ? [
          (results.stock_assets / totalUnprotected) * 100,
          (results.bond_assets / totalUnprotected) * 100
        ]
      : [0, 0],
    `Investment Profile (${results.profile_label})`,
    true,
    ["#ed7d31", "#ffc000"],
    true
  );

  makeOutcomeRangeChart(
    chartRefs,
    "outcomesChart",
    Number(results.market_mean || 0),
    Number(results.market_range_98_low || 0),
    Number(results.market_range_98_high || 0),
    Number(results.market_range_68_low || 0),
    Number(results.market_range_68_high || 0)
  );

  makePie(
    chartRefs,
    "allocationChart",
    ["Guaranteed Income", "Stock", "Bond/Alternative"],
    [results.protected_assets, results.stock_assets, results.bond_assets],
    "Asset Allocation",
    false,
    ["#5b9bd5", "#ed7d31", "#ffc000"]
  );

  makePie(
    chartRefs,
    "earlyDeathChart",
    ["Assets at Risk", "The Rest"],
    [
      results.assets_at_risk_early_death,
      Math.max(results.investable_assets - results.assets_at_risk_early_death, 0)
    ],
    "Impact of Early Death in Retirement",
    false,
    ["#c00000", "#00b050"]
  );

  makePie(
    chartRefs,
    "ltcChart",
    ["Assets at Risk", "The Rest"],
    [
      results.assets_at_risk_ltc,
      Math.max(results.investable_assets - results.assets_at_risk_ltc, 0)
    ],
    `Impact of ${ltcYears}-Year Long Term Care Stay`,
    false,
    ["#c00000", "#00b050"]
  );

  makePie(
    chartRefs,
    "lawsuitChart",
    ["Net Amount at Risk", "The Rest"],
    [
      results.net_at_risk_lawsuit,
      Math.max(results.investable_assets - results.net_at_risk_lawsuit, 0)
    ],
    `Impact of ${currency(payload.lawsuit_award)} Lawsuit on Investable Assets`,
    false,
    ["#c00000", "#00b050"]
  );

  makePie(
    chartRefs,
    "lawsuitIncomeChart",
    ["Income Vulnerable to Lawsuit", "The Rest"],
    [lawsuitIncomeAtRisk, protectedIncomeRest],
    `Impact of ${currency(payload.lawsuit_award)} on Income`,
    false,
    ["#ed7d31", "#cfcfcf"]
  );

  makeSelfInsuranceChart(
    "selfInsuranceChart",
    Number(results.assets_at_risk_early_death || 0),
    Number(results.assets_at_risk_ltc || 0),
    Number(results.net_at_risk_lawsuit || 0)
  );

  makePie(
    chartRefs,
    "selfInsurancePieChart",
    ["Self-Insurance Need", "Remaining Assets"],
    [
      results.self_insurance_total,
      Math.max(results.investable_assets - results.self_insurance_total, 0)
    ],
    "Self-Insurance as % of Investable Assets",
    true,
    ["#c00000", "#00b050"]
  );
}

async function calculate() {
  const payload = { ...getPayload(), balance_sheet_mode: balanceSheetMode };

  const response = await fetch("/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const text = await response.text();
    alert(`Calculation failed:\n\n${text}`);
    return;
  }

  const results = await response.json();
  lastPayload = payload;
  lastResults = results;
  syncAccordion(payload);
  renderResults(payload, results);

  getEl("entry-screen")?.classList.add("hidden");
  getEl("results-screen")?.classList.remove("hidden");
}

async function recalculateFromAccordion() {
  const payload = { ...pullAccordion(), balance_sheet_mode: balanceSheetMode };

  const response = await fetch("/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const text = await response.text();
    alert(`Recalculation failed:\n\n${text}`);
    return;
  }

  const results = await response.json();
  lastPayload = payload;
  lastResults = results;
  renderResults(payload, results);
}

function getCurrentInputsForExport() {
  const resultsScreen = getEl("results-screen");
  const resultsVisible = resultsScreen && !resultsScreen.classList.contains("hidden");
  const base = resultsVisible ? pullAccordion() : getPayload();
  return { ...base, balance_sheet_mode: balanceSheetMode };
}

function canvasToDataUrl(id) {
  const chart = chartRefs[id];
  if (chart && typeof chart.toBase64Image === "function") {
    try {
      return chart.toBase64Image("image/png", 1.0);
    } catch (e) {
      console.error(`Could not export chart ${id}:`, e);
    }
  }

  const canvas = getEl(id);
  if (!canvas) return null;
  try {
    return canvas.toDataURL("image/png", 1.0);
  } catch (e) {
    console.error(`Could not export canvas ${id}:`, e);
    return null;
  }
}

/** Lay out every tab panel so width/height exist for Chart.js (visibility hidden keeps UI flash-free). */
function prepareChartsForExport() {
  const tabPanels = Array.from(document.querySelectorAll(".tab-content"));
  const previous = tabPanels.map((el) => ({
    el,
    display: el.style.display,
    visibility: el.style.visibility
  }));

  tabPanels.forEach((el) => {
    el.style.display = "block";
    el.style.visibility = "hidden";
  });

  return function restore() {
    previous.forEach(({ el, display, visibility }) => {
      el.style.display = display;
      el.style.visibility = visibility;
    });
  };
}

async function exportPdf() {
  const inputs = getCurrentInputsForExport();
  const restoreTabs = prepareChartsForExport();
  let restorePieSnap = () => {};

  if (lastPayload && lastResults) {
    renderResults(lastPayload, lastResults);
  }

  resizeAllCharts(chartRefs);
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  restorePieSnap = snapPieHostsForExport(resolvePieExportSidePx());
  resizeAllCharts(chartRefs);
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  resizeAllCharts(chartRefs);
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  stopAllChartAnimations(chartRefs);

  const charts = {
    cashflow: canvasToDataUrl("cashFlowChart"),
    coverage: canvasToDataUrl("expenseCoverageChart"),
    profile: canvasToDataUrl("profileChart"),
    allocation: canvasToDataUrl("allocationChart"),
    outcomes: canvasToDataUrl("outcomesChart"),
    early_death: canvasToDataUrl("earlyDeathChart"),
    ltc: canvasToDataUrl("ltcChart"),
    lawsuit: canvasToDataUrl("lawsuitChart"),
    lawsuit_income: canvasToDataUrl("lawsuitIncomeChart"),
    self_insurance: canvasToDataUrl("selfInsuranceChart"),
    self_insurance_pie: canvasToDataUrl("selfInsurancePieChart")
  };

  try {
    const response = await fetch("/export-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        inputs,
        charts,
        tier: "free",
        store_for_upgrade: true,
      }),
    });

    if (!response.ok) {
      const text = await response.text();
      alert(text || "PDF export failed.");
      return;
    }

    const cacheId = response.headers.get("X-Export-Cache-Id");
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "retirement_report.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);

    if (cacheId) {
      sessionStorage.setItem("allocatorExportCacheId", cacheId);
      window.location.href = `/upgrade?cache=${encodeURIComponent(cacheId)}`;
      return;
    }
  } catch (err) {
    console.error(err);
    alert(`PDF export failed:\n\n${err.message}`);
  } finally {
    restorePieSnap();
    restoreTabs();
    if (lastPayload && lastResults) {
      resizeAllCharts(chartRefs);
    }
  }
}

document.addEventListener("DOMContentLoaded", function () {
  renderEntryProfilePreview();
  updateBalanceSheetSelectorUI();
  getEl("entryAdvancedDetails")?.removeAttribute("open");

  getEl("risk_profile")?.addEventListener("change", renderEntryProfilePreview);
  getEl("edit_risk_profile")?.addEventListener("change", syncAccordionRiskPreview);

  getEl("accordion-investment-profile")?.addEventListener("toggle", (event) => {
    if (!event.target.open) return;
    requestAnimationFrame(() => {
      syncAccordionRiskPreview();
      requestAnimationFrame(resizeAccordionProfileCharts);
    });
  });

  [
    "aggressive_equity", "aggressive_mean", "aggressive_stdev",
    "growth_equity", "growth_mean", "growth_stdev",
    "growthIncome_equity", "growthIncome_mean", "growthIncome_stdev",
    "intermediate_equity", "intermediate_mean", "intermediate_stdev"
  ].forEach((id) => {
    getEl(id)?.addEventListener("input", renderEntryProfilePreview);
    getEl(`edit_${id}`)?.addEventListener("input", syncAccordionRiskPreview);
  });
});