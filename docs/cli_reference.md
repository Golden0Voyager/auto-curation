# CLI 使用手册

## 基本语法

```bash
python run_collector.py [--site KEY | --all | --list-sites] [选项]
```

---

## 命令速查

### 查看机构列表

```bash
python run_collector.py --list-sites
```

输出示例：
```
🏛️  Registered Contemporary Art Institutions:
────────────────────────────────────────────────────────────
 - moma           : MoMA                      (New York)    | ✅ GitHub 开放数据集 (1929-1989)
 - tate           : Tate Modern               (London)      | ✅ 按年份历史过滤 (--since YEAR)
 - mplus          : M+ Museum                 (Hong Kong)   | ✅ 历史档案支持
 - serpentine     : Serpentine Galleries      (London)      | ✅ 历史档案支持
 - mori           : Mori Art Museum           (Tokyo)       | ✅ 历史档案支持
 - met            : The Met                   (New York)    | ⚠️  仅当前展览
 - pompidou       : Centre Pompidou           (Paris)       | ⚠️  仅当前展览
 - guggenheim     : Guggenheim Museum         (New York)    | ⚠️  仅当前展览
 - palais_tokyo   : Palais de Tokyo           (Paris)       | ⚠️  仅当前展览
 - biennale       : Venice Biennale           (Venice)      | ⚠️  仅当前展览
```

---

## 采集命令

### 单机构采集

```bash
# 基础采集
python run_collector.py --site mplus

# 限制数量（测试用）
python run_collector.py --site serpentine --limit 3

# 时间范围过滤
python run_collector.py --site moma --since 1970

# 强制重新抓取（跳过去重）
python run_collector.py --site tate --force

# 模拟运行（不写入数据库）
python run_collector.py --site mori --dry-run --limit 2

# 详细日志
python run_collector.py --site mplus --verbose
```

### 全量采集

```bash
# 全量采集所有机构（当前展览）
python run_collector.py --all

# 全量 + 限制每站数量
python run_collector.py --all --limit 5

# 全量 + 时间范围（支持该功能的机构生效）
python run_collector.py --all --since 2015

# 全量模拟运行
python run_collector.py --all --dry-run
```

---

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|:--|:--|:--|:--|
| `--site KEY` | string | — | 指定机构 key（见 `--list-sites`） |
| `--all` | flag | — | 采集所有注册机构 |
| `--list-sites` | flag | — | 列出所有机构并退出 |
| `--since YEAR` | int | None | 仅采集该年份及以后的展览 |
| `--limit N` | int | None | 每站最多处理 N 条，不设则全量 |
| `--force` | flag | False | 重新处理已存在于 DB 的 URL |
| `--dry-run` | flag | False | 不写入数据库 |
| `--verbose` | flag | False | 输出 DEBUG 级别日志 |
| `--db PATH` | string | `exhibitions.db` | SQLite 数据库路径 |

---

## 各机构推荐命令

### MoMA（GitHub 开放数据集，零 LLM 消耗）

```bash
# 入库 1970 年以来所有展览（~716 条，秒级完成）
python run_collector.py --site moma --since 1970

# 入库全量 1929-1989（~1,727 条展览，含完整艺术家名录）
python run_collector.py --site moma --since 1929
```

### M+ Museum（全历史，LLM 解析）

```bash
# 全量：当前 + 历史共 38 个展览
python run_collector.py --site mplus
```

> ⚠️ 需要网络稳定（Gemini API），DNS 故障时部分失败，重跑会自动跳过已入库项。

### Serpentine Galleries（归档分页，最多 142 页）

```bash
# 默认：当前展览 + 15 页历史归档（约 150 个展览）
python run_collector.py --site serpentine

# 只要近 5 年的历史
python run_collector.py --site serpentine --since 2020
```

### Tate Modern（年份分页）

```bash
# 采集 2015 年以来的展览（自动生成年份 URL）
python run_collector.py --site tate --since 2015
```

---

## 查询数据库

```bash
# 快速统计
python -c "
import sqlite3
conn = sqlite3.connect('exhibitions.db')
print('展览数:', conn.execute('SELECT count(*) FROM exhibitions').fetchone()[0])
print('作品数:', conn.execute('SELECT count(*) FROM artworks').fetchone()[0])
for row in conn.execute('SELECT source, count(*) FROM exhibitions GROUP BY source ORDER BY 2 DESC'):
    print(f'  {row[0]}: {row[1]}')
"

# 查询特定艺术家
python -c "
import sqlite3
conn = sqlite3.connect('exhibitions.db')
conn.row_factory = sqlite3.Row
for row in conn.execute(\"SELECT e.title, e.source, e.start_date, a.work_title, a.medium FROM artworks a JOIN exhibitions e ON a.exhibition_id=e.id WHERE a.artist_name LIKE '%Rothko%'\"):
    print(dict(row))
"
```

---

## 常见问题

### `[Errno 8] nodename nor servname provided`

Gemini API 的 DNS 解析间歇性失败（Mac 网络问题）。解决方法：

```bash
# 重新运行，已入库的展览自动跳过
python run_collector.py --site mplus
```

### 展览重复入库

系统以 `url` 字段为唯一键自动去重。使用 `--force` 可强制覆盖。

### 某站点返回 0 条展览

检查该机构网站是否有反爬策略变化，或使用 `--verbose` 查看详细错误。
