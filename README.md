# GoldPulse 金价哨兵

现货金价监控与阈值提醒 —— 自动化微 SaaS 的 MVP（v0）。
全部跑在 GitHub Actions 免费额度上：**0 服务器成本**。

## 产品规格 v0

| 项 | 说明 |
|---|---|
| 输入 | 多源现货金价，自动降级：Binance.US PAXG → Binance PAXG → goldprice.org（PAXG = 1 金衡盎司实物金） |
| 调度 | GitHub Actions 每 30 分钟一次（`*/30 * * * *`） |
| 规则 | `config/alerts.json` 里的阈值规则（above/below） |
| 输出 | `data/last_check.json` + `docs/data.json`（最新价、各源读数、触发记录，自动回写仓库） |
| 提醒 | 配置仓库 Secret `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` 后，触发即发 Telegram |
| 成本 | $0（公开仓库的 Actions 不限量） |

## 本地自测

```bash
python fetch_price.py
```

纯 Python 标准库，无第三方依赖。

## 已知注意

- PAXG 为现货参考价；不同交易所价差会记录在 `all_sources` 字段用于交叉验证。
- GitHub 定时任务可能有 0~30 分钟延迟，属正常现象。

## 路线图

- [x] v0 自动抓价 + 阈值引擎 + 自动流水线
- [ ] v1 GitHub Pages 落地页上线（docs/index.html 已就位）
- [ ] v2 Telegram 提醒通道接入
- [ ] v3 收款（订阅）→ 对外售卖
