"""
Multi-Cloud Recommendation Engine
Generates cost-optimized recommendations across AWS, GCP, and Azure.
"""

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.cloud_provider import CloudProvider, CloudInstance, CloudPricing
from src.services.cost_calculator import CostCalculator
from src.core.cache import get_redis_client

logger = logging.getLogger(__name__)


@dataclass
class MultiCloudRequirements:
    """Input requirements for multi-cloud recommendations."""
    min_vcpus: int
    min_memory_gb: float
    max_vcpus: Optional[int] = None
    max_memory_gb: Optional[float] = None
    
    # Cloud provider preferences
    providers: Optional[List[str]] = None  # aws, gcp, azure (None = all)
    
    # Region preferences (per provider)
    aws_regions: Optional[List[str]] = None
    gcp_regions: Optional[List[str]] = None
    azure_regions: Optional[List[str]] = None
    
    # Workload characteristics
    workload_type: str = "steady"  # steady, variable, burst, batch
    spot_eligible: bool = False
    hours_per_month: int = 730
    
    # Interruption tolerance for spot/preemptible instances
    # none: no interruptions (don't recommend spot)
    # low: only stable spot instances
    # medium: moderate interruption OK
    # high: fully fault-tolerant workloads
    interruption_tolerance: str = "medium"
    
    # Budget constraints
    max_hourly_cost: Optional[float] = None
    max_monthly_budget: Optional[float] = None
    
    # Instance preferences
    requires_gpu: bool = False
    gpu_type: Optional[str] = None
    exclude_burstable: bool = False
    
    def to_hash(self) -> str:
        """Generate hash for caching."""
        data = {
            "vcpus": (self.min_vcpus, self.max_vcpus),
            "memory": (self.min_memory_gb, self.max_memory_gb),
            "providers": sorted(self.providers) if self.providers else None,
            "workload": self.workload_type,
            "spot": self.spot_eligible,
            "gpu": self.requires_gpu,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


class MultiCloudRecommender:
    """
    Generates recommendations across AWS, GCP, and Azure.
    
    Features:
    - Cross-cloud cost comparison
    - Equivalent instance mapping
    - Multi-cloud optimization
    - Provider-specific pricing strategies
    """
    
    # Scoring weights
    WEIGHTS = {
        "cost": 0.35,
        "fit": 0.25,
        "risk": 0.20,          # Interruption risk for spot/preemptible
        "performance": 0.20,
    }
    
    # Known interruption risk data by provider
    # Based on published data and empirical analysis
    PROVIDER_INTERRUPTION_DATA = {
        "aws": {
            # AWS Spot interruption rates vary by instance type
            "general_purpose": {"risk": 25, "level": "low"},     # t3, m5, m6i
            "compute_optimized": {"risk": 35, "level": "medium"}, # c5, c6i
            "memory_optimized": {"risk": 30, "level": "low"},    # r5, r6i
            "gpu": {"risk": 55, "level": "high"},                # p3, g4
            "unknown": {"risk": 40, "level": "medium"},
        },
        "gcp": {
            # GCP Preemptible VMs have MAX 24h lifetime, but lower interruption otherwise
            "general_purpose": {"risk": 30, "level": "medium"},  # n2, e2
            "compute_optimized": {"risk": 35, "level": "medium"}, # c2
            "memory_optimized": {"risk": 35, "level": "medium"}, # m2, n2-highmem
            "gpu": {"risk": 60, "level": "high"},                # a2, n1+gpu
            "unknown": {"risk": 40, "level": "medium"},
            "note": "Preemptible VMs have max 24h lifetime",
        },
        "azure": {
            # Azure Spot VMs - similar to AWS
            "general_purpose": {"risk": 30, "level": "medium"},  # D, Ds series
            "compute_optimized": {"risk": 40, "level": "medium"}, # F series
            "memory_optimized": {"risk": 35, "level": "medium"}, # E series
            "gpu": {"risk": 60, "level": "high"},                # NC, ND series
            "unknown": {"risk": 40, "level": "medium"},
        },
    }
    
    MAX_RECOMMENDATIONS = 15
    
    # Provider display names
    PROVIDER_NAMES = {
        "aws": "Amazon Web Services",
        "gcp": "Google Cloud Platform",
        "azure": "Microsoft Azure",
    }
    
    def __init__(self, db_session: AsyncSession):
        """Initialize recommender."""
        self.db = db_session
        self.cost_calculator = CostCalculator()
    
    async def generate_recommendations(
        self,
        requirements: MultiCloudRequirements,
    ) -> Dict:
        """
        Generate multi-cloud recommendations with Redis caching.
        
        Args:
            requirements: Multi-cloud workload requirements
            
        Returns:
            Recommendations grouped by provider with cross-cloud comparison
        """
        logger.info(f"Generating multi-cloud recommendations: {requirements}")
        
        # Try to get from cache
        cache_key = f"multicloud:recommendations:{requirements.to_hash()}"
        redis = await get_redis_client()
        
        if redis:
            try:
                cached = await redis.get(cache_key)
                if cached:
                    logger.info(f"Cache HIT for recommendations: {cache_key}")
                    return json.loads(cached)
                logger.info(f"Cache MISS for recommendations: {cache_key}")
            except Exception as e:
                logger.warning(f"Redis cache read error: {e}")
        
        # Generate recommendations
        providers = requirements.providers or ["aws", "gcp", "azure"]
        
        # Find matching instances across all providers
        all_candidates = []
        
        for provider in providers:
            instances = await self._find_matching_instances(provider, requirements)
            candidates = await self._get_pricing_candidates(instances, provider, requirements)
            all_candidates.extend(candidates)
        
        if not all_candidates:
            return {
                "error": "No matching instances found across providers",
                "requirements": {
                    "min_vcpus": requirements.min_vcpus,
                    "min_memory_gb": requirements.min_memory_gb,
                },
            }
        
        # Score and rank all candidates
        scored = self._score_candidates(all_candidates, requirements)
        
        # Group by provider
        by_provider = {"aws": [], "gcp": [], "azure": []}
        for candidate in scored:
            provider = candidate["provider"]
            if provider in by_provider:
                by_provider[provider].append(candidate)
        
        # Get top recommendations per provider
        top_per_provider = {}
        for provider, candidates in by_provider.items():
            if candidates:
                top_per_provider[provider] = candidates[:5]
        
        # Overall best recommendations
        overall_best = sorted(scored, key=lambda x: x["score"], reverse=True)[:self.MAX_RECOMMENDATIONS]
        
        # Calculate savings comparison
        comparison = self._calculate_cross_cloud_comparison(overall_best, requirements)
        
        result = {
            "requirements_summary": {
                "min_vcpus": requirements.min_vcpus,
                "min_memory_gb": requirements.min_memory_gb,
                "providers": providers,
                "spot_eligible": requirements.spot_eligible,
                "hours_per_month": requirements.hours_per_month,
            },
            "overall_best": [self._format_recommendation(c, rank+1) for rank, c in enumerate(overall_best)],
            "by_provider": {
                provider: [self._format_recommendation(c, rank+1) for rank, c in enumerate(candidates)]
                for provider, candidates in top_per_provider.items()
            },
            "cross_cloud_comparison": comparison,
            "generated_at": datetime.utcnow().isoformat(),
        }
        
        # Cache the result for 10 minutes (600 seconds)
        if redis:
            try:
                await redis.setex(
                    cache_key,
                    600,  # 10 minutes
                    json.dumps(result, default=str)
                )
                logger.info(f"Cached recommendations for 10 minutes: {cache_key}")
            except Exception as e:
                logger.warning(f"Redis cache write error: {e}")
        
        return result
    
    async def _find_matching_instances(
        self,
        provider: str,
        requirements: MultiCloudRequirements
    ) -> List[CloudInstance]:
        """Find instances matching requirements for a provider."""
        
        conditions = [
            CloudInstance.provider == provider,
            CloudInstance.vcpus >= requirements.min_vcpus,
            CloudInstance.memory_gb >= requirements.min_memory_gb,
        ]
        
        if requirements.max_vcpus:
            conditions.append(CloudInstance.vcpus <= requirements.max_vcpus)
        if requirements.max_memory_gb:
            conditions.append(CloudInstance.memory_gb <= requirements.max_memory_gb)
        
        if requirements.requires_gpu:
            conditions.append(CloudInstance.gpu_count > 0)
            if requirements.gpu_type:
                conditions.append(CloudInstance.gpu_type.ilike(f"%{requirements.gpu_type}%"))
        else:
            conditions.append(or_(
                CloudInstance.gpu_count == None,
                CloudInstance.gpu_count == 0
            ))
        
        if requirements.exclude_burstable:
            conditions.append(CloudInstance.is_burstable == False)
        
        query = select(CloudInstance).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _get_pricing_candidates(
        self,
        instances: List[CloudInstance],
        provider: str,
        requirements: MultiCloudRequirements
    ) -> List[Dict]:
        """Get pricing for instances."""
        
        if not instances:
            return []
        
        # Determine regions for this provider
        regions = self._get_regions_for_provider(provider, requirements)
        
        instance_types = [i.instance_type for i in instances]
        
        # Get pricing
        pricing_query = select(CloudPricing).where(
            CloudPricing.provider == provider,
            CloudPricing.instance_type.in_(instance_types),
            CloudPricing.region.in_(regions),
        )
        result = await self.db.execute(pricing_query)
        all_pricing = result.scalars().all()
        
        # Group pricing by instance/region
        pricing_map = {}
        for p in all_pricing:
            key = (p.instance_type, p.region)
            if key not in pricing_map:
                pricing_map[key] = {}
            pricing_map[key][p.pricing_type] = p
        
        # Build candidates
        candidates = []
        instance_map = {i.instance_type: i for i in instances}
        
        for (instance_type, region), pricing in pricing_map.items():
            instance = instance_map.get(instance_type)
            if not instance:
                continue
            
            on_demand = pricing.get("on_demand")
            if not on_demand:
                continue
            
            # Apply budget filter
            if requirements.max_hourly_cost:
                if float(on_demand.hourly_price) > requirements.max_hourly_cost:
                    continue
            
            spot = pricing.get("spot") or pricing.get("preemptible")
            reserved_1yr = pricing.get("reserved_1yr") or pricing.get("committed_1yr")
            reserved_3yr = pricing.get("reserved_3yr") or pricing.get("committed_3yr")
            
            candidates.append({
                "provider": provider,
                "instance": instance,
                "region": region,
                "on_demand": on_demand,
                "spot": spot,
                "reserved_1yr": reserved_1yr,
                "reserved_3yr": reserved_3yr,
            })
        
        return candidates
    
    def _get_regions_for_provider(
        self,
        provider: str,
        requirements: MultiCloudRequirements
    ) -> List[str]:
        """Get regions to query for a provider."""
        if provider == "aws":
            return requirements.aws_regions or ["us-east-1", "us-west-2", "eu-west-1"]
        elif provider == "gcp":
            return requirements.gcp_regions or ["us-central1", "us-east1", "europe-west1"]
        elif provider == "azure":
            return requirements.azure_regions or ["eastus", "westus2", "northeurope"]
        return []
    
    def _score_candidates(
        self,
        candidates: List[Dict],
        requirements: MultiCloudRequirements
    ) -> List[Dict]:
        """Score and rank all candidates, including interruption risk."""
        
        scored = []
        
        for candidate in candidates:
            instance = candidate["instance"]
            on_demand = candidate["on_demand"]
            spot = candidate["spot"]
            reserved_1yr = candidate["reserved_1yr"]
            provider = candidate["provider"]
            
            # Determine best pricing strategy
            interruption_risk = None
            
            if requirements.spot_eligible and spot:
                # Calculate interruption risk for spot/preemptible
                interruption_risk = self._estimate_interruption_risk(
                    provider, instance, requirements.interruption_tolerance
                )
                
                # FILTER OUT if risk exceeds tolerance
                if not self._is_risk_acceptable(interruption_risk, requirements.interruption_tolerance):
                    continue
                
                best_price = spot.hourly_price
                strategy = "spot"
            elif requirements.workload_type == "steady" and reserved_1yr:
                best_price = reserved_1yr.hourly_price
                strategy = "reserved_1yr"
            else:
                best_price = on_demand.hourly_price
                strategy = "on_demand"
            
            monthly_cost = float(best_price) * requirements.hours_per_month
            
            # Apply monthly budget filter
            if requirements.max_monthly_budget and monthly_cost > requirements.max_monthly_budget:
                continue
            
            # Calculate scores
            cost_score = self._calculate_cost_score(best_price, on_demand.hourly_price)
            fit_score = self._calculate_fit_score(instance, requirements)
            perf_score = self._calculate_performance_score(instance)
            
            # Risk score (100 = safe, 0 = very risky)
            # Only applies to spot instances
            if strategy == "spot" and interruption_risk:
                risk_score = 100 - interruption_risk["risk_score"]
            else:
                risk_score = 100  # On-demand/reserved = no interruption risk
            
            # Composite score
            score = (
                self.WEIGHTS["cost"] * cost_score +
                self.WEIGHTS["fit"] * fit_score +
                self.WEIGHTS["performance"] * perf_score +
                self.WEIGHTS["risk"] * risk_score
            )
            
            scored.append({
                **candidate,
                "best_price": best_price,
                "strategy": strategy,
                "monthly_cost": monthly_cost,
                "cost_score": cost_score,
                "fit_score": fit_score,
                "perf_score": perf_score,
                "risk_score": risk_score,
                "interruption_risk": interruption_risk,
                "score": score,
            })
        
        return sorted(scored, key=lambda x: x["score"], reverse=True)
    
    def _estimate_interruption_risk(
        self,
        provider: str,
        instance: CloudInstance,
        tolerance: str
    ) -> Dict:
        """
        Estimate interruption risk for spot/preemptible instances.
        
        This uses provider-level data and instance category to estimate risk.
        For AWS, we could enhance this with real-time data from SpotPriceTracker.
        
        Returns:
            {
                "risk_score": 0-100 (higher = more risky),
                "risk_level": "low" | "medium" | "high" | "very_high",
                "provider_notes": str,
                "interruption_frequency": str,
                "recommendations": [str]
            }
        """
        provider_data = self.PROVIDER_INTERRUPTION_DATA.get(provider, {})
        
        # Determine instance category
        category = instance.category.lower() if instance.category else "unknown"
        
        if "general" in category or "standard" in category:
            risk_data = provider_data.get("general_purpose", provider_data.get("unknown", {}))
        elif "compute" in category:
            risk_data = provider_data.get("compute_optimized", provider_data.get("unknown", {}))
        elif "memory" in category:
            risk_data = provider_data.get("memory_optimized", provider_data.get("unknown", {}))
        elif "gpu" in category or instance.gpu_count:
            risk_data = provider_data.get("gpu", provider_data.get("unknown", {}))
        else:
            risk_data = provider_data.get("unknown", {"risk": 40, "level": "medium"})
        
        risk_score = risk_data.get("risk", 40)
        risk_level = risk_data.get("level", "medium")
        
        # Estimate interruption frequency
        freq_map = {
            "low": "<5% - Rare interruptions expected",
            "medium": "5-15% - Occasional interruptions",
            "high": "15-30% - Frequent interruptions likely",
            "very_high": ">30% - Very frequent interruptions",
        }
        
        # Generate recommendations
        recommendations = []
        
        if risk_level in ["high", "very_high"]:
            recommendations.append("⚠️ Use checkpointing to save progress frequently")
            recommendations.append("Consider Spot Fleet / Instance Pools for diversification")
        
        if provider == "gcp":
            recommendations.append("📌 GCP: Preemptible VMs have max 24h lifetime")
        
        if risk_level == "low":
            recommendations.append("✅ Good candidate for spot/preemptible usage")
        
        # Provider-specific notes
        provider_notes = {
            "aws": "AWS Spot: 2-minute interruption notice via instance metadata",
            "gcp": "GCP Preemptible: 30-second warning, max 24h runtime",
            "azure": "Azure Spot: Eviction notice via scheduled events API",
        }
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "provider_notes": provider_notes.get(provider, ""),
            "interruption_frequency": freq_map.get(risk_level, "Unknown"),
            "recommendations": recommendations,
        }
    
    def _is_risk_acceptable(self, risk_data: Dict, tolerance: str) -> bool:
        """Check if interruption risk is acceptable for user's tolerance."""
        if not risk_data:
            return True
        
        risk_score = risk_data.get("risk_score", 50)
        risk_level = risk_data.get("risk_level", "medium")
        
        # Tolerance thresholds
        thresholds = {
            "none": 0,      # Don't recommend spot at all
            "low": 25,      # Only very stable spot
            "medium": 50,   # Moderate risk OK
            "high": 100,    # Any risk OK
        }
        
        max_acceptable = thresholds.get(tolerance, 50)
        
        # Additional safety checks
        if tolerance != "high" and risk_level == "very_high":
            return False
        
        return risk_score <= max_acceptable
    
    def _calculate_cost_score(self, best_price: Decimal, on_demand_price: Decimal) -> float:
        """Calculate cost score (0-100)."""
        savings_ratio = 1 - (float(best_price) / float(on_demand_price))
        return min(100, 50 + savings_ratio * 100)
    
    def _calculate_fit_score(self, instance: CloudInstance, requirements: MultiCloudRequirements) -> float:
        """Calculate fit score (0-100)."""
        vcpu_ratio = instance.vcpus / requirements.min_vcpus
        memory_ratio = instance.memory_gb / requirements.min_memory_gb
        
        # Penalize over-provisioning
        vcpu_score = 100 if vcpu_ratio <= 1.5 else max(50, 100 - (vcpu_ratio - 1) * 30)
        memory_score = 100 if memory_ratio <= 1.5 else max(50, 100 - (memory_ratio - 1) * 30)
        
        return (vcpu_score + memory_score) / 2
    
    def _calculate_performance_score(self, instance: CloudInstance) -> float:
        """Calculate performance score (0-100)."""
        score = 60  # Base
        
        if instance.is_current_generation:
            score += 20
        
        if instance.network_bandwidth_gbps and instance.network_bandwidth_gbps >= 10:
            score += 10
        
        if not instance.is_burstable:
            score += 10
        
        return min(100, score)
    
    def _format_recommendation(self, candidate: Dict, rank: int) -> Dict:
        """Format recommendation for API response."""
        instance = candidate["instance"]
        on_demand = candidate["on_demand"]
        strategy = candidate["strategy"]
        
        savings_pct = (1 - float(candidate["best_price"]) / float(on_demand.hourly_price)) * 100
        
        result = {
            "rank": rank,
            "provider": candidate["provider"],
            "provider_name": self.PROVIDER_NAMES.get(candidate["provider"], candidate["provider"]),
            "instance_type": instance.instance_type,
            "display_name": instance.display_name,
            "region": candidate["region"],
            "specs": {
                "vcpus": instance.vcpus,
                "memory_gb": instance.memory_gb,
                "category": instance.category,
                "is_burstable": instance.is_burstable,
                "gpu_count": instance.gpu_count,
                "gpu_type": instance.gpu_type,
            },
            "pricing": {
                "strategy": strategy,
                "hourly_cost": float(candidate["best_price"]),
                "monthly_cost": candidate["monthly_cost"],
                "annual_cost": candidate["monthly_cost"] * 12,
                "on_demand_hourly": float(on_demand.hourly_price),
            },
            "savings": {
                "percentage": round(savings_pct, 1),
                "monthly_amount": round(float(on_demand.hourly_price) * 730 - candidate["monthly_cost"], 2),
            },
            "scores": {
                "overall": round(candidate["score"], 1),
                "cost": round(candidate.get("cost_score", 0), 1),
                "fit": round(candidate.get("fit_score", 0), 1),
                "performance": round(candidate.get("perf_score", 0), 1),
                "risk": round(candidate.get("risk_score", 100), 1),
            },
        }
        
        # Include interruption analysis for spot/preemptible
        if strategy == "spot" and candidate.get("interruption_risk"):
            risk = candidate["interruption_risk"]
            result["interruption_analysis"] = {
                "risk_level": risk.get("risk_level"),
                "risk_score": risk.get("risk_score"),
                "interruption_frequency": risk.get("interruption_frequency"),
                "provider_notes": risk.get("provider_notes"),
                "recommendations": risk.get("recommendations", []),
            }
        
        return result
    
    def _calculate_cross_cloud_comparison(
        self,
        recommendations: List[Dict],
        requirements: MultiCloudRequirements
    ) -> Dict:
        """Calculate cross-cloud comparison metrics."""
        
        by_provider = {}
        for rec in recommendations:
            provider = rec["provider"]
            if provider not in by_provider:
                by_provider[provider] = []
            by_provider[provider].append(rec)
        
        comparison = {}
        
        for provider, recs in by_provider.items():
            if recs:
                costs = [r["monthly_cost"] for r in recs]
                comparison[provider] = {
                    "cheapest_monthly": min(costs),
                    "average_monthly": sum(costs) / len(costs),
                    "cheapest_instance": recs[0]["instance"].instance_type,
                    "options_count": len(recs),
                }
        
        # Find overall cheapest
        if comparison:
            cheapest_provider = min(comparison.keys(), key=lambda p: comparison[p]["cheapest_monthly"])
            comparison["cheapest_overall"] = {
                "provider": cheapest_provider,
                "monthly_cost": comparison[cheapest_provider]["cheapest_monthly"],
            }
            
            # Calculate potential savings vs other providers
            baseline = comparison[cheapest_provider]["cheapest_monthly"]
            for provider, data in comparison.items():
                if provider != "cheapest_overall":
                    data["vs_cheapest_pct"] = round(
                        (data["cheapest_monthly"] / baseline - 1) * 100, 1
                    ) if baseline > 0 else 0
        
        return comparison
    
    async def find_equivalent_instances(
        self,
        instance_type: str,
        source_provider: str,
    ) -> Dict:
        """
        Find equivalent instances across clouds.
        
        Args:
            instance_type: Source instance type
            source_provider: Source cloud provider
            
        Returns:
            Equivalent instances in other providers
        """
        # Get source instance specs
        source_query = select(CloudInstance).where(
            CloudInstance.provider == source_provider,
            CloudInstance.instance_type == instance_type,
        )
        result = await self.db.execute(source_query)
        source = result.scalar_one_or_none()
        
        if not source:
            return {"error": f"Instance {instance_type} not found for {source_provider}"}
        
        # Find similar instances in other providers
        other_providers = [p for p in ["aws", "gcp", "azure"] if p != source_provider]
        
        equivalents = {"source": source.to_dict(), "equivalents": {}}
        
        for provider in other_providers:
            # Find instances with similar specs (within 20% tolerance)
            query = select(CloudInstance).where(
                CloudInstance.provider == provider,
                CloudInstance.vcpus >= source.vcpus * 0.8,
                CloudInstance.vcpus <= source.vcpus * 1.2,
                CloudInstance.memory_gb >= source.memory_gb * 0.8,
                CloudInstance.memory_gb <= source.memory_gb * 1.2,
            ).order_by(CloudInstance.vcpus, CloudInstance.memory_gb)
            
            result = await self.db.execute(query)
            matches = result.scalars().all()
            
            if matches:
                equivalents["equivalents"][provider] = [m.to_dict() for m in matches[:5]]
        
        return equivalents

