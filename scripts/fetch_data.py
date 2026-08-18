#!/usr/bin/env python3
"""
fetch_data.py — Liquid-Glass-Profil 数据仓库
==========================================
职责: 定时从 BCLC Keno 数据源获取20个原始号码，
      按官方规则计算三球(b1/b2/b3)和特码(sum)，
      写入 data/latest.json 供其他仓库读取。

BCLC官方规则:
  20个号码从小到大排序后:
  b1 = (第2+5+8+11+14+17位) % 10
  b2 = (第3+6+9+12+15+18位) % 10
  b3 = (第4+7+10+13+16+19位) % 10
  sum = b1 + b2 + b3

由 GitHub Actions 每5分钟触发一次。
"""
import json
import time
import sys
import os
from pathlib import Path

# 导入同目录的 bclc_calc 模块
sys.path.insert(0, str(Path(__file__).parent))
from bclc_calc import BCLCCalc

# ============================================================
# 配置
# ============================================================
# Keno 原始数据接口（返回20个号码）
KENO_SOURCES = [
    "https://pc28.help/api/keno.json?nbr=60",
    "https://yu28.top/api/bclc?count=60&key=yu28-f9f41d673b447fac",
]

# 输出路径
OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "latest.json"

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 3
TIMEOUT = 10

# ============================================================
# 数据获取
# ============================================================
def fetch_keno_data(url: str) -> list:
    """从单个URL获取并解析Keno数据"""
    import urllib.request
    import urllib.error

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "LiquidGlass-Profil/2.0",
            "Accept": "application/json",
        }
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        raw = json.loads(resp.read().decode("utf-8"))

    # 解析各种格式
    items = raw.get("data") or raw.get("list") or raw.get("results") or []
    if not items and isinstance(raw, list):
        items = raw

    results = []
    for item in items:
        try:
            nbr = str(item.get("nbr") or item.get("issue") or item.get("period") or "")
            if not nbr:
                continue

            # 获取20个号码
            nums = (
                item.get("nums") or
                item.get("numbers") or
                item.get("raw") or
                item.get("rawNums") or
                item.get("nbrs")
            )

            # 尝试从字符串解析
            if not nums:
                num_str = item.get("num") or item.get("numbers_str") or ""
                if isinstance(num_str, str) and "," in num_str:
                    nums = [int(x) for x in num_str.split(",")]

            if not nums or len(nums) < 20:
                # 号码不够20个，尝试从number反推
                number_str = item.get("number") or ""
                if "+" in str(number_str):
                    parts = str(number_str).split("+")
                    if len(parts) == 3:
                        b1, b2, b3 = int(parts[0]), int(parts[1]), int(parts[2])
                        s = b1 + b2 + b3
                        results.append({
                            "nbr": nbr,
                            "date": item.get("date") or "",
                            "time": item.get("time") or "",
                            "b1": b1, "b2": b2, "b3": b3,
                            "sum": s,
                            "combination": item.get("combination") or BCLCCalc._combo_of(s),
                            "nbrs": [],
                        })
                continue

            # 转换为整数并排序
            nums = [int(x) for x in nums[:20]]
            sorted_nums = sorted(nums)

            # 用BCLC官方规则计算
            balls = BCLCCalc.calc_balls(sorted_nums)
            s = balls["sum"]

            combo = item.get("combination") or BCLCCalc._combo_of(s)

            results.append({
                "nbr": nbr,
                "date": item.get("date") or "",
                "time": item.get("time") or "",
                "b1": balls["b1"],
                "b2": balls["b2"],
                "b3": balls["b3"],
                "sum": s,
                "combination": combo,
                "nbrs": sorted_nums,
            })

        except Exception as e:
            print(f"  [WARN] 解析条目失败: {e}")
            continue

    return results


def fetch_with_retry() -> list:
    """遍历所有数据源，带重试"""
    for url in KENO_SOURCES:
        for attempt in range(MAX_RETRIES):
            try:
                print(f"  [FETCH] 尝试: {url} (第{attempt+1}次)")
                data = fetch_keno_data(url)
                if data:
                    print(f"  [OK] 获取 {len(data)} 条有效数据")
                    return data
                else:
                    print(f"  [WARN] 返回空数据")
            except Exception as e:
                print(f"  [ERR] {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    return []


# ============================================================
# 输出构建
# ============================================================
def build_output(data: list) -> dict:
    """构建标准输出JSON"""
    bjt = BCLCCalc.now_bjt()
    per, cd, next_draw, seq, sess_start = BCLCCalc.period_info(bjt)
    is_dst = BCLCCalc.is_dst(bjt.astimezone(__import__('datetime').timezone.utc))
    tz_name = "PDT" if is_dst else "PST"

    m, s = divmod(cd, 60)
    cd_str = f"{m}:{s:02d}"

    # 按期号升序排列（最旧的在前，最新的在最后）
    data.sort(key=lambda x: int(x["nbr"]))

    return {
        "countdown": cd_str,
        "current_period": per,
        "next_draw": next_draw.strftime("%Y-%m-%d %H:%M:%S"),
        "is_open": BCLCCalc.is_open(bjt),
        "timezone": tz_name,
        "source": "BCLC Keno 官方规则 · Liquid-Glass-Profil",
        "rule": "b1=(pos2+5+8+11+14+17)%10, b2=(pos3+6+9+12+15+18)%10, b3=(pos4+7+10+13+16+19)%10",
        "updated": int(time.time()),
        "fetched_at": bjt.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(data),
        "data": [
            {
                "nbr": d["nbr"],
                "date": d.get("date", ""),
                "time": d.get("time", ""),
                "number": f"{d['b1']}+{d['b2']}+{d['b3']}",
                "num": d["sum"],
                "combination": d.get("combination", ""),
                "b1": d["b1"],
                "b2": d["b2"],
                "b3": d["b3"],
                "nbrs": d.get("nbrs", []),
            }
            for d in data
        ],
        "message": "success" if data else "no_data",
    }


# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 60, flush=True)
    print("  Liquid-Glass-Profil · BCLC 官方规则数据采集", flush=True)
    print(f"  时间: {BCLCCalc.now_bjt().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 60, flush=True)

    # 1. 获取原始数据
    data = fetch_with_retry()

    if not data:
        print("\n  [WARN] 所有数据源失败，保留旧数据", flush=True)
        if OUTPUT_FILE.exists():
            print(f"  [KEEP] 旧文件保留: {OUTPUT_FILE}", flush=True)
            return 0
        else:
            print("  [ERR] 无旧数据可保留", flush=True)
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            with open(OUTPUT_FILE, "w") as f:
                json.dump({"message": "no_data", "count": 0, "data": []}, f)
            return 1

    # 2. 构建输出
    output = build_output(data)

    # 3. 写入文件
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    size = OUTPUT_FILE.stat().st_size
    latest = data[-1] if data else None
    print(f"\n  ✅ 写入: {OUTPUT_FILE} ({size} bytes)", flush=True)
    if latest:
        print(f"  ✅ 最新: 期{latest['nbr']} {latest['b1']}+{latest['b2']}+{latest['b3']}={latest['sum']} {latest.get('combination','')}", flush=True)
    print(f"  ✅ 共 {len(data)} 期 | 倒计时: {output['countdown']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
