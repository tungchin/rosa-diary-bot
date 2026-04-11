from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
NOTION_TOKEN = os.environ['NOTION_TOKEN']
DIARY_DB_ID = os.environ['DIARY_DB_ID']
CHAT_ID = os.environ['CHAT_ID']


def send_message(text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    )


def save_to_notion(topic, content):
    today = datetime.now().strftime('%Y-%m-%d')
    res = requests.post(
        "https://api.notion.com/v1/pages",
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        },
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


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        update = json.loads(body)

        if 'message' in update:
            message = update['message']
            chat_id = str(message['chat']['id'])

            # 只接受 Rosa 自己的訊息
            if chat_id != str(CHAT_ID):
                self.send_response(200)
                self.end_headers()
                return

            if 'text' in message:
                text = message['text']

                if text.startswith('/start'):
                    send_message(
                        "👋 嗨 Rosa！\n\n"
                        "直接傳文字給我，我幫你存進 Notion 日記。\n\n"
                        "格式：\n"
                        "• 直接輸入內容（主題自動用今天日期）\n"
                        "• 或第一行寫主題，第二行起寫內容\n\n"
                        "記得用鍵盤的 🎙️ 語音輸入唷！"
                    )
                else:
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
                    else:
                        send_message("❌ 儲存失敗，請稍後再試")

            elif 'voice' in message:
                send_message(
                    "🎙️ 收到語音檔！\n\n"
                    "建議用鍵盤上的 🎤 麥克風按鈕說話，"
                    "iOS 會直接幫你把語音轉成文字再傳出來，這樣就能存進 Notion 囉！"
                )

        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass
