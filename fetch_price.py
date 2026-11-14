#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GoldPulse — 现货金价抓取与阈值提醒 (MVP v0)

多源自动降级（顺序即优先级，第一个成功者作为基准价）:
  1. Binance.US  PAXG/USDT  (美国合规站, GitHub Actions 可达)
  2. Binance     PAXG/USDT  (1 PAXG = 1 金衡盎司实物金)
  3. goldprice.org           (需浏览器 UA, 部分网络 Forbidden)

每次运行会尝试全部数据源，把各源读数记入 data/last_check.json 的
all_sources 字段 —— 用于交叉验证不同交易所报价是否一致。
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; GoldPulse/0.1)"}


def http_get(url, timeout=10):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_binance_us():
    d = json.loads(http_get("https://api.binance.us/api/v3/ticker/price?symbol=PAXGUSDT"))
    return float(d["price"])


def fetch_binance_com():
    d = json.loads(http_get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT"))
    return float(d["price"])


def fetch_goldprice_org():
    d = json.loads(http_get("https://data-asg.goldprice.org/dbXRates/USD"))
    return float(d["items"][0]["xauPrice"])


SOURCES = [("binance.us-paxg", fetch_binance_us),
           ("binance.com-paxg", fetch_binance_com),
           ("goldprice.org", fetch_goldprice_org)]


def get_price():
    """返回 (基准价, 基准源名, 全源读数 dict)"""
    readings, errors = {}, []
    primary_price, primary_name = None, None
    for name, fn in SOURCES:
        try:
            p = fn()
            readings[name] = round(p, 2)
            if primary_price is None:
                primary_price, primary_name = p, name
        except Exception as e:  # noqa: BLE001
            readings[name] = None
            errors.append(f"{name}: {type(e).__name__}: {e}")
    if primary_price is None:
        raise RuntimeError("all sources failed -> " + " | ".join(errors))
    return primary_price, primary_name, readings


def load_config(path="config/alerts.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_thresholds(price, cfg):
    fired = []
    for rule in cfg.get("rules", []):
        if not rule.get("enabled", True):
            continue
        level = float(rule["level"])
        hit = price >= level if rule["op"] == "above" else price <= level
        if hit:
            fired.append({"name": rule["name"], "op": rule["op"],
                          "level": level, "price": round(price, 2)})
    return fired


def notify(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    if token and chat:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        body = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=body, headers=UA), timeout=15)
        return "telegram"
    return "stdout (未配置 TELEGRAM_BOT_TOKEN)"


def main():
    price, source, readings = get_price()
    fired = check_thresholds(price, load_config())
    record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "price": round(price, 2), "source": source,
              "all_sources": readings, "fired": fired}
    os.makedirs("data", exist_ok=True)
    with open("data/last_check.json", "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    print(json.dumps(record, ensure_ascii=False))
    if fired:
        msg = "💰 GoldPulse 触发提醒\n" + "\n".join(
            f"{x['name']}: 现价 {x['price']} ({x['op']} {x['level']})" for x in fired)
        print("notify ->", notify(msg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
