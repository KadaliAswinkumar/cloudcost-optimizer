"""
Spot Price Tracker Service
Tracks and analyzes Spot price trends for risk assessment.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from statistics import mean, stdev
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.pricing import SpotPricing
from src.models.cloud_provider import SpotPriceHistory
from src.services.aws_price_fetcher import AWSPriceFetcher
from src.core.config import settings

logger = logging.getLogger(__name__)


class SpotPriceTracker:
    """
    Tracks Spot prices and calculates risk metrics.
    
    Features:
    - Real-time spot price updates
    - Historical trend analysis
    - Volatility calculation
    - Interruption risk scoring
    """
    
    # Volatility thresholds for risk assessment
    VOLATILITY_LOW = 0.1      # < 10% std dev
    VOLATILITY_MEDIUM = 0.25  # 10-25% std dev
    VOLATILITY_HIGH = 0.5     # > 25% std dev
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize tracker with database session.
        
        Args:
            db_session: SQLAlchemy async session
        """
        self.db = db_session
        self.price_fetcher = AWSPriceFetcher()
    
    async def update_spot_prices(self, region: str) -> int:
        """
        Update spot prices for a region.
        
        Args:
            region: AWS region code
            
        Returns:
            Number of prices updated
        """
        logger.info(f"Updating spot prices for {region}")
        
        try:
            # Fetch current prices from AWS
            current_prices = await self.price_fetcher.fetch_spot_prices(region)
            
            updated_count = 0
            for price_data in current_prices:
                # Update or insert current price
                await self._upsert_spot_price(price_data)
                
                # Record in history
                await self._record_price_history(price_data)
                
                updated_count += 1
            
            await self.db.commit()
            logger.info(f"Updated {updated_count} spot prices for {region}")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating spot prices for {region}: {e}")
            await self.db.rollback()
            raise
    
    async def _upsert_spot_price(self, price_data: Dict) -> None:
        """Insert or update spot price record."""
        query = select(SpotPricing).where(
            SpotPricing.instance_type == price_data["instance_type"],
            SpotPricing.availability_zone == price_data["availability_zone"],
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.spot_price = price_data["spot_price"]
            existing.timestamp = price_data["timestamp"]
            existing.updated_at = datetime.utcnow()
        else:
            new_price = SpotPricing(
                instance_type=price_data["instance_type"],
                region=price_data["region"],
                availability_zone=price_data["availability_zone"],
                spot_price=price_data["spot_price"],
                timestamp=price_data["timestamp"],
            )
            self.db.add(new_price)
    
    async def _record_price_history(self, price_data: Dict) -> None:
        """Record price in history table (multi-cloud schema)."""
        az = price_data["availability_zone"]
        region = az[:-1] if az and len(az) > 1 else price_data.get("region", "us-east-1")
        
        history_record = SpotPriceHistory(
            provider="aws",
            instance_type=price_data["instance_type"],
            region=region,
            zone=az,
            os_type="linux",
            spot_price=price_data["spot_price"],
            timestamp=price_data["timestamp"],
        )
        self.db.add(history_record)
    
    async def calculate_spot_statistics(
        self,
        instance_type: str,
        availability_zone: str,
        days: int = 30
    ) -> Dict:
        """
        Calculate spot price statistics for risk assessment.
        
        Args:
            instance_type: EC2 instance type
            availability_zone: Availability zone
            days: Number of days of history to analyze
            
        Returns:
            Statistics dictionary
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        query = select(SpotPriceHistory).where(
            SpotPriceHistory.provider == "aws",
            SpotPriceHistory.instance_type == instance_type,
            SpotPriceHistory.zone == availability_zone,
            SpotPriceHistory.timestamp >= since,
        ).order_by(SpotPriceHistory.timestamp)
        
        result = await self.db.execute(query)
        history = result.scalars().all()
        
        if not history:
            return {
                "data_available": False,
                "message": "No historical data available",
            }
        
        prices = [float(h.spot_price) for h in history]
        
        # Calculate statistics
        avg_price = mean(prices)
        min_price = min(prices)
        max_price = max(prices)
        price_std = stdev(prices) if len(prices) > 1 else 0
        volatility = price_std / avg_price if avg_price > 0 else 0
        
        # Calculate different period averages
        now = datetime.utcnow()
        prices_24h = [float(h.spot_price) for h in history if h.timestamp >= now - timedelta(hours=24)]
        prices_7d = [float(h.spot_price) for h in history if h.timestamp >= now - timedelta(days=7)]
        
        return {
            "data_available": True,
            "instance_type": instance_type,
            "availability_zone": availability_zone,
            "period_days": days,
            "data_points": len(prices),
            "current_price": prices[-1] if prices else None,
            "avg_price": round(avg_price, 6),
            "min_price": round(min_price, 6),
            "max_price": round(max_price, 6),
            "std_deviation": round(price_std, 6),
            "volatility": round(volatility, 4),
            "avg_price_24h": round(mean(prices_24h), 6) if prices_24h else None,
            "avg_price_7d": round(mean(prices_7d), 6) if prices_7d else None,
            "price_range": round(max_price - min_price, 6),
            "price_range_pct": round((max_price - min_price) / avg_price * 100, 2) if avg_price > 0 else 0,
        }
    
    async def calculate_interruption_risk(
        self,
        instance_type: str,
        availability_zone: str
    ) -> Dict:
        """
        Calculate interruption risk score for Spot instances.
        
        The risk score is based on:
        - Price volatility
        - Price trends
        - Historical interruption patterns
        
        Args:
            instance_type: EC2 instance type
            availability_zone: Availability zone
            
        Returns:
            Risk assessment dictionary
        """
        stats = await self.calculate_spot_statistics(
            instance_type, availability_zone, days=30
        )
        
        if not stats.get("data_available"):
            return {
                "risk_score": 50,  # Default medium risk when no data
                "risk_level": "unknown",
                "confidence": "low",
                "reason": "Insufficient historical data",
            }
        
        # Calculate risk components
        volatility = stats.get("volatility", 0)
        price_range_pct = stats.get("price_range_pct", 0)
        
        # Volatility risk (0-40 points)
        if volatility < self.VOLATILITY_LOW:
            volatility_risk = 10
        elif volatility < self.VOLATILITY_MEDIUM:
            volatility_risk = 25
        elif volatility < self.VOLATILITY_HIGH:
            volatility_risk = 35
        else:
            volatility_risk = 40
        
        # Price range risk (0-30 points)
        if price_range_pct < 20:
            range_risk = 5
        elif price_range_pct < 50:
            range_risk = 15
        elif price_range_pct < 100:
            range_risk = 25
        else:
            range_risk = 30
        
        # Trend risk (0-30 points)
        # Compare recent average to longer-term average
        avg_24h = stats.get("avg_price_24h")
        avg_30d = stats.get("avg_price")
        
        trend_risk = 15  # Default
        trend_direction = "stable"  # Track trend direction for warnings
        
        if avg_24h and avg_30d:
            trend_ratio = avg_24h / avg_30d
            if trend_ratio > 1.2:  # Price increasing rapidly
                trend_risk = 30
                trend_direction = "rising"
            elif trend_ratio > 1.1:
                trend_risk = 25
                trend_direction = "rising"
            elif trend_ratio < 0.9:  # Price decreasing
                trend_risk = 5
                trend_direction = "falling"
            elif trend_ratio < 0.95:
                trend_risk = 10
                trend_direction = "falling"
        
        # Total risk score
        risk_score = volatility_risk + range_risk + trend_risk
        
        # Determine risk level
        if risk_score < 25:
            risk_level = "low"
        elif risk_score < 50:
            risk_level = "medium"
        elif risk_score < 75:
            risk_level = "high"
        else:
            risk_level = "very_high"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "confidence": "high" if stats.get("data_points", 0) > 100 else "medium",
            "trend": trend_direction,  # "rising", "falling", or "stable"
            "volatility": volatility,  # Raw volatility value for callers
            "components": {
                "volatility_risk": volatility_risk,
                "range_risk": range_risk,
                "trend_risk": trend_risk,
            },
            "statistics": stats,
            "recommendation": self._get_risk_recommendation(risk_level),
        }
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level."""
        recommendations = {
            "low": "Spot instances are relatively stable. Good candidate for spot usage with appropriate interruption handling.",
            "medium": "Moderate price fluctuations. Consider using Spot Fleet or capacity pools for better availability.",
            "high": "Significant price volatility. Recommend using Spot only for fault-tolerant workloads with short checkpointing.",
            "very_high": "High interruption probability. Consider On-Demand or Reserved instances for critical workloads.",
            "unknown": "Insufficient data to assess risk. Monitor prices before committing to Spot.",
        }
        return recommendations.get(risk_level, recommendations["unknown"])
    
    async def get_best_spot_zones(
        self,
        instance_type: str,
        region: str,
        top_n: int = 3
    ) -> List[Dict]:
        """
        Find the best availability zones for Spot instances.
        
        Args:
            instance_type: EC2 instance type
            region: AWS region code
            top_n: Number of top zones to return
            
        Returns:
            List of zones ranked by price and stability
        """
        query = select(SpotPricing).where(
            SpotPricing.instance_type == instance_type,
            SpotPricing.region == region,
        ).order_by(SpotPricing.spot_price)
        
        result = await self.db.execute(query)
        spot_prices = result.scalars().all()
        
        # Batch fetch risk data for all zones in parallel to avoid N+1
        risk_tasks = [
            self.calculate_interruption_risk(instance_type, spot.availability_zone)
            for spot in spot_prices
        ]
        risk_results = await asyncio.gather(*risk_tasks)
        
        zones_with_scores = []
        
        for spot, risk_data in zip(spot_prices, risk_results):
            # Calculate combined score (lower is better)
            # Price normalized (0-50) + Risk (0-50)
            price_score = float(spot.spot_price) * 10
            risk_score = risk_data.get("risk_score", 50) / 2
            combined_score = price_score + risk_score
            
            zones_with_scores.append({
                "availability_zone": spot.availability_zone,
                "current_price": float(spot.spot_price),
                "risk_score": risk_data.get("risk_score"),
                "risk_level": risk_data.get("risk_level"),
                "combined_score": round(combined_score, 2),
            })
        
        # Sort by combined score and return top N
        zones_with_scores.sort(key=lambda x: x["combined_score"])
        return zones_with_scores[:top_n]

