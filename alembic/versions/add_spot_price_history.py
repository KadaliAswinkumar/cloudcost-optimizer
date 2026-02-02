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
    # Check if table exists and drop it if it's incomplete/corrupted
    # This handles the case where a previous migration partially created the table
    conn = op.get_bind()
    
    # Check if table exists
    table_exists = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'spot_price_history'
        )
    """)).scalar()
    
    if table_exists:
        # Check if table has all required columns (validate schema)
        columns_exist = conn.execute(sa.text("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'spot_price_history' 
            AND column_name IN ('id', 'provider', 'instance_type', 'region', 'zone', 
                              'spot_price', 'os_type', 'timestamp', 'created_at')
        """)).scalar()
        
        if columns_exist < 9:  # Should have all 9 columns
            print(f"⚠️  Table exists but is incomplete ({columns_exist}/9 columns). Dropping and recreating...")
            op.execute("DROP TABLE IF EXISTS spot_price_history CASCADE")
            table_exists = False
        else:
            print("✅ spot_price_history table already exists with correct schema")
    
    if not table_exists:
        # Create fresh table
        print("🔨 Creating spot_price_history table...")
        op.execute("""
            CREATE TABLE spot_price_history (
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
        print("✅ Table created successfully")
    
    # Create indexes (idempotent - uses IF NOT EXISTS)
    print("🔨 Creating indexes...")
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
    
    print("✅ Migration complete: spot_price_history ready!")


def downgrade():
    # Drop indexes and table (idempotent - uses IF EXISTS)
    op.execute("DROP INDEX IF EXISTS idx_spot_history_instance")
    op.execute("DROP INDEX IF EXISTS idx_spot_history_timestamp")
    op.execute("DROP INDEX IF EXISTS idx_spot_history_lookup")
    op.execute("DROP TABLE IF EXISTS spot_price_history")
    print("✅ spot_price_history table and indexes dropped (if they existed)")
