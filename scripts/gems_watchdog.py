#!/usr/bin/env python3
import argparse, re
from pathlib import Path
import pandas as pd
from datetime import datetime

CATEGORIES = [
    ("authorization", r"\bauth(?!or)\b|authorization|authorisation|pre[- ]?auth|no auth|missing auth"),
    ("claim_rejected", r"reject|declined|not covered|benefit exhausted|code invalid|tariff invalid"),
    ("payment_delay", r"delay|pending|processing|will be paid|awaiting"),
    ("info_request", r"please provide|need .* (icd|code|motivation|letter|clinical)"),
]

DRAFTS = {
    "authorization": (
        "Subject: Urgent: Authorization Failure Impacting Patient Care\n\n"
        "Dear GEMS Team,\n\nWe are unable to proceed due to missing/failed authorization on the referenced case. "
        "Please confirm authorization status today and advise corrective action required. "
        "This delay is putting our client relationship at risk. If unresolved within 2 business days, "
        "we will escalate to the Council for Medical Schemes.\n\nRegards,\nPractice Ops"
    ),
    "claim_rejected": (
        "Subject: Rejection Query — Request for Resolution\n\n"
        "Dear GEMS Team,\n\nWe received a rejection for the referenced claim. "
        "Please confirm the specific rule and corrective step. If resubmission is required, "
        "confirm acceptable ICD/tariff/code combination and necessary clinical notes.\n\nRegards,\nPractice Ops"
    ),
    "payment_delay": (
        "Subject: Payment Delay — Follow-up\n\n"
        "Dear GEMS Team,\n\nKindly confirm the payment date and reason for delay on the referenced items. "
        "Please share the remittance/ERA reference number once processed.\n\nRegards,\nPractice Ops"
    ),
    "info_request": (
        "Subject: Additional Information — Submission\n\n"
        "Dear GEMS Team,\n\nAttached are the requested details for the referenced patient/claim. "
        "Please confirm once the file is updated and provide an ETA for authorization/payment.\n\nRegards,\nPractice Ops"
    ),
    "other": (
        "Subject: Query — Assistance Required\n\n"
        "Dear GEMS Team,\n\nWe require assistance on the referenced case. "
        "Please advise next steps and expected timelines.\n\nRegards,\nPractice Ops"
    ),
}

def classify(text: str) -> str:
    t = text.lower()
    for name, pattern in CATEGORIES:
        if re.search(pattern, t):
            return name
    return "other"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", required=True, help="Folder with .txt emails")
    ap.add_argument("--out", dest="out_dir", required=True)
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for f in sorted(in_dir.glob("*.txt")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        cat = classify(text)
        rows.append({"file": f.name, "category": cat, "chars": len(text)})

    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame([{"file": "(none)", "category": "other", "chars": 0}])

    (out_dir / "gems_classified.csv").write_text(df.to_csv(index=False))

    # One draft per category present
    drafts = []
    for cat in sorted(df["category"].unique()):
        drafts.append(f"=== {cat.upper()} ===\n{DRAFTS.get(cat, DRAFTS['other'])}\n")
    (out_dir / "gems_drafts.txt").write_text("\n".join(drafts), encoding="utf-8")

    # simple HTML summary
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    items = "\n".join([f"<tr><td>{r['file']}</td><td>{r['category']}</td><td>{r['chars']}</td></tr>" for r in rows]) if rows else "<tr><td colspan='3'>(no files)</td></tr>"
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>GEMS Watchdog — {now}</title>
<style>
body{{font-family:system-ui,Segoe UI,Inter,Arial;margin:20px;background:#0f1115;color:#eaeef7}}
table{{border-collapse:collapse;width:100%;background:#171923}}
th,td{{padding:10px 12px;border-bottom:1px solid #222737;text-align:left}}
</style></head><body>
<h1>GEMS Watchdog</h1>
<div>Generated {now}</div>
<table><thead><tr><th>File</th><th>Category</th><th>Chars</th></tr></thead>
<tbody>{items}</tbody></table>
</body></html>"""
    (out_dir / "gems_summary.html").write_text(html, encoding="utf-8")
    print("[ok] Wrote gems_classified.csv, gems_drafts.txt, gems_summary.html")

if __name__ == "__main__":
    main()
