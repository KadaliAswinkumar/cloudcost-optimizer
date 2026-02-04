"""Fix cloud_pricing unique constraint to include zone

Revision ID: fix_pricing_zone_constraint
Revises: add_spot_price_history
Create Date: 2026-02-04 17:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_pricing_zone_constraint'
down_revision = 'add_spot_price_history'
branch_labels = None
depends_on = None


def upgrade():
    """
    Drop old unique constraint and create new one with zone included
    This fixes the issue where spot prices for different zones were treated as duplicates
    """
    
    # Drop the old constraint
    op.drop_constraint('uq_cloud_pricing', 'cloud_pricing', type_='unique')
    
    # Create new constraint that includes zone
    op.create_unique_constraint(
        'uq_cloud_pricing',
        'cloud_pricing',
        ['provider', 'instance_type', 'region', 'zone', 'pricing_type', 'os_type']
    )


def downgrade():
    """
    Revert to old constraint (without zone)
    """
    
    # Drop the new constraint
    op.drop_constraint('uq_cloud_pricing', 'cloud_pricing', type_='unique')
    
    # Restore old constraint
    op.create_unique_constraint(
        'uq_cloud_pricing',
        'cloud_pricing',
        ['provider', 'instance_type', 'region', 'pricing_type', 'os_type']
    )
