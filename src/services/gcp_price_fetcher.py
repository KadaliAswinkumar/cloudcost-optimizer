"""
GCP Price Fetcher Service
Fetches Google Cloud Compute Engine instance specifications and pricing.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from src.core.config import settings
from src.models.cloud_provider import CloudProvider, GCP_REGIONS

logger = logging.getLogger(__name__)


class GCPPriceFetcher:
    """
    Fetches GCP Compute Engine instance data.
    
    Uses:
    - GCP Compute Engine API for instance types
    - GCP Cloud Billing API for pricing
    """
    
    # GCP Machine Type Families
    MACHINE_FAMILIES = {
        "general_purpose": ["e2", "n1", "n2", "n2d", "t2d", "t2a", "c3", "c3d"],
        "compute_optimized": ["c2", "c2d", "h3"],
        "memory_optimized": ["m1", "m2", "m3"],
        "accelerator_optimized": ["a2", "a3", "g2"],
        "storage_optimized": ["z3"],
    }
    
    # Standard machine type specs (simplified for demo)
    STANDARD_MACHINE_TYPES = {
        # E2 Series (Cost-optimized)
        "e2-micro": {"vcpus": 0.25, "memory_gb": 1, "shared_core": True},
        "e2-small": {"vcpus": 0.5, "memory_gb": 2, "shared_core": True},
        "e2-medium": {"vcpus": 1, "memory_gb": 4, "shared_core": True},
        "e2-standard-2": {"vcpus": 2, "memory_gb": 8},
        "e2-standard-4": {"vcpus": 4, "memory_gb": 16},
        "e2-standard-8": {"vcpus": 8, "memory_gb": 32},
        "e2-standard-16": {"vcpus": 16, "memory_gb": 64},
        "e2-highmem-2": {"vcpus": 2, "memory_gb": 16},
        "e2-highmem-4": {"vcpus": 4, "memory_gb": 32},
        "e2-highmem-8": {"vcpus": 8, "memory_gb": 64},
        "e2-highcpu-2": {"vcpus": 2, "memory_gb": 2},
        "e2-highcpu-4": {"vcpus": 4, "memory_gb": 4},
        "e2-highcpu-8": {"vcpus": 8, "memory_gb": 8},
        
        # N2 Series (Balanced)
        "n2-standard-2": {"vcpus": 2, "memory_gb": 8},
        "n2-standard-4": {"vcpus": 4, "memory_gb": 16},
        "n2-standard-8": {"vcpus": 8, "memory_gb": 32},
        "n2-standard-16": {"vcpus": 16, "memory_gb": 64},
        "n2-standard-32": {"vcpus": 32, "memory_gb": 128},
        "n2-highmem-2": {"vcpus": 2, "memory_gb": 16},
        "n2-highmem-4": {"vcpus": 4, "memory_gb": 32},
        "n2-highmem-8": {"vcpus": 8, "memory_gb": 64},
        "n2-highcpu-2": {"vcpus": 2, "memory_gb": 2},
        "n2-highcpu-4": {"vcpus": 4, "memory_gb": 4},
        "n2-highcpu-8": {"vcpus": 8, "memory_gb": 8},
        
        # N2D Series (AMD)
        "n2d-standard-2": {"vcpus": 2, "memory_gb": 8, "cpu_platform": "AMD EPYC"},
        "n2d-standard-4": {"vcpus": 4, "memory_gb": 16, "cpu_platform": "AMD EPYC"},
        "n2d-standard-8": {"vcpus": 8, "memory_gb": 32, "cpu_platform": "AMD EPYC"},
        "n2d-highmem-2": {"vcpus": 2, "memory_gb": 16, "cpu_platform": "AMD EPYC"},
        "n2d-highmem-4": {"vcpus": 4, "memory_gb": 32, "cpu_platform": "AMD EPYC"},
        
        # C2 Series (Compute-optimized)
        "c2-standard-4": {"vcpus": 4, "memory_gb": 16, "category": "compute_optimized"},
        "c2-standard-8": {"vcpus": 8, "memory_gb": 32, "category": "compute_optimized"},
        "c2-standard-16": {"vcpus": 16, "memory_gb": 64, "category": "compute_optimized"},
        "c2-standard-30": {"vcpus": 30, "memory_gb": 120, "category": "compute_optimized"},
        "c2-standard-60": {"vcpus": 60, "memory_gb": 240, "category": "compute_optimized"},
        
        # M2 Series (Memory-optimized)
        "m2-ultramem-208": {"vcpus": 208, "memory_gb": 5888, "category": "memory_optimized"},
        "m2-ultramem-416": {"vcpus": 416, "memory_gb": 11776, "category": "memory_optimized"},
        "m2-megamem-416": {"vcpus": 416, "memory_gb": 5888, "category": "memory_optimized"},
        
        # A2 Series (GPU)
        "a2-highgpu-1g": {"vcpus": 12, "memory_gb": 85, "gpu_count": 1, "gpu_type": "NVIDIA A100"},
        "a2-highgpu-2g": {"vcpus": 24, "memory_gb": 170, "gpu_count": 2, "gpu_type": "NVIDIA A100"},
        "a2-highgpu-4g": {"vcpus": 48, "memory_gb": 340, "gpu_count": 4, "gpu_type": "NVIDIA A100"},
        "a2-highgpu-8g": {"vcpus": 96, "memory_gb": 680, "gpu_count": 8, "gpu_type": "NVIDIA A100"},
    }
    
    # Approximate pricing per region (USD/hour) - simplified
    BASE_PRICING = {
        "e2-micro": 0.0084,
        "e2-small": 0.0168,
        "e2-medium": 0.0335,
        "e2-standard-2": 0.0670,
        "e2-standard-4": 0.1340,
        "e2-standard-8": 0.2680,
        "e2-standard-16": 0.5765,
        "e2-highmem-2": 0.0903,
        "e2-highmem-4": 0.1806,
        "e2-highmem-8": 0.3612,
        "e2-highcpu-2": 0.0496,
        "e2-highcpu-4": 0.0992,
        "e2-highcpu-8": 0.1984,
        "n2-standard-2": 0.0971,
        "n2-standard-4": 0.1942,
        "n2-standard-8": 0.3885,
        "n2-standard-16": 0.7769,
        "n2-standard-32": 1.5538,
        "n2-highmem-2": 0.1310,
        "n2-highmem-4": 0.2620,
        "n2-highmem-8": 0.5240,
        "n2-highcpu-2": 0.0717,
        "n2-highcpu-4": 0.1434,
        "n2-highcpu-8": 0.2868,
        "n2d-standard-2": 0.0845,
        "n2d-standard-4": 0.1690,
        "n2d-standard-8": 0.3380,
        "n2d-highmem-2": 0.1140,
        "n2d-highmem-4": 0.2280,
        "c2-standard-4": 0.2088,
        "c2-standard-8": 0.4176,
        "c2-standard-16": 0.8352,
        "c2-standard-30": 1.5660,
        "c2-standard-60": 3.1321,
        "m2-ultramem-208": 42.186,
        "m2-ultramem-416": 84.371,
        "m2-megamem-416": 50.372,
        "a2-highgpu-1g": 3.6731,
        "a2-highgpu-2g": 7.3462,
        "a2-highgpu-4g": 14.6924,
        "a2-highgpu-8g": 29.3849,
    }
    
    # Regional price multipliers
    REGION_MULTIPLIERS = {
        "us-central1": 1.0,
        "us-east1": 1.0,
        "us-west1": 1.0,
        "us-west2": 1.05,
        "us-east4": 1.05,
        "europe-west1": 1.10,
        "europe-west2": 1.15,
        "europe-west3": 1.15,
        "europe-west4": 1.10,
        "asia-east1": 1.08,
        "asia-northeast1": 1.18,
        "asia-southeast1": 1.08,
        "australia-southeast1": 1.20,
        "southamerica-east1": 1.40,
    }
    
    def __init__(self):
        """Initialize GCP client."""
        self._compute_client = None
        self._billing_client = None
    
    async def fetch_machine_types(self) -> List[Dict]:
        """
        Fetch all GCP machine types with specifications.
        
        Returns:
            List of machine type specifications
        """
        logger.info("Fetching GCP machine types...")
        
        machine_types = []
        
        for machine_type, specs in self.STANDARD_MACHINE_TYPES.items():
            # Parse family from machine type name
            family = machine_type.split("-")[0]
            
            # Determine category
            category = specs.get("category", "general_purpose")
            for cat, families in self.MACHINE_FAMILIES.items():
                if family in families:
                    category = cat
                    break
            
            machine_types.append({
                "provider": CloudProvider.GCP.value,
                "instance_type": machine_type,
                "instance_family": family,
                "display_name": machine_type.replace("-", " ").title(),
                "vcpus": specs["vcpus"] if isinstance(specs["vcpus"], int) else int(specs["vcpus"]),
                "memory_gb": specs["memory_gb"],
                "processor_architecture": "x86_64",
                "cpu_platform": specs.get("cpu_platform"),
                "category": category,
                "is_burstable": specs.get("shared_core", False),
                "supports_spot": True,  # GCP calls it Preemptible/Spot
                "gpu_count": specs.get("gpu_count"),
                "gpu_type": specs.get("gpu_type"),
                "is_current_generation": True,
            })
        
        logger.info(f"Fetched {len(machine_types)} GCP machine types")
        return machine_types
    
    async def fetch_pricing(
        self,
        region: str = "us-central1"
    ) -> List[Dict]:
        """
        Fetch GCP pricing for a region.
        
        Args:
            region: GCP region
            
        Returns:
            List of pricing data
        """
        logger.info(f"Fetching GCP pricing for {region}...")
        
        pricing_data = []
        multiplier = self.REGION_MULTIPLIERS.get(region, 1.1)
        
        for machine_type, base_price in self.BASE_PRICING.items():
            # On-demand pricing
            hourly_price = base_price * multiplier
            
            pricing_data.append({
                "provider": CloudProvider.GCP.value,
                "instance_type": machine_type,
                "region": region,
                "pricing_type": "on_demand",
                "os_type": "linux",
                "hourly_price": Decimal(str(round(hourly_price, 6))),
                "monthly_price": Decimal(str(round(hourly_price * 730, 2))),
                "currency": "USD",
                "effective_date": datetime.utcnow(),
            })
            
            # Preemptible/Spot pricing (60-90% discount)
            spot_price = hourly_price * 0.3  # ~70% discount
            pricing_data.append({
                "provider": CloudProvider.GCP.value,
                "instance_type": machine_type,
                "region": region,
                "pricing_type": "spot",
                "os_type": "linux",
                "hourly_price": Decimal(str(round(spot_price, 6))),
                "monthly_price": Decimal(str(round(spot_price * 730, 2))),
                "currency": "USD",
                "effective_date": datetime.utcnow(),
            })
            
            # Committed Use Discount (1 year - ~37% discount)
            cud_1yr_price = hourly_price * 0.63
            pricing_data.append({
                "provider": CloudProvider.GCP.value,
                "instance_type": machine_type,
                "region": region,
                "pricing_type": "committed_1yr",
                "os_type": "linux",
                "hourly_price": Decimal(str(round(cud_1yr_price, 6))),
                "monthly_price": Decimal(str(round(cud_1yr_price * 730, 2))),
                "commitment_term": "1yr",
                "currency": "USD",
                "effective_date": datetime.utcnow(),
            })
            
            # Committed Use Discount (3 year - ~55% discount)
            cud_3yr_price = hourly_price * 0.45
            pricing_data.append({
                "provider": CloudProvider.GCP.value,
                "instance_type": machine_type,
                "region": region,
                "pricing_type": "committed_3yr",
                "os_type": "linux",
                "hourly_price": Decimal(str(round(cud_3yr_price, 6))),
                "monthly_price": Decimal(str(round(cud_3yr_price * 730, 2))),
                "commitment_term": "3yr",
                "currency": "USD",
                "effective_date": datetime.utcnow(),
            })
        
        logger.info(f"Generated {len(pricing_data)} GCP pricing records for {region}")
        return pricing_data
    
    async def fetch_all_pricing(
        self,
        regions: Optional[List[str]] = None
    ) -> Dict:
        """
        Fetch all GCP pricing data.
        
        Args:
            regions: List of regions (defaults to primary regions)
            
        Returns:
            Dictionary with machine types and pricing
        """
        regions = regions or [
            "us-central1", "us-east1", "us-west1",
            "europe-west1", "asia-east1", "asia-northeast1"
        ]
        
        machine_types = await self.fetch_machine_types()
        
        all_pricing = []
        for region in regions:
            pricing = await self.fetch_pricing(region)
            all_pricing.extend(pricing)
        
        return {
            "provider": "gcp",
            "machine_types": machine_types,
            "pricing": all_pricing,
            "regions": regions,
            "fetched_at": datetime.utcnow().isoformat(),
        }

