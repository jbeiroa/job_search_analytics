---
name: job-tracker-updater
description: Update the job application tracker by fetching new applications and responses from Gmail and extracting data using a local LLM (Ollama).
---

# Job Tracker Updater Skill

This skill automates the incremental update of the `job_applications_final.csv` file by scanning Gmail for job-related emails and delegating data extraction to a local LLM via Ollama.

## Prerequisites

- Access to `mcp_google-workspace_gmail` tools.
- `job_applications_final.csv` must exist in the workspace root.
- `update_tracker.py` and `extract_jobs.py` scripts must be available in the workspace root.
- **Ollama** installed and running with the `llama3.2:3b` model.
- Python dependencies: `uv add ollama pydantic pandas`

## Workflow

### 1. Determine Date Range
Find the most recent `application_date` in `job_applications_final.csv`. 
Perform a standard update from that date, or a "Deep Sync" (e.g., 30 days back) if requested.

### 2. Search & Fetch Emails
Run BROAD Gmail searches to capture all potential applications and responses:
- **Applications:** `after:{DATE} ("Thanks for applying" OR "application was sent to" OR "recibieron tu postulación" OR "Postulación recibida" OR "Confirmación de postulación" OR "Gracias por postularte" OR "recibió tu postulación" OR "received your application" OR "Solicitud recibida" OR "candidatura recibida") -from:(jobalerts-noreply@linkedin.com)`
- **Responses:** `after:{DATE} ("unfortunately" OR "rejected" OR "entrevista" OR "rechazado" OR "proceso" OR "oportunidad" OR "interview" OR "next steps" OR "candidatura" OR "selección" OR "resultado") -from:(jobalerts-noreply@linkedin.com)`

### 3. Dump Raw Data
Fetch message metadata (id, from, subject, date, snippet) for all results and save them to `raw_emails.json` in the workspace root. **Do not parse the data manually.**

### 4. Extract with Local LLM
Run the extraction script:
```bash
uv run python extract_jobs.py
```
This script uses `llama3.2:3b` to parse the JSON and generate `batch_new.csv`.

### 5. Merge & Cleanup
- Run the update script: `uv run python update_tracker.py`.
- Verify the new entries in `job_applications_final.csv`.
- Delete `raw_emails.json` and `batch_new.csv`.
