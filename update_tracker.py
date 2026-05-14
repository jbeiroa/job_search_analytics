import pandas as pd
import os
import json
import subprocess
from datetime import datetime

def get_processed_ids(id_file='all_ids.txt'):
    if os.path.exists(id_file):
        with open(id_file, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_new_ids(new_ids, id_file='all_ids.txt'):
    with open(id_file, 'a') as f:
        for msg_id in new_ids:
            f.write(f"{msg_id}\n")

def update_job_search_data(new_records_path='batch_new.csv', final_csv_path='job_applications_final.csv'):
    """
    Merges new records into the final CSV, handling duplicates and updating statuses.
    """
    if not os.path.exists(new_records_path):
        print(f"Warning: {new_records_path} not found. Nothing to merge.")
        return

    df_new = pd.read_csv(new_records_path)
    if df_new.empty:
        print("No new records to update.")
        return

    if os.path.exists(final_csv_path):
        df_final = pd.read_csv(final_csv_path)
        df_combined = pd.concat([df_final, df_new], ignore_index=True)
        
        # Standardize dates
        for col in ['application_date', 'response_date']:
            df_combined[col] = pd.to_datetime(df_combined[col], errors='coerce', format='mixed').dt.strftime('%Y-%m-%d')
        
        # Standardize strings
        df_combined['job_title'] = df_combined['job_title'].fillna('N/A').str.strip()
        df_combined['company'] = df_combined['company'].fillna('Unknown').str.strip()

        # Deduplication with status priority
        status_priority = {
            'Rejected': 4,
            'Interview': 4,
            'Technical Test': 3,
            'Questionnaire': 3,
            'Update Received': 2,
            'In Progress': 2,
            'Received': 1,
            'No Response': 0
        }
        df_combined['status_rank'] = df_combined['response_status'].apply(
            lambda x: status_priority.get(x, 1) if pd.notnull(x) else 0
        )
        
        df_combined = df_combined.sort_values(
            by=['company', 'job_title', 'status_rank', 'application_date'], 
            ascending=[True, True, False, False]
        )
        df_combined = df_combined.drop_duplicates(subset=['company', 'job_title'], keep='first')
        df_combined = df_combined.drop(columns=['status_rank'])
    else:
        df_combined = df_new

    df_combined.to_csv(final_csv_path, index=False)
    print(f"Successfully updated {final_csv_path}. Total records: {len(df_combined)}")

def run_extraction():
    """Runs the extraction script if raw_emails.json exists."""
    if os.path.exists('raw_emails.json'):
        print("Starting extraction with local LLM...")
        try:
            subprocess.run(['uv', 'run', 'python', 'extract_jobs.py'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error during extraction: {e}")
            return False
        return True
    return False

if __name__ == "__main__":
    # 1. Check for raw_emails.json
    if run_extraction():
        # 2. Merge data
        update_job_search_data()
        
        # 3. Mark IDs as processed (this assumes the agent passes only new IDs to raw_emails.json)
        # However, for safety, if raw_emails.json was generated, we assume those IDs are now 'seen'.
        if os.path.exists('raw_emails.json'):
            with open('raw_emails.json', 'r') as f:
                emails = json.load(f)
                new_ids = [e['id'] for e in emails]
                save_new_ids(new_ids)
            
            # 4. Cleanup
            os.remove('raw_emails.json')
            if os.path.exists('batch_new.csv'):
                os.remove('batch_new.csv')
            print("Cleanup complete.")
    else:
        print("No raw_emails.json found to process.")
