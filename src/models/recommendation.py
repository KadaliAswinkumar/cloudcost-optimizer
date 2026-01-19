"""
Recommendation and Workload Profile Models
Stores user workload requirements and generated recommendations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum

from sqlalchemy import (
    String, Integer, Float, DateTime, JSON, Text,
    Numeric, Enum as SQLEnum, Index
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class WorkloadType(str, Enum):
    """Types of workload patterns."""
    STEADY = "steady"          # Consistent load 24/7
    VARIABLE = "variable"      # Variable load patterns
    BURST = "burst"           # Occasional high demand
    BATCH = "batch"           # Batch processing jobs
    DEV_TEST = "dev_test"     # Development/testing


class InterruptionTolerance(str, Enum):
    """Tolerance for instance interruptions (for Spot)."""
    NONE = "none"     # Cannot tolerate interruptions
    LOW = "low"       # Can handle rare interruptions
    MEDIUM = "medium" # Can handle occasional interruptions
    HIGH = "high"     # Fully tolerant of interruptions


class WorkloadProfile(Base):
    """User-defined workload requirements for recommendations."""
    
    __tablename__ = "workload_profiles"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Profile Identity
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Compute Requirements
    min_vcpus: Mapped[int] = mapped_column(Integer)
    max_vcpus: Mapped[Optional[int]] = mapped_column(Integer)
    min_memory_gb: Mapped[float] = mapped_column(Float)
    max_memory_gb: Mapped[Optional[float]] = mapped_column(Float)
    
    # Storage Requirements
    requires_instance_storage: Mapped[bool] = mapped_column(default=False)
    min_storage_gb: Mapped[Optional[float]] = mapped_column(Float)
    
    # GPU Requirements
    requires_gpu: Mapped[bool] = mapped_column(default=False)
    min_gpu_count: Mapped[Optional[int]] = mapped_column(Integer)
    min_gpu_memory_gb: Mapped[Optional[float]] = mapped_column(Float)
    
    # Network Requirements
    network_performance: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Workload Characteristics
    workload_type: Mapped[WorkloadType] = mapped_column(
        SQLEnum(WorkloadType), default=WorkloadType.STEADY
    )
    expected_hours_per_month: Mapped[int] = mapped_column(Integer, default=730)
    interruption_tolerance: Mapped[InterruptionTolerance] = mapped_column(
        SQLEnum(InterruptionTolerance), default=InterruptionTolerance.NONE
    )
    
    # Region Preferences
    preferred_regions: Mapped[Optional[List[str]]] = mapped_column(JSON)
    excluded_regions: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    # Budget Constraints
    max_monthly_budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    max_hourly_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    
    # Architecture Preference
    architecture: Mapped[str] = mapped_column(String(20), default="x86_64")  # x86_64, arm64
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    __table_args__ = (
        Index("idx_workload_user", "user_id"),
    )
    
    def __repr__(self) -> str:
        return f"<WorkloadProfile(name={self.name}, vcpus>={self.min_vcpus}, memory>={self.min_memory_gb}GB)>"


class Recommendation(Base):
    """Generated instance recommendations."""
    
    __tablename__ = "recommendations"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Reference to workload profile
    workload_profile_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    request_hash: Mapped[str] = mapped_column(String(64), index=True)  # For caching
    
    # Recommended Instance
    instance_type: Mapped[str] = mapped_column(String(50))
    region: Mapped[str] = mapped_column(String(20))
    availability_zone: Mapped[Optional[str]] = mapped_column(String(25))
    
    # Pricing Strategy
    pricing_strategy: Mapped[str] = mapped_column(String(20))  # on_demand, reserved_1yr, reserved_3yr, spot
    
    # Cost Analysis
    hourly_cost: Mapped[Decimal] = mapped_column(Numeric(10, 6))
    monthly_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    annual_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    
    # Savings Analysis
    ondemand_hourly: Mapped[Decimal] = mapped_column(Numeric(10, 6))
    savings_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    savings_percentage: Mapped[float] = mapped_column(Float)
    
    # Risk Assessment (for Spot)
    risk_score: Mapped[float] = mapped_column(Float, default=0)  # 0-100
    interruption_probability: Mapped[Optional[float]] = mapped_column(Float)
    
    # Ranking
    rank: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Float)  # Overall recommendation score
    
    # Explanation
    reasoning: Mapped[str] = mapped_column(Text)
    pros: Mapped[Optional[List[str]]] = mapped_column(JSON)
    cons: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)  # Recommendations expire
    
    __table_args__ = (
        Index("idx_recommendation_lookup", "request_hash", "rank"),
    )
    
    def __repr__(self) -> str:
        return f"<Recommendation(#{self.rank}: {self.instance_type}@{self.region} via {self.pricing_strategy})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "rank": self.rank,
            "instance_type": self.instance_type,
            "region": self.region,
            "pricing_strategy": self.pricing_strategy,
            "hourly_cost": float(self.hourly_cost),
            "monthly_cost": float(self.monthly_cost),
            "annual_cost": float(self.annual_cost),
            "savings_percentage": self.savings_percentage,
            "risk_score": self.risk_score,
            "score": self.score,
            "reasoning": self.reasoning,
            "pros": self.pros,
            "cons": self.cons,
        }

