# 📔 Rosa Diary Bot

個人日記自動化系統——透過 Telegram 語音輸入日記，自動存入 Notion，並定時提醒寫日記。

---

## 專案動機

希望讓日記記錄更低摩擦、更容易持續。過去手動開 App、建頁面的流程容易中斷，想透過 Telegram Bot 降低記錄門檻，並用自動提醒養成習慣。

---

## 功能

- **Telegram → Notion**：直接在 Telegram 傳文字（或語音轉文字），自動存入 Notion 日記資料庫
- **每日 11:30 提醒**：Bot 主動傳送今日引導問題，提醒記錄當天的事
- **隨時詢問摘要**：透過 Claude Code + Notion MCP 手動請 AI 整理日記摘要與洞察

---

## 系統架構

```
Telegram Bot
    │
    ├── 傳訊息 → GitHub Actions（每 5 分鐘輪詢）→ Notion Diary DB
    │
    └── 收通知 ← GitHub Actions（排程）
                    ├── 每日 23:30 → 引導問題提醒
                    ├── 每週六 00:00 → 週報（已暫停）
                    └── 每月底 00:00 → 月報（已暫停）

Claude Code + Notion MCP → 手動詢問日記摘要
```

---

## 技術棧

| 工具 | 用途 |
|------|------|
| Python | 核心腳本 |
| Telegram Bot API | 訊息接收與發送 |
| Notion API | 日記資料庫讀寫 |
| GitHub Actions | 雲端排程執行（免費） |
| Claude Code + MCP | AI 輔助日記摘要分析 |

---

## 學到什麼

- 如何設計一個低成本、全雲端的個人自動化系統
- Telegram Bot API 的訊息處理與輪詢機制
- Notion API 的資料庫查詢與頁面建立
- GitHub Actions 的排程設定（cron）與 Secrets/Variables 管理
- MCP（Model Context Protocol）讓 AI 直接讀取外部資料來源

---

## 建立日期

2026 年 4 月 | 使用工具：Claude Code
