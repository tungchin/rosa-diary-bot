import os
import requests
import random
from datetime import datetime

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

QUESTIONS = [
    "今天有什麼讓你印象深刻的事或對話？",
    "今天的心情如何？有什麼觸動你的瞬間？",
    "今天學到什麼新東西，或有什麼新的想法？",
    "今天和誰互動？有什麼收穫或感受？",
    "有什麼事情讓你感恩或珍惜？",
    "今天遇到什麼挑戰？你怎麼面對的？",
    "有什麼事情你想對未來的自己說？",
    "今天身體狀況如何？有照顧好自己嗎？",
    "今天最開心的一件事是什麼？",
    "有什麼計劃或夢想在心裡醞釀著？",
    "今天有沒有讓你想起某個人或某段記憶？",
    "如果今天是一種顏色，會是什麼顏色？為什麼？",
]

def send_reminder():
    selected = random.sample(QUESTIONS, 3)
    today = datetime.now().strftime('%Y年%m月%d日')

    message = (
        f"📔 晚安 Rosa，{today}\n\n"
        f"今天記錄了嗎？\n\n"
        f"✏️ 今日引導問題：\n"
        f"1. {selected[0]}\n"
        f"2. {selected[1]}\n"
        f"3. {selected[2]}\n\n"
        f"直接回覆這則訊息就可以記錄囉 🎙️"
    )

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": message}
    )
    print("✅ 每日提醒已發送")

if __name__ == "__main__":
    send_reminder()
