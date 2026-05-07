"""Add FinOps traction tables and verification lifecycle columns.

Revision ID: finops_20260506_1601
Revises: infra_intel_20260428
Create Date: 2026-05-06 16:01:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "finops_20260506_1601"
down_revision: Union[str, None] = "infra_intel_20260428"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "finops_recommendation_actions"):
        op.create_table(
            "finops_recommendation_actions",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("organization_slug", sa.String(length=80), nullable=False),
            sa.Column("recommendation_id", sa.String(length=80), nullable=False),
            sa.Column("title", sa.String(length=220), nullable=False),
            sa.Column("cloud_provider", sa.String(length=16), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False),
            sa.Column("confidence_score", sa.Numeric(5, 2), nullable=False),
            sa.Column("confidence_level", sa.String(length=16), nullable=False),
            sa.Column("confidence_reasons_json", sa.JSON(), nullable=False),
            sa.Column("effort_level", sa.String(length=16), nullable=False),
            sa.Column("risk_score", sa.Numeric(5, 2), nullable=False),
            sa.Column("blast_radius", sa.String(length=16), nullable=False),
            sa.Column("decision_bucket", sa.String(length=24), nullable=False),
            sa.Column("estimated_monthly_savings_usd", sa.Numeric(14, 2), nullable=False),
            sa.Column("realized_monthly_savings_usd", sa.Numeric(14, 2), nullable=True),
            sa.Column("context_json", sa.JSON(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("actioned_by", sa.String(length=120), nullable=True),
            sa.Column("accepted_at", sa.DateTime(), nullable=True),
            sa.Column("in_progress_at", sa.DateTime(), nullable=True),
            sa.Column("implemented_at", sa.DateTime(), nullable=True),
            sa.Column("verified_at", sa.DateTime(), nullable=True),
            sa.Column("dismissed_at", sa.DateTime(), nullable=True),
            sa.Column("rolled_back_at", sa.DateTime(), nullable=True),
            sa.Column("rollback_reason", sa.Text(), nullable=True),
            sa.Column("verification_notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_finops_recommendation_actions_organization_slug",
            "finops_recommendation_actions",
            ["organization_slug"],
            unique=False,
        )
        op.create_index(
            "ix_finops_recommendation_actions_recommendation_id",
            "finops_recommendation_actions",
            ["recommendation_id"],
            unique=False,
        )
        op.create_index(
            "ix_finops_action_org_status",
            "finops_recommendation_actions",
            ["organization_slug", "status"],
            unique=False,
        )
        op.create_index(
            "ix_finops_action_rec_org",
            "finops_recommendation_actions",
            ["recommendation_id", "organization_slug"],
            unique=False,
        )
    else:
        cols = _column_names(inspector, "finops_recommendation_actions")
        if "in_progress_at" not in cols:
            op.add_column(
                "finops_recommendation_actions",
                sa.Column("in_progress_at", sa.DateTime(), nullable=True),
            )
        if "verified_at" not in cols:
            op.add_column(
                "finops_recommendation_actions",
                sa.Column("verified_at", sa.DateTime(), nullable=True),
            )
        if "rolled_back_at" not in cols:
            op.add_column(
                "finops_recommendation_actions",
                sa.Column("rolled_back_at", sa.DateTime(), nullable=True),
            )
        if "rollback_reason" not in cols:
            op.add_column(
                "finops_recommendation_actions",
                sa.Column("rollback_reason", sa.Text(), nullable=True),
            )
        if "verification_notes" not in cols:
            op.add_column(
                "finops_recommendation_actions",
                sa.Column("verification_notes", sa.Text(), nullable=True),
            )

    inspector = sa.inspect(bind)
    if not _has_table(inspector, "finops_ingestion_sources"):
        op.create_table(
            "finops_ingestion_sources",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("organization_slug", sa.String(length=80), nullable=False),
            sa.Column("source_type", sa.String(length=32), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False),
            sa.Column("freshness_status", sa.String(length=24), nullable=False),
            sa.Column("records_ingested", sa.Integer(), nullable=False),
            sa.Column("confidence_score", sa.Numeric(5, 2), nullable=False),
            sa.Column("details_json", sa.JSON(), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("last_synced_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_finops_ingestion_sources_organization_slug",
            "finops_ingestion_sources",
            ["organization_slug"],
            unique=False,
        )
        op.create_index(
            "ix_finops_source_org_type",
            "finops_ingestion_sources",
            ["organization_slug", "source_type"],
            unique=False,
        )

    inspector = sa.inspect(bind)
    if not _has_table(inspector, "finops_action_events"):
        op.create_table(
            "finops_action_events",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("organization_slug", sa.String(length=80), nullable=False),
            sa.Column("recommendation_id", sa.String(length=80), nullable=False),
            sa.Column("event_type", sa.String(length=24), nullable=False),
            sa.Column("actor", sa.String(length=120), nullable=True),
            sa.Column("payload_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_finops_action_events_organization_slug",
            "finops_action_events",
            ["organization_slug"],
            unique=False,
        )
        op.create_index(
            "ix_finops_action_events_recommendation_id",
            "finops_action_events",
            ["recommendation_id"],
            unique=False,
        )
        op.create_index(
            "ix_finops_event_org_time",
            "finops_action_events",
            ["organization_slug", "created_at"],
            unique=False,
        )
        op.create_index(
            "ix_finops_event_rec",
            "finops_action_events",
            ["recommendation_id"],
            unique=False,
        )

    inspector = sa.inspect(bind)
    if not _has_table(inspector, "finops_anomaly_events"):
        op.create_table(
            "finops_anomaly_events",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("organization_slug", sa.String(length=80), nullable=False),
            sa.Column("anomaly_type", sa.String(length=40), nullable=False),
            sa.Column("severity", sa.String(length=16), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False),
            sa.Column("metric_name", sa.String(length=80), nullable=False),
            sa.Column("baseline_value", sa.Numeric(14, 2), nullable=False),
            sa.Column("observed_value", sa.Numeric(14, 2), nullable=False),
            sa.Column("deviation_pct", sa.Numeric(8, 2), nullable=False),
            sa.Column("details_json", sa.JSON(), nullable=False),
            sa.Column("detected_at", sa.DateTime(), nullable=False),
            sa.Column("resolved_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_finops_anomaly_events_organization_slug",
            "finops_anomaly_events",
            ["organization_slug"],
            unique=False,
        )
        op.create_index(
            "ix_finops_anomaly_org_status",
            "finops_anomaly_events",
            ["organization_slug", "status"],
            unique=False,
        )
        op.create_index(
            "ix_finops_anomaly_time",
            "finops_anomaly_events",
            ["detected_at"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "finops_anomaly_events"):
        for idx in ("ix_finops_anomaly_time", "ix_finops_anomaly_org_status", "ix_finops_anomaly_events_organization_slug"):
            try:
                op.drop_index(idx, table_name="finops_anomaly_events")
            except Exception:
                pass
        op.drop_table("finops_anomaly_events")

    inspector = sa.inspect(bind)
    if _has_table(inspector, "finops_action_events"):
        for idx in ("ix_finops_event_rec", "ix_finops_event_org_time", "ix_finops_action_events_recommendation_id", "ix_finops_action_events_organization_slug"):
            try:
                op.drop_index(idx, table_name="finops_action_events")
            except Exception:
                pass
        op.drop_table("finops_action_events")

    inspector = sa.inspect(bind)
    if _has_table(inspector, "finops_ingestion_sources"):
        for idx in ("ix_finops_source_org_type", "ix_finops_ingestion_sources_organization_slug"):
            try:
                op.drop_index(idx, table_name="finops_ingestion_sources")
            except Exception:
                pass
        op.drop_table("finops_ingestion_sources")

    inspector = sa.inspect(bind)
    if _has_table(inspector, "finops_recommendation_actions"):
        for idx in (
            "ix_finops_action_rec_org",
            "ix_finops_action_org_status",
            "ix_finops_recommendation_actions_recommendation_id",
            "ix_finops_recommendation_actions_organization_slug",
        ):
            try:
                op.drop_index(idx, table_name="finops_recommendation_actions")
            except Exception:
                pass
        op.drop_table("finops_recommendation_actions")

