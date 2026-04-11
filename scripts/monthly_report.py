import os
import requests
from datetime import datetime
import calendar

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


def get_this_month_entries():
    today = datetime.now()
    month_start = today.replace(day=1).strftime('%Y-%m-%d')
    month_end = today.strftime('%Y-%m-%d')

    res = requests.post(
        f"https://api.notion.com/v1/databases/{DIARY_DB_ID}/query",
        headers=HEADERS,
        json={
            "filter": {
                "and": [
                    {"property": "Created Date", "date": {"on_or_after": month_start}},
                    {"property": "Created Date", "date": {"on_or_before": month_end}}
                ]
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
    if not content:
        return ""
    content = content.strip()
    if len(content) <= max_len:
        return content
    for punct in ['。', '！', '？', '.', '!', '?', '\n']:
        idx = content.find(punct, max_len // 2)
        if idx != -1 and idx <= max_len:
            return content[:idx + 1]
    return content[:max_len] + "..."


def build_monthly_report(entries):
    today = datetime.now()
    month_name = today.strftime('%Y年%m月')

    if not entries:
        return f"📅 {month_name} 月報\n\n這個月沒有日記記錄，下個月加油！💪"

    learn_entries = [e for e in entries if 'Learn' in e['tags']]
    work_entries = [e for e in entries if 'Work' in e['tags']]
    family_entries = [e for e in entries if 'Family' in e['tags']]
    expense_entries = [e for e in entries if 'Expense' in e['tags']]
    diary_entries = [e for e in entries if
                     'Diary' in e['tags'] or 'Couple' in e['tags'] or 'Friends' in e['tags']
                     or not e['tags']]

    report = f"📅 {month_name} 月報\n"
    report += f"{'='*30}\n\n"
    report += f"📝 本月共記錄 {len(entries)} 則\n\n"

    def format_entries(label, emoji, elist):
        if not elist:
            return ""
        block = f"{emoji} {label}（{len(elist)} 則）：\n"
        for e in elist:
            block += f"  [{e['date']}] {e['topic']}\n"
            summary = summarize(e['content'])
            if summary:
                block += f"  　　{summary}\n"
        return block + "\n"

    report += format_entries("學習成長", "🧠", learn_entries)
    report += format_entries("工作", "💼", work_entries)
    report += format_entries("家人", "👨‍👩‍👧", family_entries)
    report += format_entries("生活日記", "📔", diary_entries)

    # 花費單獨處理（顯示金額）
    if expense_entries:
        report += f"💰 花費記錄（{len(expense_entries)} 則）：\n"
        for e in expense_entries:
            report += f"  [{e['date']}] {e['topic']}"
            summary = summarize(e['content'], 40)
            if summary:
                report += f"：{summary}"
            report += "\n"
        report += "\n"
        report += "\n"

    report += "─" * 30 + "\n"
    report += f"🌱 {today.strftime('%m')}月的你，持續在成長！\n"
    report += f"期待下個月更多精彩的記錄 ✨"

    return report


def save_report_to_notion(report_text, month_label):
    requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json={
            "parent": {"database_id": REPORT_DB_ID},
            "properties": {
                "Title": {"title": [{"text": {"content": f"月報 {month_label}"}}]},
                "Content": {"rich_text": [{"text": {"content": report_text}}]},
                "Date": {"date": {"start": datetime.now().strftime('%Y-%m-%d')}},
                "Type(Weekly, Monthly)": {"select": {"name": "Monthly"}}
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
    month_label = today.strftime('%Y年%m月')

    print(f"📖 讀取 {month_label} 日記...")
    results = get_this_month_entries()
    entries = parse_entries(results)

    print(f"找到 {len(entries)} 則記錄，生成月報...")
    report = build_monthly_report(entries)

    print("📤 發送到 Telegram...")
    send_to_telegram(report)

    print("💾 存入 Notion...")
    save_report_to_notion(report, month_label)

    print("✅ 月報完成！")
