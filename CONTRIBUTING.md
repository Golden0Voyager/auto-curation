# 贡献指南

欢迎贡献！本项目遵循"**以数据真实性为第一原则**"。

## 开发流程

1. Fork 仓库
2. 创建特性分支：`git checkout -b feat/your-feature`
3. 编写代码 + 测试 + 更新文档
4. 跑本地检查：
   ```bash
   uv run ruff check src/ tests/
   uv run pytest
   ```
5. 提交（**中英双语 conventional commit**，英文块在前）：
   ```
   feat: add Taipei parser support

   feat: 新增台北某美术馆 parser 支持
   ```
6. Push 并发起 Pull Request

## 新增机构接入

1. 在 `src/sites/` 下新建解析器文件，继承 `BaseSiteParser` 或独立实现 CSV/API 逻辑
2. 设置必需类属性：`source`, `city`, `parser_key`, `list_url`, `link_patterns`
3. 声明 `strategy = ParserStrategy.XXX`（默认 HTML_LLM 可省略）
4. **自动注册**：`src/sites/__init__.py` 通过 `pkgutil.iter_modules()` 扫描，无需手动导入
5. 如需 Playwright（React SPA），参考 `src/sites/psa.py` 实现 `get_exhibition_urls()`

## 数据质量规范

**禁止合成数据**。所有字段必须来源于真实数据，宁可留空也不要模板填充：

- **Concept**：必须来自 LLM 提取 / API 原始字段 / preface 截取
- **Preface**：必须来自 API 原始字段 / HTML 抓取
- **Curators**：必须来自 CSV 原始数据 / LLM 提取
- **Dates**：必须来自 API / HTML，不推测

## 测试要求

- 新功能必须有单元测试（`tests/` 目录）
- 跑通 `uv run pytest` 再提交
- 提交前确保 `ruff check` 无错误

## PR 检查清单

- [ ] 测试通过
- [ ] ruff lint 干净
- [ ] 数据无合成痕迹
- [ ] 文档更新（CLAUDE.md / README.md）
- [ ] Commit message 遵循 conventional commits + 中英双语
- [ ] 一文件一提交（不要把多个无关修改打包）
