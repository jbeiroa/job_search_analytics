# Job Search Analytics & Tracker

An automated tool to track job applications and company responses directly from your Gmail. It uses a local LLM (Ollama) to parse email metadata into structured data, maintaining a clean and up-to-date CSV of your job search progress.

## 🚀 Features

- **Automated Gmail Sync:** Scans your inbox for application confirmations and recruiter responses.
- **Local LLM Extraction:** Uses `llama3.2:3b` via Ollama to intelligently extract company names, job titles, and statuses.
- **Smart Deduplication:** Tracks processed email IDs to avoid redundant parsing and API calls.
- **Low-Friction Updates:** A unified controller handles the entire fetch-extract-merge pipeline.
- **Privacy First:** Job application data (`.csv`) and message IDs (`.txt`) are ignored by Git.

## 📋 Prerequisites

- **Python 3.10+**
- **[uv](https://github.com/astral-sh/uv):** For fast dependency management.
- **[Ollama](https://ollama.com/):** Installed and running locally.
  - Required model: `ollama pull llama3.2:3b`
- **Gemini CLI / Gmail MCP:** Access to the `mcp_google-workspace_gmail` tools.

## 🛠️ Setup

1. **Install Dependencies:**
   ```bash
   uv add ollama pydantic pandas
   ```

2. **Prepare the Files:**
   Ensure `job_applications_final.csv` (or an empty one with the headers below) exists in the root:
   `application_date,company,job_title,platform,response_date,response_status`

3. **Gemini Skill Setup:**
   The skill definition is located in `.gemini/skills/job-tracker-updater/SKILL.md`.

## ⚡ Usage

### Using the Gemini CLI Skill
Simply tell Gemini:
> "Update my job search tracker"

The agent will automatically determine the date range, fetch new emails, run the extraction, and merge the results.

### Manual Execution
You can also run the update manually if you have a `raw_emails.json` file ready:

```bash
uv run python update_tracker.py
```

## 📂 Project Structure

- `update_tracker.py`: The main controller that manages the workflow and data merging.
- `extract_jobs.py`: Contains the LLM logic for classifying and extracting job data.
- `all_ids.txt`: (Local only) Persistent list of processed Gmail message IDs.
- `job_applications_final.csv`: (Local only) Your master job search database.

## 🛡️ Data Privacy
This project is designed to be shared without exposing your personal job search data. The following files are ignored by Git:
- `*.csv`
- `all_ids.txt`
- `raw_emails.json`
