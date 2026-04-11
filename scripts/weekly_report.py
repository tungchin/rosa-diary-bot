import os
import requests
from datetime import datetime, timedelta

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
NOTION_TOKEN = os.environ['NOTION_TOKEN']
DIARY_DB_ID = os.environ['DIARY_DB_ID']
REPORT_DB_ID = os.environ['REPORT_DB_ID']

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


def get_last_7_days_entries():
    today = datetime.now()
    seven_days_ago = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')

    res = requests.post(
        f"https://api.notion.com/v1/databases/{DIARY_DB_ID}/query",
        headers=HEADERS,
        json={
            "filter": {
                "property": "Created Date",
                "date": {"on_or_after": seven_days_ago}
            },
            "sorts": [{"property": "Created Date", "direction": "ascending"}]
        }
    )
    return res.json().get('results', [])


def parse_entries(results):
    entries = []
    for page in results:
        props = page['properties']
        date = props.get('Created Date', {}).get('date', {})
        date_str = date.get('start', '') if date else ''
        topic = ''.join([t['plain_text'] for t in props.get('Topic', {}).get('title', [])])
        content = ''.join([t['plain_text'] for t in props.get('Content', {}).get('rich_text', [])])
        tags = [t['name'] for t in props.get('tag', {}).get('multi_select', [])]
        if topic or content:
            entries.append({'date': date_str, 'topic': topic, 'content': content, 'tags': tags})
    return entries


def summarize(content, max_len=80):
    """取內容摘要，在句號或換行處截斷"""
    if not content:
        return ""
    content = content.strip()
    if len(content) <= max_len:
        return content
    # 嘗試在句號處截斷
    for punct in ['。', '！', '？', '.', '!', '?', '\n']:
        idx = content.find(punct, max_len // 2)
        if idx != -1 and idx <= max_len:
            return content[:idx + 1]
    return content[:max_len] + "..."


def build_report(entries):
    today = datetime.now()
    week_start = (today - timedelta(days=7)).strftime('%m/%d')
    week_end = today.strftime('%m/%d')

    if not entries:
        return f"📊 週報 {week_start} - {week_end}\n\n這週沒有日記記錄，下週加油！💪"

    # 分類（一則可能有多個 tag）
    learn_entries = [e for e in entries if 'Learn' in e['tags']]
    work_entries = [e for e in entries if 'Work' in e['tags']]
    family_entries = [e for e in entries if 'Family' in e['tags']]
    expense_entries = [e for e in entries if 'Expense' in e['tags']]
    diary_entries = [e for e in entries if
                     'Diary' in e['tags'] or 'Couple' in e['tags'] or 'Friends' in e['tags']
                     or not e['tags']]

    report = f"📊 本週週報 {week_start} - {week_end}\n"
    report += f"{'='*30}\n\n"
    report += f"📝 共記錄 {len(entries)} 則\n\n"

    def format_entries(label, emoji, elist):
        if not elist:
            return ""
        block = f"{emoji} {label}：\n"
        for e in elist:
            date_short = e['date'][5:] if e['date'] else ''  # MM-DD
            block += f"  [{date_short}] {e['topic']}\n"
            summary = summarize(e['content'])
            if summary:
                block += f"  　　{summary}\n"
        return block + "\n"

    report += format_entries("學習成長", "🧠", learn_entries)
    report += format_entries("工作", "💼", work_entries)
    report += format_entries("家人", "👨‍👩‍👧", family_entries)
    report += format_entries("生活日記", "📔", diary_entries)
    report += format_entries("花費", "💰", expense_entries)

    report += "─" * 30 + "\n"
    report += "💭 下週提醒自己：持續記錄，持續成長 🌱\n"

    return report


def save_report_to_notion(report_text, week_label):
    requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json={
            "parent": {"database_id": REPORT_DB_ID},
            "properties": {
                "Title": {"title": [{"text": {"content": f"週報 {week_label}"}}]},
                "Content": {"rich_text": [{"text": {"content": report_text}}]},
                "Date": {"date": {"start": datetime.now().strftime('%Y-%m-%d')}},
                "Type(Weekly, Monthly)": {"select": {"name": "Weekly"}}
            }
        }
    )


def send_to_telegram(text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text}
    )


if __name__ == "__main__":
    today = datetime.now()
    week_start = (today - timedelta(days=7)).strftime('%m/%d')
    week_end = today.strftime('%m/%d')
    week_label = f"{week_start}-{week_end}"

    print("📖 讀取本週日記...")
    results = get_last_7_days_entries()
    entries = parse_entries(results)

    print(f"找到 {len(entries)} 則記錄，生成週報...")
    report = build_report(entries)

    print("📤 發送到 Telegram...")
    send_to_telegram(report)

    print("💾 存入 Notion...")
    save_report_to_notion(report, week_label)

    print("✅ 週報完成！")
