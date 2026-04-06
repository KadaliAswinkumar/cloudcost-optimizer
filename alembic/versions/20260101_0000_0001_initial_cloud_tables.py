"""Create cloud_instances and cloud_pricing (base schema for multicloud).

Revision ID: 0001_initial_cloud_tables
Revises:
Create Date: 2026-01-01

Fresh databases must have these tables before index migrations run.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_cloud_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cloud_instances",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(length=10), nullable=False),
        sa.Column("instance_type", sa.String(length=100), nullable=False),
        sa.Column("instance_family", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=True),
        sa.Column("vcpus", sa.Integer(), nullable=False),
        sa.Column("memory_gb", sa.Float(), nullable=False),
        sa.Column("processor_architecture", sa.String(length=20), nullable=False),
        sa.Column("cpu_platform", sa.String(length=100), nullable=True),
        sa.Column("local_ssd_gb", sa.Float(), nullable=True),
        sa.Column("storage_type", sa.String(length=50), nullable=False),
        sa.Column("network_bandwidth_gbps", sa.Float(), nullable=True),
        sa.Column("network_tier", sa.String(length=50), nullable=True),
        sa.Column("gpu_count", sa.Integer(), nullable=True),
        sa.Column("gpu_type", sa.String(length=100), nullable=True),
        sa.Column("gpu_memory_gb", sa.Float(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("is_current_generation", sa.Boolean(), nullable=False),
        sa.Column("is_burstable", sa.Boolean(), nullable=False),
        sa.Column("supports_spot", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "instance_type", name="uq_cloud_instance"),
    )
    op.create_index(
        "idx_cloud_instance_specs",
        "cloud_instances",
        ["provider", "vcpus", "memory_gb"],
        unique=False,
    )

    op.create_table(
        "cloud_pricing",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(length=10), nullable=False),
        sa.Column("instance_type", sa.String(length=100), nullable=False),
        sa.Column("region", sa.String(length=50), nullable=False),
        sa.Column("zone", sa.String(length=60), nullable=True),
        sa.Column("pricing_type", sa.String(length=30), nullable=False),
        sa.Column("os_type", sa.String(length=20), nullable=False),
        sa.Column("hourly_price", sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column("monthly_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("commitment_term", sa.String(length=20), nullable=True),
        sa.Column("upfront_cost", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("effective_date", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "instance_type",
            "region",
            "zone",
            "pricing_type",
            "os_type",
            name="uq_cloud_pricing",
        ),
    )
    op.create_index(
        "idx_cloud_pricing_lookup",
        "cloud_pricing",
        ["provider", "instance_type", "region"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_cloud_pricing_lookup", table_name="cloud_pricing")
    op.drop_table("cloud_pricing")
    op.drop_index("idx_cloud_instance_specs", table_name="cloud_instances")
    op.drop_table("cloud_instances")
