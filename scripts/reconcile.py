#!/usr/bin/env python3
import argparse, re, json, sys
from pathlib import Path
import pandas as pd

def load_alias_map(path: Path):
    df = pd.read_csv(path)
    rules = []
    for _, row in df.iterrows():
        rules.append((row["scheme"], re.compile(row["alias_regex"])))
    return rules

def detect_scheme_from_desc(desc: str, rules):
    for scheme, pattern in rules:
        if pattern.search(desc):
            return scheme
    return "UNMAPPED"

def load_bank(dir_path: Path, rules):
    frames = []
    for csv in sorted(dir_path.glob("*.csv")):
        try:
            df = pd.read_csv(csv)
        except Exception as e:
            print(f"[warn] Could not read {csv}: {e}", file=sys.stderr)
            continue
        cols = {c.lower(): c for c in df.columns}
        amount_col = cols.get("amount")
        desc_col = cols.get("description") or cols.get("details") or cols.get("narration")
        if not amount_col or not desc_col:
            print(f"[warn] {csv} missing required columns (Amount, Description) -> skipping", file=sys.stderr)
            continue
        df = df.rename(columns={amount_col: "Amount", desc_col: "Description"})
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)
        df["SchemeDetected"] = df["Description"].astype(str).apply(lambda d: detect_scheme_from_desc(d, rules))
        frames.append(df[["Description", "Amount", "SchemeDetected"]])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["Description","Amount","SchemeDetected"])

def load_remits(dir_path: Path):
    frames = []
    for csv in sorted(dir_path.glob("*.csv")):
        try:
            df = pd.read_csv(csv)
        except Exception as e:
            print(f"[warn] Could not read {csv}: {e}", file=sys.stderr)
            continue
        cols = {c.lower(): c for c in df.columns}
        scheme_col = cols.get("scheme")
        amount_col = cols.get("amount")
        if not scheme_col or not amount_col:
            print(f"[warn] {csv} missing required columns (Scheme, Amount) -> skipping", file=sys.stderr)
            continue
        df = df.rename(columns={scheme_col: "Scheme", amount_col: "Amount"})
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)
        frames.append(df[["Scheme","Amount"]])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["Scheme","Amount"])

def main():
    ap = argparse.ArgumentParser(description="Reconcile bank vs remits by scheme alias rules.")
    ap.add_argument("--in", dest="bank_dir", required=True)
    ap.add_argument("--remits", dest="remits_dir", required=True)
    ap.add_argument("--alias", dest="alias_csv", required=True)
    ap.add_argument("--out", dest="out_dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    rules = load_alias_map(Path(args.alias_csv))

    bank_df = load_bank(Path(args.bank_dir), rules)
    rem_df  = load_remits(Path(args.remits_dir))

    bank_totals = bank_df.groupby("SchemeDetected", dropna=False)["Amount"].sum().rename("BankTotal").reset_index()
    rem_totals  = rem_df.groupby("Scheme", dropna=False)["Amount"].sum().rename("RemitTotal").reset_index()

    merged = pd.merge(bank_totals, rem_totals, left_on="SchemeDetected", right_on="Scheme", how="outer")
    merged["SchemeFinal"] = merged["SchemeDetected"].fillna(merged["Scheme"])
    merged = merged.drop(columns=["SchemeDetected","Scheme"])
    merged = merged.groupby("SchemeFinal", dropna=False).sum(numeric_only=True).reset_index()

    merged["BankTotal"] = merged["BankTotal"].fillna(0.0)
    merged["RemitTotal"] = merged["RemitTotal"].fillna(0.0)
    merged["Delta"] = merged["BankTotal"] - merged["RemitTotal"]
    merged["AbsDelta"] = merged["Delta"].abs()
    merged = merged.sort_values("AbsDelta", ascending=False)

    (out_dir / "unmatched.csv").write_text(merged.drop(columns=["AbsDelta"]).to_csv(index=False))
    kpis = {
        "total_bank": float(merged["BankTotal"].sum()),
        "total_remits": float(merged["RemitTotal"].sum()),
        "net_delta": float((merged["BankTotal"] - merged["RemitTotal"]).sum()),
        "top_gaps": merged.head(5)[["SchemeFinal","BankTotal","RemitTotal","Delta"]].to_dict(orient="records"),
    }
    (out_dir / "kpis.json").write_text(json.dumps(kpis, indent=2))
    print("[ok] Wrote unmatched.csv and kpis.json")

if __name__ == "__main__":
    main()
