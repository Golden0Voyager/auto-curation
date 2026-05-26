#!/usr/bin/env python
import argparse
import asyncio
import sys
import logging
from datetime import date
from src.scraper import ExhibitionScraper
from src.sites import SITES

def setup_logging(verbose: bool):
    """Configures clean, informative logging to standard output."""
    level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=log_format, handlers=[
        logging.StreamHandler(sys.stdout)
    ])

def list_registered_sites():
    """Prints all registered institutions and their capabilities."""
    from src.sites.base import ParserStrategy

    print(f"\n🏛️  Registered Contemporary Art Institutions ({len(SITES)} sites):")
    print("-" * 70)
    for key, parser in sorted(SITES.items()):
        strategy = getattr(parser, 'strategy', ParserStrategy.HTML_LLM)
        strategy_label = strategy.value

        # Historical support detection
        has_history = bool(
            getattr(parser, 'extra_list_urls', [])
            or 'get_list_urls' in parser.__class__.__dict__
            or strategy in (ParserStrategy.CSV_LOCAL, ParserStrategy.CSV_REMOTE, ParserStrategy.REST_API, ParserStrategy.SPARQL)
        )
        hist = "✅ 历史档案支持" if has_history else "⚠️  仅当前展览"

        # Institution type badge
        itype = getattr(parser, 'institution_type', 'museum')
        type_badge = ""
        if itype == 'biennial':
            type_badge = " [双年展]"
        elif itype == 'triennial':
            type_badge = " [三年展]"

        print(f" - {key:<18}: {parser.source:<26} ({parser.city}) | {strategy_label:<12} | {hist}{type_badge}")
    print("-" * 70)
    print("Usage: --site <key> [--since YEAR]  (e.g., --site mplus --since 2015)\n")

def main():
    arg_parser = argparse.ArgumentParser(
        description=(
            "Auto Curation Collector — 智能当代艺术展览数据采集系统\n"
            "抓取全球 10 大顶级艺术机构的展览数据（含历史记录）并结构化存储至 SQLite。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    group = arg_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--site", type=str, help="抓取指定机构 (e.g. 'moma', 'tate', 'mplus')")
    group.add_argument("--all", action="store_true", help="抓取全部 10 大机构")
    group.add_argument("--list-sites", action="store_true", help="列出所有机构及其历史数据支持情况")
    
    arg_parser.add_argument(
        "--since",
        type=int,
        default=None,
        metavar="YEAR",
        help="只抓取该年份及之后的展览 (e.g. --since 2015)。支持机构：moma/tate/mori/mplus"
    )
    arg_parser.add_argument("--limit", type=int, default=None, help="每个机构最多处理的展览页面数（不设则全量抓取）")
    arg_parser.add_argument("--force", action="store_true", help="重新抓取已存入 DB 的展览（跳过去重检查）")
    arg_parser.add_argument("--dry-run", action="store_true", help="模拟运行：只抓取和解析，不写入数据库")
    arg_parser.add_argument("--verbose", action="store_true", help="输出详细 DEBUG 日志")
    arg_parser.add_argument("--concurrent", action="store_true", help="启用异步并发采集（仅对 HTML 策略生效）")
    arg_parser.add_argument("--db", type=str, default="exhibitions.db", help="SQLite 数据库文件路径（默认: exhibitions.db）")

    args = arg_parser.parse_args()
    setup_logging(args.verbose)

    if args.list_sites:
        list_registered_sites()
        return

    # Validate --since year
    if args.since:
        current_year = date.today().year
        if args.since < 1900 or args.since > current_year:
            print(f"❌ 无效的年份: {args.since}. 请输入 1900–{current_year} 之间的年份。")
            sys.exit(1)
        print(f"📅 时间范围过滤: 仅采集 {args.since} 年及以后的展览")

    # Initialize orchestrator
    scraper = ExhibitionScraper(args.db)
    
    try:
        if args.all:
            print(f"🚀 全量采集所有 10 大机构中... 数据库: {args.db}")
            if args.dry_run:
                print("⚠️  [DRY-RUN] 模拟运行，不写入数据库。")
            if args.concurrent:
                results = asyncio.run(scraper.ascrape_all_sites(
                    limit_per_site=args.limit,
                    force=args.force,
                    dry_run=args.dry_run,
                    since_year=args.since
                ))
            else:
                results = scraper.scrape_all_sites(
                    limit_per_site=args.limit,
                    force=args.force,
                    dry_run=args.dry_run,
                    since_year=args.since
                )

            print("\n📊 全量采集汇总报告:")
            print("=" * 70)
            total_saved = 0
            for res in results:
                if "error" in res:
                    continue
                total_saved += res.get("saved", 0)
                print(
                    f" {res['site']:<25}: 发现={res['discovered']:<4} "
                    f"跳过={res['skipped']:<4} 解析={res['parsed']:<4} "
                    f"存入={res['saved']:<4} 失败={res['failed']:<4}"
                )
            print("=" * 70)
            print(f" 本次总计新增入库展览: {total_saved} 条")
            print("=" * 70)
            
        elif args.site:
            site_key = args.site.lower().strip()
            if site_key not in SITES:
                print(f"❌ 未注册的机构 key: '{args.site}'")
                list_registered_sites()
                sys.exit(1)
                
            print(f"🚀 采集 {SITES[site_key].source}... 数据库: {args.db}")
            if args.dry_run:
                print("⚠️  [DRY-RUN] 模拟运行，不写入数据库。")

            if args.concurrent:
                res = asyncio.run(scraper.ascrape_site(
                    site_key,
                    limit=args.limit,
                    force=args.force,
                    dry_run=args.dry_run,
                    since_year=args.since
                ))
            else:
                res = scraper.scrape_site(
                    site_key,
                    limit=args.limit,
                    force=args.force,
                    dry_run=args.dry_run,
                    since_year=args.since
                )

            print("\n📊 采集结果报告:")
            print("=" * 50)
            print(f" 机构名称   : {res['site']}")
            print(f" 发现 URL数  : {res['discovered']}")
            print(f" 跳过（已存）: {res['skipped']}")
            print(f" 成功解析   : {res['parsed']}")
            print(f" 存入数据库  : {res['saved']}")
            print(f" 失败       : {res['failed']}")
            print("=" * 50)
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断，安全退出。")
    finally:
        scraper.close()
        
        # Print current DB stats
        from src.database import ExhibitionDatabase
        db = ExhibitionDatabase(args.db)
        ex_count = db.count_exhibitions()
        art_count = db.count_artworks()
        print(f"\n📦 数据库当前状态: 展览 {ex_count} 条 | 作品 {art_count} 条 | 路径: {args.db}")
        print("🏁 采集任务完成。")

if __name__ == "__main__":
    main()
