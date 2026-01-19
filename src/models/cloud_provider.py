"""
Multi-Cloud Provider Models
Supports AWS, GCP, and Azure instance types and pricing.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from enum import Enum

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Numeric, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class CloudInstance(Base):
    """
    Unified cloud instance model supporting AWS, GCP, and Azure.
    """
    
    __tablename__ = "cloud_instances"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Provider Info
    provider: Mapped[str] = mapped_column(String(10), index=True)  # aws, gcp, azure
    
    # Instance Identity
    instance_type: Mapped[str] = mapped_column(String(100), index=True)
    instance_family: Mapped[str] = mapped_column(String(50), index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Compute Specifications
    vcpus: Mapped[int] = mapped_column(Integer)
    memory_gb: Mapped[float] = mapped_column(Float)
    
    # CPU Details
    processor_architecture: Mapped[str] = mapped_column(String(20), default="x86_64")
    cpu_platform: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Storage
    local_ssd_gb: Mapped[Optional[float]] = mapped_column(Float)
    storage_type: Mapped[str] = mapped_column(String(50), default="SSD")
    
    # Network
    network_bandwidth_gbps: Mapped[Optional[float]] = mapped_column(Float)
    network_tier: Mapped[Optional[str]] = mapped_column(String(50))
    
    # GPU
    gpu_count: Mapped[Optional[int]] = mapped_column(Integer)
    gpu_type: Mapped[Optional[str]] = mapped_column(String(100))
    gpu_memory_gb: Mapped[Optional[float]] = mapped_column(Float)
    
    # Provider-specific fields
    # GCP: shared-core, standard, highmem, highcpu, etc.
    # Azure: General purpose, Compute optimized, Memory optimized, etc.
    # AWS: General purpose, Compute optimized, etc.
    category: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Flags
    is_current_generation: Mapped[bool] = mapped_column(Boolean, default=True)
    is_burstable: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_spot: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    __table_args__ = (
        UniqueConstraint("provider", "instance_type", name="uq_cloud_instance"),
        Index("idx_cloud_instance_specs", "provider", "vcpus", "memory_gb"),
    )
    
    def __repr__(self) -> str:
        return f"<CloudInstance({self.provider}:{self.instance_type})>"
    
    @property
    def memory_per_vcpu(self) -> float:
        return self.memory_gb / self.vcpus if self.vcpus > 0 else 0
    
    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "instance_type": self.instance_type,
            "instance_family": self.instance_family,
            "display_name": self.display_name,
            "vcpus": self.vcpus,
            "memory_gb": self.memory_gb,
            "processor_architecture": self.processor_architecture,
            "local_ssd_gb": self.local_ssd_gb,
            "network_bandwidth_gbps": self.network_bandwidth_gbps,
            "gpu_count": self.gpu_count,
            "gpu_type": self.gpu_type,
            "category": self.category,
            "is_burstable": self.is_burstable,
            "supports_spot": self.supports_spot,
        }


class CloudPricing(Base):
    """
    Unified pricing model for all cloud providers.
    """
    
    __tablename__ = "cloud_pricing"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Provider & Instance
    provider: Mapped[str] = mapped_column(String(10), index=True)
    instance_type: Mapped[str] = mapped_column(String(100), index=True)
    
    # Region/Zone
    region: Mapped[str] = mapped_column(String(50), index=True)
    zone: Mapped[Optional[str]] = mapped_column(String(60))
    
    # Pricing Type
    pricing_type: Mapped[str] = mapped_column(String(30))  # on_demand, spot, preemptible, reserved
    
    # Operating System
    os_type: Mapped[str] = mapped_column(String(20), default="linux")
    
    # Pricing
    hourly_price: Mapped[Decimal] = mapped_column(Numeric(10, 6))
    monthly_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    
    # For reserved/committed use
    commitment_term: Mapped[Optional[str]] = mapped_column(String(20))  # 1yr, 3yr
    upfront_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    
    # Currency
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Metadata
    effective_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    __table_args__ = (
        UniqueConstraint(
            "provider", "instance_type", "region", "pricing_type", "os_type",
            name="uq_cloud_pricing"
        ),
        Index("idx_cloud_pricing_lookup", "provider", "instance_type", "region"),
    )
    
    def __repr__(self) -> str:
        return f"<CloudPricing({self.provider}:{self.instance_type}@{self.region}: ${self.hourly_price}/hr)>"


# GCP Region mappings
GCP_REGIONS = [
    "us-central1", "us-east1", "us-east4", "us-west1", "us-west2", "us-west3", "us-west4",
    "europe-west1", "europe-west2", "europe-west3", "europe-west4", "europe-west6",
    "europe-north1", "europe-central2",
    "asia-east1", "asia-east2", "asia-northeast1", "asia-northeast2", "asia-northeast3",
    "asia-south1", "asia-south2", "asia-southeast1", "asia-southeast2",
    "australia-southeast1", "australia-southeast2",
    "southamerica-east1", "northamerica-northeast1", "northamerica-northeast2",
]

# Azure Region mappings
AZURE_REGIONS = [
    "eastus", "eastus2", "westus", "westus2", "westus3",
    "centralus", "northcentralus", "southcentralus", "westcentralus",
    "canadacentral", "canadaeast",
    "northeurope", "westeurope", "uksouth", "ukwest",
    "francecentral", "germanywestcentral", "norwayeast", "swedencentral", "switzerlandnorth",
    "eastasia", "southeastasia", "japaneast", "japanwest",
    "australiaeast", "australiasoutheast", "australiacentral",
    "centralindia", "southindia", "westindia",
    "koreacentral", "koreasouth",
    "brazilsouth", "southafricanorth", "uaenorth",
]

