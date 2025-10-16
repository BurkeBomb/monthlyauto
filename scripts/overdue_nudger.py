#!/usr/bin/env python3
import argparse
from pathlib import Path
import pandas as pd
from datetime import datetime

def normalize_cols(df):
    m = {c.lower(): c for c in df.columns}
    def pick(*names):
        for n in names:
            if n.lower() in m: return m[n.lower()]
        return None
    return {
        "patient": pick("patient","name","account","account_name"),
        "scheme": pick("scheme","medical scheme","payer"),
        "days": pick("days_overdue","age","days","dpd"),
        "amount": pick("amount","balance","outstanding","value"),
        "last": pick("last_action","last_note","last_contact","last_action_date"),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="aging_csv", required=True)
    ap.add_argument("--out", dest="out_dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.aging_csv)
    cols = normalize_cols(df)
    missing = [k for k,v in cols.items() if v is None and k in ("patient","days","amount")]
    if missing:
        raise SystemExit(f"Missing required columns in aging file: {missing}")

    df = df.rename(columns={
        cols["patient"]: "Patient",
        cols["scheme"] or cols["patient"]: "Scheme",  # fallback
        cols["days"]: "Days",
        cols["amount"]: "Amount",
        (cols["last"] or cols["patient"]): "LastAction"
    })
    df["Days"] = pd.to_numeric(df["Days"], errors="coerce").fillna(0).astype(int)
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)

    def bucket(d):
        if d >= 90: return "90+"
        if d >= 60: return "60-89"
        if d >= 30: return "30-59"
        return "0-29"

    df["Bucket"] = df["Days"].apply(bucket)

    def next_step(row):
        if row["Bucket"] == "30-59":
            return "Call scheme; verify auth/benefit; note ref; set 7-day follow-up."
        if row["Bucket"] == "60-89":
            return "Escalate with formal email incl. refs; request payment date; set 5-day follow-up."
        if row["Bucket"] == "90+":
            return "Final demand + scheme complaint draft; manager review; 3-day follow-up."
        return "Monitor; include in weekly check."
    df["NextAction"] = df.apply(next_step, axis=1)

    # outputs
    nudger_csv = out_dir / "nudger.csv"
    df.sort_values(["Bucket","Amount"], ascending=[True,False]).to_csv(nudger_csv, index=False)

    # html
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = "\n".join(
        f"<tr><td>{r.Patient}</td><td>{r.Scheme if 'Scheme' in df.columns else ''}</td>"
        f"<td>{r.Days}</td><td>ZAR {r.Amount:,.2f}</td><td>{r.Bucket}</td><td>{r.NextAction}</td></tr>"
        for r in df.itertuples()
    )
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Overdue Nudger — {now}</title>
<style>
body{{font-family:system-ui,Segoe UI,Inter,Arial;margin:20px;background:#0f1115;color:#eaeef7}}
table{{border-collapse:collapse;width:100%;background:#171923}}
th,td{{padding:10px 12px;border-bottom:1px solid #222737;text-align:left}}
</style></head><body>
<h1>Overdue Nudger</h1><div>Generated {now}</div>
<table><thead><tr>
<th>Patient</th><th>Scheme</th><th>Days</th><th>Amount</th><th>Bucket</th><th>Next Action</th>
</tr></thead><tbody>{rows}</tbody></table>
</body></html>"""
    (out_dir / "nudger.html").write_text(html, encoding="utf-8")
    print("[ok] Wrote nudger.csv and nudger.html")

if __name__ == "__main__":
    main()
