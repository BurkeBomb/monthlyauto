#!/usr/bin/env python3
import os
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def build_html(rows, out_path):
    lines = []
    lines.append('<html><head><meta charset="utf-8"></head><body>')
    lines.append('<h1>Unmatched Transactions</h1>')
    lines.append('<table border="1" cellpadding="4" cellspacing="0">')
    lines.append('<tr><th>Scheme</th><th>Bank Total</th><th>Remit Total</th><th>Difference</th></tr>')
    for row in rows:
        lines.append(f"<tr><td>{row['scheme']}</td><td>{row['bank_total']}</td><td>{row['remit_total']}</td><td>{row['difference']}</td></tr>")
    lines.append('</table></body></html>')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def build_pdf(rows, out_path):
    doc = SimpleDocTemplate(out_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph('Unmatched Transactions', styles['Heading1']))
    elements.append(Spacer(1, 12))
    data = [['Scheme', 'Bank Total', 'Remit Total', 'Difference']]
    for row in rows:
        data.append([row['scheme'], row['bank_total'], row['remit_total'], row['difference']])
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))
    elements.append(table)
    doc.build(elements)

def main():
    out_dir = 'out'
    unmatched_csv = os.path.join(out_dir, 'unmatched.csv')
    if not os.path.exists(unmatched_csv):
        print('unmatched.csv not found; nothing to build.')
        return
    rows = []
    with open(unmatched_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    os.makedirs(out_dir, exist_ok=True)
    build_html(rows, os.path.join(out_dir, 'unmatched.html'))
    build_pdf(rows, os.path.join(out_dir, 'unmatched.pdf'))

if __name__ == '__main__':
    main()
