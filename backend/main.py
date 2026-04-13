from datetime import UTC, datetime
import io
import os
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models
from database import engine, get_db
from services.eclat_service import compute_frequent_patterns
from services.prediction_service import PredictionService
from auth import create_access_token, decode_access_token, hash_password, is_hashed_password, verify_password

app = FastAPI(title="Cattle Disease Pattern Prediction API")

cors_origins = [origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501").split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prediction_service = PredictionService()
UPLOADS_DIR = Path(__file__).resolve().parent / "uploads" / "lab_reports"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {
        "user_id": payload.get("sub", ""),
        "role": payload.get("role", ""),
        "name": payload.get("name", ""),
    }


def require_roles(*allowed_roles: str):
    def _checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Access denied for this role")
        return current_user

    return _checker


def _ensure_owner_or_role(requested_user_id: str, current_user: dict, allowed_roles: set[str]) -> None:
    if current_user["role"] in allowed_roles:
        return
    if current_user["user_id"] != requested_user_id:
        raise HTTPException(status_code=403, detail="You can access only your own records")


def initialize_database() -> None:
    try:
        with Session(engine) as db:
            admin = db.query(models.Admin).filter(models.Admin.admin_id == "admin").first()
            if not admin:
                try:
                    db.add(models.Admin(admin_id="admin", password=hash_password(os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123"))))
                    db.commit()
                except IntegrityError:
                    db.rollback()
    except OperationalError as exc:
        raise RuntimeError("Database schema is not initialized. Run: alembic -c backend/alembic.ini upgrade head") from exc


initialize_database()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Cattle Disease Pattern Prediction API"}

@app.post("/predict")
def predict_disease(symptoms: str):
    disease = prediction_service.predict_disease(symptoms)
    treatment = prediction_service.get_treatment(disease)
    return {
        "symptoms": symptoms,
        "predicted_disease": disease,
        "recommended_treatment": treatment
    }

@app.post("/eclat/run", summary="Run Eclat algorithm on uploaded Excel file")
async def run_eclat(
    file: UploadFile = File(...),
    min_support: float = 0.04,
    min_confidence: float = 0.5,
    current_user: dict = Depends(require_roles("admin", "doctor")),
):
    """
    Upload an Excel file containing training data (e.g. TrainingDataset1.xls)
    and run the pattern prediction algorithm.
    """
    if not file.filename.endswith('.xls') and not file.filename.endswith('.xlsx') and not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only Excel (.xls, .xlsx) or CSV files are supported")

    contents = await file.read()
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            # Requires openpyxl or xlrd
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    # In the legacy app, the transactions are usually in a specific column or format.
    # We will assume a 'Data' column exists as it did in the C# `dt.Rows[i]["Data"]`
    if 'Data' not in df.columns:
        raise HTTPException(status_code=400, detail="The dataset must contain a 'Data' column with comma-separated items.")

    transactions = df['Data'].dropna().astype(str).tolist()
    
    # Run the algorithm
    frequent_items, rules = compute_frequent_patterns(
        transactions=transactions, 
        min_support=min_support, 
        min_confidence=min_confidence
    )
    
    # Format rules for JSON response
    formatted_rules = []
    for (x, y, conf) in rules:
        formatted_rules.append({
            "lhs": x,
            "rhs": y,
            "confidence": conf
        })

    return {
        "transaction_count": len(transactions),
        "frequent_items_count": len(frequent_items),
        "frequent_items": frequent_items,
        "rules_count": len(formatted_rules),
        "strong_rules": formatted_rules
    }

# --- Pydantic Schemas ---
class HistoryCreate(BaseModel):
    farmer_id: str
    description: str
    symptoms: str
    disease: str
    treatments: str

class QueryCreate(BaseModel):
    farmer_id: str
    query_text: str

class QueryReply(BaseModel):
    reply_text: str

class FarmerRegister(BaseModel):
    farmer_id: str
    password: str
    name: str
    contact_no: str
    address: str

class DoctorRegister(BaseModel):
    ic_id: str
    password: str
    name: str
    address: str
    contact_no: str
    email_id: str
    city_name: str  # Send city name and map to city_id

class UserLogin(BaseModel):
    user_id: str
    password: str
    role: str # "farmer", "doctor", "admin"


class CattleProfileCreate(BaseModel):
    farmer_id: str
    animal_tag: str
    animal_name: str
    breed: str
    age_years: Optional[float] = None
    weight_kg: Optional[float] = None
    gender: str
    pregnancy_status: str = "not_applicable"
    milk_yield_liters: Optional[float] = None
    village: str = ""
    notes: str = ""


class CaseSheetCreate(BaseModel):
    cattle_id: int
    farmer_id: str
    doctor_id: str
    symptoms: str
    diagnosis: str
    confirmed_disease: Optional[str] = None
    treatment: str
    dosage_notes: str = ""
    follow_up_date: Optional[datetime] = None
    notes: str = ""
    recovery_progress: str = "under_treatment"
    emergency_flag: bool = False
    case_status: str = "open"


class QueryTriageUpdate(BaseModel):
    doctor_id: str
    priority: str = "normal"
    status: str = "pending"
    follow_up_needed: bool = False
    notes: str = ""


class PreventiveCareCreate(BaseModel):
    cattle_id: int
    farmer_id: str
    care_type: str
    item_name: str
    due_date: datetime
    completed_date: Optional[datetime] = None
    status: str = "scheduled"
    notes: str = ""


def serialize_cattle(cattle: models.CattleProfile) -> dict:
    return {
        "id": cattle.id,
        "farmer_id": cattle.farmer_id,
        "animal_tag": cattle.animal_tag,
        "animal_name": cattle.animal_name,
        "breed": cattle.breed,
        "age_years": cattle.age_years,
        "weight_kg": cattle.weight_kg,
        "gender": cattle.gender,
        "pregnancy_status": cattle.pregnancy_status,
        "milk_yield_liters": cattle.milk_yield_liters,
        "village": cattle.village,
        "notes": cattle.notes,
        "created_at": cattle.created_at,
    }


def serialize_case_sheet(case: models.CaseSheet, cattle: Optional[models.CattleProfile] = None) -> dict:
    return {
        "id": case.id,
        "cattle_id": case.cattle_id,
        "farmer_id": case.farmer_id,
        "doctor_id": case.doctor_id,
        "visit_date": case.visit_date,
        "symptoms": case.symptoms,
        "diagnosis": case.diagnosis,
        "confirmed_disease": case.confirmed_disease,
        "treatment": case.treatment,
        "dosage_notes": case.dosage_notes,
        "follow_up_date": case.follow_up_date,
        "notes": case.notes,
        "recovery_progress": case.recovery_progress,
        "emergency_flag": case.emergency_flag,
        "case_status": case.case_status,
        "animal_tag": cattle.animal_tag if cattle else None,
        "animal_name": cattle.animal_name if cattle else None,
        "village": cattle.village if cattle else None,
    }


def serialize_preventive(record: models.PreventiveCareRecord, cattle: Optional[models.CattleProfile] = None) -> dict:
    return {
        "id": record.id,
        "cattle_id": record.cattle_id,
        "farmer_id": record.farmer_id,
        "care_type": record.care_type,
        "item_name": record.item_name,
        "due_date": record.due_date,
        "completed_date": record.completed_date,
        "status": record.status,
        "notes": record.notes,
        "animal_tag": cattle.animal_tag if cattle else None,
        "animal_name": cattle.animal_name if cattle else None,
    }


def serialize_lab_report(report: models.LabReport, cattle: Optional[models.CattleProfile] = None) -> dict:
    return {
        "id": report.id,
        "cattle_id": report.cattle_id,
        "case_sheet_id": report.case_sheet_id,
        "report_name": report.report_name,
        "report_type": report.report_type,
        "file_path": report.file_path,
        "notes": report.notes,
        "uploaded_at": report.uploaded_at,
        "animal_tag": cattle.animal_tag if cattle else None,
        "animal_name": cattle.animal_name if cattle else None,
    }

# --- Endpoints ---

@app.get("/symptoms")
def get_symptoms():
    from services.prediction_service import PredictionService
    return {"symptoms": sorted(list(PredictionService.SYMPTOMS))}

@app.post("/history")
def add_history(history: HistoryCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    _ensure_owner_or_role(history.farmer_id, current_user, {"doctor", "admin"})
    db_item = models.History(
        farmer_id=history.farmer_id,
        description=history.description,
        symptoms=history.symptoms,
        disease=history.disease,
        treatments=history.treatments
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/history/{farmer_id}")
def get_history(farmer_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    _ensure_owner_or_role(farmer_id, current_user, {"doctor", "admin"})
    records = db.query(models.History).filter(models.History.farmer_id == farmer_id).order_by(models.History.date.desc()).all()
    return records

@app.post("/queries")
def add_query(query: QueryCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    _ensure_owner_or_role(query.farmer_id, current_user, {"admin", "doctor"})
    db_item = models.Query(
        farmer_id=query.farmer_id,
        query_text=query.query_text
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/queries")
def get_all_queries(farmer_id: Optional[str] = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "farmer":
        farmer_id = current_user["user_id"]
    query = db.query(models.Query)
    if farmer_id:
        query = query.filter(models.Query.farmer_id == farmer_id)
    records = query.order_by(models.Query.query_date.desc()).all()
    return records

@app.post("/queries/{query_id}/reply")
def reply_query(query_id: int, reply: QueryReply, db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin"))):
    db_item = db.query(models.Query).filter(models.Query.id == query_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Query not found")
    
    db_item.reply_text = reply.reply_text
    db_item.reply_date = datetime.now(UTC)
    db.commit()
    db.refresh(db_item)
    return db_item


# --- Auth Endpoints ---

@app.post("/register/farmer")
def register_farmer(farmer: FarmerRegister, db: Session = Depends(get_db)):
    # Check if exists
    if db.query(models.Farmer).filter(models.Farmer.farmer_id == farmer.farmer_id).first():
        raise HTTPException(status_code=400, detail="Farmer ID already registered")
    
    db_item = models.Farmer(
        farmer_id=farmer.farmer_id,
        password=hash_password(farmer.password),  # Storing plain text as requested by legacy design migration
        name=farmer.name,
        contact_no=farmer.contact_no,
        address=farmer.address
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return {"message": "Farmer registered successfully."}

@app.post("/register/vdoctor")
def register_doctor(doctor: DoctorRegister, db: Session = Depends(get_db)):
    if db.query(models.VDoctor).filter(models.VDoctor.ic_id == doctor.ic_id).first():
        raise HTTPException(status_code=400, detail="Doctor IC ID already registered")
        
    # Get or create city
    city = db.query(models.City).filter(models.City.city_name == doctor.city_name).first()
    if not city:
        city = models.City(city_name=doctor.city_name)
        db.add(city)
        db.commit()
        db.refresh(city)
        
    db_item = models.VDoctor(
        ic_id=doctor.ic_id,
        password=hash_password(doctor.password),
        name=doctor.name,
        address=doctor.address,
        contact_no=doctor.contact_no,
        email_id=doctor.email_id,
        city_id=city.city_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return {"message": "Doctor registered successfully."}

@app.post("/login")
def login(creds: UserLogin, db: Session = Depends(get_db)):
    user = None
    stored_password = None
    display_name = "Administrator"

    if creds.role == "farmer":
        user = db.query(models.Farmer).filter(models.Farmer.farmer_id == creds.user_id).first()
        stored_password = user.password if user else None
        display_name = user.name if user else display_name
    elif creds.role == "doctor":
        user = db.query(models.VDoctor).filter(models.VDoctor.ic_id == creds.user_id).first()
        stored_password = user.password if user else None
        display_name = user.name if user else display_name
    elif creds.role == "admin":
        user = db.query(models.Admin).filter(models.Admin.admin_id == creds.user_id).first()
        stored_password = user.password if user else None

    if not user or not stored_password:
        raise HTTPException(status_code=401, detail="Invalid credentials for the specified role.")

    password_ok = False
    if is_hashed_password(stored_password):
        password_ok = verify_password(creds.password, stored_password)
    else:
        password_ok = creds.password == stored_password
        if password_ok:
            user.password = hash_password(creds.password)
            db.commit()

    if not password_ok:
        raise HTTPException(status_code=401, detail="Invalid credentials for the specified role.")

    token = create_access_token(user_id=creds.user_id, role=creds.role, name=display_name)

    return {
        "user_id": creds.user_id,
        "role": creds.role,
        "name": display_name,
        "access_token": token,
        "token_type": "bearer",
    }

@app.get("/users")
def get_users(db: Session = Depends(get_db), current_user: dict = Depends(require_roles("admin"))):
    farmers = db.query(models.Farmer).all()
    doctors = db.query(models.VDoctor).all()
    
    return {
        "farmers": [{"farmer_id": f.farmer_id, "name": f.name, "contact_no": f.contact_no, "address": f.address} for f in farmers],
        "doctors": [{"ic_id": d.ic_id, "name": d.name, "email_id": d.email_id, "contact_no": d.contact_no} for d in doctors]
    }


@app.post("/cattle")
def create_cattle_profile(payload: CattleProfileCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin"))):
    db_item = models.CattleProfile(**payload.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return serialize_cattle(db_item)


@app.get("/cattle")
def get_cattle_profiles(farmer_id: Optional[str] = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "farmer":
        farmer_id = current_user["user_id"]
    query = db.query(models.CattleProfile)
    if farmer_id:
        query = query.filter(models.CattleProfile.farmer_id == farmer_id)
    cattle = query.order_by(models.CattleProfile.created_at.desc()).all()
    return [serialize_cattle(item) for item in cattle]


@app.post("/case-sheets")
def create_case_sheet(payload: CaseSheetCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin"))):
    case = models.CaseSheet(**payload.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    cattle = db.query(models.CattleProfile).filter(models.CattleProfile.id == case.cattle_id).first()
    return {
        "case_sheet": serialize_case_sheet(case, cattle),
        "prescription": {
            "animal": cattle.animal_name if cattle else "",
            "animal_tag": cattle.animal_tag if cattle else "",
            "diagnosis": case.confirmed_disease or case.diagnosis,
            "treatment": case.treatment,
            "dosage_notes": case.dosage_notes,
            "follow_up_date": case.follow_up_date,
        },
    }


@app.get("/case-sheets")
def get_case_sheets(
    cattle_id: Optional[int] = None,
    farmer_id: Optional[str] = None,
    symptoms: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] == "farmer":
        farmer_id = current_user["user_id"]
    cases = db.query(models.CaseSheet).order_by(models.CaseSheet.visit_date.desc()).all()
    cattle_lookup = {item.id: item for item in db.query(models.CattleProfile).all()}
    symptom_tokens = {token.strip().lower() for token in symptoms.split(",")} if symptoms else set()

    results = []
    for case in cases:
        if cattle_id and case.cattle_id != cattle_id:
            continue
        if farmer_id and case.farmer_id != farmer_id:
            continue
        if symptom_tokens:
            case_tokens = {token.strip().lower() for token in str(case.symptoms).split(",") if token.strip()}
            if not symptom_tokens.intersection(case_tokens):
                continue
        results.append(serialize_case_sheet(case, cattle_lookup.get(case.cattle_id)))
    return results


@app.get("/follow-ups")
def get_follow_ups(status: str = "all", db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin"))):
    now = datetime.now(UTC)
    cases = db.query(models.CaseSheet).filter(models.CaseSheet.follow_up_date.isnot(None)).order_by(models.CaseSheet.follow_up_date.asc()).all()
    cattle_lookup = {item.id: item for item in db.query(models.CattleProfile).all()}
    results = []
    for case in cases:
        due_date = case.follow_up_date
        if status == "due" and due_date > now:
            continue
        if status == "upcoming" and due_date <= now:
            continue
        if status == "open" and case.case_status == "closed":
            continue
        results.append(serialize_case_sheet(case, cattle_lookup.get(case.cattle_id)))
    return results


@app.get("/doctor/queries")
def get_doctor_queries(db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin"))):
    queries = db.query(models.Query).order_by(models.Query.query_date.desc()).all()
    reviews = {item.query_id: item for item in db.query(models.QueryReview).all()}
    results = []
    for query in queries:
        review = reviews.get(query.id)
        results.append({
            "id": query.id,
            "farmer_id": query.farmer_id,
            "query_text": query.query_text,
            "query_date": query.query_date,
            "reply_text": query.reply_text,
            "reply_date": query.reply_date,
            "priority": review.priority if review else "normal",
            "status": review.status if review else ("answered" if query.reply_text else "pending"),
            "follow_up_needed": review.follow_up_needed if review else False,
            "doctor_notes": review.notes if review else "",
            "doctor_id": review.doctor_id if review else None,
        })
    return results


@app.post("/doctor/queries/{query_id}/triage")
def triage_query(query_id: int, payload: QueryTriageUpdate, db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin"))):
    review = db.query(models.QueryReview).filter(models.QueryReview.query_id == query_id).first()
    if not review:
        review = models.QueryReview(query_id=query_id, **payload.model_dump())
        db.add(review)
    else:
        for key, value in payload.model_dump().items():
            setattr(review, key, value)
        review.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(review)
    return {
        "query_id": review.query_id,
        "priority": review.priority,
        "status": review.status,
        "follow_up_needed": review.follow_up_needed,
        "doctor_notes": review.notes,
        "doctor_id": review.doctor_id,
    }


@app.post("/preventive-care")
def create_preventive_care(payload: PreventiveCareCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin"))):
    record = models.PreventiveCareRecord(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    cattle = db.query(models.CattleProfile).filter(models.CattleProfile.id == record.cattle_id).first()
    return serialize_preventive(record, cattle)


@app.get("/preventive-care")
def get_preventive_care(status: str = "all", db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin"))):
    query = db.query(models.PreventiveCareRecord).order_by(models.PreventiveCareRecord.due_date.asc())
    if status != "all":
        query = query.filter(models.PreventiveCareRecord.status == status)
    records = query.all()
    cattle_lookup = {item.id: item for item in db.query(models.CattleProfile).all()}
    return [serialize_preventive(item, cattle_lookup.get(item.cattle_id)) for item in records]


@app.post("/lab-reports")
async def upload_lab_report(
    cattle_id: int,
    case_sheet_id: Optional[int] = None,
    report_type: str = "general",
    notes: str = "",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("doctor", "admin")),
):
    filename = f"{int(datetime.now(UTC).timestamp())}_{file.filename}"
    path = UPLOADS_DIR / filename
    contents = await file.read()
    path.write_bytes(contents)

    report = models.LabReport(
        cattle_id=cattle_id,
        case_sheet_id=case_sheet_id,
        report_name=file.filename,
        report_type=report_type,
        file_path=str(path),
        notes=notes,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    cattle = db.query(models.CattleProfile).filter(models.CattleProfile.id == cattle_id).first()
    return serialize_lab_report(report, cattle)


@app.get("/lab-reports")
def get_lab_reports(cattle_id: Optional[int] = None, db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin"))):
    query = db.query(models.LabReport).order_by(models.LabReport.uploaded_at.desc())
    if cattle_id:
        query = query.filter(models.LabReport.cattle_id == cattle_id)
    reports = query.all()
    cattle_lookup = {item.id: item for item in db.query(models.CattleProfile).all()}
    return [serialize_lab_report(item, cattle_lookup.get(item.cattle_id)) for item in reports]


@app.get("/doctor/trends")
def get_doctor_trends(db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin"))):
    cases = db.query(models.CaseSheet).all()
    cattle_lookup = {item.id: item for item in db.query(models.CattleProfile).all()}
    disease_counts = {}
    village_counts = {}
    monthly_counts = {}
    for case in cases:
        disease = case.confirmed_disease or case.diagnosis or "Unknown"
        disease_counts[disease] = disease_counts.get(disease, 0) + 1
        village = (cattle_lookup.get(case.cattle_id).village if cattle_lookup.get(case.cattle_id) else "") or "Unknown"
        village_counts[village] = village_counts.get(village, 0) + 1
        month_key = case.visit_date.strftime("%Y-%m")
        monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
    return {
        "disease_counts": disease_counts,
        "village_counts": village_counts,
        "monthly_counts": monthly_counts,
    }


@app.get("/doctor/emergency-alerts")
def get_emergency_alerts(db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin"))):
    severe_keywords = {"breathing-difficulty", "high-fever", "bleeding", "asphyxia", "convulsions", "seizures"}
    cases = db.query(models.CaseSheet).order_by(models.CaseSheet.visit_date.desc()).all()
    cattle_lookup = {item.id: item for item in db.query(models.CattleProfile).all()}
    results = []
    for case in cases:
        case_tokens = {token.strip().lower() for token in str(case.symptoms).split(",") if token.strip()}
        if case.emergency_flag or severe_keywords.intersection(case_tokens):
            results.append(serialize_case_sheet(case, cattle_lookup.get(case.cattle_id)))
    return results


@app.get("/doctor/similar-cases")
def get_similar_cases(symptoms: str, db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin"))):
    input_tokens = {token.strip().lower() for token in symptoms.split(",") if token.strip()}
    cattle_lookup = {item.id: item for item in db.query(models.CattleProfile).all()}
    cases = db.query(models.CaseSheet).order_by(models.CaseSheet.visit_date.desc()).all()
    ranked = []
    for case in cases:
        case_tokens = {token.strip().lower() for token in str(case.symptoms).split(",") if token.strip()}
        overlap = len(input_tokens.intersection(case_tokens))
        if overlap == 0:
            continue
        score = overlap / max(len(input_tokens.union(case_tokens)), 1)
        ranked.append((score, case))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [serialize_case_sheet(case, cattle_lookup.get(case.cattle_id)) for score, case in ranked[:10]]

@app.get("/analytics")
def get_analytics(db: Session = Depends(get_db), current_user: dict = Depends(require_roles("admin"))):
    # Calculate disease frequencies from History
    histories = db.query(models.History).all()
    disease_counts = {}
    for h in histories:
        if h.disease:
            disease_counts[h.disease] = disease_counts.get(h.disease, 0) + 1
            
    # Calculate User distributions
    farmer_count = db.query(models.Farmer).count()
    doctor_count = db.query(models.VDoctor).count()
    query_count = db.query(models.Query).count()
    
    return {
        "disease_counts": disease_counts,
        "metrics": {
            "total_farmers": farmer_count,
            "total_doctors": doctor_count,
            "total_queries": query_count,
            "total_predictions": len(histories)
        }
    }
