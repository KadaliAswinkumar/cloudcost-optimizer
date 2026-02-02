#!/usr/bin/env python3
"""
Quick test to verify the migration file is syntactically correct.
Run this before deploying to Render.
"""

import sys

def test_migration_syntax():
    """Test that the migration file has valid Python syntax."""
    try:
        # Try to import the migration
        sys.path.insert(0, '.')
        from alembic.versions import add_spot_price_history
        
        # Check that required functions exist
        assert hasattr(add_spot_price_history, 'upgrade'), "Missing upgrade() function"
        assert hasattr(add_spot_price_history, 'downgrade'), "Missing downgrade() function"
        
        # Check revision info
        assert add_spot_price_history.revision == 'add_spot_price_history', "Wrong revision ID"
        assert add_spot_price_history.down_revision == '57139d6d9aca', "Wrong down_revision"
        
        print("✅ Migration file syntax: VALID")
        print("✅ upgrade() function: EXISTS")
        print("✅ downgrade() function: EXISTS")
        print("✅ Revision chain: CORRECT")
        print("")
        print("🎉 Migration is ready to deploy!")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax Error: {e}")
        return False
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Assertion Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = test_migration_syntax()
    sys.exit(0 if success else 1)
