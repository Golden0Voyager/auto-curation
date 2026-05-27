# 前端国际化与双语对照功能设计文档

## 1. 概述

为 CurationInsight 仪表盘引入完整的国际化（i18n）架构，支持全局语言切换（中文/英文）与中英双语对照模式的独立开关。

## 2. 目标

- 所有用户可见的 UI 文本支持中英双语切换
- 详情弹窗的展览内容（Preface / Concept / Biographies）支持「单语模式」与「双语对照模式」
- 双语对照开关默认关闭
- 用户语言偏好持久化（localStorage）

## 3. 技术方案

采用 **i18next** 生态作为国际化核心框架，理由如下：
- 项目定位大型平台，未来可能扩展至更多语言
- i18next 提供插值、复数、命名空间、懒加载等完整能力
- 社区成熟，生态丰富（检测器、后端加载器、React/Vue 绑定等）

### 3.1 引入的库（CDN）

```html
<script src="https://cdn.jsdelivr.net/npm/i18next@23.x/i18next.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/i18next-browser-languagedetector@7.x/i18nextBrowserLanguageDetector.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/i18next-http-backend@2.x/i18nextHttpBackend.min.js"></script>
```

### 3.2 翻译资源文件

```
src/web/static/locales/zh/translation.json
src/web/static/locales/en/translation.json
```

采用标准 i18next JSON 格式，按页面模块分组（`header`, `filter`, `modal`, `chart`, `common`）。

### 3.3 初始化配置

```javascript
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
  });
```

## 4. 全局状态设计

| 状态 | 类型 | 默认值 | 存储 | 说明 |
|:---|:---|:---|:---|:---|
| `appLanguage` | `string` | `'zh'` | i18next + localStorage | 全局界面语言 |
| `bilingualEnabled` | `boolean` | `false` | localStorage (`bilingualEnabled`) | 双语对照总开关 |
| `currentBilingualMode` | `string` | `'cn-top'` | 内存 | 双语开启时的上下优先级 |

### 状态联动规则

1. **首次加载**：
   - i18next 自动检测浏览器语言（优先 localStorage，其次 navigator）
   - `bilingualEnabled` 从 localStorage 读取，无记录则默认 `false`

2. **切换全局语言**（中/EN）：
   - 调用 `i18next.changeLanguage(lng)`
   - 所有 `data-i18n` 属性元素自动更新
   - 如双语开启，同步更新 `currentBilingualMode` 以匹配新语言（中文→`cn-top`，英文→`en-top`）
   - 重新渲染详情弹窗内容

3. **切换双语开关**（开/关）：
   - 持久化到 localStorage
   - 如从关→开，根据当前语言设置默认优先级
   - 重新渲染详情弹窗内容（如果已打开）

## 5. UI 设计

### 5.1 设置控件位置

Header 右上角，metrics 左侧（或与其同行），紧凑设计：

```
[中 | EN]  [双语对照 toggle]
```

- 语言选择：胶囊按钮组，当前语言高亮
- 双语开关：小型 toggle switch，右侧标注当前状态文字（随语言切换）

### 5.2 HTML 文本绑定

所有用户可见文本改用 `data-i18n` 属性：

```html
<span data-i18n="header.metric_exhibitions">展览总收录</span>
<input data-i18n="[placeholder]filter.search_placeholder" placeholder="检索展览...">
```

i18next 初始化后自动扫描并替换。动态生成的内容（如 JS 中 `textContent`）改用 `i18next.t('key')`。

## 6. 详情弹窗渲染逻辑

### 6.1 单语模式（bilingualEnabled = false）

隐藏「双语对照学术阅读模式」控制条，隐藏 separator 和 lower-block，upper-block 只显示当前语言文本。

| 全局语言 | 显示内容 |
|:---|:---|
| 中文 | `preface`, `concept`, `biographies_cn` |
| 英文 | `preface_en`, `concept_en`, `biographies` |

若目标语言文本不存在，回退到另一语言并标注「原文仅中文可用」/「Original Chinese only」。

### 6.2 双语模式（bilingualEnabled = true）

显示控制条，恢复上下堆叠布局：

- upper-block：优先级语言（由 `currentBilingualMode` 决定）
- lower-block：次语言
- 分隔线可见

`currentBilingualMode` 初始值由 `appLanguage` 推导。

### 6.3 数据回退策略

```
if (目标语言文本存在 && 文本.trim() !== ""):
    显示目标语言文本
else:
    显示回退语言文本 + 提示标签
```

## 7. 翻译字典范围

覆盖全部用户可见文本，预估 ~60-80 条 key：

- `header.*`：品牌标题、metrics 标签
- `filter.*`：过滤器标题、搜索占位符、机构筛选、年份标签
- `chart.*`：图表标题、tooltip、图例
- `gallery.*`：画廊标题、计数、空状态、卡片标签
- `modal.*`：弹窗所有 section 标题、字段标签、按钮、提示
- `common.*`：通用词汇（未知、无题、未标注等）

## 8. 文件变更清单

| 文件 | 变更类型 | 说明 |
|:---|:---|:---|
| `src/web/templates/index.html` | 修改 | 引入 i18next CDN，添加 `data-i18n` 属性，新增 header 设置控件 |
| `src/web/static/app.js` | 修改 | i18next 初始化、状态管理、翻译回掉、渲染逻辑更新 |
| `src/web/static/style.css` | 修改 | 语言选择器与双语 toggle 样式 |
| `src/web/static/locales/zh/translation.json` | 新增 | 中文翻译资源 |
| `src/web/static/locales/en/translation.json` | 新增 | 英文翻译资源 |

## 9. 边界情况

- **无英文数据的旧记录**：单语英文模式下回退到中文并提示
- **快速连续切换语言**：i18next changeLanguage 是异步的，确保弹窗重新渲染在语言变更完成后触发
- **localStorage 被禁用**：i18next 检测器会优雅回退到 navigator 检测；双语开关状态丢失，回到默认关闭
