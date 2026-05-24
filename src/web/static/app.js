// CurationInsight Dashboard Core Application Script

// Global State
let currentSource = "";
let currentQuery = "";
let currentStartYear = 1929;
let currentEndYear = 2026;
let timelineChart = null;
let mediumChart = null;
let networkChart = null;

// Initialize when DOM loaded
document.addEventListener("DOMContentLoaded", () => {
  // Initialize Lucide Icons
  lucide.createIcons();
  
  // Setup Event Listeners
  setupEventListeners();
  
  // Fetch initial dashboard stats & build dynamic filters
  fetchStatsAndSetupFilters();
  
  // Fetch & Draw charts
  loadTimelineChart();
  loadNetworkChart();
  
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
  
  // Close Modal on clicking outside
  document.getElementById("detail-modal").addEventListener("click", (e) => {
    if (e.target === document.getElementById("detail-modal")) {
      hideExhibitionModal();
    }
  });

  // Respond to window resize dynamically
  window.addEventListener("resize", () => {
    if (timelineChart) timelineChart.resize();
    if (mediumChart) mediumChart.resize();
    if (networkChart) networkChart.resize();
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
    text: "策展河流加载中...",
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
    text: "引力星云运转中...",
    color: "#5ef3e8",
    textColor: "#a0aec0",
    maskColor: "rgba(8, 9, 13, 0.45)"
  });
  
  try {
    const res = await fetch("/api/network?limit_artists=120&min_cooccurrence=2");
    const data = await res.json();
    networkChart.hideLoading();
    
    const option = {
      tooltip: {
        trigger: "item",
        formatter: (params) => {
          if (params.dataType === "node") {
            return `🌟 艺术家: <strong class="text-amber-400">${params.data.name}</strong><br/>展览收录作品数: ${params.data.value} 件`;
          } else {
            return `🔗 共同参展关联:<br/>${params.data.source} ✖ ${params.data.target}<br/>共同出场次数: <strong class="text-cyan-400">${params.data.value}</strong> 次`;
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
            formatter: "{b}",
            color: "#c5c6c7",
            fontSize: 9,
            fontFamily: "Space Grotesk",
            minMargin: 5
          },
          labelLayout: {
            hideOverlap: true
          },
          force: {
            repulsion: 80,
            gravity: 0.08,
            edgeLength: 45,
            layoutAnimation: true
          },
          lineStyle: {
            color: "rgba(255, 255, 255, 0.11)",
            width: 1,
            curveness: 0.1
          },
          emphasis: {
            focus: "adjacency",
            lineStyle: {
              width: 3,
              color: "#5ef3e8"
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
    
    countDisplay.textContent = `匹配到 ${result.total} 个展览`;
    
    if (result.data.length === 0) {
      grid.innerHTML = `
        <div class="col-span-full py-16 flex flex-col items-center justify-center text-slate-500 border border-dashed border-slate-800 rounded-2xl bg-slate-900/10">
          <i data-lucide="info" class="w-8 h-8 text-amber-500/50 mb-2"></i>
          <span class="text-xs">在当前筛选条件下，未捕获任何当代艺术展览</span>
        </div>
      `;
      lucide.createIcons();
      return;
    }
    
    result.data.forEach(ex => {
      // Setup timeline label text
      let dateText = ex.start_date || "未知日期";
      if (ex.end_date) dateText += ` ~ ${ex.end_date}`;
      
      const curators = (ex.curators && ex.curators.length > 0) 
        ? ex.curators.join(", ") 
        : "馆方学术委员会 / 独立策展人";
        
      const card = document.createElement("div");
      card.className = "ex_card glass-panel p-4 flex flex-col justify-between gap-3 border border-slate-800/80 bg-slate-900/30";
      card.onclick = () => showExhibitionModal(ex.id);
      
      card.innerHTML = `
        <div class="flex flex-col gap-1.5">
          <div class="flex items-center justify-between gap-2">
            <span class="px-2 py-0.5 rounded text-[9px] font-bold tracking-wider uppercase font-space bg-amber-500/10 border border-amber-500/20 text-amber-400">
              ${ex.source}
            </span>
            <span class="text-[10px] text-slate-500 flex items-center gap-1 font-space">
              <i data-lucide="map-pin" class="w-3 h-3 text-amber-500/50"></i> ${ex.city || "全球"}
            </span>
          </div>
          
          <h3 class="text-sm font-semibold text-slate-100 font-cinzel line-clamp-2 tracking-wide leading-snug group-hover:text-amber-400">
            ${ex.title}
          </h3>
          
          <div class="text-[10px] text-slate-400 font-light flex items-center gap-1 leading-relaxed mt-1">
            <i data-lucide="user" class="w-3 h-3 text-amber-500/40"></i> 策展: ${curators}
          </div>
        </div>
        
        <div class="flex justify-between items-center border-t border-slate-900/60 pt-2 text-[10px] text-slate-500 font-space mt-1">
          <span class="flex items-center gap-1">
            <i data-lucide="calendar" class="w-3.5 h-3.5 text-slate-600"></i> ${dateText}
          </span>
          <span class="px-2 py-0.5 rounded bg-cyan-950/40 text-cyan-400 font-bold border border-cyan-950">
            ${ex.artwork_count} 件作品
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
    
    // Render Modal metadata
    document.getElementById("modal-source").textContent = ex.source;
    document.getElementById("modal-title").textContent = ex.title;
    
    let dateText = ex.start_date || "未知";
    if (ex.end_date) dateText += ` 至 ${ex.end_date}`;
    document.getElementById("modal-date").textContent = dateText;
    
    document.getElementById("modal-city").innerHTML = `<i data-lucide="map-pin" class="w-3.5 h-3.5 text-amber-500"></i> ${ex.city || "美术馆展厅"} (${ex.location || "展厅展位"})`;
    
    const curators = (ex.curators && ex.curators.length > 0) 
      ? ex.curators.join(", ") 
      : "联合策划 / 特邀学者";
    document.getElementById("modal-curators").textContent = curators;
    
    document.getElementById("modal-art-count").textContent = `${ex.artworks.length} 件`;
    
    // Details texts
    document.getElementById("modal-preface").textContent = ex.preface || "该展览未提供独立前言文本或正在解析中。";
    document.getElementById("modal-concept").textContent = ex.concept || "学术策展理念由大模型从网页中抽取整合，本展览未进行概念提炼。";
    
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
          <td colspan="5" class="py-8 text-center text-slate-500 italic">该展览暂未关联具体代表作品数据 (由爬虫采集补充中)</td>
        </tr>
      `;
    } else {
      ex.artworks.forEach(art => {
        const tr = document.createElement("tr");
        tr.className = "hover:bg-slate-900/60 transition-colors";
        tr.innerHTML = `
          <td class="py-2 px-3 font-semibold text-amber-400/90">${art.artist_name || "未知艺术家"}</td>
          <td class="py-2 px-3 italic font-medium text-slate-100">${art.work_title || "无题"}</td>
          <td class="py-2 px-3 font-space text-[10px]">${art.work_year || "未标注"}</td>
          <td class="py-2 px-3 text-slate-400 font-light text-[11px]">${art.medium || "-"}</td>
          <td class="py-2 px-3 text-slate-400 font-light font-space text-[10px]">${art.dimensions || "-"}</td>
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
