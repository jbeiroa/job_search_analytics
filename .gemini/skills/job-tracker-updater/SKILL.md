---
name: job-tracker-updater
description: Update the job application tracker by fetching new applications and responses from Gmail and extracting data using a local LLM (Ollama).
---

# Job Tracker Updater Skill

This skill automates the incremental update of the `job_applications_final.csv` file by scanning Gmail for job-related emails and delegating data extraction to a local LLM via Ollama.

## Prerequisites

- Access to `mcp_google-workspace_gmail` tools.
- `job_applications_final.csv` must exist in the workspace root.
- `all_ids.txt` (optional, created automatically) to track processed emails.
- `update_tracker.py` and `extract_jobs.py` scripts must be available in the workspace root.
- **Ollama** installed and running with the `llama3.2:3b` model.
- Python dependencies: `uv add ollama pydantic pandas`

## Workflow

### 1. Determine Date Range
Find the most recent `application_date` in `job_applications_final.csv`. 

### 2. Search & Fetch Emails
Run Gmail searches to capture potential applications and responses:
- **Applications:** `after:{DATE} ("Thanks for applying" OR "application was sent to" OR "recibieron tu postulación" OR "Postulación recibida" OR "Confirmación de postulación" OR "Gracias por postularte" OR "recibió tu postulación" OR "received your application" OR "Solicitud recibida" OR "candidatura recibida") -from:(jobalerts-noreply@linkedin.com)`
- **Responses:** `after:{DATE} ("unfortunately" OR "rejected" OR "entrevista" OR "rechazado" OR "proceso" OR "oportunidad" OR "interview" OR "next steps" OR "candidatura" OR "selección" OR "resultado") -from:(jobalerts-noreply@linkedin.com)`

### 3. Deduplicate and Fetch Metadata
- Read `all_ids.txt` to get a list of already processed message IDs.
- Filter out any IDs from the search results that are already in `all_ids.txt`.
- For NEW IDs only, fetch message metadata (id, from, subject, date, snippet) using `mcp_google-workspace_gmail.get`.
- Save the results as a JSON array to `raw_emails.json` in the workspace root.

### 4. Execute Unified Update
Run the main controller script:
```bash
uv run python update_tracker.py
```
This script handles:
1. Extraction with the local LLM (`extract_jobs.py`).
2. Merging new records into the CSV.
3. Appending processed IDs to `all_ids.txt`.
4. Cleaning up `raw_emails.json` and temporary files.

### 5. Verification
Verify the update in `job_applications_final.csv`.
