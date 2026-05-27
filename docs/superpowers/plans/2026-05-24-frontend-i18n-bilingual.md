# 前端国际化与双语对照功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 引入 i18next 国际化框架，实现全局中英文切换与详情弹窗双语对照开关。

**Architecture:** i18next + browser language detector 管理静态 UI 文本；自定义 `bilingualEnabled` 状态管理弹窗动态内容的双语/单语渲染。翻译资源按模块分组存放在 `locales/{lang}/translation.json`。

**Tech Stack:** i18next (CDN), i18next-browser-languagedetector (CDN), i18next-http-backend (CDN), Vanilla JS, Tailwind CSS

---

## 文件结构映射

| 文件 | 类型 | 职责 |
|:---|:---|:---|
| `src/web/static/locales/zh/translation.json` | 新建 | 中文 UI 文本资源 |
| `src/web/static/locales/en/translation.json` | 新建 | 英文 UI 文本资源 |
| `src/web/templates/index.html` | 修改 | 引入 i18next CDN，Header 新增语言设置控件，所有文本元素加 `data-i18n` |
| `src/web/static/style.css` | 修改 | 语言选择胶囊与双语 toggle 开关样式 |
| `src/web/static/app.js` | 修改 | i18next 初始化、全局状态管理、文本渲染逻辑重构 |

---

### Task 1: 创建中文翻译资源文件

**Files:**
- Create: `src/web/static/locales/zh/translation.json`

- [ ] **Step 1: 编写中文翻译字典**

```json
{
  "header": {
    "brand_title": "全球当代艺术展览智能分析大屏",
    "brand_subtitle": "GLOBAL CONTEMPORARY ART EXHIBITION INTELLIGENCE",
    "metric_exhibitions": "展览总收录",
    "metric_artworks": "结构化作品",
    "metric_museums": "覆盖艺术机构"
  },
  "settings": {
    "language": "语言",
    "bilingual": "双语对照",
    "bilingual_on": "开启",
    "bilingual_off": "关闭"
  },
  "filter": {
    "title": "智能过滤器",
    "search_placeholder": "检索展览、艺术家、媒介或策展词...",
    "source_label": "机构筛选",
    "source_all": "全部机构",
    "year_range_label": "展期年份段",
    "year_range_to": "至"
  },
  "chart": {
    "timeline_title": "时光策展河流 (展览变迁趋势)",
    "medium_title": "媒介极坐标分布 (艺术材质占比)",
    "network_title": "艺术家参展社交网络星空图 (共同参展关系)",
    "network_hint": "拖拽星点/双击下钻",
    "network_legend": "关系发现：",
    "network_legend_node": "节点大小代表全球参展作品计数。",
    "network_legend_edge": "节点连线代表共同参与了相同的展览。"
  },
  "gallery": {
    "title": "展览探索画廊",
    "count_loading": "正在检索...",
    "count_result": "匹配到 {{count}} 个展览",
    "empty_title": "在当前筛选条件下，未捕获任何当代艺术展览",
    "card_curators": "策展: {{curators}}",
    "card_artworks": "{{count}} 件作品",
    "card_date_unknown": "未知日期",
    "card_city_global": "全球"
  },
  "modal": {
    "close": "关闭",
    "date_prefix": "",
    "date_separator": " 至 ",
    "city_suffix": " ({{location}})",
    "curators_default": "联合策划 / 特邀学者",
    "artwork_count": "{{count}} 件",
    "preface_title": "展览简介 (Preface)",
    "concept_title": "策展学术理念 (Concept)",
    "biographies_title": "艺术家与合作团队传记 (Biographies)",
    "credits_title": "学术鸣谢与制作团队 (Credits & Production)",
    "artworks_title": "参展艺术品图册 (Structure Artworks)",
    "artworks_empty": "该展览暂未关联具体代表作品数据 (由爬虫采集补充中)",
    "table_artist": "艺术家 (Artist)",
    "table_title": "作品标题 (Title)",
    "table_year": "年份",
    "table_medium": "媒介 (Medium)",
    "table_dimensions": "尺寸 (Dimensions)",
    "artist_unknown": "未知艺术家",
    "work_untitled": "无题",
    "year_unknown": "未标注",
    "medium_unknown": "-",
    "dimensions_unknown": "-",
    "bilingual_mode": "双语对照学术阅读模式 (Bilingual Curation Mode)",
    "bilingual_cn_top": "中文置顶",
    "bilingual_en_top": "English Top",
    "visit_website": "访问官方展览网页",
    "fallback_hint": "[原文仅{{lang}}可用] ",
    "preface_missing_cn": "该展览未提供独立前言文本或正在解析中。",
    "preface_missing_en": "The raw English preface is not available for this record.",
    "concept_missing_cn": "学术策展理念由大模型从网页中抽取整合，本展览未进行概念提炼。",
    "concept_missing_en": "No original English curatorial concept theoretical details extracted for this record.",
    "biographies_missing_cn": "暂无艺术家的简短中文介绍。",
    "biographies_missing_en": "No English biographies available for this record."
  },
  "common": {
    "unknown": "未知"
  }
}
```

- [ ] **Step 2: 提交中文翻译文件**

```bash
cd /Users/hainingyu/Code/auto_curation
rtk git add src/web/static/locales/zh/translation.json
rtk git commit -m "feat(i18n): add Chinese translation resource for dashboard UI

添加仪表盘中文翻译字典，覆盖 header、filter、chart、gallery、modal 全部模块。"
```

---

### Task 2: 创建英文翻译资源文件

**Files:**
- Create: `src/web/static/locales/en/translation.json`

- [ ] **Step 1: 编写英文翻译字典**

```json
{
  "header": {
    "brand_title": "CurationInsight - Global Contemporary Art Exhibition Intelligence",
    "brand_subtitle": "GLOBAL CONTEMPORARY ART EXHIBITION INTELLIGENCE",
    "metric_exhibitions": "Total Exhibitions",
    "metric_artworks": "Structured Artworks",
    "metric_museums": "Institutions"
  },
  "settings": {
    "language": "Language",
    "bilingual": "Bilingual",
    "bilingual_on": "On",
    "bilingual_off": "Off"
  },
  "filter": {
    "title": "Interactive Controls",
    "search_placeholder": "Search exhibitions, artists, mediums, or curatorial terms...",
    "source_label": "Institution Filter",
    "source_all": "All Institutions",
    "year_range_label": "Exhibition Year Range",
    "year_range_to": "to"
  },
  "chart": {
    "timeline_title": "Curatorial Timeline River (Exhibition Trends)",
    "medium_title": "Medium Polar Distribution (Art Material Composition)",
    "network_title": "Artist Co-Exhibition Social Network Star Map",
    "network_hint": "Drag nodes / Double-click to drill",
    "network_legend": "Relationship Discovery:",
    "network_legend_node": "Node size represents total artworks in global exhibitions.",
    "network_legend_edge": "Edges represent co-participation in the same exhibitions."
  },
  "gallery": {
    "title": "Exhibition Discovery Gallery",
    "count_loading": "Searching...",
    "count_result": "{{count}} exhibitions matched",
    "empty_title": "No contemporary art exhibitions found under current filters.",
    "card_curators": "Curated by: {{curators}}",
    "card_artworks": "{{count}} artworks",
    "card_date_unknown": "Unknown date",
    "card_city_global": "Global"
  },
  "modal": {
    "close": "Close",
    "date_prefix": "",
    "date_separator": " to ",
    "city_suffix": " ({{location}})",
    "curators_default": "Joint curation / Guest scholars",
    "artwork_count": "{{count}} artworks",
    "preface_title": "Exhibition Preface",
    "concept_title": "Curatorial Concept",
    "biographies_title": "Artist & Team Biographies",
    "credits_title": "Credits & Production",
    "artworks_title": "Structured Artworks Catalogue",
    "artworks_empty": "No specific representative artworks linked to this exhibition yet (crawler supplementation in progress).",
    "table_artist": "Artist",
    "table_title": "Title",
    "table_year": "Year",
    "table_medium": "Medium",
    "table_dimensions": "Dimensions",
    "artist_unknown": "Unknown artist",
    "work_untitled": "Untitled",
    "year_unknown": "N/A",
    "medium_unknown": "-",
    "dimensions_unknown": "-",
    "bilingual_mode": "Bilingual Curation Mode",
    "bilingual_cn_top": "CN Top",
    "bilingual_en_top": "EN Top",
    "visit_website": "Visit Official Exhibition Page",
    "fallback_hint": "[Original {{lang}} only] ",
    "preface_missing_cn": "No independent preface text available or still parsing.",
    "preface_missing_en": "The raw English preface is not available for this record.",
    "concept_missing_cn": "Curatorial concept not yet extracted for this exhibition.",
    "concept_missing_en": "No original English curatorial concept theoretical details extracted for this record.",
    "biographies_missing_cn": "No brief Chinese artist biography available.",
    "biographies_missing_en": "No English biographies available for this record."
  },
  "common": {
    "unknown": "Unknown"
  }
}
```

- [ ] **Step 2: 提交英文翻译文件**

```bash
cd /Users/hainingyu/Code/auto_curation
rtk git add src/web/static/locales/en/translation.json
rtk git commit -m "feat(i18n): add English translation resource for dashboard UI

添加仪表盘英文翻译字典，覆盖 header、filter、chart、gallery、modal 全部模块。"
```

---

### Task 3: 引入 i18next 并初始化（HTML + JS）

**Files:**
- Modify: `src/web/templates/index.html:12-16`（CDN 引入区域）
- Modify: `src/web/static/app.js:1-33`（全局状态 + DOMContentLoaded）

- [ ] **Step 1: 在 index.html 的 `<head>` 中引入 i18next CDN**

在 `src/web/templates/index.html` 中，找到现有的 CDN 引入区域（lucide 之后），添加：

```html
  <!-- i18next Internationalization -->
  <script src="https://cdn.jsdelivr.net/npm/i18next@23.15.0/i18next.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/i18next-browser-languagedetector@7.2.0/i18nextBrowserLanguageDetector.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/i18next-http-backend@2.6.0/i18nextHttpBackend.min.js"></script>
```

- [ ] **Step 2: 在 app.js 顶部添加 i18next 初始化代码**

替换 `src/web/static/app.js` 前 15 行为：

```javascript
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
```

- [ ] **Step 3: 修改 DOMContentLoaded 为异步，等待 i18next 初始化完成**

将：
```javascript
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
```

改为：
```javascript
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
  
  // Fetch & Draw charts
  loadTimelineChart();
  loadNetworkChart();
  
  // Load exhibitions gallery
  loadExhibitionsGallery();
});
```

- [ ] **Step 4: 添加 `updateStaticTexts()` 函数**

在 app.js 中新增（放在 `setupEventListeners` 之前）：

```javascript
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
```

- [ ] **Step 5: 提交 i18next 初始化**

```bash
cd /Users/hainingyu/Code/auto_curation
rtk git add src/web/templates/index.html src/web/static/app.js
rtk git commit -m "feat(i18n): integrate i18next with language detection and static text updater

引入 i18next 核心、浏览器语言检测器、HTTP 后端。初始化配置使用 localStorage 持久化语言偏好，添加 updateStaticTexts() 遍历 data-i18n 属性更新 DOM。"
```

---

### Task 4: 在 Header 添加语言设置控件

**Files:**
- Modify: `src/web/templates/index.html:51-67`（header metrics 区域）
- Modify: `src/web/static/style.css`（新增设置控件样式）

- [ ] **Step 1: 在 index.html header 中添加设置控件**

在 `src/web/templates/index.html` 中，找到 metrics dashboard div（`<!-- Metrics Dashboard -->`），在其前面或后面插入：

```html
      <!-- Language & Bilingual Settings -->
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2">
          <span class="text-[10px] text-slate-500 uppercase tracking-wider font-space" data-i18n="settings.language">语言</span>
          <div class="flex items-center p-0.5 bg-slate-950/60 rounded-lg border border-slate-800/80">
            <button id="lang-zh-btn" class="px-2.5 py-1 text-[10px] rounded-md transition-all duration-200 font-space" onclick="setLanguage('zh')">中</button>
            <button id="lang-en-btn" class="px-2.5 py-1 text-[10px] rounded-md transition-all duration-200 font-space text-slate-400" onclick="setLanguage('en')">EN</button>
          </div>
        </div>
        
        <div class="flex items-center gap-2">
          <span class="text-[10px] text-slate-500 uppercase tracking-wider font-space" data-i18n="settings.bilingual">双语对照</span>
          <button id="bilingual-toggle-btn" class="relative w-9 h-5 rounded-full bg-slate-800 border border-slate-700 transition-all duration-300" onclick="toggleBilingual()">
            <span id="bilingual-toggle-knob" class="absolute top-0.5 left-0.5 w-3.5 h-3.5 rounded-full bg-slate-500 transition-all duration-300"></span>
          </button>
          <span id="bilingual-status-text" class="text-[10px] text-slate-500 font-space" data-i18n="settings.bilingual_off">关闭</span>
        </div>
      </div>
```

放在 header 的 flex 容器里，与 brand 和 metrics 并列。需要调整 header 的 class 确保布局合理。将 header 改为：

```html
    <header class="glass-panel p-6 flex flex-col md:flex-row justify-between items-center gap-6 border-b gold-glow-border">
```

保持原样即可，新增的设置控件放在 metrics 后面，用 `flex-wrap` 处理小屏幕：

```html
      <!-- Metrics Dashboard + Settings -->
      <div class="flex flex-wrap items-center gap-6 md:gap-8">
        <!-- Metrics -->
        <div class="flex items-center gap-6 md:gap-12">...</div>
        
        <div class="h-8 w-[1px] bg-slate-800 hidden md:block"></div>
        
        <!-- Settings -->
        <div class="flex items-center gap-4">...</div>
      </div>
```

- [ ] **Step 2: 添加设置控件样式到 style.css**

在 `src/web/static/style.css` 末尾添加：

```css
/* Language Settings Controls */
#lang-zh-btn.active,
#lang-en-btn.active {
  background: rgba(226, 183, 85, 0.15);
  border: 1px solid rgba(226, 183, 85, 0.3);
  color: #e2b755;
  font-weight: 600;
}

#bilingual-toggle-btn.active {
  background: rgba(94, 243, 232, 0.15);
  border-color: rgba(94, 243, 232, 0.3);
}

#bilingual-toggle-btn.active #bilingual-toggle-knob {
  transform: translateX(16px);
  background: #5ef3e8;
  box-shadow: 0 0 8px rgba(94, 243, 232, 0.5);
}
```

- [ ] **Step 3: 在 app.js 中添加 `setLanguage()` 和 `toggleBilingual()` 函数**

在 `updateStaticTexts()` 之后添加：

```javascript
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
    statusText.textContent = i18next.t(bilingualEnabled ? 'settings.bilingual_on' : 'settings.bilingual_off');
  }
}
```

- [ ] **Step 4: 提交设置控件**

```bash
cd /Users/hainingyu/Code/auto_curation
rtk git add src/web/templates/index.html src/web/static/style.css src/web/static/app.js
rtk git commit -m "feat(i18n): add header language selector and bilingual toggle controls

在 Header 右上角添加语言选择胶囊（中/EN）和双语对照 toggle 开关。默认语言中文，双语默认关闭。状态持久化到 localStorage。"
```

---

### Task 5: 给 HTML 所有文本元素添加 data-i18n 属性

**Files:**
- Modify: `src/web/templates/index.html`（全文）

- [ ] **Step 1: 批量替换 header 和 filter 区域**

将以下文本元素添加 `data-i18n` 属性（保留原有文本作为 fallback）：

| 元素 | data-i18n 值 |
|:---|:---|
| `#metric-exhibitions` 前面的 label | `header.metric_exhibitions` |
| `#metric-artworks` 前面的 label | `header.metric_artworks` |
| `#metric-museums` 前面的 label | `header.metric_museums` |
| 智能过滤器 h2 | `filter.title` |
| `#search-input` placeholder | `[placeholder]filter.search_placeholder` |
| 机构筛选 span | `filter.source_label` |
| 全部机构 button | `filter.source_all` |
| 展期年份段 span | `filter.year_range_label` |
| 至 span | `filter.year_range_to` |
| 时光策展河流 h2 | `chart.timeline_title` |
| 媒介极坐标分布 h2 | `chart.medium_title` |
| 艺术家社交网络 h2 | `chart.network_title` |
| 拖拽星点提示 | `chart.network_hint` |
| 关系发现 overlay | `chart.network_legend` / `chart.network_legend_node` / `chart.network_legend_edge` |
| 展览探索画廊 h2 | `gallery.title` |
| `#gallery-count` | `gallery.count_loading` |
| 空状态文本 | `gallery.empty_title` |
| 卡片内「策展:」 | 动态生成，见 Task 6 |
| 卡片内「件作品」 | 动态生成，见 Task 6 |
| 卡片内「全球」 | 动态生成，见 Task 6 |
| 弹窗内所有 section 标题 | `modal.*_title` |
| 弹窗表格列头 | `modal.table_*` |
| 弹窗空状态 | `modal.artworks_empty` |
| 访问官网链接 | `modal.visit_website` |
| 双语对照模式 label | `modal.bilingual_mode` |
| 中文置顶 / English Top | `modal.bilingual_cn_top` / `modal.bilingual_en_top` |

- [ ] **Step 2: 提交 HTML 文本绑定**

```bash
cd /Users/hainingyu/Code/auto_curation
rtk git add src/web/templates/index.html
rtk git commit -m "feat(i18n): bind data-i18n attributes to all UI text elements

为所有静态文本元素添加 data-i18n 属性，覆盖 header metrics、filter、chart titles、gallery、modal sections。保留原中文文本作为 i18next 加载前的 fallback。"
```

---

### Task 6: 重构动态生成文本为 i18next.t() 调用

**Files:**
- Modify: `src/web/static/app.js`（多处动态文本生成）

- [ ] **Step 1: 重构 `fetchStatsAndSetupFilters` 中的博物馆筛选按钮和图表标题**

将 `data.museum_stats.forEach` 中的 button text：
```javascript
btn.textContent = `${mus.source} (${mus.count})`;
```
保持不变（数据源名称是专有名词，不需要翻译）。

将 `renderMediumChart` 中的 tooltip formatter：
```javascript
formatter: "{b} : {c}件 ({d}%)",
```
改为：
```javascript
formatter: (params) => {
  return `${params.name} : ${params.value}${i18next.t('gallery.card_artworks', {count: ''})} (${params.percent}%)`;
},
```

这个需要再想想... 实际上图表里的 formatter 不用翻译，或者简单处理。让我简化，只翻译明确的 UI 标签。

实际上更好的方式是：图表标题在 HTML 中已有 data-i18n，echarts option 中的 title 不需要单独处理。tooltip 中的 "件" 可以改为统一格式。

让我重新规划这一步，只修改真正需要翻译的动态文本：

1. `fetchStatsAndSetupFilters` - 按钮上的 source 名称不翻译
2. `loadTimelineChart` / `renderMediumChart` / `loadNetworkChart` - tooltip 和 loading 文本
3. `loadExhibitionsGallery` - 卡片内的 "策展:", "件作品", "未知日期", "全球", 空状态提示
4. `showExhibitionModal` - 弹窗内所有动态生成的文本

- [ ] **Step 1: 修改图表 loading 和 tooltip 文本**

在 `loadTimelineChart` 中：
```javascript
timelineChart.showLoading({
  text: i18next.t('gallery.count_loading'),
  ...
});
```

在 `loadNetworkChart` 中：
```javascript
networkChart.showLoading({
  text: i18nReady ? i18next.t('gallery.count_loading') : "引力星云运转中...",
  ...
});
```

- [ ] **Step 2: 修改 gallery 卡片动态文本**

在 `loadExhibitionsGallery` 中：

将 `countDisplay.textContent = \`匹配到 ${result.total} 个展览\`;`
改为：
```javascript
countDisplay.textContent = i18next.t('gallery.count_result', {count: result.total});
```

将空状态 HTML 中的文本改为 data-i18n：
```html
<span class="text-xs" data-i18n="gallery.empty_title">...</span>
```

将卡片内的 "策展:" 改为：
```javascript
const curatorLabel = i18next.t('gallery.card_curators', {curators: ''}).replace('{{curators}}', '');
// 或使用 i18next 的 interpolation
```

实际上对于卡片内的动态文本，最好这样重构：

```javascript
const cardCurators = (ex.curators && ex.curators.length > 0) 
  ? ex.curators.join(", ") 
  : i18next.t('modal.curators_default');
```

卡片 innerHTML 中的 "策展: " 改为 `${i18next.t('gallery.card_curators', {curators: ''}).split('{{curators}}')[0]}`

不，这样太复杂了。让我简化：在翻译字典中，curators 相关的 key 直接用完整格式，JS 中用 `replace()` 替换变量。

或者更简单：不在翻译字典中放带变量的模板，而是把标签和值分开。比如：

```javascript
// HTML 中
<span class="curator-label" data-i18n="gallery.card_curators_prefix">策展:</span>
<span>${curators}</span>
```

但这需要改 HTML 结构。让我用一个更简洁的方式：

```javascript
const curatorPrefix = i18next.t('gallery.card_curators').replace('{{curators}}', '').trim();
// 如果翻译是 "策展: {{curators}}"，replace 后得到 "策展:"
```

好的，让我在卡片 innerHTML 中使用这种方式。

同样对于 "件作品"：
```javascript
const artworkLabel = i18next.t('gallery.card_artworks', {count: ex.artwork_count});
```

"未知日期":
```javascript
const dateText = ex.start_date ? (ex.end_date ? `${ex.start_date} ~ ${ex.end_date}` : ex.start_date) : i18next.t('gallery.card_date_unknown');
```

"全球":
```javascript
${ex.city || i18next.t('gallery.card_city_global')}
```

- [ ] **Step 3: 修改弹窗动态文本**

在 `showExhibitionModal` 中：

```javascript
document.getElementById("modal-curators").textContent = (ex.curators && ex.curators.length > 0) 
  ? ex.curators.join(", ") 
  : i18next.t('modal.curators_default');

document.getElementById("modal-art-count").textContent = i18next.t('modal.artwork_count', {count: ex.artworks.length});

let dateText = ex.start_date || i18next.t('common.unknown');
if (ex.end_date) dateText += i18next.t('modal.date_separator') + ex.end_date;
document.getElementById("modal-date").textContent = dateText;

document.getElementById("modal-city").innerHTML = `<i data-lucide="map-pin" class="w-3.5 h-3.5 text-amber-500"></i> ${ex.city || i18next.t('common.unknown')} (${ex.location || i18next.t('common.unknown')})`;
```

- [ ] **Step 4: 修改 artworks 表格空状态和列头**

表格列头已经在 HTML 中加 data-i18n，不需要改 JS。
空状态：
```javascript
tbody.innerHTML = `
  <tr>
    <td colspan="5" class="py-8 text-center text-slate-500 italic" data-i18n="modal.artworks_empty">该展览暂未关联具体代表作品数据 (由爬虫采集补充中)</td>
  </tr>
`;
```

表格内动态数据：
```javascript
<td class="py-2 px-3 font-semibold text-amber-400/90">${art.artist_name || i18next.t('modal.artist_unknown')}</td>
<td class="py-2 px-3 italic font-medium text-slate-100">${art.work_title || i18next.t('modal.work_untitled')}</td>
<td class="py-2 px-3 font-space text-[10px]">${art.work_year || i18next.t('modal.year_unknown')}</td>
<td class="py-2 px-3 text-slate-400 font-light text-[11px]">${art.medium || i18next.t('modal.medium_unknown')}</td>
<td class="py-2 px-3 text-slate-400 font-light font-space text-[10px]">${art.dimensions || i18next.t('modal.dimensions_unknown')}</td>
```

- [ ] **Step 5: 提交动态文本重构**

```bash
cd /Users/hainingyu/Code/auto_curation
rtk git add src/web/static/app.js
rtk git commit -m "feat(i18n): refactor all dynamic text to use i18next.t() with interpolation

将图表 loading 文本、gallery 卡片文本、弹窗元数据与作品表格全部改用 i18next.t() 调用，支持变量插值（count, curators 等）。"
```

---

### Task 7: 重构双语对照渲染逻辑

**Files:**
- Modify: `src/web/static/app.js`（`renderBilingualTexts` 和 `updateBilingualSliderUI`）
- Modify: `src/web/templates/index.html`（弹窗双语区域结构微调）

- [ ] **Step 1: 修改 `updateBilingualSliderUI` 为根据 `bilingualEnabled` 控制整体显示/隐藏**

修改 `updateBilingualSliderUI()` 函数：

```javascript
function updateBilingualSliderUI() {
  const toggleContainer = document.getElementById("bilingual-toggle").parentElement;
  const slider = document.getElementById("bilingual-slider");
  const btnCn = document.getElementById("btn-cn-top");
  const btnEn = document.getElementById("btn-en-top");
  
  // Show/hide entire bilingual toggle bar
  if (toggleContainer) {
    toggleContainer.style.display = bilingualEnabled ? 'flex' : 'none';
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
```

- [ ] **Step 2: 重写 `renderBilingualTexts` 支持单语/双语两种模式**

将现有 `renderBilingualTexts` 替换为：

```javascript
function renderBilingualTexts() {
  if (!activeExhibitionData) return;
  
  const ex = activeExhibitionData;
  
  // Get localized fallback texts
  const getPreface = (lang) => {
    const key = lang === 'zh' ? 'preface' : 'preface_en';
    const fallbackKey = lang === 'zh' ? 'modal.preface_missing_cn' : 'modal.preface_missing_en';
    return (ex[key] && ex[key].trim()) ? ex[key] : i18next.t(fallbackKey);
  };
  
  const getConcept = (lang) => {
    const key = lang === 'zh' ? 'concept' : 'concept_en';
    const fallbackKey = lang === 'zh' ? 'modal.concept_missing_cn' : 'modal.concept_missing_en';
    return (ex[key] && ex[key].trim()) ? ex[key] : i18next.t(fallbackKey);
  };
  
  const getBio = (lang) => {
    const key = lang === 'zh' ? 'biographies_cn' : 'biographies';
    const fallbackKey = lang === 'zh' ? 'modal.biographies_missing_cn' : 'modal.biographies_missing_en';
    return (ex[key] && ex[key].trim()) ? ex[key] : i18next.t(fallbackKey);
  };
  
  const pUpper = document.getElementById("preface-upper-block");
  const pLower = document.getElementById("preface-lower-block");
  const pSeparator = pUpper?.parentElement.querySelector('.h-\[1px\]');
  const cUpper = document.getElementById("concept-upper-block");
  const cLower = document.getElementById("concept-lower-block");
  const cSeparator = cUpper?.parentElement.querySelector('.h-\[1px\]');
  
  const bioSection = document.getElementById("modal-biographies-section");
  const creditsSection = document.getElementById("modal-credits-section");
  const bUpper = document.getElementById("biographies-upper-block");
  const bLower = document.getElementById("biographies-lower-block");
  const bSeparator = document.getElementById("biographies-separator");
  const creditsContent = document.getElementById("credits-content");
  
  const applyFade = (el, text) => {
    if (!el) return;
    el.style.opacity = "0.2";
    setTimeout(() => {
      el.textContent = text;
      el.style.opacity = "1";
    }, 100);
  };
  
  // Preface & Concept rendering
  if (bilingualEnabled) {
    // Bilingual mode: show both blocks with separator
    if (pLower) { pLower.style.display = 'block'; }
    if (pSeparator) { pSeparator.style.display = 'block'; }
    if (cLower) { cLower.style.display = 'block'; }
    if (cSeparator) { cSeparator.style.display = 'block'; }
    
    const cnPreface = getPreface('zh');
    const enPreface = getPreface('en');
    const cnConcept = getConcept('zh');
    const enConcept = getConcept('en');
    
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
    // Monolingual mode: hide lower blocks and separators
    if (pLower) { pLower.style.display = 'none'; }
    if (pSeparator) { pSeparator.style.display = 'none'; }
    if (cLower) { cLower.style.display = 'none'; }
    if (cSeparator) { cSeparator.style.display = 'none'; }
    
    const preface = getPreface(appLanguage);
    const concept = getConcept(appLanguage);
    applyFade(pUpper, preface);
    applyFade(cUpper, concept);
  }
  
  // Biographies
  const hasBio = (ex.biographies && ex.biographies.trim()) || (ex.biographies_cn && ex.biographies_cn.trim());
  if (hasBio) {
    if (bioSection) bioSection.classList.remove("hidden");
    
    if (bilingualEnabled) {
      if (bSeparator) bSeparator.style.display = "block";
      if (bUpper) bUpper.style.display = "block";
      if (bLower) bLower.style.display = "block";
      
      const cnBio = getBio('zh');
      const enBio = getBio('en');
      
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
        const bio = getBio(appLanguage);
        applyFade(bUpper, bio);
      }
    }
  } else {
    if (bioSection) bioSection.classList.add("hidden");
  }
  
  // Credits
  if (ex.credits && ex.credits.trim() !== "") {
    if (creditsSection) creditsSection.classList.remove("hidden");
    if (creditsContent) applyFade(creditsContent, ex.credits);
  } else {
    if (creditsSection) creditsSection.classList.add("hidden");
  }
}
```

- [ ] **Step 3: 提交双语渲染重构**

```bash
cd /Users/hainingyu/Code/auto_curation
rtk git add src/web/static/app.js
rtk git commit -m "feat(i18n): refactor bilingual rendering to support on/off toggle

重写 renderBilingualTexts()：双语关闭时隐藏 lower-block 和分隔线，仅显示当前语言文本；双语开启时恢复完整堆叠布局。支持数据缺失时的本地化 fallback 提示。"
```

---

### Task 8: 端到端验证

**Files:**
- 无新文件，仅验证

- [ ] **Step 1: 启动后端服务**

```bash
cd /Users/hainingyu/Code/auto_curation
python src/web/app.py
```

或查找正确的启动命令：
```bash
grep -r "app.run\|uvicorn\|fastapi\|flask" /Users/hainingyu/Code/auto_curation/src/web/ --include="*.py"
```

- [ ] **Step 2: 浏览器验证清单**

打开 `http://localhost:5000`（或实际端口），依次验证：

1. **首次加载**：默认中文，双语开关关闭，弹窗内只显示中文文本
2. **切换英文**：点击 EN，所有 UI 文本变为英文，弹窗打开后只显示英文文本
3. **开启双语**：点击双语 toggle，弹窗显示双语堆叠，默认英文在上（因为当前语言是 EN）
4. **双语优先级切换**：点击 "EN Top" / "CN Top" 胶囊，上下文本互换
5. **切回中文 + 双语**：点击 "中"，双语弹窗默认中文在上
6. **关闭双语**：toggle 关闭，弹窗恢复单语显示
7. **刷新页面**：语言偏好和双语开关状态正确恢复
8. **空数据回退**：找一个没有英文翻译的旧记录，英文模式下显示中文 fallback 并带提示标签

- [ ] **Step 3: 修复验证中发现的问题**

根据验证结果修复 bug，每项修复单独提交。

---

## 自检

### Spec 覆盖检查

| Spec 要求 | 对应 Task |
|:---|:---|
| i18next + browser detector + http backend | Task 3 |
| 翻译资源文件 `locales/{lang}/translation.json` | Task 1, 2 |
| 全局状态 `appLanguage`, `bilingualEnabled` | Task 3, 4 |
| Header 语言设置控件 | Task 4 |
| 所有 UI 文本 `data-i18n` 绑定 | Task 5 |
| 动态文本 `i18next.t()` 调用 | Task 6 |
| 单语/双语弹窗渲染逻辑 | Task 7 |
| localStorage 持久化 | Task 3, 4 |
| 数据回退策略 | Task 7 |
| 状态联动规则 | Task 3, 4, 7 |

### Placeholder 扫描

无 TBD/TODO/"implement later"/"add appropriate error handling" 等占位符。所有步骤包含具体代码。

### 类型一致性检查

- `appLanguage` 始终为 `'zh'` 或 `'en'`
- `bilingualEnabled` 始终为 `boolean`
- `currentBilingualMode` 始终为 `'cn-top'` 或 `'en-top'`
- i18next key 命名采用 `module.key` 或 `module.subkey` 格式，全局统一
