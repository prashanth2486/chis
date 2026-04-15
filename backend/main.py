from datetime import UTC, datetime
import io
import os
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Query as FastAPIQuery
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

import models
from database import engine, get_db
from services.eclat_service import compute_frequent_patterns
from services.prediction_service import PredictionService
from services.clinical_service import build_prescription_guidance, normalize_symptoms, season_from_date, severity_from_query_text, severity_from_symptoms
from auth import create_access_token, decode_access_token, hash_password, is_hashed_password, verify_password
from config import settings
from observability import setup_observability
from api_models import EclatRunResponse, GenericMessageResponse, HealthResponse, LoginResponse, PredictResponse, ReadyResponse, RootResponse

app = FastAPI(title=settings.app_name)

cors_origins = [origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
setup_observability(app)

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


RBAC_RULES = {
    "/users": {"admin", "doctor"},
    "/analytics": {"admin"},
    "/admin": {"admin"},
    "/doctor": {"doctor", "admin"},
    "/case-sheets": {"doctor", "admin", "farmer"},
    "/cattle": {"doctor", "admin", "farmer"},
    "/predict": {"farmer", "doctor", "admin"},
    "/symptoms": {"farmer", "doctor", "admin"},
    "/queries": {"farmer", "doctor", "admin"},
    "/history": {"farmer", "doctor", "admin"},
    "/eclat": {"doctor", "admin"},
    "/follow-ups": {"doctor", "admin"},
    "/preventive-care": {"doctor", "admin"},
    "/lab-reports": {"doctor", "admin"},
}


@app.middleware("http")
async def rbac_guard_middleware(request, call_next):
    path = request.url.path

    if path in {"/", "/health", "/ready", "/login", "/register/farmer", "/register/vdoctor", "/docs", "/openapi.json", "/redoc"}:
        return await call_next(request)

    required_roles = None
    for prefix, roles in RBAC_RULES.items():
        if path.startswith(prefix):
            required_roles = roles
            break

    if not required_roles:
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "status_code": 401,
                    "message": "Missing bearer token",
                    "details": None,
                    "request_id": getattr(request.state, "request_id", ""),
                }
            },
        )

    token = auth_header.replace("Bearer ", "", 1)
    payload = decode_access_token(token)
    if not payload:
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "status_code": 401,
                    "message": "Invalid or expired token",
                    "details": None,
                    "request_id": getattr(request.state, "request_id", ""),
                }
            },
        )

    role = payload.get("role", "")
    if role not in required_roles:
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "status_code": 403,
                    "message": "Access denied for this role",
                    "details": None,
                    "request_id": getattr(request.state, "request_id", ""),
                }
            },
        )

    return await call_next(request)


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

@app.get("/", response_model=RootResponse)
def read_root():
    return {"message": "Welcome to the Cattle Disease Pattern Prediction API"}

@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env}


@app.get("/ready", response_model=ReadyResponse)
def readiness_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    uploads_ok = UPLOADS_DIR.exists()
    return {"status": "ready", "database": "ok", "uploads": "ok" if uploads_ok else "missing"}


@app.post("/predict", response_model=PredictResponse)
def predict_disease(
    symptoms: str = FastAPIQuery(..., min_length=2, max_length=2000),
    current_user: dict = Depends(require_roles("farmer", "doctor", "admin")),
):
    disease = prediction_service.predict_disease(symptoms)
    treatment = prediction_service.get_treatment(disease)
    return {
        "symptoms": symptoms,
        "predicted_disease": disease,
        "recommended_treatment": treatment
    }

@app.post("/eclat/run", response_model=EclatRunResponse, summary="Run Eclat algorithm on uploaded Excel file")
async def run_eclat(
    file: UploadFile = File(...),
    min_support: float = FastAPIQuery(0.04, ge=0.001, le=1.0),
    min_confidence: float = FastAPIQuery(0.5, ge=0.1, le=1.0),
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
    farmer_id: str = Field(..., min_length=2, max_length=64)
    description: str = Field(..., min_length=2, max_length=200)
    symptoms: str = Field(..., min_length=2, max_length=2000)
    disease: str = Field(..., min_length=2, max_length=120)
    treatments: str = Field(..., min_length=2, max_length=2000)

class QueryCreate(BaseModel):
    farmer_id: str = Field(..., min_length=2, max_length=64)
    query_text: str = Field(..., min_length=5, max_length=2000)

class QueryReply(BaseModel):
    reply_text: str = Field(..., min_length=2, max_length=2000)

class FarmerRegister(BaseModel):
    farmer_id: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    name: str = Field(..., min_length=2, max_length=120)
    contact_no: str = Field(..., min_length=6, max_length=32)
    address: str = Field(..., min_length=5, max_length=300)

class DoctorRegister(BaseModel):
    ic_id: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    name: str = Field(..., min_length=2, max_length=120)
    address: str = Field(..., min_length=5, max_length=300)
    contact_no: str = Field(..., min_length=6, max_length=32)
    email_id: EmailStr
    city_name: str = Field(..., min_length=2, max_length=120)  # Send city name and map to city_id

class UserLogin(BaseModel):
    user_id: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)
    role: str = Field(..., pattern="^(farmer|doctor|admin)$")

class CattleProfileCreate(BaseModel):
    farmer_id: str = Field(..., min_length=2, max_length=64)
    animal_tag: str = Field(..., min_length=1, max_length=64)
    animal_name: str = Field(..., min_length=1, max_length=120)
    breed: str = Field(..., min_length=1, max_length=120)
    age_years: Optional[float] = Field(None, ge=0, le=40)
    weight_kg: Optional[float] = Field(None, ge=0, le=2000)
    gender: str = Field(..., pattern="^(female|male)$")
    pregnancy_status: str = Field("not_applicable", pattern="^(not_applicable|pregnant|not_pregnant|unknown)$")
    milk_yield_liters: Optional[float] = Field(None, ge=0, le=200)
    village: str = Field("", max_length=120)
    notes: str = Field("", max_length=2000)


class CaseSheetCreate(BaseModel):
    cattle_id: int = Field(..., ge=1)
    farmer_id: str = Field(..., min_length=2, max_length=64)
    doctor_id: str = Field(..., min_length=2, max_length=64)
    symptoms: str = Field(..., min_length=2, max_length=2000)
    diagnosis: str = Field(..., min_length=2, max_length=120)
    confirmed_disease: Optional[str] = Field(None, max_length=120)
    treatment: str = Field(..., min_length=2, max_length=3000)
    dosage_notes: str = Field("", max_length=2000)
    follow_up_date: Optional[datetime] = None
    notes: str = Field("", max_length=3000)
    recovery_progress: str = Field("under_treatment", pattern="^(under_treatment|stable|improving|critical|recovered)$")
    emergency_flag: bool = False
    case_status: str = Field("open", pattern="^(open|under_review|closed)$")


class QueryTriageUpdate(BaseModel):
    doctor_id: str = Field(..., min_length=2, max_length=64)
    priority: str = Field("normal", pattern="^(normal|urgent|critical)$")
    status: str = Field("pending", pattern="^(pending|answered|follow_up_needed|closed)$")
    follow_up_needed: bool = False
    notes: str = Field("", max_length=2000)


class CaseOutcomeUpdate(BaseModel):
    outcome_status: str = Field(..., pattern="^(pending|improving|resolved|failed)$")
    outcome_notes: str = Field("", max_length=2000)
    resolved_at: Optional[datetime] = None


class PreventiveCareCreate(BaseModel):
    cattle_id: int = Field(..., ge=1)
    farmer_id: str = Field(..., min_length=2, max_length=64)
    care_type: str = Field(..., pattern="^(vaccination|deworming|other)$")
    item_name: str = Field(..., min_length=2, max_length=120)
    due_date: datetime
    completed_date: Optional[datetime] = None
    status: str = Field("scheduled", pattern="^(scheduled|completed|missed)$")
    notes: str = Field("", max_length=2000)


class DemoSeedResponse(BaseModel):
    message: str
    created: dict[str, int]
    existing: dict[str, int]


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
        "normalized_symptoms": case.normalized_symptoms,
        "diagnosis": case.diagnosis,
        "predicted_disease": case.predicted_disease,
        "confirmed_disease": case.confirmed_disease,
        "treatment": case.treatment,
        "dosage_notes": case.dosage_notes,
        "follow_up_date": case.follow_up_date,
        "notes": case.notes,
        "recovery_progress": case.recovery_progress,
        "outcome_status": case.outcome_status,
        "outcome_notes": case.outcome_notes,
        "resolved_at": case.resolved_at,
        "severity_score": case.severity_score,
        "escalation_level": case.escalation_level,
        "data_quality_flags": case.data_quality_flags,
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

@app.get("/symptoms", response_model=dict[str, list[str]])
def get_symptoms(current_user: dict = Depends(require_roles("farmer", "doctor", "admin"))):
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

@app.get("/history/{farmer_id}", response_model=list[dict[str, Any]])
def get_history(farmer_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user), limit: int = FastAPIQuery(50, ge=1, le=200), offset: int = FastAPIQuery(0, ge=0)):
    _ensure_owner_or_role(farmer_id, current_user, {"doctor", "admin"})
    records = db.query(models.History).filter(models.History.farmer_id == farmer_id).order_by(models.History.date.desc()).offset(offset).limit(limit).all()
    return [{"id": item.id, "farmer_id": item.farmer_id, "description": item.description, "symptoms": item.symptoms, "disease": item.disease, "treatments": item.treatments, "date": item.date} for item in records]

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

@app.get("/queries", response_model=list[dict[str, Any]])
def get_all_queries(farmer_id: Optional[str] = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user), limit: int = FastAPIQuery(50, ge=1, le=200), offset: int = FastAPIQuery(0, ge=0)):
    if current_user["role"] == "farmer":
        farmer_id = current_user["user_id"]
    query = db.query(models.Query)
    if farmer_id:
        query = query.filter(models.Query.farmer_id == farmer_id)
    records = query.order_by(models.Query.query_date.desc()).offset(offset).limit(limit).all()
    return [{"id": item.id, "farmer_id": item.farmer_id, "query_text": item.query_text, "query_date": item.query_date, "reply_text": item.reply_text, "reply_date": item.reply_date} for item in records]

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

@app.post("/register/farmer", response_model=GenericMessageResponse)
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

@app.post("/register/vdoctor", response_model=GenericMessageResponse)
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

@app.post("/login", response_model=LoginResponse)
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
        if password_ok and stored_password.startswith("$pbkdf2-sha256$"):
            user.password = hash_password(creds.password)
            db.commit()
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

@app.get("/users", response_model=dict[str, list[dict[str, str]]])
def get_users(db: Session = Depends(get_db), current_user: dict = Depends(require_roles("admin", "doctor"))):
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


@app.get("/cattle", response_model=list[dict[str, Any]])
def get_cattle_profiles(farmer_id: Optional[str] = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user), limit: int = FastAPIQuery(100, ge=1, le=500), offset: int = FastAPIQuery(0, ge=0)):
    if current_user["role"] == "farmer":
        farmer_id = current_user["user_id"]
    query = db.query(models.CattleProfile)
    if farmer_id:
        query = query.filter(models.CattleProfile.farmer_id == farmer_id)
    cattle = query.order_by(models.CattleProfile.created_at.desc()).offset(offset).limit(limit).all()
    return [serialize_cattle(item) for item in cattle]


@app.post("/case-sheets")
def create_case_sheet(payload: CaseSheetCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin"))):
    cattle = db.query(models.CattleProfile).filter(models.CattleProfile.id == payload.cattle_id).first()
    if not cattle:
        raise HTTPException(status_code=404, detail="Cattle profile not found")

    normalized_symptoms, unknown_symptoms = normalize_symptoms(payload.symptoms, PredictionService.SYMPTOMS)
    predicted_disease = prediction_service.predict_disease(normalized_symptoms or payload.symptoms)
    severity_score, escalation_level = severity_from_symptoms(normalized_symptoms or payload.symptoms)

    case_data = payload.model_dump()
    case_data["normalized_symptoms"] = normalized_symptoms
    case_data["predicted_disease"] = predicted_disease
    case_data["severity_score"] = severity_score
    case_data["escalation_level"] = escalation_level
    case_data["emergency_flag"] = payload.emergency_flag or escalation_level in {"high", "critical"}
    case_data["data_quality_flags"] = ",".join(unknown_symptoms) if unknown_symptoms else ""

    case = models.CaseSheet(**case_data)
    db.add(case)
    db.commit()
    db.refresh(case)

    prescription_meta = build_prescription_guidance(
        diagnosis=case.confirmed_disease or case.diagnosis,
        treatment=case.treatment,
        weight_kg=cattle.weight_kg,
        pregnancy_status=cattle.pregnancy_status,
    )

    return {
        "case_sheet": serialize_case_sheet(case, cattle),
        "prescription": {
            "animal": cattle.animal_name if cattle else "",
            "animal_tag": cattle.animal_tag if cattle else "",
            "predicted_disease": predicted_disease,
            "doctor_confirmed_disease": case.confirmed_disease,
            "diagnosis": case.confirmed_disease or case.diagnosis,
            "treatment": case.treatment,
            "dosage_notes": case.dosage_notes,
            "follow_up_date": case.follow_up_date,
            **prescription_meta,
        },
    }


@app.get("/case-sheets", response_model=list[dict[str, Any]])
def get_case_sheets(
    cattle_id: Optional[int] = None,
    farmer_id: Optional[str] = None,
    symptoms: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    limit: int = FastAPIQuery(100, ge=1, le=500),
    offset: int = FastAPIQuery(0, ge=0),
):
    if current_user["role"] == "farmer":
        farmer_id = current_user["user_id"]
    cases = db.query(models.CaseSheet).order_by(models.CaseSheet.visit_date.desc()).offset(offset).limit(limit).all()
    cattle_lookup = {item.id: item for item in db.query(models.CattleProfile).all()}
    symptom_tokens = {token.strip().lower() for token in symptoms.split(",")} if symptoms else set()

    results = []
    for case in cases:
        if cattle_id and case.cattle_id != cattle_id:
            continue
        if farmer_id and case.farmer_id != farmer_id:
            continue
        if symptom_tokens:
            case_tokens = {token.strip().lower() for token in str(case.normalized_symptoms or case.symptoms).split(",") if token.strip()}
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


@app.get("/doctor/queries", response_model=list[dict[str, Any]])
def get_doctor_queries(db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin")), limit: int = FastAPIQuery(100, ge=1, le=500), offset: int = FastAPIQuery(0, ge=0)):
    queries = db.query(models.Query).order_by(models.Query.query_date.desc()).offset(offset).limit(limit).all()
    reviews = {item.query_id: item for item in db.query(models.QueryReview).all()}
    results = []
    for query in queries:
        review = reviews.get(query.id)
        auto_score, auto_escalation = severity_from_query_text(query.query_text)
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
            "severity_score": review.severity_score if review and review.severity_score is not None else auto_score,
            "escalation_level": review.escalation_level if review and review.escalation_level else auto_escalation,
        })
    return results


@app.post("/doctor/queries/{query_id}/triage")
def triage_query(query_id: int, payload: QueryTriageUpdate, db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin"))):
    query_item = db.query(models.Query).filter(models.Query.id == query_id).first()
    if not query_item:
        raise HTTPException(status_code=404, detail="Query not found")

    auto_score, auto_escalation = severity_from_query_text(query_item.query_text)

    review = db.query(models.QueryReview).filter(models.QueryReview.query_id == query_id).first()
    if not review:
        review = models.QueryReview(query_id=query_id, **payload.model_dump())
        db.add(review)
    else:
        for key, value in payload.model_dump().items():
            setattr(review, key, value)

    review.severity_score = auto_score
    review.escalation_level = auto_escalation
    if auto_escalation == "high":
        review.priority = "critical" if review.priority == "critical" else "urgent"
        review.follow_up_needed = True
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
        "severity_score": review.severity_score,
        "escalation_level": review.escalation_level,
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


@app.get("/lab-reports", response_model=list[dict[str, Any]])
def get_lab_reports(cattle_id: Optional[int] = None, db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin")), limit: int = FastAPIQuery(100, ge=1, le=500), offset: int = FastAPIQuery(0, ge=0)):
    query = db.query(models.LabReport).order_by(models.LabReport.uploaded_at.desc())
    if cattle_id:
        query = query.filter(models.LabReport.cattle_id == cattle_id)
    reports = query.offset(offset).limit(limit).all()
    cattle_lookup = {item.id: item for item in db.query(models.CattleProfile).all()}
    return [serialize_lab_report(item, cattle_lookup.get(item.cattle_id)) for item in reports]


@app.get("/doctor/trends", response_model=dict[str, dict[str, int]])
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


@app.get("/doctor/emergency-alerts", response_model=list[dict[str, Any]])
def get_emergency_alerts(db: Session = Depends(get_db), current_user: dict = Depends(require_roles("doctor", "admin"))):
    severe_keywords = {"breathing-difficulty", "high-fever", "bleeding", "asphyxia", "convulsions", "seizures"}
    cases = db.query(models.CaseSheet).order_by(models.CaseSheet.visit_date.desc()).all()
    cattle_lookup = {item.id: item for item in db.query(models.CattleProfile).all()}
    results = []
    for case in cases:
        case_tokens = {token.strip().lower() for token in str(case.normalized_symptoms or case.symptoms).split(",") if token.strip()}
        if case.emergency_flag or severe_keywords.intersection(case_tokens):
            results.append(serialize_case_sheet(case, cattle_lookup.get(case.cattle_id)))
    return results


@app.get("/doctor/similar-cases", response_model=list[dict[str, Any]])
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

@app.patch("/case-sheets/{case_id}/outcome")
def update_case_outcome(
    case_id: int,
    payload: CaseOutcomeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("doctor", "admin")),
):
    case = db.query(models.CaseSheet).filter(models.CaseSheet.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case sheet not found")

    case.outcome_status = payload.outcome_status
    case.outcome_notes = payload.outcome_notes
    case.resolved_at = payload.resolved_at or (datetime.now(UTC) if payload.outcome_status in {"resolved", "failed"} else None)

    if payload.outcome_status == "resolved":
        case.recovery_progress = "recovered"
        case.case_status = "closed"

    db.commit()
    db.refresh(case)
    cattle = db.query(models.CattleProfile).filter(models.CattleProfile.id == case.cattle_id).first()
    return serialize_case_sheet(case, cattle)


@app.get("/cattle/{cattle_id}/timeline")
def get_cattle_timeline(
    cattle_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("doctor", "admin")),
):
    cattle = db.query(models.CattleProfile).filter(models.CattleProfile.id == cattle_id).first()
    if not cattle:
        raise HTTPException(status_code=404, detail="Cattle profile not found")

    visits = db.query(models.CaseSheet).filter(models.CaseSheet.cattle_id == cattle_id).order_by(models.CaseSheet.visit_date.desc()).all()
    labs = db.query(models.LabReport).filter(models.LabReport.cattle_id == cattle_id).order_by(models.LabReport.uploaded_at.desc()).all()

    return {
        "cattle": serialize_cattle(cattle),
        "timeline": [serialize_case_sheet(item, cattle) for item in visits],
        "lab_reports": [serialize_lab_report(item, cattle) for item in labs],
        "summary": {
            "visit_count": len(visits),
            "lab_report_count": len(labs),
            "open_cases": len([item for item in visits if item.case_status != "closed"]),
            "resolved_cases": len([item for item in visits if item.outcome_status == "resolved"]),
        },
    }


@app.get("/doctor/outcomes", response_model=dict[str, Any])
def get_doctor_outcomes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("doctor", "admin")),
):
    cases = db.query(models.CaseSheet).all()
    cattle_lookup = {item.id: item for item in db.query(models.CattleProfile).all()}

    by_disease = {}
    by_farm = {}
    by_season = {}
    by_doctor = {}

    for case in cases:
        disease = (case.confirmed_disease or case.predicted_disease or case.diagnosis or "unknown").lower()
        farm = case.farmer_id or "unknown"
        season = season_from_date(case.visit_date)
        doctor = case.doctor_id or "unknown"

        is_success = 1 if case.outcome_status == "resolved" or case.recovery_progress == "recovered" else 0

        for bucket, key in ((by_disease, disease), (by_farm, farm), (by_season, season), (by_doctor, doctor)):
            if key not in bucket:
                bucket[key] = {"total": 0, "success": 0}
            bucket[key]["total"] += 1
            bucket[key]["success"] += is_success

    def _rate_map(bucket: dict) -> dict:
        result = {}
        for key, value in bucket.items():
            total = value["total"]
            success = value["success"]
            result[key] = {
                "total_cases": total,
                "successful_cases": success,
                "success_rate": round((success / total) * 100, 2) if total else 0.0,
            }
        return result

    return {
        "by_disease": _rate_map(by_disease),
        "by_farm": _rate_map(by_farm),
        "by_season": _rate_map(by_season),
        "by_doctor": _rate_map(by_doctor),
        "overall": {
            "total_cases": len(cases),
            "resolved_cases": len([c for c in cases if c.outcome_status == "resolved"]),
        },
    }


@app.get("/doctor/data-quality", response_model=dict[str, Any])
def get_data_quality(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("doctor", "admin")),
):
    known = {item.lower() for item in PredictionService.SYMPTOMS}
    cases = db.query(models.CaseSheet).order_by(models.CaseSheet.visit_date.desc()).all()

    missing_fields = []
    duplicate_candidates = []
    invalid_symptoms = []

    seen = {}
    for case in cases:
        key = (
            case.cattle_id,
            (case.normalized_symptoms or case.symptoms or "").strip().lower(),
            case.visit_date.strftime("%Y-%m-%d"),
        )
        if key in seen:
            duplicate_candidates.append({"current_case_id": case.id, "possible_duplicate_of": seen[key]})
        else:
            seen[key] = case.id

        missing = []
        if not case.diagnosis:
            missing.append("diagnosis")
        if not case.treatment:
            missing.append("treatment")
        if not case.confirmed_disease:
            missing.append("confirmed_disease")
        if missing:
            missing_fields.append({"case_id": case.id, "missing": missing})

        raw_tokens = {token.strip().lower() for token in str(case.symptoms or "").split(",") if token.strip()}
        unknown = sorted([token for token in raw_tokens if token not in known])
        if unknown:
            invalid_symptoms.append({"case_id": case.id, "invalid_tokens": unknown})

    return {
        "summary": {
            "case_count": len(cases),
            "missing_field_cases": len(missing_fields),
            "duplicate_candidates": len(duplicate_candidates),
            "invalid_symptom_cases": len(invalid_symptoms),
        },
        "missing_fields": missing_fields,
        "duplicate_candidates": duplicate_candidates,
        "invalid_symptoms": invalid_symptoms,
    }


@app.get("/analytics", response_model=dict[str, Any])
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


@app.post("/admin/demo-seed", response_model=DemoSeedResponse)
def seed_demo_data(db: Session = Depends(get_db), current_user: dict = Depends(require_roles("admin"))):
    created = {
        "farmers": 0,
        "doctors": 0,
        "cattle_profiles": 0,
        "case_sheets": 0,
        "history_records": 0,
        "queries": 0,
    }
    existing = {key: 0 for key in created}

    farmer_id = "FMR1001"
    doctor_id = "DOC2001"

    city = db.query(models.City).filter(models.City.city_name == "Bangalore").first()
    if not city:
        city = models.City(city_name="Bangalore")
        db.add(city)
        db.commit()
        db.refresh(city)

    farmer = db.query(models.Farmer).filter(models.Farmer.farmer_id == farmer_id).first()
    if not farmer:
        farmer = models.Farmer(
            farmer_id=farmer_id,
            password=hash_password("farmer123"),
            name="Demo Farmer",
            contact_no="9000000001",
            address="Village Demo, Karnataka",
        )
        db.add(farmer)
        db.commit()
        created["farmers"] += 1
    else:
        existing["farmers"] += 1

    doctor = db.query(models.VDoctor).filter(models.VDoctor.ic_id == doctor_id).first()
    if not doctor:
        doctor = models.VDoctor(
            ic_id=doctor_id,
            password=hash_password("doctor123"),
            name="Demo Veterinary Doctor",
            address="Demo Clinic, Bangalore",
            contact_no="9000000002",
            email_id="doctor.demo@example.com",
            city_id=city.city_id,
        )
        db.add(doctor)
        db.commit()
        created["doctors"] += 1
    else:
        existing["doctors"] += 1

    cattle = db.query(models.CattleProfile).filter(
        models.CattleProfile.farmer_id == farmer_id,
        models.CattleProfile.animal_tag == "TAG-001",
    ).first()
    if not cattle:
        cattle = models.CattleProfile(
            farmer_id=farmer_id,
            animal_tag="TAG-001",
            animal_name="Lakshmi",
            breed="Jersey",
            age_years=4.0,
            weight_kg=350.0,
            gender="female",
            pregnancy_status="not_pregnant",
            milk_yield_liters=9.5,
            village="Mandya",
            notes="Seeded demo cattle profile.",
        )
        db.add(cattle)
        db.commit()
        db.refresh(cattle)
        created["cattle_profiles"] += 1
    else:
        existing["cattle_profiles"] += 1

    case = db.query(models.CaseSheet).filter(
        models.CaseSheet.cattle_id == cattle.id,
        models.CaseSheet.doctor_id == doctor_id,
        models.CaseSheet.diagnosis == "Mastitis",
    ).first()
    if not case:
        normalized_symptoms, unknown_symptoms = normalize_symptoms("udder-swelling,fever,milk-reduction", PredictionService.SYMPTOMS)
        severity_score, escalation_level = severity_from_symptoms(normalized_symptoms)
        case = models.CaseSheet(
            cattle_id=cattle.id,
            farmer_id=farmer_id,
            doctor_id=doctor_id,
            symptoms="udder-swelling,fever,milk-reduction",
            normalized_symptoms=normalized_symptoms,
            diagnosis="Mastitis",
            predicted_disease="Mastitis",
            confirmed_disease="Mastitis",
            treatment="Antibiotic therapy, anti-inflammatory, and udder hygiene protocol",
            dosage_notes="Adjust dose by weight and milk withdrawal advice",
            follow_up_date=datetime.now(UTC),
            notes="Seeded demo case sheet.",
            recovery_progress="improving",
            outcome_status="improving",
            severity_score=severity_score,
            escalation_level=escalation_level,
            data_quality_flags=",".join(unknown_symptoms) if unknown_symptoms else "",
            emergency_flag=escalation_level in {"high", "critical"},
            case_status="under_review",
        )
        db.add(case)
        db.commit()
        created["case_sheets"] += 1
    else:
        existing["case_sheets"] += 1

    history = db.query(models.History).filter(
        models.History.farmer_id == farmer_id,
        models.History.description == "Seeded Demo Prediction",
    ).first()
    if not history:
        db.add(
            models.History(
                farmer_id=farmer_id,
                description="Seeded Demo Prediction",
                symptoms="udder-swelling,fever,milk-reduction",
                disease="Mastitis",
                treatments="Antibiotic + udder care",
            )
        )
        db.commit()
        created["history_records"] += 1
    else:
        existing["history_records"] += 1

    query = db.query(models.Query).filter(
        models.Query.farmer_id == farmer_id,
        models.Query.query_text == "Milk output reduced after fever. What should I monitor next?",
    ).first()
    if not query:
        db.add(
            models.Query(
                farmer_id=farmer_id,
                query_text="Milk output reduced after fever. What should I monitor next?",
                reply_text="Track appetite, udder heat, and milk texture. Recheck in 24 hours.",
                reply_date=datetime.now(UTC),
            )
        )
        db.commit()
        created["queries"] += 1
    else:
        existing["queries"] += 1

    return {
        "message": "Demo data is ready. Use FMR1001/farmer123 and DOC2001/doctor123 for walkthrough.",
        "created": created,
        "existing": existing,
    }
