"""
Pricing Database Models
Stores On-Demand, Reserved, and Spot pricing data for EC2 instances.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String, Integer, Float, DateTime, 
    Numeric, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class OnDemandPricing(Base):
    """On-Demand pricing for EC2 instances."""
    
    __tablename__ = "on_demand_pricing"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Instance & Region
    instance_type: Mapped[str] = mapped_column(String(50), index=True)
    region: Mapped[str] = mapped_column(String(20), index=True)
    availability_zone: Mapped[Optional[str]] = mapped_column(String(25))
    
    # Pricing (per hour in USD)
    price_per_hour: Mapped[Decimal] = mapped_column(Numeric(10, 6))
    
    # Operating System
    operating_system: Mapped[str] = mapped_column(String(20), default="Linux")
    tenancy: Mapped[str] = mapped_column(String(20), default="Shared")
    
    # Metadata
    effective_date: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    __table_args__ = (
        UniqueConstraint(
            "instance_type", "region", "operating_system", "tenancy",
            name="uq_ondemand_pricing"
        ),
        Index("idx_ondemand_lookup", "instance_type", "region"),
    )
    
    def __repr__(self) -> str:
        return f"<OnDemandPricing({self.instance_type}@{self.region}: ${self.price_per_hour}/hr)>"


class ReservedPricing(Base):
    """Reserved Instance pricing for EC2 instances."""
    
    __tablename__ = "reserved_pricing"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Instance & Region
    instance_type: Mapped[str] = mapped_column(String(50), index=True)
    region: Mapped[str] = mapped_column(String(20), index=True)
    
    # Reservation Terms
    lease_term: Mapped[str] = mapped_column(String(10))  # 1yr, 3yr
    purchase_option: Mapped[str] = mapped_column(String(20))  # No Upfront, Partial Upfront, All Upfront
    offering_class: Mapped[str] = mapped_column(String(20), default="standard")  # standard, convertible
    
    # Pricing
    upfront_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    hourly_cost: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=0)
    effective_hourly: Mapped[Decimal] = mapped_column(Numeric(10, 6))  # Calculated total
    
    # Operating System
    operating_system: Mapped[str] = mapped_column(String(20), default="Linux")
    tenancy: Mapped[str] = mapped_column(String(20), default="Shared")
    
    # Metadata
    effective_date: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    __table_args__ = (
        UniqueConstraint(
            "instance_type", "region", "lease_term", "purchase_option",
            "offering_class", "operating_system", "tenancy",
            name="uq_reserved_pricing"
        ),
        Index("idx_reserved_lookup", "instance_type", "region", "lease_term"),
    )
    
    def __repr__(self) -> str:
        return f"<ReservedPricing({self.instance_type}@{self.region} {self.lease_term}: ${self.effective_hourly}/hr)>"
    
    @property
    def savings_vs_ondemand(self) -> Optional[float]:
        """Calculate savings percentage vs on-demand (requires join)."""
        # This would be calculated at query time
        return None


class SpotPricing(Base):
    """Current Spot pricing for EC2 instances."""
    
    __tablename__ = "spot_pricing"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Instance & Region
    instance_type: Mapped[str] = mapped_column(String(50), index=True)
    region: Mapped[str] = mapped_column(String(20), index=True)
    availability_zone: Mapped[str] = mapped_column(String(25), index=True)
    
    # Current Pricing
    spot_price: Mapped[Decimal] = mapped_column(Numeric(10, 6))
    
    # Statistics (calculated from history)
    avg_price_24h: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    avg_price_7d: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    avg_price_30d: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    min_price_30d: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    max_price_30d: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    price_volatility: Mapped[Optional[float]] = mapped_column(Float)  # Std deviation
    
    # Interruption Metrics
    interruption_rate: Mapped[Optional[float]] = mapped_column(Float)  # 0-100%
    interruption_frequency: Mapped[Optional[str]] = mapped_column(String(20))  # low, medium, high
    
    # Metadata
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    __table_args__ = (
        UniqueConstraint(
            "instance_type", "availability_zone",
            name="uq_spot_pricing"
        ),
        Index("idx_spot_lookup", "instance_type", "region"),
        Index("idx_spot_az", "availability_zone"),
    )
    
    def __repr__(self) -> str:
        return f"<SpotPricing({self.instance_type}@{self.availability_zone}: ${self.spot_price}/hr)>"

