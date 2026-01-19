"""
Azure Price Fetcher Service
Fetches Microsoft Azure VM specifications and pricing.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from src.core.config import settings
from src.models.cloud_provider import CloudProvider, AZURE_REGIONS

logger = logging.getLogger(__name__)


class AzurePriceFetcher:
    """
    Fetches Azure VM instance data.
    
    Uses:
    - Azure Compute API for VM sizes
    - Azure Retail Prices API for pricing
    """
    
    # Azure VM Series Categories
    VM_SERIES = {
        "general_purpose": ["A", "B", "D", "DC", "Ds", "Dv2", "Dv3", "Dv4", "Dv5", "Dasv4", "Dasv5", "Dadsv5"],
        "compute_optimized": ["F", "Fs", "Fsv2", "Fx"],
        "memory_optimized": ["E", "Ev3", "Ev4", "Ev5", "Easv4", "Easv5", "Eadsv5", "M", "Mv2", "Msv2"],
        "storage_optimized": ["L", "Ls", "Lsv2", "Lsv3"],
        "gpu": ["NC", "NCv2", "NCv3", "ND", "NDv2", "NV", "NVv3", "NVv4", "NCasT4_v3"],
        "high_performance": ["H", "HB", "HBv2", "HBv3", "HC"],
    }
    
    # Standard VM sizes (simplified for demo)
    STANDARD_VM_SIZES = {
        # B Series (Burstable)
        "Standard_B1s": {"vcpus": 1, "memory_gb": 1, "burstable": True},
        "Standard_B1ms": {"vcpus": 1, "memory_gb": 2, "burstable": True},
        "Standard_B2s": {"vcpus": 2, "memory_gb": 4, "burstable": True},
        "Standard_B2ms": {"vcpus": 2, "memory_gb": 8, "burstable": True},
        "Standard_B4ms": {"vcpus": 4, "memory_gb": 16, "burstable": True},
        "Standard_B8ms": {"vcpus": 8, "memory_gb": 32, "burstable": True},
        
        # D Series v4 (General Purpose)
        "Standard_D2s_v4": {"vcpus": 2, "memory_gb": 8},
        "Standard_D4s_v4": {"vcpus": 4, "memory_gb": 16},
        "Standard_D8s_v4": {"vcpus": 8, "memory_gb": 32},
        "Standard_D16s_v4": {"vcpus": 16, "memory_gb": 64},
        "Standard_D32s_v4": {"vcpus": 32, "memory_gb": 128},
        "Standard_D48s_v4": {"vcpus": 48, "memory_gb": 192},
        "Standard_D64s_v4": {"vcpus": 64, "memory_gb": 256},
        
        # D Series v5 (Latest General Purpose)
        "Standard_D2s_v5": {"vcpus": 2, "memory_gb": 8},
        "Standard_D4s_v5": {"vcpus": 4, "memory_gb": 16},
        "Standard_D8s_v5": {"vcpus": 8, "memory_gb": 32},
        "Standard_D16s_v5": {"vcpus": 16, "memory_gb": 64},
        "Standard_D32s_v5": {"vcpus": 32, "memory_gb": 128},
        
        # E Series v4 (Memory Optimized)
        "Standard_E2s_v4": {"vcpus": 2, "memory_gb": 16},
        "Standard_E4s_v4": {"vcpus": 4, "memory_gb": 32},
        "Standard_E8s_v4": {"vcpus": 8, "memory_gb": 64},
        "Standard_E16s_v4": {"vcpus": 16, "memory_gb": 128},
        "Standard_E32s_v4": {"vcpus": 32, "memory_gb": 256},
        "Standard_E48s_v4": {"vcpus": 48, "memory_gb": 384},
        "Standard_E64s_v4": {"vcpus": 64, "memory_gb": 504},
        
        # E Series v5 (Latest Memory Optimized)
        "Standard_E2s_v5": {"vcpus": 2, "memory_gb": 16},
        "Standard_E4s_v5": {"vcpus": 4, "memory_gb": 32},
        "Standard_E8s_v5": {"vcpus": 8, "memory_gb": 64},
        "Standard_E16s_v5": {"vcpus": 16, "memory_gb": 128},
        
        # F Series v2 (Compute Optimized)
        "Standard_F2s_v2": {"vcpus": 2, "memory_gb": 4, "category": "compute_optimized"},
        "Standard_F4s_v2": {"vcpus": 4, "memory_gb": 8, "category": "compute_optimized"},
        "Standard_F8s_v2": {"vcpus": 8, "memory_gb": 16, "category": "compute_optimized"},
        "Standard_F16s_v2": {"vcpus": 16, "memory_gb": 32, "category": "compute_optimized"},
        "Standard_F32s_v2": {"vcpus": 32, "memory_gb": 64, "category": "compute_optimized"},
        "Standard_F48s_v2": {"vcpus": 48, "memory_gb": 96, "category": "compute_optimized"},
        "Standard_F64s_v2": {"vcpus": 64, "memory_gb": 128, "category": "compute_optimized"},
        "Standard_F72s_v2": {"vcpus": 72, "memory_gb": 144, "category": "compute_optimized"},
        
        # L Series v2 (Storage Optimized)
        "Standard_L8s_v2": {"vcpus": 8, "memory_gb": 64, "local_ssd_gb": 1920, "category": "storage_optimized"},
        "Standard_L16s_v2": {"vcpus": 16, "memory_gb": 128, "local_ssd_gb": 3840, "category": "storage_optimized"},
        "Standard_L32s_v2": {"vcpus": 32, "memory_gb": 256, "local_ssd_gb": 7680, "category": "storage_optimized"},
        "Standard_L48s_v2": {"vcpus": 48, "memory_gb": 384, "local_ssd_gb": 11520, "category": "storage_optimized"},
        "Standard_L64s_v2": {"vcpus": 64, "memory_gb": 512, "local_ssd_gb": 15360, "category": "storage_optimized"},
        
        # NC Series (GPU - NVIDIA Tesla)
        "Standard_NC6s_v3": {"vcpus": 6, "memory_gb": 112, "gpu_count": 1, "gpu_type": "NVIDIA V100"},
        "Standard_NC12s_v3": {"vcpus": 12, "memory_gb": 224, "gpu_count": 2, "gpu_type": "NVIDIA V100"},
        "Standard_NC24s_v3": {"vcpus": 24, "memory_gb": 448, "gpu_count": 4, "gpu_type": "NVIDIA V100"},
        
        # NCas T4 v3 (GPU - NVIDIA T4)
        "Standard_NC4as_T4_v3": {"vcpus": 4, "memory_gb": 28, "gpu_count": 1, "gpu_type": "NVIDIA T4"},
        "Standard_NC8as_T4_v3": {"vcpus": 8, "memory_gb": 56, "gpu_count": 1, "gpu_type": "NVIDIA T4"},
        "Standard_NC16as_T4_v3": {"vcpus": 16, "memory_gb": 110, "gpu_count": 1, "gpu_type": "NVIDIA T4"},
        "Standard_NC64as_T4_v3": {"vcpus": 64, "memory_gb": 440, "gpu_count": 4, "gpu_type": "NVIDIA T4"},
    }
    
    # Base pricing (USD/hour) - approximate
    BASE_PRICING = {
        "Standard_B1s": 0.0104,
        "Standard_B1ms": 0.0207,
        "Standard_B2s": 0.0416,
        "Standard_B2ms": 0.0832,
        "Standard_B4ms": 0.1660,
        "Standard_B8ms": 0.3320,
        "Standard_D2s_v4": 0.0960,
        "Standard_D4s_v4": 0.1920,
        "Standard_D8s_v4": 0.3840,
        "Standard_D16s_v4": 0.7680,
        "Standard_D32s_v4": 1.5360,
        "Standard_D48s_v4": 2.3040,
        "Standard_D64s_v4": 3.0720,
        "Standard_D2s_v5": 0.0960,
        "Standard_D4s_v5": 0.1920,
        "Standard_D8s_v5": 0.3840,
        "Standard_D16s_v5": 0.7680,
        "Standard_D32s_v5": 1.5360,
        "Standard_E2s_v4": 0.1260,
        "Standard_E4s_v4": 0.2520,
        "Standard_E8s_v4": 0.5040,
        "Standard_E16s_v4": 1.0080,
        "Standard_E32s_v4": 2.0160,
        "Standard_E48s_v4": 3.0240,
        "Standard_E64s_v4": 4.0320,
        "Standard_E2s_v5": 0.1260,
        "Standard_E4s_v5": 0.2520,
        "Standard_E8s_v5": 0.5040,
        "Standard_E16s_v5": 1.0080,
        "Standard_F2s_v2": 0.0846,
        "Standard_F4s_v2": 0.1690,
        "Standard_F8s_v2": 0.3380,
        "Standard_F16s_v2": 0.6770,
        "Standard_F32s_v2": 1.3530,
        "Standard_F48s_v2": 2.0300,
        "Standard_F64s_v2": 2.7060,
        "Standard_F72s_v2": 3.0450,
        "Standard_L8s_v2": 0.6240,
        "Standard_L16s_v2": 1.2480,
        "Standard_L32s_v2": 2.4960,
        "Standard_L48s_v2": 3.7440,
        "Standard_L64s_v2": 4.9920,
        "Standard_NC6s_v3": 3.0600,
        "Standard_NC12s_v3": 6.1200,
        "Standard_NC24s_v3": 12.2400,
        "Standard_NC4as_T4_v3": 0.5260,
        "Standard_NC8as_T4_v3": 0.7520,
        "Standard_NC16as_T4_v3": 1.2040,
        "Standard_NC64as_T4_v3": 4.3520,
    }
    
    # Regional price multipliers
    REGION_MULTIPLIERS = {
        "eastus": 1.0,
        "eastus2": 1.0,
        "westus": 1.0,
        "westus2": 1.0,
        "centralus": 1.0,
        "northeurope": 1.08,
        "westeurope": 1.12,
        "uksouth": 1.10,
        "eastasia": 1.15,
        "southeastasia": 1.08,
        "japaneast": 1.18,
        "australiaeast": 1.15,
        "brazilsouth": 1.45,
        "centralindia": 1.05,
    }
    
    def __init__(self):
        """Initialize Azure client."""
        self._compute_client = None
        self._pricing_client = None
    
    async def fetch_vm_sizes(self) -> List[Dict]:
        """
        Fetch all Azure VM sizes with specifications.
        
        Returns:
            List of VM size specifications
        """
        logger.info("Fetching Azure VM sizes...")
        
        vm_sizes = []
        
        for vm_size, specs in self.STANDARD_VM_SIZES.items():
            # Parse series from VM name
            parts = vm_size.replace("Standard_", "").split("_")
            series = parts[0][:2] if parts else "D"
            
            # Determine category
            category = specs.get("category", "general_purpose")
            for cat, series_list in self.VM_SERIES.items():
                if any(series.startswith(s) for s in series_list):
                    category = cat
                    break
            
            vm_sizes.append({
                "provider": CloudProvider.AZURE.value,
                "instance_type": vm_size,
                "instance_family": series,
                "display_name": vm_size.replace("Standard_", "").replace("_", " "),
                "vcpus": specs["vcpus"],
                "memory_gb": specs["memory_gb"],
                "processor_architecture": "x86_64",
                "local_ssd_gb": specs.get("local_ssd_gb"),
                "category": category,
                "is_burstable": specs.get("burstable", False),
                "supports_spot": True,
                "gpu_count": specs.get("gpu_count"),
                "gpu_type": specs.get("gpu_type"),
                "is_current_generation": "v4" in vm_size or "v5" in vm_size or "v3" in vm_size,
            })
        
        logger.info(f"Fetched {len(vm_sizes)} Azure VM sizes")
        return vm_sizes
    
    async def fetch_pricing(
        self,
        region: str = "eastus"
    ) -> List[Dict]:
        """
        Fetch Azure pricing for a region.
        
        Args:
            region: Azure region
            
        Returns:
            List of pricing data
        """
        logger.info(f"Fetching Azure pricing for {region}...")
        
        pricing_data = []
        multiplier = self.REGION_MULTIPLIERS.get(region, 1.1)
        
        for vm_size, base_price in self.BASE_PRICING.items():
            # Pay-as-you-go pricing
            hourly_price = base_price * multiplier
            
            pricing_data.append({
                "provider": CloudProvider.AZURE.value,
                "instance_type": vm_size,
                "region": region,
                "pricing_type": "on_demand",
                "os_type": "linux",
                "hourly_price": Decimal(str(round(hourly_price, 6))),
                "monthly_price": Decimal(str(round(hourly_price * 730, 2))),
                "currency": "USD",
                "effective_date": datetime.utcnow(),
            })
            
            # Spot pricing (60-90% discount)
            spot_price = hourly_price * 0.35  # ~65% discount average
            pricing_data.append({
                "provider": CloudProvider.AZURE.value,
                "instance_type": vm_size,
                "region": region,
                "pricing_type": "spot",
                "os_type": "linux",
                "hourly_price": Decimal(str(round(spot_price, 6))),
                "monthly_price": Decimal(str(round(spot_price * 730, 2))),
                "currency": "USD",
                "effective_date": datetime.utcnow(),
            })
            
            # Reserved (1 year - ~35% discount)
            reserved_1yr_price = hourly_price * 0.65
            pricing_data.append({
                "provider": CloudProvider.AZURE.value,
                "instance_type": vm_size,
                "region": region,
                "pricing_type": "reserved_1yr",
                "os_type": "linux",
                "hourly_price": Decimal(str(round(reserved_1yr_price, 6))),
                "monthly_price": Decimal(str(round(reserved_1yr_price * 730, 2))),
                "commitment_term": "1yr",
                "currency": "USD",
                "effective_date": datetime.utcnow(),
            })
            
            # Reserved (3 year - ~55% discount)
            reserved_3yr_price = hourly_price * 0.45
            pricing_data.append({
                "provider": CloudProvider.AZURE.value,
                "instance_type": vm_size,
                "region": region,
                "pricing_type": "reserved_3yr",
                "os_type": "linux",
                "hourly_price": Decimal(str(round(reserved_3yr_price, 6))),
                "monthly_price": Decimal(str(round(reserved_3yr_price * 730, 2))),
                "commitment_term": "3yr",
                "currency": "USD",
                "effective_date": datetime.utcnow(),
            })
        
        logger.info(f"Generated {len(pricing_data)} Azure pricing records for {region}")
        return pricing_data
    
    async def fetch_all_pricing(
        self,
        regions: Optional[List[str]] = None
    ) -> Dict:
        """
        Fetch all Azure pricing data.
        
        Args:
            regions: List of regions (defaults to primary regions)
            
        Returns:
            Dictionary with VM sizes and pricing
        """
        regions = regions or [
            "eastus", "westus2", "centralus",
            "northeurope", "westeurope",
            "southeastasia", "japaneast"
        ]
        
        vm_sizes = await self.fetch_vm_sizes()
        
        all_pricing = []
        for region in regions:
            pricing = await self.fetch_pricing(region)
            all_pricing.extend(pricing)
        
        return {
            "provider": "azure",
            "vm_sizes": vm_sizes,
            "pricing": all_pricing,
            "regions": regions,
            "fetched_at": datetime.utcnow().isoformat(),
        }

