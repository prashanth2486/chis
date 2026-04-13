from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float, Text
from sqlalchemy.orm import relationship
import datetime

from database import Base

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(String, unique=True, index=True)
    password = Column(String)

class City(Base):
    __tablename__ = "cities"

    city_id = Column(Integer, primary_key=True, index=True)
    city_name = Column(String, unique=True, index=True)

class VDoctor(Base):
    __tablename__ = "vdoctors"

    id = Column(Integer, primary_key=True, index=True)
    ic_id = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)
    address = Column(String)
    contact_no = Column(String)
    email_id = Column(String, index=True)
    city_id = Column(Integer, ForeignKey("cities.city_id"))

    city = relationship("City")

class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)
    contact_no = Column(String)
    address = Column(String)

class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(String, ForeignKey("farmers.farmer_id"))
    description = Column(String)
    symptoms = Column(String)
    disease = Column(String)
    treatments = Column(String)
    date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(String, ForeignKey("farmers.farmer_id"))
    query_text = Column(String)
    query_date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    reply_text = Column(String, nullable=True)
    reply_date = Column(DateTime, nullable=True)


class CattleProfile(Base):
    __tablename__ = "cattle_profiles"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(String, ForeignKey("farmers.farmer_id"))
    animal_tag = Column(String, index=True)
    animal_name = Column(String)
    breed = Column(String)
    age_years = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    gender = Column(String)
    pregnancy_status = Column(String)
    milk_yield_liters = Column(Float, nullable=True)
    village = Column(String)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class CaseSheet(Base):
    __tablename__ = "case_sheets"

    id = Column(Integer, primary_key=True, index=True)
    cattle_id = Column(Integer, ForeignKey("cattle_profiles.id"))
    farmer_id = Column(String, ForeignKey("farmers.farmer_id"))
    doctor_id = Column(String, ForeignKey("vdoctors.ic_id"))
    visit_date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    symptoms = Column(Text)
    diagnosis = Column(String)
    confirmed_disease = Column(String, nullable=True)
    treatment = Column(Text)
    dosage_notes = Column(Text, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    recovery_progress = Column(String, default="under_treatment")
    emergency_flag = Column(Boolean, default=False)
    case_status = Column(String, default="open")


class QueryReview(Base):
    __tablename__ = "query_reviews"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("queries.id"), unique=True)
    doctor_id = Column(String, ForeignKey("vdoctors.ic_id"))
    priority = Column(String, default="normal")
    status = Column(String, default="pending")
    follow_up_needed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class PreventiveCareRecord(Base):
    __tablename__ = "preventive_care_records"

    id = Column(Integer, primary_key=True, index=True)
    cattle_id = Column(Integer, ForeignKey("cattle_profiles.id"))
    farmer_id = Column(String, ForeignKey("farmers.farmer_id"))
    care_type = Column(String)  # vaccination or deworming
    item_name = Column(String)
    due_date = Column(DateTime)
    completed_date = Column(DateTime, nullable=True)
    status = Column(String, default="scheduled")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))


class LabReport(Base):
    __tablename__ = "lab_reports"

    id = Column(Integer, primary_key=True, index=True)
    cattle_id = Column(Integer, ForeignKey("cattle_profiles.id"))
    case_sheet_id = Column(Integer, ForeignKey("case_sheets.id"), nullable=True)
    report_name = Column(String)
    report_type = Column(String)
    file_path = Column(String)
    notes = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
