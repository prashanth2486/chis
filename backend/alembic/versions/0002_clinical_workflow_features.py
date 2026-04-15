"""clinical workflow features

Revision ID: 0002_clinical_workflow_features
Revises: 0001_initial_schema
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_clinical_workflow_features"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("case_sheets", sa.Column("predicted_disease", sa.String(), nullable=True))
    op.add_column("case_sheets", sa.Column("normalized_symptoms", sa.Text(), nullable=True))
    op.add_column("case_sheets", sa.Column("severity_score", sa.Float(), nullable=True, server_default="0"))
    op.add_column("case_sheets", sa.Column("escalation_level", sa.String(), nullable=True, server_default="normal"))
    op.add_column("case_sheets", sa.Column("data_quality_flags", sa.Text(), nullable=True))
    op.add_column("case_sheets", sa.Column("outcome_status", sa.String(), nullable=True, server_default="pending"))
    op.add_column("case_sheets", sa.Column("outcome_notes", sa.Text(), nullable=True))
    op.add_column("case_sheets", sa.Column("resolved_at", sa.DateTime(), nullable=True))

    op.add_column("query_reviews", sa.Column("severity_score", sa.Float(), nullable=True, server_default="0"))
    op.add_column("query_reviews", sa.Column("escalation_level", sa.String(), nullable=True, server_default="normal"))


def downgrade() -> None:
    op.drop_column("query_reviews", "escalation_level")
    op.drop_column("query_reviews", "severity_score")

    op.drop_column("case_sheets", "resolved_at")
    op.drop_column("case_sheets", "outcome_notes")
    op.drop_column("case_sheets", "outcome_status")
    op.drop_column("case_sheets", "data_quality_flags")
    op.drop_column("case_sheets", "escalation_level")
    op.drop_column("case_sheets", "severity_score")
    op.drop_column("case_sheets", "normalized_symptoms")
    op.drop_column("case_sheets", "predicted_disease")
