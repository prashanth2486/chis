"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.String(), nullable=True),
        sa.Column("password", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admins_admin_id"), "admins", ["admin_id"], unique=True)
    op.create_index(op.f("ix_admins_id"), "admins", ["id"], unique=False)

    op.create_table(
        "cities",
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("city_name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("city_id"),
    )
    op.create_index(op.f("ix_cities_city_id"), "cities", ["city_id"], unique=False)
    op.create_index(op.f("ix_cities_city_name"), "cities", ["city_name"], unique=True)

    op.create_table(
        "farmers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("farmer_id", sa.String(), nullable=True),
        sa.Column("password", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("contact_no", sa.String(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_farmers_farmer_id"), "farmers", ["farmer_id"], unique=True)
    op.create_index(op.f("ix_farmers_id"), "farmers", ["id"], unique=False)

    op.create_table(
        "vdoctors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ic_id", sa.String(), nullable=True),
        sa.Column("password", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("contact_no", sa.String(), nullable=True),
        sa.Column("email_id", sa.String(), nullable=True),
        sa.Column("city_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["city_id"], ["cities.city_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vdoctors_email_id"), "vdoctors", ["email_id"], unique=False)
    op.create_index(op.f("ix_vdoctors_ic_id"), "vdoctors", ["ic_id"], unique=True)
    op.create_index(op.f("ix_vdoctors_id"), "vdoctors", ["id"], unique=False)

    op.create_table(
        "history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("farmer_id", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("symptoms", sa.String(), nullable=True),
        sa.Column("disease", sa.String(), nullable=True),
        sa.Column("treatments", sa.String(), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.farmer_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_history_id"), "history", ["id"], unique=False)

    op.create_table(
        "queries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("farmer_id", sa.String(), nullable=True),
        sa.Column("query_text", sa.String(), nullable=True),
        sa.Column("query_date", sa.DateTime(), nullable=True),
        sa.Column("reply_text", sa.String(), nullable=True),
        sa.Column("reply_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.farmer_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_queries_id"), "queries", ["id"], unique=False)

    op.create_table(
        "cattle_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("farmer_id", sa.String(), nullable=True),
        sa.Column("animal_tag", sa.String(), nullable=True),
        sa.Column("animal_name", sa.String(), nullable=True),
        sa.Column("breed", sa.String(), nullable=True),
        sa.Column("age_years", sa.Float(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("gender", sa.String(), nullable=True),
        sa.Column("pregnancy_status", sa.String(), nullable=True),
        sa.Column("milk_yield_liters", sa.Float(), nullable=True),
        sa.Column("village", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.farmer_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cattle_profiles_animal_tag"), "cattle_profiles", ["animal_tag"], unique=False)
    op.create_index(op.f("ix_cattle_profiles_id"), "cattle_profiles", ["id"], unique=False)

    op.create_table(
        "case_sheets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cattle_id", sa.Integer(), nullable=True),
        sa.Column("farmer_id", sa.String(), nullable=True),
        sa.Column("doctor_id", sa.String(), nullable=True),
        sa.Column("visit_date", sa.DateTime(), nullable=True),
        sa.Column("symptoms", sa.Text(), nullable=True),
        sa.Column("diagnosis", sa.String(), nullable=True),
        sa.Column("confirmed_disease", sa.String(), nullable=True),
        sa.Column("treatment", sa.Text(), nullable=True),
        sa.Column("dosage_notes", sa.Text(), nullable=True),
        sa.Column("follow_up_date", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recovery_progress", sa.String(), nullable=True),
        sa.Column("emergency_flag", sa.Boolean(), nullable=True),
        sa.Column("case_status", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["cattle_id"], ["cattle_profiles.id"]),
        sa.ForeignKeyConstraint(["doctor_id"], ["vdoctors.ic_id"]),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.farmer_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_case_sheets_id"), "case_sheets", ["id"], unique=False)

    op.create_table(
        "query_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("query_id", sa.Integer(), nullable=True),
        sa.Column("doctor_id", sa.String(), nullable=True),
        sa.Column("priority", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("follow_up_needed", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["doctor_id"], ["vdoctors.ic_id"]),
        sa.ForeignKeyConstraint(["query_id"], ["queries.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("query_id"),
    )
    op.create_index(op.f("ix_query_reviews_id"), "query_reviews", ["id"], unique=False)

    op.create_table(
        "preventive_care_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cattle_id", sa.Integer(), nullable=True),
        sa.Column("farmer_id", sa.String(), nullable=True),
        sa.Column("care_type", sa.String(), nullable=True),
        sa.Column("item_name", sa.String(), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("completed_date", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["cattle_id"], ["cattle_profiles.id"]),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.farmer_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_preventive_care_records_id"), "preventive_care_records", ["id"], unique=False)

    op.create_table(
        "lab_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cattle_id", sa.Integer(), nullable=True),
        sa.Column("case_sheet_id", sa.Integer(), nullable=True),
        sa.Column("report_name", sa.String(), nullable=True),
        sa.Column("report_type", sa.String(), nullable=True),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["case_sheet_id"], ["case_sheets.id"]),
        sa.ForeignKeyConstraint(["cattle_id"], ["cattle_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lab_reports_id"), "lab_reports", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_lab_reports_id"), table_name="lab_reports")
    op.drop_table("lab_reports")
    op.drop_index(op.f("ix_preventive_care_records_id"), table_name="preventive_care_records")
    op.drop_table("preventive_care_records")
    op.drop_index(op.f("ix_query_reviews_id"), table_name="query_reviews")
    op.drop_table("query_reviews")
    op.drop_index(op.f("ix_case_sheets_id"), table_name="case_sheets")
    op.drop_table("case_sheets")
    op.drop_index(op.f("ix_cattle_profiles_id"), table_name="cattle_profiles")
    op.drop_index(op.f("ix_cattle_profiles_animal_tag"), table_name="cattle_profiles")
    op.drop_table("cattle_profiles")
    op.drop_index(op.f("ix_queries_id"), table_name="queries")
    op.drop_table("queries")
    op.drop_index(op.f("ix_history_id"), table_name="history")
    op.drop_table("history")
    op.drop_index(op.f("ix_vdoctors_id"), table_name="vdoctors")
    op.drop_index(op.f("ix_vdoctors_ic_id"), table_name="vdoctors")
    op.drop_index(op.f("ix_vdoctors_email_id"), table_name="vdoctors")
    op.drop_table("vdoctors")
    op.drop_index(op.f("ix_farmers_id"), table_name="farmers")
    op.drop_index(op.f("ix_farmers_farmer_id"), table_name="farmers")
    op.drop_table("farmers")
    op.drop_index(op.f("ix_cities_city_name"), table_name="cities")
    op.drop_index(op.f("ix_cities_city_id"), table_name="cities")
    op.drop_table("cities")
    op.drop_index(op.f("ix_admins_id"), table_name="admins")
    op.drop_index(op.f("ix_admins_admin_id"), table_name="admins")
    op.drop_table("admins")
