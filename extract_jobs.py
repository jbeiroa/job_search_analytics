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
    is_job_related: bool = Field(description="True if the email is a job application, a rejection, an interview invite, or a direct response from a company regarding a specific position. False if it is a generic newsletter, an ad, a government notification (like AGIP/UBA), an investment update, or unrelated to a professional job search.")
    application_date: Optional[str] = Field(None, description="The date the application was sent in YYYY-MM-DD format.")
    company: Optional[str] = Field(None, description="The name of the company. Look at the 'from' and 'subject' fields.")
    job_title: Optional[str] = Field(None, description="The job title or position. Look at the 'subject' and 'snippet' fields.")
    platform: Optional[str] = Field(None, description="One of: LinkedIn, Bumeran, Hiring Room, Workable, Silver.dev, or Direct Email.")
    response_date: Optional[str] = Field(None, description="The date of the response email in YYYY-MM-DD format, if applicable.")
    response_status: Optional[str] = Field(None, description="One of: Received, Interview, Rejected, Technical Test, Questionnaire, Update Received, In Progress.")

def parse_emails(json_file='raw_emails.json', out_csv='batch_new.csv', model_name='llama3.2:3b'):
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
        Analyze the following email metadata and snippet to extract job application data.
        
        CRITICAL CLASSIFICATION RULE:
        - Set 'is_job_related' to FALSE if the email is:
            * A generic newsletter or digest (e.g., 'Weekly Digest', 'Cenital', 'The AI Report').
            * An advertisement or promotional email (e.g., Glassdoor job recommendations, 'Remote Tech Jobs Are Disappearing').
            * Unrelated personal or government mail (e.g., AGIP taxes, UBA university notifications, bank balances like IOL/BBVA).
            * Educational competitions or general campus news (e.g., 'Competencia de Datos', 'Coloquio').
        - Set 'is_job_related' to TRUE only for:
            * Application confirmations ('Thanks for applying', 'Postulación recibida').
            * Rejection notices ('Unfortunately', 'No seguiremos').
            * Interview invitations or follow-ups.
        
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
        - If 'is_job_related' is TRUE, DO NOT return empty strings for 'company' or 'job_title'.
        - The 'application_date' MUST be '{formatted_date}'.
        - If 'response_status' is NOT 'Received', 'response_date' must be '{formatted_date}'.

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
            
            if data.get('is_job_related'):
                # Cleanup and append
                clean_data = {k: v for k, v in data.items() if k != 'is_job_related'}
                records.append(clean_data)
                print(f"✅ Extracted: {clean_data.get('company')} - {clean_data.get('response_status')}")
            else:
                print(f"⏩ Skipped (Unrelated): {email.get('from')} - {email.get('subject')[:30]}...")
                
        except Exception as e:
            print(f"❌ Failed to parse email from {email.get('from')}: {e}")
            
    if records:
        df = pd.DataFrame(records)
        df.to_csv(out_csv, index=False)
        print(f"\n🎉 Saved {len(records)} records to {out_csv}.")
    else:
        print("No job-related records extracted.")

if __name__ == '__main__':
    parse_emails()
