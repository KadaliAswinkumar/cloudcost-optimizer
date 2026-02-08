#!/usr/bin/env python3
"""
DIAGNOSTIC SCRIPT: Test fetch_real_spot_pricing.py
This script will identify why spot pricing isn't being inserted into cloud_pricing table
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

async def diagnose():
    print("\n" + "="*70)
    print("🔍 DIAGNOSING SPOT PRICING ISSUE")
    print("="*70)
    
    # Step 1: Check database connection
    print("\n1️⃣ Testing Database Connection...")
    try:
        from src.core.database import get_db_context
        from src.models.cloud_provider import CloudPricing, CloudInstance
        from sqlalchemy import select, func
        
        async with get_db_context() as db:
            # Test basic query
            result = await db.execute(select(func.count()).select_from(CloudInstance))
            count = result.scalar()
            print(f"   ✅ Database connected! Found {count} instances")
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False
    
    # Step 2: Check if on-demand prices exist (required for GCP/Azure spot calculation)
    print("\n2️⃣ Checking On-Demand Pricing Data...")
    try:
        async with get_db_context() as db:
            # AWS on-demand
            aws_od = await db.execute(
                select(func.count()).select_from(CloudPricing).where(
                    CloudPricing.provider == "aws",
                    CloudPricing.pricing_type == "on_demand"
                )
            )
            # GCP on-demand
            gcp_od = await db.execute(
                select(func.count()).select_from(CloudPricing).where(
                    CloudPricing.provider == "gcp",
                    CloudPricing.pricing_type == "on_demand"
                )
            )
            # Azure on-demand
            azure_od = await db.execute(
                select(func.count()).select_from(CloudPricing).where(
                    CloudPricing.provider == "azure",
                    CloudPricing.pricing_type == "on_demand"
                )
            )
            
            aws_count = aws_od.scalar()
            gcp_count = gcp_od.scalar()
            azure_count = azure_od.scalar()
            
            print(f"   AWS on-demand prices:   {aws_count}")
            print(f"   GCP on-demand prices:   {gcp_count}")
            print(f"   Azure on-demand prices: {azure_count}")
            
            if aws_count == 0 and gcp_count == 0 and azure_count == 0:
                print(f"   ❌ NO ON-DEMAND PRICING DATA!")
                print(f"   ⚠️  fetch_real_data.py must run first to populate on-demand prices")
                return False
            else:
                print(f"   ✅ On-demand pricing exists")
    except Exception as e:
        print(f"   ❌ Failed to check on-demand pricing: {e}")
        return False
    
    # Step 3: Check current spot pricing
    print("\n3️⃣ Checking Current Spot Pricing...")
    try:
        async with get_db_context() as db:
            result = await db.execute(
                select(func.count()).select_from(CloudPricing).where(
                    CloudPricing.pricing_type.in_(["spot", "preemptible"])
                )
            )
            spot_count = result.scalar()
            print(f"   Current spot prices in cloud_pricing: {spot_count}")
            
            if spot_count == 0:
                print(f"   ❌ NO SPOT PRICING! This is the problem.")
            else:
                print(f"   ✅ Spot pricing exists (already loaded)")
    except Exception as e:
        print(f"   ❌ Failed to check spot pricing: {e}")
        return False
    
    # Step 4: Test AWS credentials
    print("\n4️⃣ Testing AWS Credentials...")
    try:
        import os
        import boto3
        
        if not os.getenv('AWS_ACCESS_KEY_ID'):
            print(f"   ⚠️  AWS_ACCESS_KEY_ID not set")
        else:
            print(f"   ✅ AWS_ACCESS_KEY_ID is set")
        
        if not os.getenv('AWS_SECRET_ACCESS_KEY'):
            print(f"   ⚠️  AWS_SECRET_ACCESS_KEY not set")
        else:
            print(f"   ✅ AWS_SECRET_ACCESS_KEY is set")
        
        # Try to connect
        try:
            ec2 = boto3.client('ec2', region_name='us-east-1')
            # Test a simple API call
            response = ec2.describe_regions()
            print(f"   ✅ AWS API connection successful! Found {len(response['Regions'])} regions")
        except Exception as e:
            print(f"   ❌ AWS API connection failed: {e}")
    except Exception as e:
        print(f"   ⚠️  boto3 not available: {e}")
    
    # Step 5: Check unique constraint
    print("\n5️⃣ Checking Database Unique Constraint...")
    try:
        from sqlalchemy import inspect
        
        async with get_db_context() as db:
            inspector = inspect(db.bind)
            constraints = inspector.get_unique_constraints('cloud_pricing')
            
            print(f"   Found {len(constraints)} unique constraints:")
            for c in constraints:
                print(f"      - {c['name']}: {c['column_names']}")
            
            # Check if 'zone' is included
            uq_pricing = next((c for c in constraints if c['name'] == 'uq_cloud_pricing'), None)
            if uq_pricing:
                if 'zone' in uq_pricing['column_names']:
                    print(f"   ✅ 'zone' is in unique constraint (correct)")
                else:
                    print(f"   ⚠️  'zone' NOT in unique constraint (migration may not have run)")
    except Exception as e:
        print(f"   ⚠️  Could not check constraints: {e}")
    
    # Step 6: Try a small insert test
    print("\n6️⃣ Testing UPSERT Logic...")
    try:
        from decimal import Decimal
        from datetime import datetime
        from sqlalchemy.dialects.postgresql import insert
        
        async with get_db_context() as db:
            # Try to insert a test spot price
            test_price = {
                'provider': 'aws',
                'instance_type': 't2.micro',
                'region': 'us-east-1',
                'zone': 'us-east-1a',
                'pricing_type': 'spot',
                'os_type': 'linux',
                'hourly_price': Decimal('0.0035'),
                'monthly_price': Decimal('2.555'),
                'currency': 'USD',
                'effective_date': datetime.utcnow(),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            stmt = insert(CloudPricing).values([test_price])
            stmt = stmt.on_conflict_do_update(
                constraint='uq_cloud_pricing',
                set_={
                    'hourly_price': stmt.excluded.hourly_price,
                    'monthly_price': stmt.excluded.monthly_price,
                    'updated_at': stmt.excluded.updated_at,
                }
            )
            
            await db.execute(stmt)
            await db.commit()
            
            print(f"   ✅ UPSERT test successful!")
            
            # Verify it was inserted
            result = await db.execute(
                select(CloudPricing).where(
                    CloudPricing.provider == 'aws',
                    CloudPricing.instance_type == 't2.micro',
                    CloudPricing.pricing_type == 'spot',
                    CloudPricing.region == 'us-east-1',
                    CloudPricing.zone == 'us-east-1a'
                )
            )
            test_record = result.scalar()
            if test_record:
                print(f"   ✅ Test record verified in database!")
            else:
                print(f"   ❌ Test record NOT found after insert!")
                
    except Exception as e:
        print(f"   ❌ UPSERT test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*70)
    print("✅ DIAGNOSIS COMPLETE")
    print("="*70)
    
    return True


if __name__ == "__main__":
    success = asyncio.run(diagnose())
    sys.exit(0 if success else 1)
