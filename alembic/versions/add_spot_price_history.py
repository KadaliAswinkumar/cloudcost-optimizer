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
down_revision = '57139d6d9aca'  # Points to: add_indexes_for_performance_optimization
branch_labels = None
depends_on = None


def upgrade():
    # Create spot_price_history table (idempotent - uses IF NOT EXISTS)
    # Use raw SQL to support IF NOT EXISTS
    op.execute("""
        CREATE TABLE IF NOT EXISTS spot_price_history (
            id SERIAL NOT NULL PRIMARY KEY,
            provider VARCHAR(10) NOT NULL,
            instance_type VARCHAR(100) NOT NULL,
            region VARCHAR(50) NOT NULL,
            zone VARCHAR(60),
            spot_price NUMERIC(10, 6) NOT NULL,
            os_type VARCHAR(20) DEFAULT 'linux' NOT NULL,
            timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
        )
    """)
    
    # Create indexes for fast queries (idempotent - uses IF NOT EXISTS)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_spot_history_lookup 
        ON spot_price_history (provider, instance_type, region, timestamp)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_spot_history_timestamp 
        ON spot_price_history (timestamp)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_spot_history_instance 
        ON spot_price_history (provider, instance_type)
    """)
    
    print("✅ spot_price_history table and indexes created (or already exist)")


def downgrade():
    # Drop indexes and table (idempotent - uses IF EXISTS)
    op.execute("DROP INDEX IF EXISTS idx_spot_history_instance")
    op.execute("DROP INDEX IF EXISTS idx_spot_history_timestamp")
    op.execute("DROP INDEX IF EXISTS idx_spot_history_lookup")
    op.execute("DROP TABLE IF EXISTS spot_price_history")
    print("✅ spot_price_history table and indexes dropped (if they existed)")
