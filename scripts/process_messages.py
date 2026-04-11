import os
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
NOTION_TOKEN = os.environ['NOTION_TOKEN']
DIARY_DB_ID = os.environ['DIARY_DB_ID']
LAST_OFFSET = int(os.environ.get('LAST_OFFSET', '0'))
GH_TOKEN = os.environ.get('GH_TOKEN', '')
GH_REPO = os.environ.get('GH_REPO', '')

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


def send_message(text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text}
    )


def save_to_notion(topic, content):
    today = datetime.now().strftime('%Y-%m-%d')
    res = requests.post(
        "https://api.notion.com/v1/pages",
        headers=NOTION_HEADERS,
        json={
            "parent": {"database_id": DIARY_DB_ID},
            "properties": {
                "Topic": {"title": [{"text": {"content": topic}}]},
                "Content": {"rich_text": [{"text": {"content": content}}]},
                "Created Date": {"date": {"start": today}}
            }
        }
    )
    return res.status_code == 200


def update_offset(new_offset):
    if not GH_TOKEN or not GH_REPO:
        return
    requests.patch(
        f"https://api.github.com/repos/{GH_REPO}/actions/variables/LAST_OFFSET",
        headers={
            "Authorization": f"Bearer {GH_TOKEN}",
            "Accept": "application/vnd.github+json"
        },
        json={"name": "LAST_OFFSET", "value": str(new_offset)}
    )


def process_updates():
    res = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
        params={"offset": LAST_OFFSET, "timeout": 0}
    )
    updates = res.json().get('result', [])

    if not updates:
        print("沒有新訊息")
        return

    new_offset = LAST_OFFSET
    for update in updates:
        new_offset = update['update_id'] + 1
        message = update.get('message', {})
        chat_id = str(message.get('chat', {}).get('id', ''))

        if chat_id != str(CHAT_ID):
            continue

        if 'text' in message:
            text = message['text']

            if text.startswith('/start'):
                send_message(
                    "👋 嗨 Rosa！我是你的日記助理 📔\n\n"
                    "輸入 /help 查看使用說明"
                )
                continue

            if text.startswith('/help'):
                send_message(
                    "📔 Rosa 日記助理 — 使用說明\n\n"
                    "✍️ 記錄日記\n"
                    "直接傳文字給我就會存進 Notion！\n\n"
                    "格式 1：直接輸入內容\n"
                    "→ 主題自動用今天日期\n\n"
                    "格式 2：第一行寫主題，第二行起寫內容\n"
                    "例如：\n"
                    "今天去看展覽\n"
                    "和乖乖一起去當代藝術館...\n\n"
                    "🎙️ 語音輸入\n"
                    "點鍵盤上的麥克風 🎤，說完後 iOS 自動轉文字發送\n\n"
                    "⏰ 自動提醒\n"
                    "每天 23:30 我會傳今日引導問題給你\n\n"
                    "🤖 AI 摘要\n"
                    "想要日記摘要時，去找 Claude Code 說：\n"
                    "「幫我看看這週的日記」"
                )
                continue

            lines = text.strip().split('\n', 1)
            if len(lines) == 2 and len(lines[0]) < 30:
                topic = lines[0].strip()
                content = lines[1].strip()
            else:
                topic = datetime.now().strftime('%Y-%m-%d 日記')
                content = text.strip()

            success = save_to_notion(topic, content)
            if success:
                send_message(f"✅ 已存入 Notion！\n📌 主題：{topic}")
                print(f"✅ 已儲存：{topic}")
            else:
                send_message("❌ 儲存失敗，請稍後再試")

        elif 'voice' in message:
            send_message(
                "🎙️ 建議用鍵盤上的 🎤 麥克風按鈕說話，\n"
                "iOS 會直接把語音轉成文字再傳出來，就能存進 Notion 囉！"
            )

    # 更新 offset 到 GitHub Variables
    if new_offset != LAST_OFFSET:
        update_offset(new_offset)
        print(f"✅ Offset 更新至 {new_offset}")


if __name__ == "__main__":
    process_updates()
