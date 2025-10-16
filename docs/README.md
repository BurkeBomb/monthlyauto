# Automation Pack

### Workflows
- Reconcile: 1st & 15th @ 06:30 SAST (+ manual + on push to /data/bank, /data/remits)
- GEMS Watchdog: daily @ 07:00 SAST (+ manual + on push to /data/gems)
- Overdue Nudger: daily @ 15:00 SAST (+ manual + on push to /data/aging)

### Run
Actions → select workflow → Run workflow → branch `main`.  
Outputs are attached as Artifacts in each run.

### Data
- Bank CSVs need `Amount` + `Description` (or `Details`/`Narration`).
- Remits CSVs need `Scheme` + `Amount`.
- Aging CSV needs Patient + Days + Amount (other names handled).
- GEMS inputs are plain `.txt` files in `data/gems/`.

### Tweak schedules
Edit the `cron` lines in each YAML (UTC; SAST = UTC+2).
