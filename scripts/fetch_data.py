#!/usr/bin/env python3
"""
Orbit星轨引擎 · 后台数据抓取脚本
由 GitHub Actions 定时调用，抓取最新开奖数据并提交到仓库
这样即使没有人打开网页，数据也会持续更新
"""
import json
import urllib.request
import urllib.error
import time
import sys
from pathlib import Path

API_URL = "https://pc28.help/api/kj.json?nbr=60"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "latest.json"

def fetch_data():
    """抓取API数据，带超时和重试"""
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                API_URL,
                headers={"User-Agent": "Orbit-Engine-Bot/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data and isinstance(data.get("data"), list) and len(data["data"]) > 0:
                    return data
                else:
                    print(f"Attempt {attempt+1}: 数据为空或格式错误")
        except Exception as e:
            print(f"Attempt {attempt+1} 失败: {e}")
        if attempt < 2:
            time.sleep(2)

    return None

def main():
    print("=== Orbit星轨引擎 数据抓取 ===")
    data = fetch_data()
    if not data:
        print("所有重试失败，保留旧数据")
        sys.exit(0)  # 不返回错误，避免Actions报错

    # 添加更新时间戳
    data["updated"] = int(time.time())
    data["fetched_at"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    # 确保输出目录存在
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 写入文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    print(f"成功抓取 {len(data['data'])} 条数据")
    print(f"最新期号: {data['data'][0].get('nbr', 'unknown')}")
    print(f"倒计时: {data.get('countdown', 'unknown')}")
    print(f"写入: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
