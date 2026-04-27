"""Infrastructure Intelligence: orgs, connectors, scans, snapshots, findings, reports, alerts.

Revision ID: infra_intel_20260428
Revises: f1x_pr1c1ng_z0ne
Create Date: 2026-04-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "infra_intel_20260428"
down_revision: Union[str, None] = "f1x_pr1c1ng_z0ne"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=False)

    op.create_table(
        "cloud_connectors",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=16), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("credentials_ciphertext", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_scan_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cloud_connectors_org", "cloud_connectors", ["organization_id"], unique=False)
    op.create_index("ix_cloud_connectors_provider", "cloud_connectors", ["provider"], unique=False)

    op.create_table(
        "scan_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("cloud_connector_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("trigger", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cloud_connector_id"], ["cloud_connectors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scan_jobs_org_connector", "scan_jobs", ["organization_id", "cloud_connector_id"], unique=False)
    op.create_index("ix_scan_jobs_status", "scan_jobs", ["status"], unique=False)

    op.create_table(
        "asset_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scan_job_id", sa.String(length=36), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("graph_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_job_id"], ["scan_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_asset_snapshots_scan", "asset_snapshots", ["scan_job_id"], unique=False)

    op.create_table(
        "infra_findings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("cloud_connector_id", sa.String(length=36), nullable=False),
        sa.Column("scan_job_id", sa.String(length=36), nullable=False),
        sa.Column("rule_id", sa.String(length=120), nullable=False),
        sa.Column("rule_version", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=24), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.Column("remediation_json", sa.JSON(), nullable=True),
        sa.Column("estimated_monthly_savings", sa.Numeric(14, 2), nullable=True),
        sa.Column("resource_key", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cloud_connector_id"], ["cloud_connectors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scan_job_id"], ["scan_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_infra_findings_org_scan", "infra_findings", ["organization_id", "scan_job_id"], unique=False)
    op.create_index("ix_infra_findings_rule", "infra_findings", ["rule_id"], unique=False)
    op.create_index("ix_infra_findings_category", "infra_findings", ["category"], unique=False)
    op.create_index("ix_infra_findings_severity", "infra_findings", ["severity"], unique=False)
    op.create_index("ix_infra_findings_resource_key", "infra_findings", ["resource_key"], unique=False)

    op.create_table(
        "infra_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_infra_reports_org", "infra_reports", ["organization_id"], unique=False)

    op.create_table(
        "alert_rules",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("condition_json", sa.JSON(), nullable=False),
        sa.Column("channel_json", sa.JSON(), nullable=False),
        sa.Column("last_evaluated_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alert_rules_org", "alert_rules", ["organization_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_alert_rules_org", table_name="alert_rules")
    op.drop_table("alert_rules")
    op.drop_index("ix_infra_reports_org", table_name="infra_reports")
    op.drop_table("infra_reports")
    op.drop_index("ix_infra_findings_resource_key", table_name="infra_findings")
    op.drop_index("ix_infra_findings_severity", table_name="infra_findings")
    op.drop_index("ix_infra_findings_category", table_name="infra_findings")
    op.drop_index("ix_infra_findings_rule", table_name="infra_findings")
    op.drop_index("ix_infra_findings_org_scan", table_name="infra_findings")
    op.drop_table("infra_findings")
    op.drop_index("ix_asset_snapshots_scan", table_name="asset_snapshots")
    op.drop_table("asset_snapshots")
    op.drop_index("ix_scan_jobs_status", table_name="scan_jobs")
    op.drop_index("ix_scan_jobs_org_connector", table_name="scan_jobs")
    op.drop_table("scan_jobs")
    op.drop_index("ix_cloud_connectors_provider", table_name="cloud_connectors")
    op.drop_index("ix_cloud_connectors_org", table_name="cloud_connectors")
    op.drop_table("cloud_connectors")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
