"""
Spot Price Monitor Tasks
Background tasks for monitoring spot prices and calculating statistics.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from statistics import mean, stdev

from celery import shared_task
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from src.jobs.celery_app import celery_app
from src.core.config import settings
from src.core.database import get_db_context
from src.services.aws_price_fetcher import AWSPriceFetcher
from src.models.pricing import SpotPricing
from src.models.cloud_provider import SpotPriceHistory

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async code in Celery tasks."""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(
    bind=True,
    name="src.jobs.spot_monitor.monitor_spot_prices",
    max_retries=3,
    default_retry_delay=60,
)
def monitor_spot_prices(self, regions: Optional[List[str]] = None):
    """
    Monitor and update spot prices for all regions.
    
    Args:
        regions: List of AWS regions (defaults to primary regions)
        
    Returns:
        Summary of monitoring results
    """
    # Focus on primary regions for frequent updates
    regions = regions or ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
    
    logger.info(f"Monitoring spot prices for {len(regions)} regions...")
    
    results = {
        "started_at": datetime.utcnow().isoformat(),
        "regions_processed": 0,
        "prices_updated": 0,
        "history_records": 0,
        "errors": [],
    }
    
    try:
        for region in regions:
            try:
                updated, history = run_async(_update_spot_prices(region))
                results["prices_updated"] += updated
                results["history_records"] += history
                results["regions_processed"] += 1
            except Exception as e:
                error_msg = f"Error monitoring {region}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        results["completed_at"] = datetime.utcnow().isoformat()
        results["success"] = len(results["errors"]) == 0
        
        logger.info(f"Spot monitoring complete: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Spot monitoring failed: {e}")
        self.retry(exc=e)


@celery_app.task(
    bind=True,
    name="src.jobs.spot_monitor.calculate_spot_statistics",
    max_retries=3,
    default_retry_delay=300,
)
def calculate_spot_statistics(self):
    """
    Calculate spot price statistics for all tracked instances.
    
    Updates average prices, volatility, and interruption metrics.
    
    Returns:
        Number of instances updated
    """
    logger.info("Calculating spot statistics...")
    
    try:
        count = run_async(_calculate_all_statistics())
        logger.info(f"Updated statistics for {count} spot prices")
        return {"instances_updated": count}
    except Exception as e:
        logger.error(f"Statistics calculation failed: {e}")
        self.retry(exc=e)


async def _update_spot_prices(region: str) -> tuple[int, int]:
    """
    Fetch and update spot prices for a region.
    
    Returns:
        (prices_updated, history_records_created)
    """
    fetcher = AWSPriceFetcher()
    spot_prices = await fetcher.fetch_spot_prices(region)
    
    updated = 0
    history = 0
    
    async with get_db_context() as db:
        for price_data in spot_prices:
            # Update current price
            stmt = insert(SpotPricing).values(
                instance_type=price_data["instance_type"],
                region=price_data["region"],
                availability_zone=price_data["availability_zone"],
                spot_price=price_data["spot_price"],
                timestamp=price_data["timestamp"],
            )
            stmt = stmt.on_conflict_do_update(
                constraint="uq_spot_pricing",
                set_={
                    "spot_price": price_data["spot_price"],
                    "timestamp": price_data["timestamp"],
                    "updated_at": datetime.utcnow(),
                },
            )
            await db.execute(stmt)
            updated += 1
            
            # Record in history (convert AWS format to multi-cloud schema)
            az = price_data["availability_zone"]
            region = az[:-1] if az and len(az) > 1 else price_data.get("region", "us-east-1")
            
            history_stmt = insert(SpotPriceHistory).values(
                provider="aws",
                instance_type=price_data["instance_type"],
                region=region,
                zone=az,
                os_type="linux",
                spot_price=price_data["spot_price"],
                timestamp=price_data["timestamp"],
            )
            await db.execute(history_stmt)
            history += 1
        
        await db.commit()
    
    return updated, history


async def _calculate_all_statistics():
    """Calculate statistics for all spot pricing records."""
    count = 0
    
    async with get_db_context() as db:
        # Get all current spot prices
        query = select(SpotPricing)
        result = await db.execute(query)
        spot_prices = result.scalars().all()
        
        for spot in spot_prices:
            stats = await _calculate_instance_stats(
                db, 
                spot.instance_type, 
                spot.availability_zone
            )
            
            if stats:
                # Update the spot pricing record with statistics
                update_stmt = (
                    update(SpotPricing)
                    .where(SpotPricing.id == spot.id)
                    .values(**stats)
                )
                await db.execute(update_stmt)
                count += 1
        
        await db.commit()
    
    return count


async def _calculate_instance_stats(
    db,
    instance_type: str,
    availability_zone: str
) -> Optional[dict]:
    """Calculate statistics for a specific instance/AZ combination."""
    now = datetime.utcnow()
    
    # Fetch history for different periods
    periods = {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
    }
    
    history_30d_query = select(SpotPriceHistory).where(
        SpotPriceHistory.instance_type == instance_type,
        SpotPriceHistory.availability_zone == availability_zone,
        SpotPriceHistory.timestamp >= now - timedelta(days=30),
    )
    result = await db.execute(history_30d_query)
    history = result.scalars().all()
    
    if not history:
        return None
    
    # Calculate statistics
    all_prices = [float(h.spot_price) for h in history]
    
    # Period averages
    avg_24h = mean([
        float(h.spot_price) for h in history 
        if h.timestamp >= now - timedelta(hours=24)
    ] or all_prices)
    
    avg_7d = mean([
        float(h.spot_price) for h in history 
        if h.timestamp >= now - timedelta(days=7)
    ] or all_prices)
    
    avg_30d = mean(all_prices)
    
    # Min/Max
    min_30d = min(all_prices)
    max_30d = max(all_prices)
    
    # Volatility (coefficient of variation)
    volatility = (stdev(all_prices) / avg_30d) if len(all_prices) > 1 and avg_30d > 0 else 0
    
    # Interruption frequency classification
    if volatility < 0.1:
        interruption_freq = "low"
    elif volatility < 0.25:
        interruption_freq = "medium"
    else:
        interruption_freq = "high"
    
    return {
        "avg_price_24h": round(avg_24h, 6),
        "avg_price_7d": round(avg_7d, 6),
        "avg_price_30d": round(avg_30d, 6),
        "min_price_30d": round(min_30d, 6),
        "max_price_30d": round(max_30d, 6),
        "price_volatility": round(volatility, 4),
        "interruption_frequency": interruption_freq,
    }


@celery_app.task(name="src.jobs.spot_monitor.cleanup_old_history")
def cleanup_old_history(days_to_keep: int = 90):
    """
    Clean up old spot price history records.
    
    Args:
        days_to_keep: Number of days of history to retain
        
    Returns:
        Number of records deleted
    """
    logger.info(f"Cleaning up spot history older than {days_to_keep} days...")
    
    count = run_async(_cleanup_history(days_to_keep))
    logger.info(f"Deleted {count} old history records")
    return {"records_deleted": count}


async def _cleanup_history(days_to_keep: int) -> int:
    """Delete old history records."""
    from sqlalchemy import delete
    
    cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
    
    async with get_db_context() as db:
        stmt = delete(SpotPriceHistory).where(
            SpotPriceHistory.timestamp < cutoff
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

