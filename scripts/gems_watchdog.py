#!/usr/bin/env python3
"""
GEMS Watchdog: scans email text files under data/gems, classifies issues, and generates a report
and draft reply suggestions. This does not send any emails; it simply writes outputs into the out/ directory.
"""
import os
import csv

INPUT_DIR = 'data/gems'
OUT_DIR = 'out'

# Define simple keyword-based classification
CLASSIFICATIONS = {
    'authorization issue': ['authorization', 'authorisation', 'missing authorisation', 'missing authorization'],
    'claim rejected': ['rejection', 'rejected', 'denied', 'declined'],
    'payment delay': ['payment delay', 'delayed payment'],
}

# Define draft replies for each classification
REPLIES = {
    'authorization issue': 'Your claim appears to lack a valid authorization. Please provide the authorization number and resubmit.',
    'claim rejected': 'Your claim has been rejected. Please review the rejection reason and correct any errors before resubmitting.',
    'payment delay': 'We note there is a delay in payment processing. Please follow up with the scheme to confirm expected payment dates.',
    'general': 'Thank you for your message. We will investigate and respond shortly.',
}

def classify_text(text):
    text_lower = text.lower()
    for cls, keywords in CLASSIFICATIONS.items():
        for kw in keywords:
            if kw in text_lower:
                return cls
    return 'general'

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    report_rows = []
    reply_lines = []
    # Iterate over text files in INPUT_DIR
    if not os.path.isdir(INPUT_DIR):
        print(f"No directory {INPUT_DIR}; nothing to scan.")
        return
    for fname in os.listdir(INPUT_DIR):
        path = os.path.join(INPUT_DIR, fname)
        if not os.path.isfile(path) or not fname.lower().endswith('.txt'):
            continue
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        cls = classify_text(text)
        reply = REPLIES.get(cls, REPLIES['general'])
        report_rows.append({'file': fname, 'classification': cls})
        reply_lines.append(f"{fname}: {reply}")
    # Write CSV report
    csv_path = os.path.join(OUT_DIR, 'gems_watchdog_report.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['file', 'classification'])
        writer.writeheader()
        for row in report_rows:
            writer.writerow(row)
    # Write draft replies text
    replies_path = os.path.join(OUT_DIR, 'gems_watchdog_draft_replies.txt')
    with open(replies_path, 'w', encoding='utf-8') as f:
        for line in reply_lines:
            f.write(line + '\n')

if __name__ == '__main__':
    main()
