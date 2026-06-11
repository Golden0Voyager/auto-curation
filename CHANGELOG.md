# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 完整 README.md（项目发布就绪）
- Apache-2.0 License
- CHANGELOG.md
- CONTRIBUTING.md
- CODE_OF_CONDUCT.md
- SECURITY.md
- Issue / Pull Request 模板
- `pyproject.toml` 元数据：authors、license、project URLs、classifiers
- CI ruff lint 步骤
- `conftest.py`：解决 `from src.xxx` 导入

### Changed
- `src/llm_parser.py` 委托 LLM 调用到 auto_hub，移除本地 httpx/tenacity 重试逻辑
- `tests/test_llm_parser_cache.py` 适配 hub 委托路径（AsyncMock）
- `pyproject.toml` 添加 `[tool.pytest.ini_options] pythonpath = ["src"]`
- `.gitignore` 新增 `*.egg-info/`

### Fixed
- `src.llm_parser` 模块导入问题（`conftest.py` 注入虚拟包）

## [0.1.0] - 2026-06-XX

### Added
- 6 种采集策略：HTML_LLM / CSV_LOCAL / CSV_REMOTE / REST_API / SPARQL / ARTWORK_ONLY
- 61 家注册机构（覆盖 MoMA / Tate / M+ / 双年展体系 等）
- 多供应商 LLM 回退链（XIAOMI MIMO → Gemini → SiliconFlow）
- 自动 parser 注册（`pkgutil.iter_modules` 扫描）
- SQLite 数据持久化（v2 schema：exhibitions + artworks）
- 数据质量监测 + 健康检查（GitHub Actions 每日 UTC 08:03）
- 零合成数据策略（所有字段必须来源于真实数据）

[Unreleased]: https://github.com/Golden0Voyager/auto_curation/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Golden0Voyager/auto_curation/releases/tag/v0.1.0
