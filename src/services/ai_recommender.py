"""
CloudCost AI™ - Intelligent Cloud Instance Recommender
Uses ML-like scoring algorithm to recommend optimal instances
"""

from typing import List, Dict, Optional, Literal
from datetime import datetime
import logging
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.cloud_provider import CloudInstance
from src.models.pricing import CloudPricing

logger = logging.getLogger(__name__)


class CloudCostAI:
    """
    Intelligent recommendation engine for cloud instances
    Analyzes requirements and recommends optimal instances across all clouds
    """
    
    # Workload profiles with characteristics
    WORKLOAD_PROFILES = {
        "web_app": {
            "cpu_weight": 0.6,
            "memory_weight": 0.4,
            "network_important": True,
            "burstable_ok": True,
            "spot_eligible": True,
            "description": "Web applications, APIs, microservices"
        },
        "database": {
            "cpu_weight": 0.4,
            "memory_weight": 0.6,
            "network_important": True,
            "burstable_ok": False,
            "spot_eligible": False,
            "description": "Databases, data stores, caches"
        },
        "compute_intensive": {
            "cpu_weight": 0.8,
            "memory_weight": 0.2,
            "network_important": False,
            "burstable_ok": False,
            "spot_eligible": True,
            "description": "Batch processing, CI/CD, video encoding"
        },
        "memory_intensive": {
            "cpu_weight": 0.3,
            "memory_weight": 0.7,
            "network_important": False,
            "burstable_ok": False,
            "spot_eligible": True,
            "description": "Big data, analytics, in-memory processing"
        },
        "ml_training": {
            "cpu_weight": 0.7,
            "memory_weight": 0.3,
            "network_important": False,
            "burstable_ok": False,
            "spot_eligible": True,
            "description": "Machine learning training, AI workloads"
        },
        "general": {
            "cpu_weight": 0.5,
            "memory_weight": 0.5,
            "network_important": False,
            "burstable_ok": True,
            "spot_eligible": True,
            "description": "General purpose workloads"
        }
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_recommendations(
        self,
        min_vcpus: int,
        min_memory_gb: float,
        workload_type: str = "general",
        traffic_pattern: Literal["steady", "variable", "spiky"] = "steady",
        providers: Optional[List[str]] = None,
        max_monthly_budget: Optional[float] = None,
        spot_eligible: bool = True,
        limit: int = 10
    ) -> Dict:
        """
        Get AI-powered instance recommendations
        
        Args:
            min_vcpus: Minimum vCPUs required
            min_memory_gb: Minimum memory (GB) required
            workload_type: Type of workload (web_app, database, etc.)
            traffic_pattern: Traffic pattern (steady, variable, spiky)
            providers: List of cloud providers to consider (default: all)
            max_monthly_budget: Maximum monthly budget
            spot_eligible: Whether spot/preemptible instances are acceptable
            limit: Maximum number of recommendations
        
        Returns:
            Dict with recommendations, savings, and insights
        """
        try:
            # Get workload profile
            profile = self.WORKLOAD_PROFILES.get(workload_type, self.WORKLOAD_PROFILES["general"])
            
            # Determine if spot instances should be recommended
            recommend_spot = spot_eligible and profile["spot_eligible"]
            
            # Build query for matching instances
            query = select(CloudInstance).where(
                and_(
                    CloudInstance.vcpus >= min_vcpus,
                    CloudInstance.memory_gb >= min_memory_gb,
                    CloudInstance.is_current_generation == True
                )
            )
            
            # Filter by providers if specified
            if providers:
                query = query.where(CloudInstance.provider.in_(providers))
            
            # Execute query
            result = await self.db.execute(query)
            instances = result.scalars().all()
            
            if not instances:
                return {
                    "recommendations": [],
                    "total": 0,
                    "error": "No instances match your requirements"
                }
            
            # Score and rank instances
            scored_instances = []
            for instance in instances:
                score = await self._calculate_instance_score(
                    instance,
                    min_vcpus,
                    min_memory_gb,
                    profile,
                    traffic_pattern,
                    max_monthly_budget
                )
                
                if score > 0:
                    scored_instances.append({
                        "instance": instance,
                        "score": score,
                        "pricing": await self._get_pricing(instance),
                        "reasoning": self._generate_reasoning(instance, profile, traffic_pattern)
                    })
            
            # Sort by score (highest first)
            scored_instances.sort(key=lambda x: x["score"], reverse=True)
            
            # Get top N recommendations
            top_recommendations = scored_instances[:limit]
            
            # Calculate savings and insights
            insights = self._generate_insights(
                top_recommendations,
                workload_type,
                traffic_pattern,
                recommend_spot
            )
            
            # Format recommendations
            formatted_recommendations = []
            for idx, rec in enumerate(top_recommendations, 1):
                instance = rec["instance"]
                pricing = rec["pricing"]
                
                formatted_recommendations.append({
                    "rank": idx,
                    "provider": instance.provider,
                    "instance_type": instance.instance_type,
                    "display_name": instance.display_name,
                    "vcpus": instance.vcpus,
                    "memory_gb": instance.memory_gb,
                    "category": instance.category,
                    "processor_architecture": instance.processor_architecture,
                    "hourly_price": pricing.get("hourly_price", 0),
                    "monthly_price": pricing.get("monthly_price", 0),
                    "spot_price": pricing.get("spot_price"),
                    "spot_savings": pricing.get("spot_savings"),
                    "score": round(rec["score"], 2),
                    "reasoning": rec["reasoning"],
                    "best_for": self._get_best_for_tags(instance, profile),
                    "is_burstable": instance.is_burstable,
                    "supports_spot": instance.supports_spot
                })
            
            return {
                "recommendations": formatted_recommendations,
                "total": len(formatted_recommendations),
                "insights": insights,
                "workload_profile": {
                    "type": workload_type,
                    "description": profile["description"],
                    "traffic_pattern": traffic_pattern
                },
                "filters_applied": {
                    "min_vcpus": min_vcpus,
                    "min_memory_gb": min_memory_gb,
                    "providers": providers or ["aws", "gcp", "azure"],
                    "max_monthly_budget": max_monthly_budget
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {
                "recommendations": [],
                "total": 0,
                "error": str(e)
            }
    
    async def _calculate_instance_score(
        self,
        instance: CloudInstance,
        min_vcpus: int,
        min_memory_gb: float,
        profile: Dict,
        traffic_pattern: str,
        max_budget: Optional[float]
    ) -> float:
        """
        Calculate a score for an instance based on requirements
        Higher score = better match
        """
        score = 100.0
        
        # Get pricing
        pricing = await self._get_pricing(instance)
        monthly_price = pricing.get("monthly_price", 0)
        
        # Budget check (hard requirement)
        if max_budget and monthly_price > max_budget:
            return 0  # Disqualify if over budget
        
        # 1. Resource efficiency score (30 points)
        # Penalize over-provisioning
        cpu_ratio = instance.vcpus / min_vcpus
        memory_ratio = instance.memory_gb / min_memory_gb
        
        # Ideal ratio is 1.0-1.5x (slightly over-provisioned for headroom)
        cpu_score = 30 * (1 - abs(1.2 - cpu_ratio) / 2) if cpu_ratio >= 1 else 0
        memory_score = 30 * (1 - abs(1.2 - memory_ratio) / 2) if memory_ratio >= 1 else 0
        
        resource_score = (cpu_score * profile["cpu_weight"]) + (memory_score * profile["memory_weight"])
        score += resource_score - 30  # Normalize
        
        # 2. Price/performance score (40 points)
        # Calculate price per vCPU-GB
        price_per_unit = monthly_price / (instance.vcpus * instance.memory_gb) if monthly_price > 0 else 999
        
        # Normalize (lower is better)
        # Typical range: $0.5-5 per vCPU-GB
        price_score = max(0, 40 - (price_per_unit * 8))
        score += price_score
        
        # 3. Workload suitability score (20 points)
        workload_score = 0
        
        # Burstable instances for variable traffic
        if traffic_pattern in ["variable", "spiky"] and instance.is_burstable:
            workload_score += 10
        
        # Non-burstable for steady/critical workloads
        if traffic_pattern == "steady" and not instance.is_burstable:
            workload_score += 10
        
        # Category match
        if profile.get("category") and instance.category == profile.get("category"):
            workload_score += 10
        
        score += workload_score
        
        # 4. Modern architecture bonus (10 points)
        if instance.is_current_generation:
            score += 5
        
        # ARM instances bonus (more efficient)
        if instance.processor_architecture == "arm64":
            score += 5
        
        # 5. Provider diversity (small bonus)
        # Slight bonus for less common providers (avoid AWS bias)
        provider_bonus = {
            "aws": 0,
            "gcp": 2,
            "azure": 2
        }
        score += provider_bonus.get(instance.provider, 0)
        
        return max(0, min(100, score))
    
    async def _get_pricing(self, instance: CloudInstance) -> Dict:
        """
        Get pricing for an instance (on-demand and spot)
        """
        try:
            # Get cheapest on-demand pricing
            pricing_query = select(CloudPricing).where(
                and_(
                    CloudPricing.provider == instance.provider,
                    CloudPricing.instance_type == instance.instance_type,
                    CloudPricing.pricing_type == "on_demand"
                )
            ).order_by(CloudPricing.hourly_price).limit(1)
            
            result = await self.db.execute(pricing_query)
            pricing = result.scalar_one_or_none()
            
            if pricing:
                hourly = float(pricing.hourly_price)
                monthly = hourly * 730
                
                # Check for spot pricing
                spot_query = select(CloudPricing).where(
                    and_(
                        CloudPricing.provider == instance.provider,
                        CloudPricing.instance_type == instance.instance_type,
                        CloudPricing.pricing_type.in_(["spot", "preemptible"])
                    )
                ).order_by(CloudPricing.hourly_price).limit(1)
                
                spot_result = await self.db.execute(spot_query)
                spot_pricing = spot_result.scalar_one_or_none()
                
                spot_price = None
                spot_savings = None
                
                if spot_pricing:
                    spot_hourly = float(spot_pricing.hourly_price)
                    spot_price = spot_hourly * 730
                    spot_savings = ((monthly - spot_price) / monthly) * 100 if monthly > 0 else 0
                
                return {
                    "hourly_price": hourly,
                    "monthly_price": monthly,
                    "spot_price": spot_price,
                    "spot_savings": spot_savings,
                    "region": pricing.region
                }
            
            return {"hourly_price": 0, "monthly_price": 0}
            
        except Exception as e:
            logger.error(f"Error getting pricing for {instance.instance_type}: {e}")
            return {"hourly_price": 0, "monthly_price": 0}
    
    def _generate_reasoning(
        self,
        instance: CloudInstance,
        profile: Dict,
        traffic_pattern: str
    ) -> str:
        """
        Generate human-readable reasoning for recommendation
        """
        reasons = []
        
        # Price/performance
        reasons.append(f"Excellent price/performance ratio for {profile['description'].lower()}")
        
        # Architecture
        if instance.processor_architecture == "arm64":
            reasons.append("ARM architecture offers better energy efficiency and cost")
        
        # Burstable
        if instance.is_burstable and traffic_pattern in ["variable", "spiky"]:
            reasons.append("Burstable performance perfect for variable traffic patterns")
        
        # Category match
        if instance.category:
            category_name = instance.category.replace("_", " ").title()
            reasons.append(f"{category_name} instance optimized for your workload")
        
        # Current generation
        if instance.is_current_generation:
            reasons.append("Latest generation with improved performance")
        
        return ". ".join(reasons[:3])  # Max 3 reasons
    
    def _get_best_for_tags(self, instance: CloudInstance, profile: Dict) -> List[str]:
        """
        Generate tags for what this instance is best for
        """
        tags = []
        
        if instance.is_burstable:
            tags.append("Variable Traffic")
        else:
            tags.append("Steady Workloads")
        
        if instance.supports_spot:
            tags.append("Spot Eligible")
        
        if instance.category:
            tags.append(instance.category.replace("_", " ").title())
        
        if instance.processor_architecture == "arm64":
            tags.append("Energy Efficient")
        
        return tags[:4]  # Max 4 tags
    
    def _generate_insights(
        self,
        recommendations: List[Dict],
        workload_type: str,
        traffic_pattern: str,
        spot_eligible: bool
    ) -> Dict:
        """
        Generate insights and savings analysis
        """
        if not recommendations:
            return {}
        
        # Get prices
        prices = [r["pricing"]["monthly_price"] for r in recommendations if r["pricing"]["monthly_price"] > 0]
        
        if not prices:
            return {}
        
        cheapest = min(prices)
        most_expensive = max(prices)
        average = sum(prices) / len(prices)
        
        # Calculate potential savings
        savings_percent = ((most_expensive - cheapest) / most_expensive * 100) if most_expensive > 0 else 0
        savings_amount = most_expensive - cheapest
        
        # Spot instance savings
        spot_opportunities = [
            r for r in recommendations 
            if r["instance"].supports_spot and r["pricing"].get("spot_price")
        ]
        
        avg_spot_savings = 0
        if spot_opportunities:
            spot_savings_list = [r["pricing"]["spot_savings"] for r in spot_opportunities]
            avg_spot_savings = sum(spot_savings_list) / len(spot_savings_list)
        
        # Generate insights
        insights = {
            "price_range": {
                "cheapest": round(cheapest, 2),
                "most_expensive": round(most_expensive, 2),
                "average": round(average, 2)
            },
            "savings_potential": {
                "percent": round(savings_percent, 1),
                "monthly_amount": round(savings_amount, 2),
                "annual_amount": round(savings_amount * 12, 2)
            },
            "spot_instance_opportunity": {
                "available": len(spot_opportunities),
                "average_savings": round(avg_spot_savings, 1) if avg_spot_savings else 0,
                "recommendation": "Consider spot instances for non-critical workloads" if spot_opportunities else None
            },
            "recommendations_summary": {
                "total": len(recommendations),
                "by_provider": self._count_by_provider(recommendations),
                "by_architecture": self._count_by_architecture(recommendations)
            },
            "key_insights": self._generate_key_insights(
                recommendations,
                workload_type,
                traffic_pattern,
                savings_percent,
                avg_spot_savings
            )
        }
        
        return insights
    
    def _count_by_provider(self, recommendations: List[Dict]) -> Dict:
        """Count recommendations by provider"""
        counts = {}
        for rec in recommendations:
            provider = rec["instance"].provider
            counts[provider] = counts.get(provider, 0) + 1
        return counts
    
    def _count_by_architecture(self, recommendations: List[Dict]) -> Dict:
        """Count recommendations by processor architecture"""
        counts = {}
        for rec in recommendations:
            arch = rec["instance"].processor_architecture or "x86_64"
            counts[arch] = counts.get(arch, 0) + 1
        return counts
    
    def _generate_key_insights(
        self,
        recommendations: List[Dict],
        workload_type: str,
        traffic_pattern: str,
        savings_percent: float,
        avg_spot_savings: float
    ) -> List[str]:
        """Generate key insights for the user"""
        insights = []
        
        # Savings insight
        if savings_percent > 30:
            insights.append(f"💰 Choosing the right instance can save you up to {savings_percent:.0f}% monthly")
        
        # Spot instance insight
        if avg_spot_savings > 50:
            insights.append(f"⚡ Spot instances can save an additional {avg_spot_savings:.0f}% for fault-tolerant workloads")
        
        # Multi-cloud insight
        provider_counts = self._count_by_provider(recommendations)
        if len(provider_counts) > 1:
            cheapest_provider = max(provider_counts, key=lambda k: provider_counts[k])
            insights.append(f"🌐 {cheapest_provider.upper()} offers the most cost-effective options for your requirements")
        
        # ARM insight
        arch_counts = self._count_by_architecture(recommendations)
        if arch_counts.get("arm64", 0) > 0:
            insights.append("🔋 ARM-based instances offer better price/performance for compatible workloads")
        
        # Traffic pattern insight
        if traffic_pattern in ["variable", "spiky"]:
            insights.append("📊 Consider auto-scaling with burstable instances for variable traffic")
        
        return insights[:4]  # Max 4 insights
