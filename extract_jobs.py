import json
import pandas as pd
from pydantic import BaseModel, Field
from typing import Optional
import datetime
from email.utils import parsedate_to_datetime

# Try importing ollama
try:
    from ollama import chat
except ImportError:
    print("Error: 'ollama' package is not installed. Please run `uv add ollama pydantic pandas`.")
    exit(1)

class JobExtraction(BaseModel):
    application_date: str = Field(min_length=1, description="The date the application was sent in YYYY-MM-DD format.")
    company: str = Field(min_length=1, description="The name of the company. Look at the 'from' and 'subject' fields.")
    job_title: str = Field(min_length=1, description="The job title or position. Look at the 'subject' and 'snippet' fields.")
    platform: str = Field(min_length=1, description="One of: LinkedIn, Bumeran, Hiring Room, Workable, Silver.dev, or Direct Email.")
    response_date: Optional[str] = Field(None, description="The date of the response email in YYYY-MM-DD format, if applicable.")
    response_status: str = Field(min_length=1, description="One of: Received, Interview, Rejected, Technical Test, Questionnaire, Update Received, In Progress.")

def parse_emails(json_file='raw_emails.json', out_csv='batch_test_nlp.csv', model_name='llama3.2:3b'):
    try:
        with open(json_file, 'r') as f:
            emails = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_file} not found. Ensure you fetch emails first.")
        return

    records = []
    print(f"Processing {len(emails)} emails with Ollama model '{model_name}'...")
    
    for email in emails:
        # Standardize email date
        raw_date = email.get('date', '')
        formatted_date = "Unknown"
        if raw_date:
            try:
                dt = parsedate_to_datetime(raw_date)
                formatted_date = dt.strftime('%Y-%m-%d')
            except Exception:
                formatted_date = raw_date
                
        prompt = f"""
        Extract job application data from the following email metadata and snippet.
        
        Rules for platform: 
        - If 'from' or 'subject' contains 'linkedin.com', platform is 'LinkedIn'.
        - If 'from' or 'subject' contains 'bumeran.com', platform is 'Bumeran'.
        - If 'from' or 'subject' contains 'hiringroom.com', platform is 'Hiring Room'.
        - If 'from' or 'subject' contains 'workablemail.com' or 'workable.com', platform is 'Workable'.
        - If 'snippet' or 'subject' mentions 'Silver.dev', platform is 'Silver.dev'.
        - If 'from' contains 'bamboohr.com', platform is 'Direct Email'.
        - Else, 'Direct Email'.
        
        Rules for status:
        - If 'snippet' or 'subject' mentions 'interview', 'entrevista', 'meeting', 'reunión', status is 'Interview'.
        - If 'snippet' or 'subject' mentions 'unfortunately', 'rejected', 'rechazado', 'descartado', 'no seguiremos', 'avanzar con otro', status is 'Rejected'.
        - If 'snippet' or 'subject' mentions 'test', 'prueba', 'challenge', 'evaluación', 'cuestionario', status is 'Technical Test'.
        - Otherwise default to 'Received'.
        
        CRITICAL: 
        - DO NOT return empty strings for 'company' or 'job_title'. Infer them from the metadata.
        - The 'application_date' MUST be '{formatted_date}'.
        - If 'response_status' is NOT 'Received', 'response_date' must be '{formatted_date}'.
        - Company name should be a clean name (e.g., 'Dev.Pro' instead of 'Dev.Pro Career').

        Email Data:
        - Date: {formatted_date}
        - From: {email.get('from')}
        - Subject: {email.get('subject')}
        - Snippet: {email.get('snippet')}
        """
        
        try:
            response = chat(
                model=model_name,
                messages=[{'role': 'user', 'content': prompt}],
                format=JobExtraction.model_json_schema()
            )
            data = json.loads(response.message.content)
            records.append(data)
            print(f"✅ Extracted: {data.get('company')} - {data.get('response_status')}")
        except Exception as e:
            print(f"❌ Failed to parse email from {email.get('from')}: {e}")
            
    if records:
        df = pd.DataFrame(records)
        df.to_csv(out_csv, index=False)
        print(f"\n🎉 Saved {len(records)} records to {out_csv}.")
    else:
        print("No records extracted.")

if __name__ == '__main__':
    parse_emails()
