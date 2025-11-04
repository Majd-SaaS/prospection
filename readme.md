# 🚀 LinkedIn Company Follow Automation

This project provides a headless-friendly way to follow LinkedIn company pages
from a remote (SSH) session.  Instead of opening tabs locally and relying on
the Chrome extension, the new CLI script launches Chrome via Selenium, checks
whether each company page is already followed, and clicks the **Follow** button
when necessary.  The script reports the outcome for every URL so it can be
integrated into larger automation pipelines or executed manually on a server.

The rest of the repository (CSV parsers, SQLite database utilities, and the
browser extension) is still available for teams that prefer the original
workflow, but the CLI described below is now the primary entry-point for
company follow operations.

---

## ✅ Key Features

- **SSH friendly:** run the automation on a remote VM without an interactive
  browser session.
- **Deterministic output:** returns `follow`, `already followed`, or `error`
  for each company URL, making it easy to chain with other scripts.
- **Chrome profile reuse:** point Selenium at an existing Chrome user profile
  that is already authenticated with LinkedIn (no password prompts in CI).
- **Flexible input:** provide URLs as command line arguments, via an input
  file, or piped through standard input.
- **JSON or table output:** choose the format that best suits your automation
  needs.

---

## 🧰 Prerequisites

- Python 3.10+
- Google Chrome or Chromium installed on the VM
- A matching `chromedriver` available on the PATH (or managed by your
  orchestration tooling)
- A Chrome user profile that is already logged into LinkedIn (the VM can reuse
  an existing desktop session by referencing its user data directory)

Install Python dependencies:

```bash
pip install -r requirements.txt
```

> **Tip:** When containerising the project for on-prem hosting, bake Chrome and
> `chromedriver` into the image or mount them from the host to guarantee
> version alignment.

---

## ▶️ Running the CLI

The main entry point is `src/main_add_linkedin_companies_and_employees.py`. The
script is fully self-contained and can be run directly after installing the
dependencies.

### Basic usage

```bash
python src/main_add_linkedin_companies_and_employees.py \
  --user-data-dir="/path/to/chrome/User Data" \
  --profile-directory="Default" \
  https://www.linkedin.com/company/example-inc/
```

If the company is already followed, the script reports `already followed`. If
not, it will click the **Follow** button and return `follow` after confirming
the state change. Errors (missing buttons, timeouts, etc.) are reported with a
helpful reason string.

### Reading URLs from a file or STDIN

```bash
# Read URLs from a file (one URL per line)
python src/main_add_linkedin_companies_and_employees.py \
  --user-data-dir="/path/to/chrome/User Data" \
  --profile-directory="Default" \
  --input-file company_urls.txt

# Or stream them via STDIN
cat company_urls.txt | python src/main_add_linkedin_companies_and_employees.py \
  --user-data-dir="/path/to/chrome/User Data" \
  --profile-directory="Default"
```

### JSON output

Use `--output-format json` when the results should be consumed by another
program:

```bash
python src/main_add_linkedin_companies_and_employees.py \
  --user-data-dir="/path/to/chrome/User Data" \
  --profile-directory="Default" \
  --output-format json \
  --input-file company_urls.txt
```

### Headless execution

When running through SSH without a display server, enable headless mode:

```bash
python src/main_add_linkedin_companies_and_employees.py \
  --user-data-dir="/path/to/chrome/User Data" \
  --profile-directory="Default" \
  --headless \
  --input-file company_urls.txt
```

Chrome must be recent enough (109+) to support `--headless=new`. If your build
is older, consider updating Chrome or running the script inside a virtual frame
buffer (Xvfb).

---

## 🧪 Output format

By default the CLI prints a fixed-width table:

```
URL                                                                              | STATUS         | REASON
------------------------------------------------------------------------------------------------------------------------
https://www.linkedin.com/company/example-inc/                                    | follow         |
https://www.linkedin.com/company/already-followed/                               | already followed |
https://www.linkedin.com/company/missing-company/                                | error          | Follow button not found
```

When `--output-format json` is specified, a JSON array is emitted:

```json
[
  {"url": "https://www.linkedin.com/company/example-inc/", "status": "follow"},
  {"url": "https://www.linkedin.com/company/already-followed/", "status": "already followed"},
  {
    "url": "https://www.linkedin.com/company/missing-company/",
    "status": "error",
    "reason": "Follow button not found"
  }
]
```

The three possible status values are:

- `follow` – the script clicked **Follow** successfully.
- `already followed` – the page already displayed the **Following** state.
- `error` – the script could not confirm a follow action (missing button,
  timeout, or navigation failure). The `reason` field includes more detail.

---

## ⚙️ Command-line options

| Flag | Description | Default |
| ---- | ----------- | ------- |
| `urls` | Optional positional arguments with LinkedIn company URLs | – |
| `--input-file` | File with one LinkedIn URL per line | – |
| `--user-data-dir` | Chrome user data directory that holds a logged-in LinkedIn session | – |
| `--profile-directory` | Profile directory inside the user data dir (e.g. `Default`, `Profile 1`) | – |
| `--chrome-binary` | Override the Chrome/Chromium binary location | autodetected |
| `--headless` | Launch Chrome in headless mode | disabled |
| `--page-load-timeout` | Seconds to wait for each page to finish loading | 30 |
| `--follow-timeout` | Seconds to wait for the follow action to succeed | 20 |
| `--delay-between` | Delay in seconds between URL navigations | 1.5 |
| `--output-format` | `table` or `json` | `table` |

> **Authentication:** Provide `--user-data-dir` (and optionally
> `--profile-directory`) so Selenium reuses an existing Chrome profile that is
> already logged into LinkedIn. This avoids storing credentials in the script.

---

## 🐳 Docker & On-Prem Hosting Tips

- Mount the Chrome user data directory into the container so the session stays
  authenticated between runs.
- Bundle Chrome, `chromedriver`, and the Python dependencies into the image or
  manage them with infrastructure as code.
- Use `--output-format json` for easier integration with orchestrators or
  monitoring tools that capture container logs.

Example service snippet:

```yaml
services:
  linkedin-follow:
    build: .
    environment:
      - DISPLAY= # leave empty for headless mode
    volumes:
      - ./chrome-profile:/headless/chrome
      - ./input/company_urls.txt:/data/company_urls.txt:ro
    command: >-
      python src/main_add_linkedin_companies_and_employees.py \
        --user-data-dir=/headless/chrome \
        --profile-directory=Default \
        --headless \
        --output-format=json \
        --input-file=/data/company_urls.txt
```

---

## 📦 Legacy Components

The repository still contains the original SQLite-backed workflow and Chrome
extension. They remain useful for teams that prefer to pre-process CSV files,
persist state, or run the automation from a local browser. Highlights:

- `src/main_parse_files.py` – Ingest BuiltWith and Mantiks CSV exports into a
  SQLite database (`prospection_data.db`).
- `src/db_prospection.py` – Helper functions to query and update the database.
- `chrome_plugin/` – Chrome extension that clicks the **Follow** button when
  pages are opened manually.

These modules are optional when using the new Selenium-based CLI but continue
to function if you rely on the previous workflow.

---

## 🧪 Testing helpers

Unit tests live under `tests/` and focus on pure-Python helper functions that
classify button states. Run them with:

```bash
python -m unittest discover tests
```

Browser-level behaviour is best validated manually on a staging LinkedIn
profile because LinkedIn employs bot-detection heuristics that can block fully
automated end-to-end tests.

---

## 🙋 Support & Contributions

Issues and pull requests are welcome. When contributing, please document any
new CLI flags or workflow changes in this README so the automation remains easy
to operate for SSH-based deployments.

