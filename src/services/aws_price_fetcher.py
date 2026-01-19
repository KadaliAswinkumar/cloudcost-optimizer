"""
AWS Price Fetcher Service
Fetches EC2 instance specifications and pricing data from AWS APIs.
"""

import json
import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
import logging

import boto3
from botocore.config import Config

from src.core.config import settings

logger = logging.getLogger(__name__)


class AWSPriceFetcher:
    """
    Fetches EC2 instance data from AWS Pricing and EC2 APIs.
    
    Uses:
    - AWS Pricing API for on-demand and reserved pricing
    - EC2 API for spot prices and instance specifications
    """
    
    # Instance family categories for grouping
    INSTANCE_FAMILIES = {
        "general": ["t", "m", "mac"],
        "compute": ["c"],
        "memory": ["r", "x", "z"],
        "storage": ["d", "h", "i"],
        "accelerated": ["p", "g", "inf", "trn", "dl"],
        "hpc": ["hpc"],
    }
    
    def __init__(self):
        """Initialize AWS clients."""
        self.config = Config(
            region_name="us-east-1",  # Pricing API only available in us-east-1
            retries={"max_attempts": 3, "mode": "adaptive"}
        )
        
        # Initialize clients
        self._pricing_client = None
        self._ec2_clients: Dict[str, Any] = {}
    
    @property
    def pricing_client(self):
        """Lazy initialization of pricing client."""
        if self._pricing_client is None:
            self._pricing_client = boto3.client(
                "pricing",
                config=self.config,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
        return self._pricing_client
    
    def get_ec2_client(self, region: str):
        """Get EC2 client for specific region."""
        if region not in self._ec2_clients:
            self._ec2_clients[region] = boto3.client(
                "ec2",
                region_name=region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
        return self._ec2_clients[region]
    
    async def fetch_instance_types(self) -> List[Dict]:
        """
        Fetch all EC2 instance types with specifications.
        
        Returns:
            List of instance specifications
        """
        logger.info("Fetching EC2 instance types...")
        
        instances = []
        paginator = self.get_ec2_client("us-east-1").get_paginator("describe_instance_types")
        
        try:
            for page in paginator.paginate():
                for instance in page["InstanceTypes"]:
                    parsed = self._parse_instance_type(instance)
                    if parsed:
                        instances.append(parsed)
            
            logger.info(f"Fetched {len(instances)} instance types")
            return instances
            
        except Exception as e:
            logger.error(f"Error fetching instance types: {e}")
            raise
    
    def _parse_instance_type(self, data: Dict) -> Optional[Dict]:
        """Parse instance type data from AWS response."""
        try:
            instance_type = data["InstanceType"]
            family = instance_type.split(".")[0]
            
            # Extract generation from instance type (e.g., t3 -> 3)
            generation = "".join(filter(str.isdigit, family)) or None
            
            # Memory is in MiB, convert to GiB
            memory_gb = data.get("MemoryInfo", {}).get("SizeInMiB", 0) / 1024
            
            # GPU info
            gpu_info = data.get("GpuInfo", {}).get("Gpus", [{}])[0] if data.get("GpuInfo") else {}
            
            # Storage info
            storage_info = data.get("InstanceStorageInfo", {})
            instance_storage = storage_info.get("TotalSizeInGB") if storage_info else None
            
            return {
                "instance_type": instance_type,
                "instance_family": family,
                "generation": generation,
                "vcpus": data.get("VCpuInfo", {}).get("DefaultVCpus", 0),
                "memory_gb": round(memory_gb, 2),
                "processor_architecture": data.get("ProcessorInfo", {}).get("SupportedArchitectures", ["x86_64"])[0],
                "physical_processor": ", ".join(data.get("ProcessorInfo", {}).get("SupportedFeatures", [])),
                "clock_speed_ghz": data.get("ProcessorInfo", {}).get("SustainedClockSpeedInGhz"),
                "storage_type": "Instance Store" if instance_storage else "EBS-Only",
                "instance_storage_gb": instance_storage,
                "network_performance": data.get("NetworkInfo", {}).get("NetworkPerformance", "Unknown"),
                "ebs_bandwidth_mbps": data.get("EbsInfo", {}).get("EbsBandwidthInfo", {}).get("MaximumBandwidthInMbps"),
                "gpu_count": gpu_info.get("Count"),
                "gpu_memory_gb": (gpu_info.get("MemoryInfo", {}).get("SizeInMiB", 0) / 1024) if gpu_info.get("MemoryInfo") else None,
                "gpu_manufacturer": gpu_info.get("Manufacturer"),
                "gpu_name": gpu_info.get("Name"),
                "current_generation": data.get("CurrentGeneration", True),
                "bare_metal": data.get("BareMetal", False),
                "hypervisor": data.get("Hypervisor"),
            }
        except Exception as e:
            logger.warning(f"Error parsing instance type: {e}")
            return None
    
    async def fetch_on_demand_pricing(
        self,
        region: str,
        operating_system: str = "Linux"
    ) -> List[Dict]:
        """
        Fetch on-demand pricing for a region.
        
        Args:
            region: AWS region code
            operating_system: OS type (Linux, Windows, etc.)
            
        Returns:
            List of pricing data
        """
        logger.info(f"Fetching on-demand pricing for {region}...")
        
        # AWS region code to region name mapping
        region_name = self._get_region_name(region)
        
        pricing_data = []
        
        try:
            paginator = self.pricing_client.get_paginator("get_products")
            
            filters = [
                {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": operating_system},
                {"Type": "TERM_MATCH", "Field": "location", "Value": region_name},
                {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "Shared"},
                {"Type": "TERM_MATCH", "Field": "preInstalledSw", "Value": "NA"},
                {"Type": "TERM_MATCH", "Field": "capacitystatus", "Value": "Used"},
            ]
            
            for page in paginator.paginate(
                ServiceCode="AmazonEC2",
                Filters=filters,
                MaxResults=100
            ):
                for price_item in page["PriceList"]:
                    parsed = self._parse_on_demand_price(price_item, region)
                    if parsed:
                        pricing_data.append(parsed)
            
            logger.info(f"Fetched {len(pricing_data)} on-demand prices for {region}")
            return pricing_data
            
        except Exception as e:
            logger.error(f"Error fetching on-demand pricing for {region}: {e}")
            raise
    
    def _parse_on_demand_price(self, price_json: str, region: str) -> Optional[Dict]:
        """Parse on-demand pricing from AWS response."""
        try:
            data = json.loads(price_json) if isinstance(price_json, str) else price_json
            
            product = data.get("product", {})
            attributes = product.get("attributes", {})
            
            instance_type = attributes.get("instanceType")
            if not instance_type:
                return None
            
            # Get pricing
            terms = data.get("terms", {}).get("OnDemand", {})
            if not terms:
                return None
            
            # Get first pricing term
            term = list(terms.values())[0]
            price_dimensions = list(term.get("priceDimensions", {}).values())[0]
            price_per_unit = price_dimensions.get("pricePerUnit", {}).get("USD", "0")
            
            return {
                "instance_type": instance_type,
                "region": region,
                "price_per_hour": Decimal(price_per_unit),
                "operating_system": attributes.get("operatingSystem", "Linux"),
                "tenancy": attributes.get("tenancy", "Shared"),
                "effective_date": datetime.utcnow(),
            }
            
        except Exception as e:
            logger.warning(f"Error parsing on-demand price: {e}")
            return None
    
    async def fetch_spot_prices(
        self,
        region: str,
        instance_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Fetch current spot prices for a region.
        
        Args:
            region: AWS region code
            instance_types: Optional list of specific instance types
            
        Returns:
            List of spot pricing data
        """
        logger.info(f"Fetching spot prices for {region}...")
        
        ec2 = self.get_ec2_client(region)
        spot_prices = []
        
        try:
            params = {
                "ProductDescriptions": ["Linux/UNIX"],
                "MaxResults": 1000,
            }
            
            if instance_types:
                params["InstanceTypes"] = instance_types
            
            paginator = ec2.get_paginator("describe_spot_price_history")
            
            for page in paginator.paginate(**params):
                for spot in page["SpotPriceHistory"]:
                    spot_prices.append({
                        "instance_type": spot["InstanceType"],
                        "availability_zone": spot["AvailabilityZone"],
                        "region": region,
                        "spot_price": Decimal(spot["SpotPrice"]),
                        "timestamp": spot["Timestamp"],
                    })
            
            # Deduplicate to get latest price per instance/AZ
            latest_prices = {}
            for price in spot_prices:
                key = (price["instance_type"], price["availability_zone"])
                if key not in latest_prices or price["timestamp"] > latest_prices[key]["timestamp"]:
                    latest_prices[key] = price
            
            result = list(latest_prices.values())
            logger.info(f"Fetched {len(result)} spot prices for {region}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching spot prices for {region}: {e}")
            raise
    
    async def fetch_spot_price_history(
        self,
        region: str,
        instance_type: str,
        days: int = 30
    ) -> List[Dict]:
        """
        Fetch spot price history for analysis.
        
        Args:
            region: AWS region code
            instance_type: Instance type to fetch history for
            days: Number of days of history
            
        Returns:
            List of historical spot prices
        """
        from datetime import timedelta
        
        ec2 = self.get_ec2_client(region)
        history = []
        
        try:
            start_time = datetime.utcnow() - timedelta(days=days)
            
            paginator = ec2.get_paginator("describe_spot_price_history")
            
            for page in paginator.paginate(
                InstanceTypes=[instance_type],
                ProductDescriptions=["Linux/UNIX"],
                StartTime=start_time,
            ):
                for spot in page["SpotPriceHistory"]:
                    history.append({
                        "instance_type": spot["InstanceType"],
                        "availability_zone": spot["AvailabilityZone"],
                        "spot_price": Decimal(spot["SpotPrice"]),
                        "timestamp": spot["Timestamp"],
                    })
            
            return sorted(history, key=lambda x: x["timestamp"])
            
        except Exception as e:
            logger.error(f"Error fetching spot history: {e}")
            raise
    
    def _get_region_name(self, region_code: str) -> str:
        """Convert AWS region code to display name for Pricing API."""
        region_names = {
            "us-east-1": "US East (N. Virginia)",
            "us-east-2": "US East (Ohio)",
            "us-west-1": "US West (N. California)",
            "us-west-2": "US West (Oregon)",
            "eu-west-1": "EU (Ireland)",
            "eu-west-2": "EU (London)",
            "eu-west-3": "EU (Paris)",
            "eu-central-1": "EU (Frankfurt)",
            "eu-north-1": "EU (Stockholm)",
            "ap-south-1": "Asia Pacific (Mumbai)",
            "ap-southeast-1": "Asia Pacific (Singapore)",
            "ap-southeast-2": "Asia Pacific (Sydney)",
            "ap-northeast-1": "Asia Pacific (Tokyo)",
            "ap-northeast-2": "Asia Pacific (Seoul)",
            "ap-northeast-3": "Asia Pacific (Osaka)",
            "sa-east-1": "South America (Sao Paulo)",
            "ca-central-1": "Canada (Central)",
        }
        return region_names.get(region_code, region_code)
    
    async def fetch_all_pricing_data(
        self,
        regions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch all pricing data for specified regions.
        
        Args:
            regions: List of regions to fetch (defaults to all configured regions)
            
        Returns:
            Dictionary containing all fetched data
        """
        regions = regions or settings.aws_regions
        
        logger.info(f"Starting full price fetch for {len(regions)} regions...")
        
        # Fetch instance types first
        instance_types = await self.fetch_instance_types()
        
        # Fetch pricing for all regions
        all_on_demand = []
        all_spot = []
        
        for region in regions:
            try:
                on_demand = await self.fetch_on_demand_pricing(region)
                all_on_demand.extend(on_demand)
                
                spot = await self.fetch_spot_prices(region)
                all_spot.extend(spot)
                
            except Exception as e:
                logger.error(f"Error fetching data for {region}: {e}")
                continue
        
        return {
            "instance_types": instance_types,
            "on_demand_pricing": all_on_demand,
            "spot_pricing": all_spot,
            "fetched_at": datetime.utcnow().isoformat(),
            "regions": regions,
        }

