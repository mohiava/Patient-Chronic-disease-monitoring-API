


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
import re
import csv
import os

app = FastAPI()

db_patients = "D:\POC1(HOSPITAL)\logs.csv"
db_logs = "D:\POC1(HOSPITAL)\logs.csv"
monitoring_counter = 1  # Counter for sequential monitoring IDs
log_counter = 1  # Counter for sequential log IDs

# Ensure CSV files exist with headers
if not os.path.exists(db_patients):
    with open(db_patients, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["patient_id", "chronic_diseases", "monitoring_frequency", "assigned_doctor", "lifestyle_notes", "monitoring_id", "timestamp"])

if not os.path.exists(db_logs):
    with open(db_logs, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["log_id", "patient_id", "reading_date", "blood_sugar_level", "blood_pressure", "weight", "notes", "timestamp"])

def validate_patient_id(patient_id: str):
    if not re.fullmatch(r'PAT\d{6}', patient_id):
        raise HTTPException(status_code=400, detail="Invalid patient ID format. Must be 'PAT' followed by 6 digits.")

class RegisterPatient(BaseModel):
    patient_id: str = Field(..., regex=r'PAT\d{6}')
    chronic_diseases: List[str]
    monitoring_frequency: str
    assigned_doctor: str
    lifestyle_notes: str

class LogReading(BaseModel):
    patient_id: str = Field(..., regex=r'PAT\d{6}')
    reading_date: date
    blood_sugar_level: Optional[int] = None
    blood_pressure: Optional[str] = None
    weight: Optional[float] = None
    notes: Optional[str] = None

@app.post("/chronic/register")
def register_patient(data: RegisterPatient):
    global monitoring_counter
    validate_patient_id(data.patient_id)
    
    # Check if patient already exists
    with open(db_patients, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == data.patient_id:
                raise HTTPException(status_code=400, detail="Patient already registered")
    
    monitoring_id = f"MON{monitoring_counter:06d}"
    monitoring_counter += 1
    timestamp = datetime.now().isoformat()
    
    # Store patient data in CSV
    with open(db_patients, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([data.patient_id, ",".join(data.chronic_diseases), data.monitoring_frequency, data.assigned_doctor, data.lifestyle_notes, monitoring_id, timestamp])
    
    return {
        "message": "Patient registered for chronic disease monitoring", 
        "monitoring_id": monitoring_id,
        "timestamp": timestamp
    }

@app.post("/chronic/log")
def log_reading(data: LogReading):
    global log_counter
    validate_patient_id(data.patient_id)
    
    # Generate log ID in sequence
    log_id = f"LOG{log_counter:06d}"
    log_counter += 1
    timestamp = datetime.now().isoformat()
    
    # Store log data in CSV
    with open(db_logs, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([log_id, data.patient_id, data.reading_date, data.blood_sugar_level, data.blood_pressure, data.weight, data.notes, timestamp])
    
    return {"message": "Chronic disease log updated successfully", "log_id": log_id, "timestamp": timestamp}

@app.get("/chronic/{patient_id}")
def fetch_chronic_history(patient_id: str):
    validate_patient_id(patient_id)
    patient_records = []
    chronic_diseases = ""
    monitoring_frequency = ""
    
    # Retrieve patient details
    with open(db_patients, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["patient_id"] == patient_id:
                chronic_diseases = row["chronic_diseases"].split(",")
                monitoring_frequency = row["monitoring_frequency"]
                break
    
    if not chronic_diseases:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Retrieve patient history
    with open(db_logs, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["patient_id"] == patient_id:
                patient_records.append({
                    "reading_date": row["reading_date"],
                    "blood_sugar_level": row["blood_sugar_level"],
                    "blood_pressure": row["blood_pressure"],
                    "weight": row["weight"],
                    "notes": row["notes"]
                })
    
    return {
        "patient_id": patient_id,
        "chronic_diseases": chronic_diseases,
        "monitoring_frequency": monitoring_frequency,
        "records": patient_records
    }




