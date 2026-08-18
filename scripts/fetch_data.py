#!/usr/bin/env python3
"""
Orbit星轨引擎 · 后台数据抓取脚本（BCLC 原始规则版）
========================================================
数据链路：
  BCLC Keno 官方开奖(20个号码) → pc28.help/api/keno.json → 本脚本
  → 用 BCLC 官方规则算出三球 → 写入 data/latest.json

计算规则（加拿大PC28官方算法）：
  20个号码升序排列后：
  - b1 = (第2+5+8+11+14+17位 之和) % 10
  - b2 = (第3+6+9+12+15+18位 之和) % 10
  - b3 = (第4+7+10+13+16+19位 之和) % 10
  - sum = b1 + b2 + b3

由 GitHub Actions 定时调用（每3.5分钟），即使没人打开网页数据也持续更新。
"""
import json
import time
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 允许直接运行和作为模块导入
sys.path.insert(0, str(Path(__file__).parent))
from bclc_calc import calc_pc28, calc_from_keno_list

# ============================================================
# 配置
# ============================================================
# 首选：pc28.help 的 keno 接口（返回20个原始号码）
KENO_API = "https://pc28.help/api/keno.json?nbr=60"
# 备用：pgsoft 的 keno 数据
BACKUP_API = "http://api.pgsoft.one/api/28/keno?limit=60"

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "latest.json"

# 北京时间
BJT = timezone(timedelta(hours=8))

# ============================================================
# 抓取
# ============================================================
def _fetch_url(url: str, headers: dict = None) -> dict:
    """用 urllib 抓取 JSON，返回 dict"""
    import urllib.request
    import urllib.error

    req = urllib.request.Request(
        url,
        headers=headers or {"User-Agent": "Orbit-Engine-Bot/2.0 (BCLC-Rule)"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_keno_data() -> dict:
    """从 pc28.help 抓取 Keno 原始数据，带重试"""
    last_err = None
    for attempt in range(3):
        try:
            print(f"  [尝试 {attempt+1}/3] GET {KENO_API}")
            data = _fetch_url(KENO_API)
            if data and isinstance(data.get("data"), list) and len(data["data"]) > 0:
                print(f"  ✅ 成功获取 {len(data['data'])} 条 Keno 原始数据")
                return data
            else:
                print(f"  ⚠ 数据为空或格式异常: {str(data)[:100]}")
                last_err = "empty data"
        except Exception as e:
            last_err = str(e)
            print(f"  ❌ 失败: {e}")
        if attempt < 2:
            time.sleep(3)
    raise RuntimeError(f"所有重试失败: {last_err}")


# ============================================================
# 解析 + 计算
# ============================================================
def parse_keno_to_pc28(keno_json: dict) -> dict:
    """
    将 keno 原始数据按 BCLC 规则转换为 PC28 三球格式
    输入：{"data": [{"nbr": "...", "nbrs": [...20个号码...], ...}, ...]}
    输出：与现有 latest.json 格式完全兼容的 dict
    """
    raw_list = keno_json.get("data", [])
    converted = []

    for item in raw_list:
        try:
            # 提取20个原始号码
            nbrs = item.get("nbrs") or item.get("numbers") or item.get("nums")
            if not nbrs:
                continue
            # 统一转为 int 列表
            if isinstance(nbrs, str):
                nbrs = [int(x.strip()) for x in nbrs.replace("+", ",").split(",") if x.strip().isdigit()]
            nbrs = sorted(int(x) for x in nbrs)

            if len(nbrs) != 20:
                print(f"  ⚠ 期号 {item.get('nbr','?')} 号码数={len(nbrs)}，跳过")
                continue

            # 用 BCLC 规则计算三球
            calc = calc_pc28(nbrs)

            converted.append({
                "nbr": str(item.get("nbr") or item.get("period") or item.get("issue") or ""),
                "date": str(item.get("date") or ""),
                "time": str(item.get("time") or item.get("opentime") or ""),
                "number": calc["number"],       # "8+8+4"
                "num": calc["num"],             # "20"
                "combination": calc["combination"],  # "大双"
                "nbrs": nbrs,                  # 保留20个原始号码
            })
        except Exception as e:
            print(f"  ⚠ 解析一期失败: {e}")
            continue

    if not converted:
        raise RuntimeError("没有成功解析出任何一期数据")

    # 组装输出（与现有 latest.json 格式兼容）
    now_bjt = datetime.now(BJT).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "countdown": keno_json.get("countdown", "03:30"),
        "data": converted,
        "message": "success",
        "updated": int(time.time()),
        "fetched_at": now_bjt,
        "rule": "BCLC-official",  # 标记使用官方规则
    }


# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 55)
    print("  Orbit星轨引擎 · BCLC 官方规则数据抓取")
    print("=" * 55)

    # 1. 抓取 Keno 原始数据
    print("\n📡 步骤1: 抓取 Keno 20个原始号码...")
    try:
        keno_json = fetch_keno_data()
    except Exception as e:
        print(f"\n❌ 抓取失败: {e}")
        print("   保留旧数据，退出码0（避免Actions报错）")
        sys.exit(0)

    # 2. 用 BCLC 规则计算三球
    print("\n🧮 步骤2: 用 BCLC 官方规则计算三球...")
    result = parse_keno_to_pc28(keno_json)
    print(f"  ✅ 成功转换 {len(result['data'])} 期")
    latest = result["data"][0]
    print(f"  最新一期: 期号={latest['nbr']} 号码={latest['number']} 和值={latest['num']} 形态={latest['combination']}")

    # 3. 写入文件
    print(f"\n💾 步骤3: 写入 {OUTPUT_FILE}...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))

    print(f"  ✅ 写入完成")
    print(f"\n🎉 全部完成！规则=BCLC-official, 数据量={len(result['data'])}期")


if __name__ == "__main__":
    main()
