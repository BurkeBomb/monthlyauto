# Life Automation – Full Suite

This repository automates several key workflows across your business, finance, and admin domains. You can drop in your own data files and let GitHub Actions take care of processing, reconciliation, and reporting.

## Contents

### Reconcile & Unmatched Report

- **Scripts**: `scripts/reconcile.py`, `scripts/make_report.py`
- **Workflow**: `.github/workflows/reconcile-semi-monthly.yml`
- **Data inputs**:
  - Bank statement CSVs in `data/bank/`
  - Remittance advice CSVs in `data/remits/`
  - Alias map in `data/ALIAS_MAP.csv` (regex mapping of schemes to bank descriptions)
- **Schedule**: 1st & 15th of each month at 06:30 SAST (04:30 UTC). You can also run manually or on file pushes.
- **Outputs**: `out/unmatched.csv`, `out/kpis.json`, `out/unmatched.html`, `out/unmatched.pdf`. These are uploaded as build artifacts.

### GEMS Watchdog

- **Script**: `scripts/gems_watchdog.py`
- **Workflow**: `.github/workflows/gems-watchdog.yml`
- **Data inputs**: Plain‑text emails (.txt) placed in `data/gems/`. Each file represents one email.
- **Schedule**: Daily at 07:00 SAST (05:00 UTC); also runs when files change or when manually triggered.
- **What it does**: Scans each email, classifies it into categories (e.g. `authorization issue`, `claim rejected`, `payment delay`, or `general`), and writes a summary CSV and a text file with suggested replies.
- **Outputs**: `out/gems_watchdog_report.csv`, `out/gems_watchdog_draft_replies.txt`.

### Overdue Follow‑ups Nudger

- **Script**: `scripts/overdue_nudger.py`
- **Workflow**: `.github/workflows/overdue-nudger.yml`
- **Data input**: Aging report CSV at `data/aging/aging.csv` with columns like `patient_name`, `days_overdue`, `amount`, `last_follow_up`.
- **Schedule**: Daily at 15:00 SAST (13:00 UTC); also runs on file changes or manual trigger.
- **What it does**: Identifies accounts overdue by 30+ days, categorizes them by age bracket, and suggests the next follow‑up action. Generates a CSV and an HTML report.
- **Outputs**: `out/overdue_followups.csv`, `out/overdue_followups.html`.

## Requirements

- Python 3.11 or newer.
- The `reportlab` package is required for PDF generation. Install dependencies via `pip install -r requirements.txt`.

## Customising Schedules

Edit the cron expressions in the workflow files under `.github/workflows/` to suit your needs. Times are specified in UTC; adjust accordingly for your timezone (Africa/Johannesburg = UTC+2).

## Notes

- SMTP/email sending has been removed by default. The workflows upload build artifacts instead of emailing them. You can enable emailing by editing `reconcile-semi-monthly.yml` and using `scripts/send_email.py` with appropriate secrets.
- The sample data provided under `data/` is for demonstration only. Replace it with your actual data to get meaningful results.
