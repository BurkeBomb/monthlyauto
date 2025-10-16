#!/usr/bin/env python3
"""
Overdue Follow-ups Nudger: Processes an aging CSV file and identifies overdue accounts.
Generates a CSV and HTML report with recommended next actions for accounts overdue >30 days.
"""
import os
import csv

INPUT_FILE = 'data/aging/aging.csv'
OUT_DIR = 'out'

# Determine category based on days overdue
def categorize(days):
    days = int(days)
    if days >= 90:
        return '90+'
    if days >= 60:
        return '60-89'
    if days >= 30:
        return '30-59'
    return 'current'

# Determine next action based on days overdue
def next_action(days):
    days = int(days)
    if days >= 90:
        return 'Send final notice and consider handing over to collections.'
    if days >= 60:
        return 'Call patient and send second reminder.'
    if days >= 30:
        return 'Send first reminder.'
    return ''

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    if not os.path.isfile(INPUT_FILE):
        print(f"Aging file {INPUT_FILE} not found; nothing to process.")
        return
    rows = []
    overdue_rows = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            days = int(row.get('days_overdue', '0'))
            row['category'] = categorize(days)
            row['next_action'] = next_action(days)
            rows.append(row)
            if days >= 30:
                overdue_rows.append(row)
    # Write CSV of overdue items
    csv_path = os.path.join(OUT_DIR, 'overdue_followups.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in overdue_rows:
            writer.writerow(row)
    # Write HTML table
    html_path = os.path.join(OUT_DIR, 'overdue_followups.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write('<html><head><meta charset="utf-8"></head><body>')
        f.write('<h1>Overdue Follow-ups</h1>')
        f.write('<table border="1" cellpadding="4" cellspacing="0">')
        # header
        headers = list(rows[0].keys())
        f.write('<tr>')
        for h in headers:
            f.write(f'<th>{h}</th>')
        f.write('</tr>')
        for row in overdue_rows:
            f.write('<tr>')
            for h in headers:
                f.write(f'<td>{row[h]}</td>')
            f.write('</tr>')
        f.write('</table></body></html>')

if __name__ == '__main__':
    main()
