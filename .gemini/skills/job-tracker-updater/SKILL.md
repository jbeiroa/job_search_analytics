---
name: job-tracker-updater
description: Update the job application tracker by fetching new applications and responses from Gmail since the last update date. Use when you need to keep the CSV list of jobs current.
---

# Job Tracker Updater Skill

This skill automates the incremental update of the `job_applications_final.csv` file by scanning Gmail for new job-related emails.

## Prerequisites

- Access to `mcp_google-workspace_gmail` tools.
- `job_applications_final.csv` must exist in the workspace root.
- `update_tracker.py` script must be available in the workspace root.

## Workflow

### 1. Determine Last Update Date
Read `job_applications_final.csv` to find the most recent `application_date`. 
If the file is empty or missing, default to `2025/12/31`.

### 2. Search for New Applications
Run a Gmail search for applications since the last update date:
```
after:{LAST_DATE} ("Thanks for applying" OR "application was sent to" OR "Ya recibieron tu postulación" OR "Postulación recibida" OR "Confirmación de postulación" OR "Gracias por postularte") -from:(jobalerts-noreply@linkedin.com)
```

### 3. Search for New Responses
Run a Gmail search for potential outcomes:
```
after:{LAST_DATE} ("unfortunately" OR "rejected" OR "entrevista" OR "rechazado" OR "proceso" OR "oportunidad" OR "interview" OR "next steps") -from:(jobalerts-noreply@linkedin.com)
```

### 4. Fetch Metadata & Process
- Fetch message metadata in batches of 10-20 IDs.
- Extract `date`, `company`, `job_title`, and `threadId`.
- Match responses to applications using `threadId` or fuzzy company name matching.

### 5. Finalize
- Save the new batch of records into `batch_new.csv`.
- Run the update script: `uv run python update_tracker.py`.
- Delete `batch_new.csv` after the update is complete.

## Platform Mapping Rules
- **LinkedIn**: sender contains `linkedin.com`
- **Bumeran**: sender contains `bumeran.com`
- **Hiring Room**: sender contains `hiringroom.com`
- **Workable**: sender contains `workablemail.com`
- **Silver.dev**: subject or body mentions `Silver.dev`
- **Direct Email**: If none of the above match.

## Status Mapping Rules
- **Interview**: subject or snippet mentions "interview", "entrevista", "meeting", "reunión".
- **Rejected**: subject or snippet mentions "unfortunately", "rejected", "no seguiremos", "descartado".
- **Technical Test**: subject or snippet mentions "test", "prueba", "challenge", "evaluación".
- **Received**: Default for new application confirmations.
