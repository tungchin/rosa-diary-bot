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


def build_monthly_report(entries):
    today = datetime.now()
    month_name = today.strftime('%Y年%m月')

    if not entries:
        return f"📅 {month_name} 月報\n\n這個月沒有日記記錄，下個月加油！💪"

    # 統計
    tag_counts = {}
    for e in entries:
        for tag in e['tags']:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    learn_entries = [e for e in entries if 'Learn' in e['tags']]
    work_entries = [e for e in entries if 'Work' in e['tags']]
    family_entries = [e for e in entries if 'Family' in e['tags']]
    expense_entries = [e for e in entries if 'Expense' in e['tags']]

    report = f"📅 {month_name} 月報\n"
    report += f"{'='*30}\n\n"
    report += f"📝 本月共記錄 {len(entries)} 則日記\n\n"

    # 月份回顧
    report += "🗓 本月重要時刻：\n"
    for e in entries:
        if e['topic']:
            report += f"  • {e['date']} {e['topic']}\n"
    report += "\n"

    # 學習成長
    if learn_entries:
        report += f"🧠 學習成長（{len(learn_entries)} 則）：\n"
        for e in learn_entries:
            report += f"  • {e['topic']}\n"
        report += "\n"

    # 工作
    if work_entries:
        report += f"💼 工作記錄（{len(work_entries)} 則）：\n"
        for e in work_entries:
            report += f"  • {e['topic']}\n"
        report += "\n"

    # 家人
    if family_entries:
        report += f"👨‍👩‍👧 家人相關（{len(family_entries)} 則）：\n"
        for e in family_entries:
            report += f"  • {e['topic']}\n"
        report += "\n"

    # 花費
    if expense_entries:
        report += f"💰 花費記錄（{len(expense_entries)} 則）：\n"
        for e in expense_entries:
            short = e['content'][:40] if e['content'] else ''
            report += f"  • {e['topic']}：{short}\n"
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
