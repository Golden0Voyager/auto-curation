#!/usr/bin/env python3
"""二次诊断：对 Red 站点延长超时并获取详细错误信息"""

import subprocess
import concurrent.futures
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Red sites from first smoke test
RED_SITES = [
    # TIMEOUT - retry with longer timeout
    "documenta", "istanbul_biennale", "lenbachhaus", "maiiam", "serpentine",
    # ZERO_URLS - need diagnosis
    "flv", "gwangju_biennale", "hirshhorn", "leeum", "lyon_biennale",
    "mca_australia", "met", "mmcaseoul", "momat", "new_museum", "nga",
    "palaistokyo", "pompidou", "psa", "sharjah_biennale", "taipei_biennale",
    "whitney_biennial",
    # BLOCKED - confirm classification
    "dia", "guggenheim", "hayward", "lacma", "mass_moca", "pinakothek",
    "whitechapel", "hamburger_bahnhof", "saopaulo_biennial",
]

TIMEOUT_SECONDS = 90  # Extended timeout for retries
MAX_WORKERS = 6


def diagnose_site(site: str) -> dict:
    start = time.time()
    result = {
        "site": site,
        "urls_found": 0,
        "status": "unknown",
        "error_type": None,
        "error_detail": None,
        "fixable": False,
        "suggestion": None,
        "elapsed": 0.0,
    }

    cmd = [
        sys.executable, "run_collector.py",
        "--site", site,
        "--limit", "1",
        "--dry-run"
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        elapsed = time.time() - start
        result["elapsed"] = round(elapsed, 2)

        stdout = proc.stdout
        stderr = proc.stderr
        combined = stdout + "\n" + stderr

        # Extract URL count
        url_count = 0
        for line in combined.splitlines():
            if "发现 URL" in line or "发现URL" in line:
                try:
                    url_count = int(line.split(":")[-1].strip())
                except (ValueError, IndexError):
                    pass
            elif "'discovered':" in line:
                try:
                    url_count = int(line.split("'discovered':")[1].split(",")[0].strip())
                except (ValueError, IndexError):
                    pass

        result["urls_found"] = url_count

        # Analyze error type
        if "403" in combined and ("cloudflare" in combined.lower() or "blocked" in combined.lower()):
            result["status"] = "BLOCKED_403"
            result["error_type"] = "cloudflare"
            result["fixable"] = False
            result["suggestion"] = "标记为 BLOCKED_CLOUDFLARE，寻找替代数据源"
        elif "403" in combined:
            result["status"] = "BLOCKED_403"
            result["error_type"] = "http_403"
            result["fixable"] = False
            result["suggestion"] = "服务器拒绝访问，可能需要更强的反爬策略"
        elif "SSL" in combined.upper() or "CERTIFICATE" in combined.upper():
            result["status"] = "BLOCKED_SSL"
            result["error_type"] = "ssl_error"
            result["fixable"] = True
            result["suggestion"] = "尝试 verify=False"
        elif "Playwright" in combined and "required" in combined:
            result["status"] = "NEEDS_PLAYWRIGHT"
            result["error_type"] = "playwright_missing"
            result["fixable"] = True
            result["suggestion"] = "安装 Playwright: uv pip install playwright && python -m playwright install"
        elif "timeout" in combined.lower() or elapsed >= TIMEOUT_SECONDS - 1:
            result["status"] = "TIMEOUT"
            result["error_type"] = "slow_response"
            result["fixable"] = False
            result["suggestion"] = "网站响应极慢，可能需要更长的超时或替代数据源"
        elif url_count == 0:
            result["status"] = "ZERO_URLS"
            # Check for specific error patterns
            if "No exhibition URLs discovered" in combined:
                result["error_type"] = "no_urls_found"
                result["fixable"] = True
                result["suggestion"] = "检查 link_patterns 是否匹配当前网站结构"
            elif "Error fetching" in combined:
                result["error_type"] = "fetch_error"
                result["fixable"] = True
                result["suggestion"] = "检查 URL 是否可达、网站是否重构"
            elif "JSON" in combined.upper() and "decode" in combined.lower():
                result["error_type"] = "json_decode"
                result["fixable"] = True
                result["suggestion"] = "API 返回格式变化，需要更新解析逻辑"
            else:
                result["error_type"] = "unknown"
                result["fixable"] = False
                result["suggestion"] = "需要手动查看输出"
        else:
            result["status"] = "PASS"
            result["fixable"] = False
            result["suggestion"] = "重试成功"

        # Capture key error lines
        error_lines = []
        for line in combined.splitlines():
            if any(k in line for k in ["ERROR", "Error", "exception", "Exception", "Failed", "failed"]):
                if len(error_lines) < 3:
                    error_lines.append(line.strip()[:200])
        result["error_detail"] = " | ".join(error_lines) if error_lines else None

    except subprocess.TimeoutExpired:
        result["status"] = "TIMEOUT"
        result["elapsed"] = round(time.time() - start, 2)
        result["error_type"] = "slow_response"
        result["fixable"] = False
        result["suggestion"] = f"{TIMEOUT_SECONDS}s 仍超时，网站极慢或不可用"
    except Exception as e:
        result["status"] = "ERROR"
        result["elapsed"] = round(time.time() - start, 2)
        result["error_type"] = "exception"
        result["error_detail"] = str(e)[:200]

    return result


def main():
    print(f"Red Site Diagnosis started at {datetime.now().isoformat()}")
    print(f"Sites: {len(RED_SITES)} | Timeout: {TIMEOUT_SECONDS}s | Workers: {MAX_WORKERS}")
    print("=" * 70)

    results = []
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_site = {
            executor.submit(diagnose_site, site): site
            for site in RED_SITES
        }
        for future in concurrent.futures.as_completed(future_to_site):
            site = future_to_site[future]
            try:
                res = future.result()
                results.append(res)
                completed += 1
                fix_tag = "FIXABLE" if res["fixable"] else "-"
                print(
                    f"[{completed:2d}/{len(RED_SITES)}] "
                    f"{res['site']:20s} | "
                    f"{res['status']:15s} | "
                    f"URLs: {res['urls_found']:3d} | "
                    f"{fix_tag:7s} | "
                    f"{res['elapsed']:5.1f}s"
                )
            except Exception as e:
                print(f"[{completed:2d}/{len(RED_SITES)}] {site:20s} | EXCEPTION: {e}")

    # Sort and summarize
    results.sort(key=lambda r: r["site"])

    fixable = [r for r in results if r["fixable"]]
    unfixable = [r for r in results if not r["fixable"] and r["urls_found"] == 0]
    recovered = [r for r in results if r["urls_found"] > 0]

    print("\n" + "=" * 70)
    print("DIAGNOSIS SUMMARY")
    print("=" * 70)
    print(f"Recovered:   {len(recovered):2d} (previously red, now have URLs)")
    print(f"Fixable:     {len(fixable):2d} (can be fixed with code changes)")
    print(f"Unfixable:   {len(unfixable):2d} (external blockers)")

    if recovered:
        print("\n## Recovered Sites\n")
        for r in recovered:
            print(f"- `{r['site']}` — {r['urls_found']} URLs ({r['elapsed']}s)")

    if fixable:
        print("\n## Fixable Sites\n")
        for r in fixable:
            print(f"- `{r['site']}` — {r['error_type']} — {r['suggestion']}")

    if unfixable:
        print("\n## Blocked Sites (External)\n")
        for r in unfixable:
            print(f"- `{r['site']}` — {r['status']} — {r['suggestion'] or 'No suggestion'}")

    # Save report
    report_path = Path("docs/plans/smoke-test-diagnosis.md")
    lines = [
        "# Red Site Diagnosis Report",
        f"\nGenerated: {datetime.now().isoformat()}",
        f"\n## Summary\n",
        f"| Category | Count |",
        f"|----------|------:|",
        f"| Recovered | {len(recovered)} |",
        f"| Fixable | {len(fixable)} |",
        f"| Blocked | {len(unfixable)} |",
    ]

    if recovered:
        lines.append("\n## Recovered\n")
        for r in recovered:
            lines.append(f"- `{r['site']}` — {r['urls_found']} URLs in {r['elapsed']}s")

    if fixable:
        lines.append("\n## Fixable\n")
        for r in fixable:
            lines.append(f"- `{r['site']}` — {r['error_type']} — {r['suggestion']}")
            if r["error_detail"]:
                lines.append(f"  - Error: `{r['error_detail']}`")

    if unfixable:
        lines.append("\n## Blocked (External)\n")
        for r in unfixable:
            lines.append(f"- `{r['site']}` — {r['status']}")

    lines.append("\n## Raw Data\n")
    lines.append("```json")
    lines.append(json.dumps(results, indent=2, ensure_ascii=False))
    lines.append("```\n")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nDiagnosis saved to: {report_path}")


if __name__ == "__main__":
    main()
