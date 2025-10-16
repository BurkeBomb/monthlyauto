#!/usr/bin/env python3
import os
import re
import csv
import json
import argparse

def load_alias_map(path):
    alias_map = {}
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scheme = row['scheme']
            regex = row['alias_regex']
            alias_map[scheme] = re.compile(regex, re.IGNORECASE)
    return alias_map

def classify(description, alias_map):
    for scheme, pattern in alias_map.items():
        if pattern.search(description):
            return scheme
    return 'UNKNOWN'

def main():
    parser = argparse.ArgumentParser(description='Reconcile bank transactions against remittance advice.')
    parser.add_argument('--in', dest='bank_dir', default='data/bank', help='Directory with bank CSV files')
    parser.add_argument('--remits', dest='remits_dir', default='data/remits', help='Directory with remittance CSV files')
    parser.add_argument('--alias', dest='alias_file', default='data/ALIAS_MAP.csv', help='CSV file with scheme regex mappings')
    parser.add_argument('--out', dest='out_dir', default='out', help='Output directory')
    args = parser.parse_args()

    alias_map = load_alias_map(args.alias_file)

    # Parse bank transactions
    bank_totals = {}
    for fname in os.listdir(args.bank_dir):
        path = os.path.join(args.bank_dir, fname)
        if not fname.lower().endswith('.csv'):
            continue
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                desc = row.get('Description') or row.get('Narration') or row.get('Details') or ''
                amount_str = row.get('Amount') or row.get('amount') or row.get('Debit/Credit') or '0'
                try:
                    amount = float(amount_str.replace(',', ''))
                except Exception:
                    amount = 0.0
                scheme = classify(desc, alias_map)
                bank_totals[scheme] = bank_totals.get(scheme, 0.0) + amount

    # Parse remittance advice
    remit_totals = {}
    for fname in os.listdir(args.remits_dir):
        path = os.path.join(args.remits_dir, fname)
        if not fname.lower().endswith('.csv'):
            continue
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                scheme = row.get('Scheme') or row.get('scheme')
                amount_str = row.get('Amount') or row.get('amount') or '0'
                try:
                    amount = float(amount_str.replace(',', ''))
                except Exception:
                    amount = 0.0
                remit_totals[scheme] = remit_totals.get(scheme, 0.0) + amount

    # Identify unmatched totals
    unmatched = []
    for scheme, bank_total in bank_totals.items():
        remit_total = remit_totals.get(scheme, 0.0)
        if abs(bank_total - remit_total) > 0.01:
            unmatched.append({
                'scheme': scheme,
                'bank_total': round(bank_total, 2),
                'remit_total': round(remit_total, 2),
                'difference': round(bank_total - remit_total, 2)
            })

    # Ensure output directory exists
    os.makedirs(args.out_dir, exist_ok=True)

    # Write unmatched.csv
    unmatched_csv = os.path.join(args.out_dir, 'unmatched.csv')
    with open(unmatched_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['scheme', 'bank_total', 'remit_total', 'difference'])
        writer.writeheader()
        for row in unmatched:
            writer.writerow(row)

    # Write kpis.json
    kpi_path = os.path.join(args.out_dir, 'kpis.json')
    kpis = {
        'unmatched_count': len(unmatched),
        'bank_totals': {k: round(v, 2) for k, v in bank_totals.items()},
        'remit_totals': {k: round(v, 2) for k, v in remit_totals.items()}
    }
    with open(kpi_path, 'w', encoding='utf-8') as f:
        json.dump(kpis, f, indent=2)

if __name__ == '__main__':
    main()
