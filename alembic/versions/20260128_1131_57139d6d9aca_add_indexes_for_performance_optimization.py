"""Add indexes for performance optimization

Revision ID: 57139d6d9aca
Revises: 
Create Date: 2026-01-28 11:31:44.223048

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57139d6d9aca'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes for frequently queried columns to improve query performance."""
    
    # CloudInstance indexes - using IF NOT EXISTS to make migration idempotent
    op.execute('CREATE INDEX IF NOT EXISTS ix_cloud_instances_provider ON cloud_instances (provider)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_cloud_instances_vcpus ON cloud_instances (vcpus)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_cloud_instances_memory_gb ON cloud_instances (memory_gb)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_cloud_instances_category ON cloud_instances (category)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_cloud_instances_provider_vcpus ON cloud_instances (provider, vcpus)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_cloud_instances_provider_category ON cloud_instances (provider, category)')
    
    # CloudPricing indexes - using IF NOT EXISTS to make migration idempotent
    op.execute('CREATE INDEX IF NOT EXISTS ix_cloud_pricing_provider ON cloud_pricing (provider)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_cloud_pricing_instance_type ON cloud_pricing (instance_type)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_cloud_pricing_region ON cloud_pricing (region)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_cloud_pricing_pricing_type ON cloud_pricing (pricing_type)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_cloud_pricing_provider_instance ON cloud_pricing (provider, instance_type)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_cloud_pricing_provider_region ON cloud_pricing (provider, region)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_cloud_pricing_instance_region ON cloud_pricing (instance_type, region)')


def downgrade() -> None:
    """Remove the performance indexes."""
    
    # CloudPricing indexes - using IF EXISTS to make migration idempotent
    op.execute('DROP INDEX IF EXISTS ix_cloud_pricing_instance_region')
    op.execute('DROP INDEX IF EXISTS ix_cloud_pricing_provider_region')
    op.execute('DROP INDEX IF EXISTS ix_cloud_pricing_provider_instance')
    op.execute('DROP INDEX IF EXISTS ix_cloud_pricing_pricing_type')
    op.execute('DROP INDEX IF EXISTS ix_cloud_pricing_region')
    op.execute('DROP INDEX IF EXISTS ix_cloud_pricing_instance_type')
    op.execute('DROP INDEX IF EXISTS ix_cloud_pricing_provider')
    
    # CloudInstance indexes - using IF EXISTS to make migration idempotent
    op.execute('DROP INDEX IF EXISTS ix_cloud_instances_provider_category')
    op.execute('DROP INDEX IF EXISTS ix_cloud_instances_provider_vcpus')
    op.execute('DROP INDEX IF EXISTS ix_cloud_instances_category')
    op.execute('DROP INDEX IF EXISTS ix_cloud_instances_memory_gb')
    op.execute('DROP INDEX IF EXISTS ix_cloud_instances_vcpus')
    op.execute('DROP INDEX IF EXISTS ix_cloud_instances_provider')

