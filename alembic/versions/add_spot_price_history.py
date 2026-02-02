"""Add spot_price_history table for real-time price tracking

Revision ID: add_spot_price_history
Revises: 
Create Date: 2026-02-02 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_spot_price_history'
down_revision = None  # Update this with your latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Create spot_price_history table
    op.create_table(
        'spot_price_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=10), nullable=False),
        sa.Column('instance_type', sa.String(length=100), nullable=False),
        sa.Column('region', sa.String(length=50), nullable=False),
        sa.Column('zone', sa.String(length=60), nullable=True),
        sa.Column('spot_price', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('os_type', sa.String(length=20), nullable=False, server_default='linux'),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for fast queries
    op.create_index(
        'idx_spot_history_lookup',
        'spot_price_history',
        ['provider', 'instance_type', 'region', 'timestamp']
    )
    
    op.create_index(
        'idx_spot_history_timestamp',
        'spot_price_history',
        ['timestamp']
    )
    
    op.create_index(
        'idx_spot_history_instance',
        'spot_price_history',
        ['provider', 'instance_type']
    )


def downgrade():
    op.drop_index('idx_spot_history_instance', table_name='spot_price_history')
    op.drop_index('idx_spot_history_timestamp', table_name='spot_price_history')
    op.drop_index('idx_spot_history_lookup', table_name='spot_price_history')
    op.drop_table('spot_price_history')
