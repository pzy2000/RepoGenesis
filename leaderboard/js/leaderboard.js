/**
 * RepoGenesis Leaderboard - Interactive Logic
 *
 * Handles: tab switching, data loading, table rendering,
 * column sorting, filtering, theme toggle, mobile sidebar.
 */

(function () {
  "use strict";

  // ====================================================================
  // State
  // ====================================================================

  let leaderboardData = null;
  let currentTab = "verified_no_docker";
  let sortColumn = "pass_at_1";
  let sortDirection = "desc";
  let filterCategory = "all";
  let filterLanguage = "all";

  // Tab key mapping
  const TAB_KEYS = {
    verified: "verified",
    full: "full",
    verified_no_docker: "verified_no_docker",
  };

  // Tab descriptions
  const TAB_DESCRIPTIONS = {
    verified:
      '<em>Verified</em> evaluates systems on 30 verified repos (22 Python + 8 Java) using the full Docker-based harness with all three metrics: Pass@1, AC, and DSR.',
    full:
      '<em>Full</em> evaluates systems on all 106 repos (60 Python + 46 Java).',
    verified_no_docker:
      '<em>Verified (Without Docker)</em> evaluates systems on 30 verified repos (22 Python + 8 Java) with all three metrics: Pass@1, AC, and DSR, computed without Docker deployment.',
  };

  // Columns per tab
  const TAB_COLUMNS = {
    verified: ["rank", "model", "category", "language", "pass_at_1", "ac", "dsr", "org", "date", "link"],
    full: ["rank", "model", "category", "language", "pass_at_1", "ac", "dsr", "org", "date", "link"],
    verified_no_docker: ["rank", "model", "category", "language", "pass_at_1", "ac", "dsr", "org", "date", "link"],
  };

  // Column display names
  const COLUMN_NAMES = {
    rank: "#",
    model: "Model",
    category: "Category",
    language: "Lang",
    pass_at_1: "Pass@1",
    ac: "AC",
    dsr: "DSR",
    org: "Org",
    date: "Date",
    link: "",
  };

  // Sortable columns
  const SORTABLE = new Set(["pass_at_1", "ac", "dsr", "date", "model"]);

  // ====================================================================
  // Data loading
  // ====================================================================

  async function loadData() {
    try {
      const resp = await fetch("data/results.json");
      leaderboardData = await resp.json();
      renderCurrentTab();
    } catch (err) {
      console.error("Failed to load leaderboard data:", err);
      document.getElementById("leaderboard-container").innerHTML =
        '<p style="color:var(--accent-red);padding:20px;">' +
        'Failed to load leaderboard data. If you opened this file directly, ' +
        'please run <code>python serve.py</code> to start a local server instead.</p>';
    }
  }

  // ====================================================================
  // Filtering
  // ====================================================================

  function getFilteredData() {
    if (!leaderboardData) return [];
    let data = leaderboardData[currentTab] || [];

    if (filterCategory !== "all") {
      data = data.filter((d) => d.category === filterCategory);
    }
    if (filterLanguage !== "all") {
      data = data.filter((d) => d.language === filterLanguage);
    }
    return data;
  }

  // ====================================================================
  // Sorting
  // ====================================================================

  function sortData(data) {
    if (!sortColumn) return data;
    const col = sortColumn;
    const dir = sortDirection === "asc" ? 1 : -1;

    return [...data].sort((a, b) => {
      let va = a[col];
      let vb = b[col];

      // nulls go last
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;

      if (typeof va === "string") {
        return dir * va.localeCompare(vb);
      }
      return dir * (va - vb);
    });
  }

  // ====================================================================
  // Rendering
  // ====================================================================

  function renderCurrentTab() {
    // Update tab buttons
    document.querySelectorAll(".tab-button").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.tab === currentTab);
    });

    // Update description
    const descEl = document.getElementById("tab-description");
    if (descEl) {
      descEl.innerHTML = TAB_DESCRIPTIONS[currentTab] || "";
    }

    // Show/hide DSR-related filter info
    renderTable();
  }

  function renderTable() {
    const container = document.getElementById("leaderboard-container");
    if (!container || !leaderboardData) return;

    const columns = TAB_COLUMNS[currentTab] || TAB_COLUMNS.verified;
    let data = getFilteredData();
    data = sortData(data);

    // Build table
    let html = '<div class="leaderboard-table-wrapper">';
    html += '<table class="leaderboard-table">';

    // Header
    html += "<thead><tr>";
    columns.forEach((col) => {
      const sortable = SORTABLE.has(col);
      let cls = "";
      if (sortable && sortColumn === col) {
        cls = sortDirection === "asc" ? "sorted-asc" : "sorted-desc";
      }
      const sortAttr = sortable ? ` data-sort="${col}"` : "";
      const style = col === "rank" ? ' style="text-align:center;width:40px"' : "";
      html += `<th class="${cls}"${sortAttr}${style}>${COLUMN_NAMES[col] || col}</th>`;
    });
    html += "</tr></thead>";

    // Body
    html += "<tbody>";
    if (data.length === 0) {
      html += `<tr><td colspan="${columns.length}" style="text-align:center;padding:24px;color:var(--text-muted)">No results match the current filters.</td></tr>`;
    } else {
      data.forEach((entry, idx) => {
        html += "<tr>";
        columns.forEach((col) => {
          html += renderCell(col, entry, idx);
        });
        html += "</tr>";
      });
    }
    html += "</tbody></table></div>";

    container.innerHTML = html;

    // Attach sort handlers
    container.querySelectorAll("th[data-sort]").forEach((th) => {
      th.addEventListener("click", function () {
        const col = this.dataset.sort;
        if (sortColumn === col) {
          sortDirection = sortDirection === "asc" ? "desc" : "asc";
        } else {
          sortColumn = col;
          sortDirection = "desc";
        }
        renderTable();
      });
    });
  }

  function renderCell(col, entry, idx) {
    switch (col) {
      case "rank":
        return `<td class="rank-cell">${idx + 1}</td>`;

      case "model":
        return `<td class="model-cell">${escapeHtml(entry.model)}</td>`;

      case "category": {
        const cls =
          entry.category === "Agent"
            ? "badge-agent"
            : entry.category === "IDE"
            ? "badge-ide"
            : "badge-cli";
        return `<td><span class="category-badge ${cls}">${entry.category}</span></td>`;
      }

      case "language": {
        const cls = entry.language === "Python" ? "lang-python" : "lang-java";
        return `<td><span class="lang-badge ${cls}">${entry.language}</span></td>`;
      }

      case "pass_at_1":
      case "ac":
      case "dsr": {
        const val = entry[col];
        if (val == null) {
          return '<td class="metric-na">N/A</td>';
        }
        const cls = val === 0 ? "metric-value zero" : "metric-value";
        return `<td class="${cls}">${val.toFixed(2)}</td>`;
      }

      case "org": {
        const orgName = escapeHtml(entry.org || "");
        const orgImg = entry.org_img ? escapeHtml(entry.org_img) : "";
        if (orgImg) {
          return `<td class="org-cell"><img src="${orgImg}" title="${orgName}" alt="${orgName}" class="org-icon"></td>`;
        }
        return `<td class="org-cell">${orgName}</td>`;
      }

      case "date":
        return `<td>${escapeHtml(entry.date || "")}</td>`;

      case "link":
        if (entry.link) {
          return `<td><a href="${escapeHtml(entry.link)}" target="_blank" rel="noopener" class="link-icon" title="View details"><i class="fas fa-external-link-alt"></i></a></td>`;
        }
        return "<td></td>";

      default:
        return `<td>${escapeHtml(String(entry[col] || ""))}</td>`;
    }
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // ====================================================================
  // Tab switching
  // ====================================================================

  function initTabs() {
    document.querySelectorAll(".tab-button").forEach((btn) => {
      btn.addEventListener("click", function () {
        currentTab = this.dataset.tab;
        sortColumn = null;
        sortDirection = "desc";
        window.location.hash = currentTab;
        renderCurrentTab();
        updateSidebarActive();
      });
    });
  }

  // ====================================================================
  // Hash-based navigation
  // ====================================================================

  const HASH_TO_TAB = {
    "#verified": "verified",
    "#full": "full",
    "#verified_no_docker": "verified_no_docker",
    "#no-docker": "verified_no_docker",
  };

  function initHashNavigation() {
    function applyHash() {
      const hash = window.location.hash;
      if (hash && HASH_TO_TAB[hash]) {
        currentTab = HASH_TO_TAB[hash];
        sortColumn = null;
        sortDirection = "desc";
        renderCurrentTab();
        updateSidebarActive();
      }
    }

    // Apply hash on load
    applyHash();

    // Listen for hash changes (e.g. sidebar link clicks, back/forward)
    window.addEventListener("hashchange", applyHash);
  }

  // ====================================================================
  // Sidebar active state
  // ====================================================================

  function updateSidebarActive() {
    document.querySelectorAll(".sidebar-nav .nav-link").forEach((link) => {
      const href = link.getAttribute("href");
      if (!href || !href.startsWith("#")) return;
      const tabForLink = HASH_TO_TAB[href];
      link.classList.toggle("active", tabForLink === currentTab);
    });
  }

  // ====================================================================
  // Filters
  // ====================================================================

  function initFilters() {
    const catSelect = document.getElementById("filter-category");
    const langSelect = document.getElementById("filter-language");

    if (catSelect) {
      catSelect.addEventListener("change", function () {
        filterCategory = this.value;
        renderTable();
      });
    }

    if (langSelect) {
      langSelect.addEventListener("change", function () {
        filterLanguage = this.value;
        renderTable();
      });
    }
  }

  // ====================================================================
  // Theme toggle
  // ====================================================================

  function initTheme() {
    const stored = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

    if (stored === "light" || (!stored && !prefersDark)) {
      document.documentElement.classList.add("light-mode");
    }

    const toggleBtn = document.getElementById("theme-toggle");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", function () {
        const isLight = document.documentElement.classList.toggle("light-mode");
        localStorage.setItem("theme", isLight ? "light" : "dark");
        updateThemeIcon();
      });
    }

    updateThemeIcon();
  }

  function updateThemeIcon() {
    const icon = document.querySelector("#theme-toggle i");
    if (!icon) return;
    const isLight = document.documentElement.classList.contains("light-mode");
    icon.className = isLight ? "fas fa-sun" : "fas fa-moon";
  }

  // ====================================================================
  // Mobile sidebar toggle
  // ====================================================================

  function initMobileSidebar() {
    const sidebar = document.querySelector(".sidebar");
    const overlay = document.querySelector(".sidebar-overlay");
    const opener = document.querySelector(".sidebar-opener");
    const closer = document.querySelector(".mobile-nav-toggle");

    function openSidebar() {
      if (sidebar) sidebar.classList.add("open");
      if (overlay) overlay.classList.add("open");
    }

    function closeSidebar() {
      if (sidebar) sidebar.classList.remove("open");
      if (overlay) overlay.classList.remove("open");
    }

    if (opener) opener.addEventListener("click", openSidebar);
    if (closer) closer.addEventListener("click", closeSidebar);
    if (overlay) overlay.addEventListener("click", closeSidebar);
  }

  // ====================================================================
  // BibTeX Citation Modal
  // ====================================================================

  function initBibtexModal() {
    const bibtexModal = document.getElementById("bibtex-modal");
    const citationsLink = document.getElementById("citations-link");
    const bibtexClose = document.getElementById("bibtex-modal-close");

    function openBibtex(e) {
      e.preventDefault();
      if (bibtexModal) bibtexModal.classList.add("open");
    }

    function closeBibtex() {
      if (bibtexModal) bibtexModal.classList.remove("open");
    }

    if (citationsLink) citationsLink.addEventListener("click", openBibtex);
    if (bibtexClose) bibtexClose.addEventListener("click", closeBibtex);
    if (bibtexModal) {
      bibtexModal.addEventListener("click", function (e) {
        if (e.target === bibtexModal) closeBibtex();
      });
    }
  }

  // ====================================================================
  // Init
  // ====================================================================

  function init() {
    initTheme();
    initTabs();
    initFilters();
    initMobileSidebar();
    initBibtexModal();
    loadData();
    initHashNavigation();
    updateSidebarActive();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
