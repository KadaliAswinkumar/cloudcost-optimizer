"""
EC2 Instance Database Model
Stores AWS EC2 instance specifications and metadata.
"""

from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class EC2Instance(Base):
    """EC2 Instance specifications model."""
    
    __tablename__ = "ec2_instances"
    
    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Instance Identity
    instance_type: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    instance_family: Mapped[str] = mapped_column(String(20), index=True)
    generation: Mapped[Optional[str]] = mapped_column(String(10))
    
    # Compute Specifications
    vcpus: Mapped[int] = mapped_column(Integer)
    memory_gb: Mapped[float] = mapped_column(Float)
    
    # CPU Details
    processor_architecture: Mapped[str] = mapped_column(String(20), default="x86_64")
    physical_processor: Mapped[Optional[str]] = mapped_column(String(100))
    clock_speed_ghz: Mapped[Optional[float]] = mapped_column(Float)
    
    # Storage
    storage_type: Mapped[str] = mapped_column(String(50), default="EBS-Only")
    instance_storage_gb: Mapped[Optional[float]] = mapped_column(Float)
    
    # Network
    network_performance: Mapped[str] = mapped_column(String(50))
    ebs_bandwidth_mbps: Mapped[Optional[int]] = mapped_column(Integer)
    
    # GPU (for GPU instances)
    gpu_count: Mapped[Optional[int]] = mapped_column(Integer)
    gpu_memory_gb: Mapped[Optional[float]] = mapped_column(Float)
    gpu_manufacturer: Mapped[Optional[str]] = mapped_column(String(50))
    gpu_name: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Features
    current_generation: Mapped[bool] = mapped_column(Boolean, default=True)
    bare_metal: Mapped[bool] = mapped_column(Boolean, default=False)
    hypervisor: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_instance_specs", "vcpus", "memory_gb"),
        Index("idx_instance_family_gen", "instance_family", "generation"),
    )
    
    def __repr__(self) -> str:
        return f"<EC2Instance(type={self.instance_type}, vcpus={self.vcpus}, memory={self.memory_gb}GB)>"
    
    @property
    def memory_per_vcpu(self) -> float:
        """Calculate memory per vCPU ratio."""
        return self.memory_gb / self.vcpus if self.vcpus > 0 else 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "instance_type": self.instance_type,
            "instance_family": self.instance_family,
            "vcpus": self.vcpus,
            "memory_gb": self.memory_gb,
            "processor_architecture": self.processor_architecture,
            "storage_type": self.storage_type,
            "network_performance": self.network_performance,
            "current_generation": self.current_generation,
            "gpu_count": self.gpu_count,
            "gpu_name": self.gpu_name,
        }

