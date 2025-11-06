# 🚀 LinkedIn Company Follow Automation

This repo now ships a queue-based automation flow: a Python CLI reads LinkedIn
company URLs from a file, opens them one by one in Chrome, and the bundled
extension clicks **Follow** (or leaves the page alone if you already follow).
Each tab stays open long enough for LinkedIn to register the action, the result
is logged immediately, and the URL disappears from the queue so you can resume
later.

Legacy CSV/SQLite helpers are still available for teams managing prospects with
the original database, but the queue + extension workflow described here is the
recommended entry point for following company pages.

---

## ✅ Key Features

- **Queue-driven:** point the CLI at a queue file; it launches each URL, waits
  for the extension status (`follow`, `already followed`, or `error`), logs the
  outcome, and rewrites the queue.
- **Extension callbacks:** the Chrome extension reports back via localhost so
  you always know why a URL failed (missing button, login wall, etc.).
- **Safety pacing:** defaults to **90 s** between tabs and keeps each page open
  for **60 s** before auto-closing.
- **Daily quota:** configurable limit (default 100 URLs/day) stored in
  `~/.prospection_daily_quota.json`; remaining URLs stay in the queue.
- **Resumable:** stop the CLI anytime—unprocessed URLs remain in the input
  file, and results are already written to CSV.

---

## 🧰 Prerequisites

- Python 3.10+
- Google Chrome on the machine running the automation
- The **LinkedIn Auto Follow** extension from `chrome_plugin/` loaded in
  Developer Mode
- A Chrome profile that is already signed in to LinkedIn

### Environment setup

```bash
cd /opt/prospection
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### Install / reload the extension

1. Open `chrome://extensions`, enable **Developer mode**.
2. Click **Load unpacked** → select the `chrome_plugin/` folder.
3. Ensure the popup toggle is **enabled** and the “Close tabs when automation
   is skipped” option matches your workflow.

---

## 🛠️ Queue Automation Workflow

1. **Prepare queue + log files**
   ```
   /home/<user>/Desktop/FollowCompany/Input.txt    # one company URL per line
   /home/<user>/Desktop/FollowCompany/results.csv  # created automatically
   ```
2. **Keep Chrome signed in** (normal desktop session is fine; no Selenium).
3. **Run the CLI** (defaults: 100 URLs/day, 90 s between tabs, 60 s dwell):
   ```bash
   /opt/prospection/.venv/bin/python -m src.main_add_linkedin_companies_and_employees \
     --queue-file "/home/<user>/Desktop/FollowCompany/Input.txt" \
     --queue-output "/home/<user>/Desktop/FollowCompany/results.csv"
   ```
   Optional flags:
   - `--daily-limit 50` – change the daily quota (set to `0` to disable).
   - `--delay-between 120` – adjust seconds between tab launches.
   - `--page-duration 75` – change how long each tab stays open before closing.
   - `--callback-timeout 120` – extend how long the CLI waits for the extension
     to report a result before marking it as `error`.
4. **Watch the workflow**
   - Tabs open sequentially; the extension follows when needed.
   - `results.csv` gets a timestamped row after each tab.
   - `Input.txt` rewrites itself so only remaining URLs stay in the queue.

---

## 📊 Monitoring & Tips

- **Output table:** every run ends with a concise `url | status | reason`
  summary.
- **CSV audit trail:** `results.csv` can be imported into Sheets/Excel or fed
  to downstream tools.
- **Queue persistence:** to add new work, drop more URLs into `Input.txt`; the
  CLI only reads what’s left.
- **Extension toggle:** disable it when you browse LinkedIn manually so your
  own tabs aren’t closed automatically.
- **Login issues:** if the CLI reports “LinkedIn redirected to a login form,”
  re-authenticate in Chrome and rerun—the automation reuses the live profile.

---

## 🧱 Legacy Tools (Optional)

The repo still includes:

- `src/csv_parser.py`, `src/parser_visitors.py`, `src/main_parse_files.py`
  – import Mantiks/BuiltWith CSVs into the SQLite DB.
- `src/db_prospection.py`, `src/main_inspect_db.py`
  – inspect or script against the database directly.
- `chrome_plugin/` – now focused on the queue workflow but can be customised
  (language tweaks, button detection, etc.).

These utilities remain useful if you want to keep a structured prospect DB,
but they’re no longer required for the company follow automation.

---

**⚡ Happy prospecting! Use responsibly and stay within LinkedIn’s terms of service.**
