"""
Web scraper for real-time cloud pricing
Scrapes official pricing pages for GCP and Azure
"""

import asyncio
import httpx
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from decimal import Decimal
import json
import re

logger = logging.getLogger(__name__)


class AzureRealPricingScraper:
    """
    Scrapes Azure pricing from official Azure Retail Prices API
    (This is actually an API, not scraping, but it's public and free!)
    """
    
    BASE_URL = "https://prices.azure.com/api/retail/prices"
    
    async def fetch_vm_pricing(self, region: str = "eastus") -> List[Dict]:
        """
        Fetch real Azure VM pricing from Microsoft's public API
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "currencyCode": "USD",
                    "armRegionName": region,
                    "$filter": "serviceName eq 'Virtual Machines' and priceType eq 'Consumption'"
                }
                
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                
                data = response.json()
                pricing_data = []
                
                for item in data.get("Items", []):
                    # Extract instance type from product name
                    product_name = item.get("armSkuName", "")
                    if not product_name:
                        continue
                    
                    pricing_data.append({
                        "provider": "azure",
                        "instance_type": product_name,
                        "region": region,
                        "pricing_type": "on_demand",
                        "os_type": "linux" if "Linux" in item.get("productName", "") else "windows",
                        "hourly_price": float(item.get("retailPrice", 0)),
                        "currency": item.get("currencyCode", "USD"),
                        "effective_date": item.get("effectiveStartDate"),
                    })
                
                logger.info(f"Fetched {len(pricing_data)} Azure prices for {region}")
                return pricing_data
                
        except Exception as e:
            logger.error(f"Failed to fetch Azure pricing for {region}: {e}")
            return []


class GCPRealPricingScraper:
    """
    Scrapes GCP pricing from official pricing pages
    Uses GCP's pricing calculator JSON endpoints
    """
    
    # GCP exposes pricing data via their calculator's API
    PRICING_API = "https://cloudpricingcalculator.appspot.com/static/data/pricelist.json"
    
    async def fetch_compute_pricing(self, region: str = "us-central1") -> List[Dict]:
        """
        Fetch real GCP Compute Engine pricing
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.PRICING_API)
                response.raise_for_status()
                
                data = response.json()
                pricing_data = []
                
                # GCP pricing structure: data['gcp_price_list']['CP-COMPUTEENGINE-VMIMAGE-*']
                compute_prices = {k: v for k, v in data.get("gcp_price_list", {}).items() 
                                if k.startswith("CP-COMPUTEENGINE")}
                
                # Parse pricing for different machine types
                for key, price_info in compute_prices.items():
                    # Extract machine type and region from key
                    # Example key: "CP-COMPUTEENGINE-VMIMAGE-N1-STANDARD-1"
                    parts = key.split("-")
                    
                    if len(parts) < 5:
                        continue
                    
                    machine_family = parts[3].lower()
                    machine_type_parts = parts[4:]
                    
                    # Reconstruct machine type (e.g., n1-standard-1)
                    if machine_type_parts:
                        vcpus = machine_type_parts[-1] if machine_type_parts[-1].isdigit() else "1"
                        type_name = "-".join(machine_type_parts[:-1]).lower() if len(machine_type_parts) > 1 else "standard"
                        machine_type = f"{machine_family}-{type_name}-{vcpus}"
                    else:
                        continue
                    
                    # Get pricing for specified region
                    region_prices = price_info.get(region, price_info.get("us", {}))
                    hourly_price = float(region_prices) if isinstance(region_prices, (int, float)) else 0
                    
                    if hourly_price > 0:
                        pricing_data.append({
                            "provider": "gcp",
                            "instance_type": machine_type,
                            "region": region,
                            "pricing_type": "on_demand",
                            "os_type": "linux",
                            "hourly_price": hourly_price,
                            "currency": "USD",
                        })
                
                logger.info(f"Fetched {len(pricing_data)} GCP prices for {region}")
                return pricing_data
                
        except Exception as e:
            logger.error(f"Failed to fetch GCP pricing for {region}: {e}")
            return []


class CloudPricingScraper:
    """
    Main scraper orchestrator
    """
    
    def __init__(self):
        self.azure_scraper = AzureRealPricingScraper()
        self.gcp_scraper = GCPRealPricingScraper()
    
    async def fetch_all_pricing(self, regions: Dict[str, List[str]]) -> Dict[str, List[Dict]]:
        """
        Fetch pricing from all providers
        
        Args:
            regions: Dict with provider as key and list of regions as value
        
        Returns:
            Dict with provider as key and pricing data as value
        """
        results = {
            "azure": [],
            "gcp": []
        }
        
        # Fetch Azure pricing
        if "azure" in regions:
            for region in regions["azure"]:
                pricing = await self.azure_scraper.fetch_vm_pricing(region)
                results["azure"].extend(pricing)
        
        # Fetch GCP pricing
        if "gcp" in regions:
            for region in regions["gcp"]:
                pricing = await self.gcp_scraper.fetch_compute_pricing(region)
                results["gcp"].extend(pricing)
        
        return results


# Example usage
async def main():
    scraper = CloudPricingScraper()
    
    regions = {
        "azure": ["eastus", "westus", "westeurope"],
        "gcp": ["us-central1", "us-east1", "europe-west1"]
    }
    
    pricing = await scraper.fetch_all_pricing(regions)
    
    print(f"Azure pricing records: {len(pricing['azure'])}")
    print(f"GCP pricing records: {len(pricing['gcp'])}")


if __name__ == "__main__":
    asyncio.run(main())
