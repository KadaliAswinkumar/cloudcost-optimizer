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
    
    # CloudInstance indexes
    op.create_index('ix_cloud_instances_provider', 'cloud_instances', ['provider'])
    op.create_index('ix_cloud_instances_vcpus', 'cloud_instances', ['vcpus'])
    op.create_index('ix_cloud_instances_memory_gb', 'cloud_instances', ['memory_gb'])
    op.create_index('ix_cloud_instances_category', 'cloud_instances', ['category'])
    op.create_index('ix_cloud_instances_provider_vcpus', 'cloud_instances', ['provider', 'vcpus'])
    op.create_index('ix_cloud_instances_provider_category', 'cloud_instances', ['provider', 'category'])
    
    # CloudPricing indexes
    op.create_index('ix_cloud_pricing_provider', 'cloud_pricing', ['provider'])
    op.create_index('ix_cloud_pricing_instance_type', 'cloud_pricing', ['instance_type'])
    op.create_index('ix_cloud_pricing_region', 'cloud_pricing', ['region'])
    op.create_index('ix_cloud_pricing_pricing_type', 'cloud_pricing', ['pricing_type'])
    op.create_index('ix_cloud_pricing_provider_instance', 'cloud_pricing', ['provider', 'instance_type'])
    op.create_index('ix_cloud_pricing_provider_region', 'cloud_pricing', ['provider', 'region'])
    op.create_index('ix_cloud_pricing_instance_region', 'cloud_pricing', ['instance_type', 'region'])


def downgrade() -> None:
    """Remove the performance indexes."""
    
    # CloudPricing indexes
    op.drop_index('ix_cloud_pricing_instance_region')
    op.drop_index('ix_cloud_pricing_provider_region')
    op.drop_index('ix_cloud_pricing_provider_instance')
    op.drop_index('ix_cloud_pricing_pricing_type')
    op.drop_index('ix_cloud_pricing_region')
    op.drop_index('ix_cloud_pricing_instance_type')
    op.drop_index('ix_cloud_pricing_provider')
    
    # CloudInstance indexes
    op.drop_index('ix_cloud_instances_provider_category')
    op.drop_index('ix_cloud_instances_provider_vcpus')
    op.drop_index('ix_cloud_instances_category')
    op.drop_index('ix_cloud_instances_memory_gb')
    op.drop_index('ix_cloud_instances_vcpus')
    op.drop_index('ix_cloud_instances_provider')

