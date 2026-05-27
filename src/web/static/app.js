// CurationInsight Dashboard Core Application Script

// Global State
let currentSource = "";
let currentQuery = "";
let currentStartYear = 1929;
let currentEndYear = 2026;
let timelineChart = null;
let mediumChart = null;
let networkChart = null;

// i18n Global State
let appLanguage = 'zh';
let bilingualEnabled = false;
let currentBilingualMode = "cn-top";
let activeExhibitionData = null;
let i18nReady = false;

// Security: HTML entity encoder to prevent XSS from database fields
function escapeHtml(text) {
  if (text == null) return "";
  const div = document.createElement("div");
  div.textContent = String(text);
  return div.innerHTML;
}

// Initialize i18next
function initI18n() {
  return new Promise((resolve) => {
    i18next
      .use(i18nextHttpBackend)
      .use(i18nextBrowserLanguageDetector)
      .init({
        fallbackLng: 'zh',
        debug: false,
        backend: {
          loadPath: '/static/locales/{{lng}}/translation.json'
        },
        detection: {
          order: ['localStorage', 'navigator'],
          caches: ['localStorage'],
          lookupLocalStorage: 'i18nextLng'
        }
      }, (err, t) => {
        if (err) console.error('i18next init error:', err);
        appLanguage = i18next.language || 'zh';
        // Load bilingual preference
        const savedBilingual = localStorage.getItem('bilingualEnabled');
        if (savedBilingual !== null) {
          bilingualEnabled = savedBilingual === 'true';
        }
        i18nReady = true;
        resolve();
      });
  });
}

// Update all DOM elements with data-i18n attributes
function updateStaticTexts() {
  if (!i18nReady) return;

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    // Support attribute bindings like [placeholder]key
    if (key.startsWith('[')) {
      const match = key.match(/\[(.+?)\](.+)/);
      if (match) {
        const attr = match[1];
        const realKey = match[2];
        el.setAttribute(attr, i18next.t(realKey));
      }
    } else {
      el.textContent = i18next.t(key);
    }
  });

  // Update HTML lang attribute
  document.documentElement.lang = appLanguage === 'zh' ? 'zh-CN' : 'en';
}

function setLanguage(lng) {
  if (!i18nReady || lng === appLanguage) return;

  i18next.changeLanguage(lng, (err) => {
    if (err) {
      console.error('Language change failed:', err);
      return;
    }
    appLanguage = lng;
    updateStaticTexts();
    updateSettingsUI();

    // If bilingual is on, sync priority to match new language
    if (bilingualEnabled) {
      currentBilingualMode = (appLanguage === 'zh') ? 'cn-top' : 'en-top';
      updateBilingualSliderUI();
      if (activeExhibitionData) renderBilingualTexts();
    }

    // Refresh dynamic content
    loadExhibitionsGallery();
  });
}

function toggleBilingual() {
  bilingualEnabled = !bilingualEnabled;
  localStorage.setItem('bilingualEnabled', bilingualEnabled.toString());
  updateSettingsUI();

  // Sync priority when turning on
  if (bilingualEnabled) {
    currentBilingualMode = (appLanguage === 'zh') ? 'cn-top' : 'en-top';
  }

  if (activeExhibitionData) {
    renderBilingualTexts();
    updateBilingualSliderUI();
  }
}

function updateSettingsUI() {
  const zhBtn = document.getElementById('lang-zh-btn');
  const enBtn = document.getElementById('lang-en-btn');
  const toggleBtn = document.getElementById('bilingual-toggle-btn');
  const statusText = document.getElementById('bilingual-status-text');

  if (zhBtn) {
    zhBtn.classList.toggle('active', appLanguage === 'zh');
    zhBtn.classList.toggle('text-slate-400', appLanguage !== 'zh');
  }
  if (enBtn) {
    enBtn.classList.toggle('active', appLanguage === 'en');
    enBtn.classList.toggle('text-slate-400', appLanguage !== 'en');
  }
  if (toggleBtn) {
    toggleBtn.classList.toggle('active', bilingualEnabled);
  }
  if (statusText) {
    statusText.textContent = bilingualEnabled ? '开启' : '关闭';
  }
}

// Initialize when DOM loaded
document.addEventListener("DOMContentLoaded", async () => {
  // Initialize i18next first
  await initI18n();

  // Update all static UI texts
  updateStaticTexts();
  updateSettingsUI();

  // Initialize Lucide Icons
  lucide.createIcons();

  // Setup Event Listeners
  setupEventListeners();

  // Fetch initial dashboard stats & build dynamic filters
  fetchStatsAndSetupFilters();

  // Fetch & Draw charts (staggered init: network chart deferred to reduce main-thread jank)
  loadTimelineChart();
  setTimeout(() => loadNetworkChart(), 250);

  // Load exhibitions gallery
  loadExhibitionsGallery();
});

// Setup Control Event Listeners
function setupEventListeners() {
  // Search Input with Debounce
  const searchInput = document.getElementById("search-input");
  let searchDebounceTimeout;
  searchInput.addEventListener("input", (e) => {
    clearTimeout(searchDebounceTimeout);
    searchDebounceTimeout = setTimeout(() => {
      currentQuery = e.target.value.trim();
      loadExhibitionsGallery();
    }, 400); // 400ms debounce
  });

  // Year Sliders
  const startSlider = document.getElementById("start-year");
  const endSlider = document.getElementById("end-year");
  const yearDisplay = document.getElementById("year-range-display");

  const handleYearChange = () => {
    let startVal = parseInt(startSlider.value);
    let endVal = parseInt(endSlider.value);
    
    // Ensure bounds validity
    if (startVal > endVal) {
      // Swapping values dynamically for premium UX
      const temp = startVal;
      startVal = endVal;
      endVal = temp;
    }
    
    currentStartYear = startVal;
    currentEndYear = endVal;
    yearDisplay.textContent = `${currentStartYear} - ${currentEndYear}`;
  };

  startSlider.addEventListener("input", handleYearChange);
  endSlider.addEventListener("input", handleYearChange);
  
  // Refetch when slider release (change event) to prevent API spamming
  startSlider.addEventListener("change", loadExhibitionsGallery);
  endSlider.addEventListener("change", loadExhibitionsGallery);

  // Close Modal Button
  document.getElementById("close-modal-btn").addEventListener("click", hideExhibitionModal);
  
  // Bilingual Priority Toggle listener
  const toggleBtn = document.getElementById("bilingual-toggle");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      currentBilingualMode = (currentBilingualMode === "cn-top") ? "en-top" : "cn-top";
      updateBilingualSliderUI();
      renderBilingualTexts();
    });
  }
  
  // Close Modal on clicking outside
  document.getElementById("detail-modal").addEventListener("click", (e) => {
    if (e.target === document.getElementById("detail-modal")) {
      hideExhibitionModal();
    }
  });

  // Respond to window resize with debounce to avoid thrashing charts
  let resizeDebounce;
  window.addEventListener("resize", () => {
    clearTimeout(resizeDebounce);
    resizeDebounce = setTimeout(() => {
      if (timelineChart) timelineChart.resize();
      if (mediumChart) mediumChart.resize();
      if (networkChart) networkChart.resize();
    }, 150);
  });
}

// Fetch stats to populate micro counters and dynamic filter buttons
async function fetchStatsAndSetupFilters() {
  try {
    const res = await fetch("/api/stats");
    if (!res.ok) throw new Error("Stats API failed");
    const data = await res.json();
    
    // 1. Update counter DOMs
    animateCounter("metric-exhibitions", data.total_exhibitions);
    animateCounter("metric-artworks", data.total_artworks);
    animateCounter("metric-museums", data.museum_stats.length);
    
    // 2. Generate Museum Filter buttons
    const filterContainer = document.getElementById("museum-filters");
    
    // Keep 'All' button, clear others
    const allBtn = filterContainer.querySelector("button");
    filterContainer.innerHTML = "";
    filterContainer.appendChild(allBtn);
    
    allBtn.onclick = () => selectMuseum("", allBtn);
    
    data.museum_stats.forEach(mus => {
      const btn = document.createElement("button");
      btn.className = "px-3 py-1.5 text-xs glass-btn";
      btn.textContent = `${mus.source} (${mus.count})`;
      btn.setAttribute("data-source", mus.source);
      btn.onclick = () => selectMuseum(mus.source, btn);
      filterContainer.appendChild(btn);
    });

    // 3. Render Medium Chart with the data
    renderMediumChart(data.medium_stats);
    
  } catch (err) {
    console.error("Error setting stats:", err);
  }
}

// Select Museum filter
function selectMuseum(source, activeBtn) {
  currentSource = source;
  
  // Toggle active CSS classes
  const filterBtns = document.querySelectorAll("#museum-filters button");
  filterBtns.forEach(btn => btn.classList.remove("active"));
  activeBtn.classList.add("active");
  
  // Highlight river timeline chart if exists
  if (timelineChart) {
    timelineChart.dispatchAction({
      type: 'highlight',
      seriesName: source || []
    });
  }
  
  // Reload Gallery list
  loadExhibitionsGallery();
}

// Counter numbers rolling up animation
function animateCounter(id, targetVal) {
  const el = document.getElementById(id);
  if (!el) return;
  
  let currentVal = 0;
  const duration = 1200; // ms
  const stepTime = 16; // ~60fps
  const steps = duration / stepTime;
  const increment = targetVal / steps;
  
  const timer = setInterval(() => {
    currentVal += increment;
    if (currentVal >= targetVal) {
      clearInterval(timer);
      el.textContent = targetVal.toLocaleString();
    } else {
      el.textContent = Math.floor(currentVal).toLocaleString();
    }
  }, stepTime);
}

// Fetch and draw ECharts Chronology River timeline
async function loadTimelineChart() {
  const dom = document.getElementById("timeline-chart");
  timelineChart = echarts.init(dom);
  
  // Show skeleton loading
  timelineChart.showLoading({
    text: i18nReady ? i18next.t('gallery.count_loading') : "策展河流加载中...",
    color: "#e2b755",
    textColor: "#a0aec0",
    maskColor: "rgba(8, 9, 13, 0.45)"
  });
  
  try {
    const res = await fetch("/api/timeline");
    const data = await res.json();
    timelineChart.hideLoading();
    
    const colors = ["#e2b755", "#5ef3e8", "#c8a2c8", "#5f9ea0", "#ff7f50", "#4682b4", "#b0c4de"];
    const series = data.museums.map((mus, idx) => {
      return {
        name: mus,
        type: "line",
        stack: "Total",
        smooth: true,
        lineStyle: { width: 1.5, color: colors[idx % colors.length] },
        showSymbol: false,
        areaStyle: {
          opacity: 0.15,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: colors[idx % colors.length] },
            { offset: 1, color: "rgba(8,9,13,0)" }
          ])
        },
        emphasis: { focus: "series" },
        data: data.series[mus]
      };
    });
    
    const option = {
      color: colors,
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(16, 20, 30, 0.95)",
        borderColor: "rgba(255, 255, 255, 0.1)",
        textStyle: { color: "#f0f2f5", fontSize: 11, fontFamily: "Inter" },
        axisPointer: { type: "line", lineStyle: { color: "rgba(226,183,85,0.4)" } }
      },
      legend: {
        textStyle: { color: "#a0aec0", fontSize: 10, fontFamily: "Space Grotesk" },
        itemWidth: 10,
        itemHeight: 10,
        bottom: 0
      },
      grid: { top: "8%", left: "4%", right: "4%", bottom: "16%", containLabel: true },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: data.years,
        axisLine: { lineStyle: { color: "rgba(255,255,255,0.12)" } },
        axisLabel: { color: "#a0aec0", fontSize: 9, fontFamily: "Space Grotesk" }
      },
      yAxis: {
        type: "value",
        splitLine: { lineStyle: { color: "rgba(255,255,255,0.04)" } },
        axisLine: { show: false },
        axisLabel: { color: "#a0aec0", fontSize: 9, fontFamily: "Space Grotesk" }
      },
      dataZoom: [
        {
          type: "inside",
          start: 0,
          end: 100
        },
        {
          type: "slider",
          height: 12,
          bottom: 25,
          borderColor: "rgba(255,255,255,0.05)",
          handleSize: "100%",
          textStyle: { color: "#a0aec0", fontSize: 8 },
          start: 0,
          end: 100
        }
      ],
      series: series
    };
    
    timelineChart.setOption(option);
    
    // Add Click listener to link with Gallery year filter
    timelineChart.on("click", (params) => {
      if (params.name) {
        const year = parseInt(params.name);
        document.getElementById("start-year").value = year - 1;
        document.getElementById("end-year").value = year + 1;
        currentStartYear = year - 1;
        currentEndYear = year + 1;
        document.getElementById("year-range-display").textContent = `${currentStartYear} - ${currentEndYear}`;
        loadExhibitionsGallery();
      }
    });
    
  } catch (err) {
    console.error("Timeline chart error:", err);
  }
}

// Render Medium Circular/Pie Distribution chart
function renderMediumChart(data) {
  const dom = document.getElementById("medium-chart");
  mediumChart = echarts.init(dom);
  
  const chartData = data.map(item => {
    // Shorten overly descriptive mediums for pristine readability
    let name = item.medium;
    if (name.length > 25) name = name.substring(0, 22) + "...";
    return { name: name, value: item.count };
  });
  
  const option = {
    tooltip: {
      trigger: "item",
      formatter: "{b} : {c}件 ({d}%)",
      backgroundColor: "rgba(16, 20, 30, 0.95)",
      borderColor: "rgba(255, 255, 255, 0.1)",
      textStyle: { color: "#f0f2f5", fontSize: 11, fontFamily: "Inter" }
    },
    series: [
      {
        name: "Art Mediums",
        type: "pie",
        radius: ["35%", "75%"],
        center: ["50%", "50%"],
        roseType: "area",
        itemStyle: {
          borderRadius: 6,
          borderColor: "rgba(8, 9, 13, 0.8)",
          borderWidth: 1.5
        },
        label: {
          show: true,
          color: "#a0aec0",
          fontSize: 8,
          fontFamily: "Inter",
          formatter: "{b}"
        },
        labelLine: {
          length: 6,
          length2: 4,
          lineStyle: { color: "rgba(255,255,255,0.15)" }
        },
        data: chartData
      }
    ]
  };
  
  mediumChart.setOption(option);
  
  // Hook up click interaction: click medium to trigger keyword search!
  mediumChart.on("click", (params) => {
    if (params.name) {
      const cleanMedium = params.name.replace("...", "");
      document.getElementById("search-input").value = cleanMedium;
      currentQuery = cleanMedium;
      loadExhibitionsGallery();
    }
  });
}

// Load and render Artist Stars Force Graph
async function loadNetworkChart() {
  const dom = document.getElementById("network-chart");
  networkChart = echarts.init(dom);
  
  networkChart.showLoading({
    text: i18nReady ? i18next.t('gallery.count_loading') : "引力星云运转中...",
    color: "#5ef3e8",
    textColor: "#a0aec0",
    maskColor: "rgba(8, 9, 13, 0.45)"
  });
  
  try {
    const res = await fetch("/api/network?limit_artists=80&min_cooccurrence=2");
    const data = await res.json();
    networkChart.hideLoading();
    
    // 视觉映射：节点大小 & 颜色按作品数分档，让核心艺术家一眼可辨
    const maxWorks = Math.max(...data.nodes.map(n => n.value));
    const minWorks = Math.min(...data.nodes.map(n => n.value));

    data.nodes.forEach(node => {
      const normalized = maxWorks === minWorks ? 0.5 : (node.value - minWorks) / (maxWorks - minWorks);
      node.symbolSize = 8 + normalized * 36; // 8px ~ 44px

      let color, borderColor, shadowBlur;
      if (node.value >= 30) {
        color = '#e2b755';
        borderColor = '#fcd34d';
        shadowBlur = 20;
      } else if (node.value >= 15) {
        color = '#d97706';
        borderColor = '#e2b755';
        shadowBlur = 10;
      } else if (node.value >= 8) {
        color = '#0d9488';
        borderColor = '#5eead4';
        shadowBlur = 5;
      } else {
        color = '#334155';
        borderColor = '#475569';
        shadowBlur = 0;
      }

      node.itemStyle = {
        color: color,
        borderColor: borderColor,
        borderWidth: node.value >= 15 ? 2.5 : 1,
        shadowBlur: shadowBlur,
        shadowColor: color
      };
    });

    // 动态映射共同参展频次，连线粗细、颜色、发光随合作强度渐变
    data.links.forEach(link => {
      let color, width, shadowBlur, shadowColor;

      if (link.value >= 5) {
        color = "rgba(226, 183, 85, 0.65)";
        width = 3.5;
        shadowBlur = 10;
        shadowColor = "rgba(226, 183, 85, 0.4)";
      } else if (link.value === 4) {
        color = "rgba(226, 183, 85, 0.35)";
        width = 2.5;
        shadowBlur = 0;
      } else if (link.value === 3) {
        color = "rgba(94, 243, 232, 0.25)";
        width = 1.8;
        shadowBlur = 0;
      } else {
        color = "rgba(255, 255, 255, 0.04)";
        width = 1.0;
        shadowBlur = 0;
      }

      link.lineStyle = {
        width: width,
        color: color,
        curveness: 0.2,
        shadowBlur: shadowBlur,
        shadowColor: shadowColor
      };
    });

    
    const option = {
      tooltip: {
        trigger: "item",
        formatter: (params) => {
          if (params.dataType === "node") {
            return `🌟 ${i18nReady ? i18next.t('modal.table_artist') : '艺术家'}: <strong class="text-amber-400">${params.data.name}</strong><br/>${i18nReady ? i18next.t('modal.artwork_count', {count: params.data.value}) : '展览收录作品数: ' + params.data.value + ' 件'}`;
          } else {
            return `🔗 ${i18nReady ? i18next.t('chart.network_legend') : '共同参展关联:'}<br/>${params.data.source} ✖ ${params.data.target}<br/>${i18nReady ? i18next.t('chart.network_legend_edge').replace('。', '') : '共同出场次数'}: <strong class="text-cyan-400">${params.data.value}</strong> ${i18nReady ? i18next.t('gallery.card_artworks', {count: ''}).replace('{{count}}', '').trim() || '次' : '次'}`;
          }
        },
        backgroundColor: "rgba(16, 20, 30, 0.95)",
        borderColor: "rgba(255, 255, 255, 0.1)",
        textStyle: { color: "#f0f2f5", fontSize: 11, fontFamily: "Inter" }
      },
      series: [
        {
          name: "Artist Network",
          type: "graph",
          layout: "force",
          data: data.nodes,
          links: data.links,
          roam: true,
          label: {
            show: true,
            position: "right",
            formatter: (params) => {
              // 作品数 > 8 即显示名字，让更多艺术家可被识别
              return params.data.value > 8 ? params.name : "";
            },
            color: (params) => params.data.value >= 20 ? "#ffffff" : "#94a3b8",
            fontSize: (params) => params.data.value >= 20 ? 11 : 9,
            fontWeight: (params) => params.data.value >= 20 ? "bold" : "normal",
            fontFamily: "Space Grotesk"
          },
          labelLayout: {
            hideOverlap: true
          },
          force: {
            repulsion: 300,
            gravity: 0.03,
            edgeLength: [60, 150],
            layoutAnimation: false
          },

          lineStyle: {
            color: "rgba(255, 255, 255, 0.05)",
            width: 0.8,
            curveness: 0.16
          },
          emphasis: {
            focus: "adjacency",
            lineStyle: {
              width: 4.0,
              color: "#5ef3e8",
              shadowColor: "rgba(94, 243, 232, 0.6)",
              shadowBlur: 12
            },

            label: {
              show: true,
              color: "#ffffff",
              fontSize: 12,
              fontWeight: "bold"
            }
          }
        }
      ]
    };
    
    networkChart.setOption(option);
    
    // Hook double click: filter by artist in search box
    networkChart.on("click", (params) => {
      if (params.dataType === "node" && params.data.name) {
        const artist = params.data.name;
        document.getElementById("search-input").value = artist;
        currentQuery = artist;
        loadExhibitionsGallery();
      }
    });
    
  } catch (err) {
    console.error("Network graph error:", err);
  }
}

// Load and construct structural cards gallery grid
async function loadExhibitionsGallery() {
  const grid = document.getElementById("gallery-grid");
  const countDisplay = document.getElementById("gallery-count");
  const loader = document.getElementById("loading-overlay");
  
  loader.classList.remove("hidden");
  
  try {
    let url = `/api/exhibitions?limit=40&offset=0`;
    if (currentSource) url += `&source=${encodeURIComponent(currentSource)}`;
    if (currentQuery) url += `&query=${encodeURIComponent(currentQuery)}`;
    if (currentStartYear) url += `&start_year=${currentStartYear}`;
    if (currentEndYear) url += `&end_year=${currentEndYear}`;
    
    const res = await fetch(url);
    if (!res.ok) throw new Error("Gallery fetch failed");
    const result = await res.json();
    
    grid.innerHTML = "";
    loader.classList.add("hidden");
    
    countDisplay.textContent = i18nReady
      ? i18next.t('gallery.count_result', {count: result.total})
      : `匹配到 ${result.total} 个展览`;
    
    if (result.data.length === 0) {
      grid.innerHTML = `
        <div class="col-span-full py-16 flex flex-col items-center justify-center text-slate-500 border border-dashed border-slate-800 rounded-2xl bg-slate-900/10">
          <i data-lucide="info" class="w-8 h-8 text-amber-500/50 mb-2"></i>
          <span class="text-xs" data-i18n="gallery.empty_title">在当前筛选条件下，未捕获任何当代艺术展览</span>
        </div>
      `;
      lucide.createIcons();
      return;
    }
    
    result.data.forEach(ex => {
      // Setup timeline label text
      let dateText = ex.start_date || (i18nReady ? i18next.t('gallery.card_date_unknown') : "未知日期");
      if (ex.end_date) dateText += ` ~ ${ex.end_date}`;

      const curators = (ex.curators && ex.curators.length > 0)
        ? ex.curators.join(", ")
        : (i18nReady ? i18next.t('modal.curators_default') : "馆方学术委员会 / 独立策展人");
        
      const card = document.createElement("div");
      card.className = "ex_card glass-panel p-4 flex flex-col justify-between gap-3 border border-slate-800/80 bg-slate-900/30";
      card.onclick = () => showExhibitionModal(ex.id);
      
      // Prepare tags markup
      let tagsHtml = "";
      let parsedTags = [];
      try {
        if (ex.tags) {
          parsedTags = typeof ex.tags === "string" ? JSON.parse(ex.tags) : ex.tags;
        }
      } catch (err) {
        parsedTags = [];
      }
      if (Array.isArray(parsedTags) && parsedTags.length > 0) {
        tagsHtml = `
          <div class="flex flex-wrap gap-1 mt-0.5">
            ${parsedTags.map(t => `<span class="px-1.5 py-0.2 rounded text-[7.5px] font-medium tracking-wide uppercase font-space bg-slate-800/80 border border-slate-700/40 text-slate-300">${escapeHtml(t)}</span>`).join('')}
          </div>
        `;
      }
      
      card.innerHTML = `
        <div class="flex flex-col gap-1.5">
          <div class="flex items-center justify-between gap-2">
            <span class="px-2 py-0.5 rounded text-[9px] font-bold tracking-wider uppercase font-space bg-amber-500/10 border border-amber-500/20 text-amber-400">
              ${escapeHtml(ex.source)}
            </span>
            <span class="text-[10px] text-slate-500 flex items-center gap-1 font-space">
              <i data-lucide="map-pin" class="w-3.5 h-3.5 text-amber-500/50"></i> ${escapeHtml(ex.city) || (i18nReady ? i18next.t('gallery.card_city_global') : "全球")}
            </span>
          </div>

          ${tagsHtml}

          <h3 class="text-sm font-semibold text-slate-100 font-cinzel line-clamp-2 tracking-wide leading-snug group-hover:text-amber-400 mt-1">
            ${escapeHtml(ex.title)}
          </h3>

          <div class="text-[10px] text-slate-400 font-light flex items-center gap-1 leading-relaxed mt-1">
            <i data-lucide="user" class="w-3 h-3 text-amber-500/40"></i> ${i18nReady ? i18next.t('gallery.card_curators', {curators: escapeHtml(curators)}) : `策展: ${escapeHtml(curators)}`}
          </div>
        </div>

        <div class="flex justify-between items-center border-t border-slate-900/60 pt-2 text-[10px] text-slate-500 font-space mt-1">
          <span class="flex items-center gap-1">
            <i data-lucide="calendar" class="w-3.5 h-3.5 text-slate-600"></i> ${escapeHtml(dateText)}
          </span>
          <span class="px-2 py-0.5 rounded bg-cyan-950/40 text-cyan-400 font-bold border border-cyan-950">
            ${i18nReady ? i18next.t('gallery.card_artworks', {count: ex.artwork_count}) : `${escapeHtml(ex.artwork_count)} 件作品`}
          </span>
        </div>
      `;
      
      grid.appendChild(card);
    });
    
    // Regenerate icons inside dynamically appended elements
    lucide.createIcons();
    
  } catch (err) {
    console.error("Gallery loading failed:", err);
    loader.classList.add("hidden");
  }
}

// Exhibition detail Popup window
async function showExhibitionModal(id) {
  const modal = document.getElementById("detail-modal");
  
  // Show base modal backdrop
  modal.classList.remove("hidden");
  setTimeout(() => modal.classList.add("opacity-100"), 10);
  
  // Query Detail API
  try {
    const res = await fetch(`/api/exhibitions/${id}`);
    const ex = await res.json();
    
    // Cache for instant bilingual priority toggle
    activeExhibitionData = ex;
    currentBilingualMode = (appLanguage === 'zh') ? 'cn-top' : 'en-top';
    updateBilingualSliderUI();
    
    // Render Modal metadata
    document.getElementById("modal-source").textContent = ex.source;
    document.getElementById("modal-title").textContent = ex.title;
    
    let dateText = ex.start_date || (i18nReady ? i18next.t('common.unknown') : "未知");
    if (ex.end_date) dateText += (i18nReady ? i18next.t('modal.date_separator') : " 至 ") + ex.end_date;
    document.getElementById("modal-date").textContent = dateText;

    const modalCity = document.getElementById("modal-city");
    modalCity.innerHTML = `<i data-lucide="map-pin" class="w-3.5 h-3.5 text-amber-500"></i> `;
    modalCity.appendChild(document.createTextNode(`${escapeHtml(ex.city) || (i18nReady ? i18next.t('common.unknown') : "美术馆展厅")} (${escapeHtml(ex.location) || (i18nReady ? i18next.t('common.unknown') : "展厅展位")})`));

    const curators = (ex.curators && ex.curators.length > 0)
      ? ex.curators.join(", ")
      : (i18nReady ? i18next.t('modal.curators_default') : "联合策划 / 特邀学者");
    document.getElementById("modal-curators").textContent = curators;

    document.getElementById("modal-art-count").textContent = i18nReady
      ? i18next.t('modal.artwork_count', {count: ex.artworks.length})
      : `${ex.artworks.length} 件`;

    // Render Modal tags
    const modalTags = document.getElementById("modal-tags");
    if (modalTags) {
      modalTags.innerHTML = "";
      let parsedTags = [];
      try {
        if (ex.tags) {
          parsedTags = typeof ex.tags === "string" ? JSON.parse(ex.tags) : ex.tags;
        }
      } catch (err) {
        parsedTags = [];
      }
      if (Array.isArray(parsedTags) && parsedTags.length > 0) {
        parsedTags.forEach(t => {
          const pill = document.createElement("span");
          pill.className = "px-2 py-0.5 rounded-full text-[9px] font-semibold tracking-wide uppercase font-space bg-cyan-950/40 text-cyan-400 border border-cyan-800/40";
          pill.textContent = t;
          modalTags.appendChild(pill);
        });
      }
    }
    
    // Render images gallery if available (saves disk & tokens, directly links remote urls)
    const imgContainer = document.getElementById("modal-images-container");
    const imgList = document.getElementById("modal-images-list");
    if (imgContainer && imgList) {
      imgList.innerHTML = "";
      let image_urls = [];
      try {
        if (ex.images) {
          image_urls = typeof ex.images === "string" ? JSON.parse(ex.images) : ex.images;
        }
      } catch (err) {
        image_urls = [];
      }
      
      if (image_urls && image_urls.length > 0) {
        imgContainer.classList.remove("hidden");
        image_urls.forEach(imgUrl => {
          const img = document.createElement("img");
          img.src = imgUrl;
          img.className = "h-36 rounded-xl border border-slate-800/80 snap-start object-cover hover:scale-[1.03] transition-transform duration-300 cursor-pointer shadow-md bg-slate-900/50";
          img.alt = "Exhibition Install Shot";
          // Click to open high-res remote image directly in new tab
          img.addEventListener("click", () => {
            window.open(imgUrl, "_blank");
          });
          imgList.appendChild(img);
        });
      } else {
        imgContainer.classList.add("hidden");
      }
    }
    
    // Details texts - Render stacked CN/EN bilingual texts
    renderBilingualTexts();
    
    // Action link
    const urlBtn = document.getElementById("modal-url");
    if (ex.url) {
      urlBtn.href = ex.url;
      urlBtn.classList.remove("hidden");
    } else {
      urlBtn.classList.add("hidden");
    }
    
    // Render artworks subtable
    const tbody = document.getElementById("modal-artworks-tbody");
    tbody.innerHTML = "";
    
    if (ex.artworks.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="py-8 text-center text-slate-500 italic" data-i18n="modal.artworks_empty">该展览暂未关联具体代表作品数据 (由爬虫采集补充中)</td>
        </tr>
      `;
    } else {
      ex.artworks.forEach(art => {
        const tr = document.createElement("tr");
        tr.className = "hover:bg-slate-900/60 transition-colors";
        tr.innerHTML = `
          <td class="py-2 px-3 font-semibold text-amber-400/90">${escapeHtml(art.artist_name) || (i18nReady ? i18next.t('modal.artist_unknown') : "未知艺术家")}</td>
          <td class="py-2 px-3 italic font-medium text-slate-100">${escapeHtml(art.work_title) || (i18nReady ? i18next.t('modal.work_untitled') : "无题")}</td>
          <td class="py-2 px-3 font-space text-[10px]">${escapeHtml(art.work_year) || (i18nReady ? i18next.t('modal.year_unknown') : "未标注")}</td>
          <td class="py-2 px-3 text-slate-400 font-light text-[11px]">${escapeHtml(art.medium) || (i18nReady ? i18next.t('modal.medium_unknown') : "-")}</td>
          <td class="py-2 px-3 text-slate-400 font-light font-space text-[10px]">${escapeHtml(art.dimensions) || (i18nReady ? i18next.t('modal.dimensions_unknown') : "-")}</td>
        `;
        tbody.appendChild(tr);
      });
    }
    
    lucide.createIcons();
    
  } catch (err) {
    console.error("Modal detail load failed:", err);
  }
}

// Hide Modal
function hideExhibitionModal() {
  const modal = document.getElementById("detail-modal");
  modal.classList.remove("opacity-100");
  setTimeout(() => modal.classList.add("hidden"), 300);
}

// Updates the bilingual slider toggle switch visuals
function updateBilingualSliderUI() {
  const toggleContainer = document.getElementById("bilingual-toggle");
  const slider = document.getElementById("bilingual-slider");
  const btnCn = document.getElementById("btn-cn-top");
  const btnEn = document.getElementById("btn-en-top");

  // Hide/show entire bilingual toggle bar
  if (toggleContainer && toggleContainer.parentElement) {
    toggleContainer.parentElement.style.display = bilingualEnabled ? 'flex' : 'none';
  }

  if (!bilingualEnabled || !slider) return;

  if (currentBilingualMode === "cn-top") {
    slider.style.left = "2.5px";
    btnCn.className = "flex-1 py-1 text-center z-10 transition-colors duration-300 text-slate-100 font-bold";
    btnEn.className = "flex-1 py-1 text-center z-10 transition-colors duration-300 text-slate-400 font-normal";
  } else {
    slider.style.left = "calc(50% + 2px)";
    btnCn.className = "flex-1 py-1 text-center z-10 transition-colors duration-300 text-slate-400 font-normal";
    btnEn.className = "flex-1 py-1 text-center z-10 transition-colors duration-300 text-slate-100 font-bold";
  }
}

// Renders the cached exhibition details bilingual text fields based on current priority mode
function renderBilingualTexts() {
  if (!activeExhibitionData) return;

  const ex = activeExhibitionData;

  // Helper: get localized text with fallback
  const getText = (primaryKey, fallbackKey, primaryValue, fallbackValue) => {
    const hasPrimary = primaryValue && primaryValue.trim();
    const hasFallback = fallbackValue && fallbackValue.trim();

    if (hasPrimary) return primaryValue;
    if (hasFallback) {
      const hint = i18nReady ? i18next.t('modal.fallback_hint', {lang: primaryKey === 'zh' ? '中文' : 'English'}) : '[原文仅中文可用] ';
      return hint + fallbackValue;
    }
    return i18nReady ? i18next.t(fallbackKey) : (primaryKey === 'zh' ? '该展览未提供独立前言文本或正在解析中。' : 'The raw English preface is not available for this record.');
  };

  const pUpper = document.getElementById("preface-upper-block");
  const pLower = document.getElementById("preface-lower-block");
  const cUpper = document.getElementById("concept-upper-block");
  const cLower = document.getElementById("concept-lower-block");

  const bioSection = document.getElementById("modal-biographies-section");
  const creditsSection = document.getElementById("modal-credits-section");
  const bUpper = document.getElementById("biographies-upper-block");
  const bLower = document.getElementById("biographies-lower-block");
  const bSeparator = document.getElementById("biographies-separator");
  const creditsContent = document.getElementById("credits-content");

  // Find separators via parent children index
  const pStack = document.getElementById("preface-stack");
  const cStack = document.getElementById("concept-stack");
  const pSeparator = pStack ? pStack.children[1] : null;
  const cSeparator = cStack ? cStack.children[1] : null;

  // Apply smooth fade transitions
  const applyFade = (el, text) => {
    if (!el) return;
    el.style.opacity = "0.2";
    setTimeout(() => {
      el.textContent = text;
      el.style.opacity = "1";
    }, 100);
  };

  if (bilingualEnabled) {
    // BILINGUAL MODE: show both blocks
    if (pLower) pLower.style.display = 'block';
    if (pSeparator) pSeparator.style.display = 'block';
    if (cLower) cLower.style.display = 'block';
    if (cSeparator) cSeparator.style.display = 'block';

    const cnPreface = getText('zh', 'modal.preface_missing_cn', ex.preface, ex.preface_en);
    const enPreface = getText('en', 'modal.preface_missing_en', ex.preface_en, ex.preface);
    const cnConcept = getText('zh', 'modal.concept_missing_cn', ex.concept, ex.concept_en);
    const enConcept = getText('en', 'modal.concept_missing_en', ex.concept_en, ex.concept);

    if (currentBilingualMode === "cn-top") {
      applyFade(pUpper, cnPreface);
      applyFade(pLower, enPreface);
      applyFade(cUpper, cnConcept);
      applyFade(cLower, enConcept);
    } else {
      applyFade(pUpper, enPreface);
      applyFade(pLower, cnPreface);
      applyFade(cUpper, enConcept);
      applyFade(cLower, cnConcept);
    }
  } else {
    // MONOLINGUAL MODE: hide lower blocks and separators
    if (pLower) pLower.style.display = 'none';
    if (pSeparator) pSeparator.style.display = 'none';
    if (cLower) cLower.style.display = 'none';
    if (cSeparator) cSeparator.style.display = 'none';

    const preface = appLanguage === 'zh'
      ? getText('zh', 'modal.preface_missing_cn', ex.preface, ex.preface_en)
      : getText('en', 'modal.preface_missing_en', ex.preface_en, ex.preface);
    const concept = appLanguage === 'zh'
      ? getText('zh', 'modal.concept_missing_cn', ex.concept, ex.concept_en)
      : getText('en', 'modal.concept_missing_en', ex.concept_en, ex.concept);

    applyFade(pUpper, preface);
    applyFade(cUpper, concept);
  }

  // 2. Biographies Section rendering
  const hasBio = (ex.biographies && ex.biographies.trim()) || (ex.biographies_cn && ex.biographies_cn.trim());
  if (hasBio) {
    if (bioSection) bioSection.classList.remove("hidden");

    if (bilingualEnabled) {
      if (bSeparator) bSeparator.style.display = "block";
      if (bUpper) bUpper.style.display = "block";
      if (bLower) bLower.style.display = "block";

      const cnBio = getText('zh', 'modal.biographies_missing_cn', ex.biographies_cn, ex.biographies);
      const enBio = getText('en', 'modal.biographies_missing_en', ex.biographies, ex.biographies_cn);

      if (currentBilingualMode === "cn-top") {
        applyFade(bUpper, cnBio);
        applyFade(bLower, enBio);
      } else {
        applyFade(bUpper, enBio);
        applyFade(bLower, cnBio);
      }
    } else {
      if (bSeparator) bSeparator.style.display = "none";
      if (bLower) bLower.style.display = "none";
      if (bUpper) {
        bUpper.style.display = "block";
        const bio = appLanguage === 'zh'
          ? getText('zh', 'modal.biographies_missing_cn', ex.biographies_cn, ex.biographies)
          : getText('en', 'modal.biographies_missing_en', ex.biographies, ex.biographies_cn);
        applyFade(bUpper, bio);
      }
    }
  } else {
    if (bioSection) bioSection.classList.add("hidden");
  }

  // 3. Credits Section rendering
  if (ex.credits && ex.credits.trim() !== "") {
    if (creditsSection) creditsSection.classList.remove("hidden");
    if (creditsContent) applyFade(creditsContent, ex.credits);
  } else {
    if (creditsSection) creditsSection.classList.add("hidden");
  }
}
