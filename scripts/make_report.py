#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import pandas as pd
from datetime import datetime

HTML_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Unmatched Report — {date}</title>
<style>
  :root {{--bg:#0f1115; --card:#171923; --ink:#eaeef7; --muted:#aab3c5; --accent:#8a5cf6; --ok:#80e27e; --warn:#ffd166; --bad:#ff7b7b;}}
  body{{background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,Segoe UI,Inter,Roboto,Helvetica,Arial,sans-serif;margin:0;padding:24px}}
  .wrap{{max-width:1100px;margin:0 auto}}
  h1{{font-weight:800;margin:0 0 8px}}
  .muted{{color:var(--muted)}}
  table{{width:100%;border-collapse:collapse;margin-top:16px;background:var(--card);border:1px solid #222737}}
  th,td{{padding:10px 12px;border-bottom:1px solid #222737;text-align:left}}
  th{{font-weight:700}}
  tr:hover{{background:#1c2030}}
  .delta-pos{{color:var(--ok);font-weight:700}}
  .delta-neg{{color:var(--bad);font-weight:700}}
  .delta-zero{{color:var(--muted)}}
  .kpi{{display:flex;gap:16px;flex-wrap:wrap;margin-top:8px}}
  .chip{{background:#1c2030;border:1px solid #222737;border-radius:8px;padding:8px 12px}}
</style>
</head>
<body>
  <div class="wrap">
    <h1>Unmatched Report</h1>
    <div class="muted">Generated {date}</div>
    <div class="kpi">
      <div class="chip"><b>Total Bank:</b> ZAR {total_bank:,.2f}</div>
      <div class="chip"><b>Total Remits:</b> ZAR {total_remits:,.2f}</div>
      <div class="chip"><b>Net Delta:</b> <span class="{net_delta_class}">{net_delta_signed}</span></div>
    </div>
    <table>
      <thead>
        <tr><th>Scheme</th><th>Bank Total (ZAR)</th><th>Remit Total (ZAR)</th><th>Delta</th></tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</body>
</html>
"""

def fmt_delta(v):
    if v > 0: return f'<span class="delta-pos">+ZAR {v:,.2f}</span>'
    if v < 0: return f'<span class="delta-neg">-ZAR {abs(v):,.2f}</span>'
    return f'<span class="delta-zero">ZAR 0.00</span>'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("indir", help="Directory containing unmatched.csv and kpis.json")
    ap.add_argument("--pdf", help="Output PDF path", default=None)
    ap.add_argument("--html", help="Output HTML path", default=None)
    args = ap.parse_args()

    indir = Path(args.indir)
    unmatched = pd.read_csv(indir / "unmatched.csv")
    kpis = json.loads((indir / "kpis.json").read_text())

    rows_html = []
    for _, r in unmatched.iterrows():
        rows_html.append(
            f"<tr><td>{r['SchemeFinal']}</td>"
            f"<td>ZAR {r['BankTotal']:,.2f}</td>"
            f"<td>ZAR {r['RemitTotal']:,.2f}</td>"
            f"<td>{fmt_delta(r['Delta'])}</td></tr>"
        )
    net_delta = float(kpis.get("net_delta", 0.0))
    net_class = "delta-zero" if abs(net_delta) < 1e-9 else ("delta-pos" if net_delta > 0 else "delta-neg")
    net_signed = f"+ZAR {net_delta:,.2f}" if net_delta > 0 else (f"-ZAR {abs(net_delta):,.2f}" if net_delta < 0 else "ZAR 0.00")

    html = HTML_TMPL.format(
        date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        total_bank=float(kpis.get("total_bank",0.0)),
        total_remits=float(kpis.get("total_remits",0.0)),
        net_delta_class=net_class,
        net_delta_signed=net_signed,
        rows="\n".join(rows_html)
    )
    if args.html:
        Path(args.html).write_text(html, encoding="utf-8")

    if args.pdf:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm

        c = canvas.Canvas(args.pdf, pagesize=A4)
        W, H = A4
        x, y = 20*mm, H - 20*mm
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x, y, "Unmatched Report Summary")
        y -= 10*mm
        c.setFont("Helvetica", 10)
        c.drawString(x, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        y -= 6*mm
        c.drawString(x, y, f"Total Bank: ZAR {kpis.get('total_bank',0):,.2f}")
        y -= 6*mm
        c.drawString(x, y, f"Total Remits: ZAR {kpis.get('total_remits',0):,.2f}")
        y -= 6*mm
        c.drawString(x, y, f"Net Delta: {net_signed}")
        y -= 12*mm

        c.setFont("Helvetica-Bold", 11)
        c.drawString(x, y, "Top Gaps")
        y -= 8*mm
        c.setFont("Helvetica", 10)
        for row in kpis.get("top_gaps", []):
            line = f"- {row['SchemeFinal']}: Bank ZAR {row['BankTotal']:,.2f} vs Remit ZAR {row['RemitTotal']:,.2f} (Δ {row['Delta']:,.2f})"
            c.drawString(x, y, line)
            y -= 6*mm
            if y < 30*mm:
                c.showPage()
                y = H - 20*mm
                c.setFont("Helvetica", 10)
        c.showPage(); c.save()

if __name__ == "__main__":
    main()
