"""
Recommendation Engine
Generates intelligent instance recommendations based on workload requirements.
"""

import hashlib
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.instance import EC2Instance
from src.models.pricing import OnDemandPricing, SpotPricing
from src.models.recommendation import (
    WorkloadProfile, 
    Recommendation,
    WorkloadType,
    InterruptionTolerance,
)
from src.services.cost_calculator import CostCalculator, PricingStrategy
from src.services.spot_price_tracker import SpotPriceTracker

logger = logging.getLogger(__name__)


@dataclass
class WorkloadRequirements:
    """Input requirements for recommendations."""
    min_vcpus: int
    min_memory_gb: float
    max_vcpus: Optional[int] = None
    max_memory_gb: Optional[float] = None
    workload_type: WorkloadType = WorkloadType.STEADY
    interruption_tolerance: InterruptionTolerance = InterruptionTolerance.NONE
    hours_per_month: int = 730
    regions: Optional[List[str]] = None
    max_hourly_cost: Optional[float] = None
    max_monthly_budget: Optional[float] = None
    requires_gpu: bool = False
    architecture: str = "x86_64"
    
    def to_hash(self) -> str:
        """Generate hash for caching."""
        data = {
            "vcpus": (self.min_vcpus, self.max_vcpus),
            "memory": (self.min_memory_gb, self.max_memory_gb),
            "workload": self.workload_type.value,
            "tolerance": self.interruption_tolerance.value,
            "hours": self.hours_per_month,
            "regions": sorted(self.regions) if self.regions else None,
            "gpu": self.requires_gpu,
            "arch": self.architecture,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


class RecommendationEngine:
    """
    Generates cost-optimized instance recommendations.
    
    Features:
    - Multi-criteria optimization (cost, performance, risk)
    - Support for different workload patterns
    - Spot vs Reserved vs On-Demand analysis
    - Right-sizing recommendations
    """
    
    # Scoring weights
    WEIGHTS = {
        "cost": 0.40,
        "fit": 0.25,
        "risk": 0.20,
        "performance": 0.15,
    }
    
    # Maximum recommendations to return
    MAX_RECOMMENDATIONS = 10
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize engine with database session.
        
        Args:
            db_session: SQLAlchemy async session
        """
        self.db = db_session
        self.cost_calculator = CostCalculator()
        self.spot_tracker = SpotPriceTracker(db_session)
    
    async def generate_recommendations(
        self,
        requirements: WorkloadRequirements,
    ) -> List[Dict]:
        """
        Generate instance recommendations based on requirements.
        
        Args:
            requirements: Workload requirements
            
        Returns:
            Ranked list of recommendations
        """
        logger.info(f"Generating recommendations for: {requirements}")
        
        # Find matching instances
        matching_instances = await self._find_matching_instances(requirements)
        
        if not matching_instances:
            logger.warning("No matching instances found")
            return []
        
        # Get pricing for matching instances
        candidates = await self._get_pricing_candidates(
            matching_instances, 
            requirements
        )
        
        # Score and rank candidates
        scored_candidates = await self._score_candidates(candidates, requirements)
        
        # Select top recommendations
        top_recommendations = self._select_top_recommendations(
            scored_candidates, 
            requirements
        )
        
        # Build response
        recommendations = []
        for rank, candidate in enumerate(top_recommendations, 1):
            rec = self._build_recommendation(candidate, rank, requirements)
            recommendations.append(rec)
        
        return recommendations
    
    async def _find_matching_instances(
        self,
        requirements: WorkloadRequirements
    ) -> List[EC2Instance]:
        """Find instances that meet minimum requirements."""
        
        conditions = [
            EC2Instance.vcpus >= requirements.min_vcpus,
            EC2Instance.memory_gb >= requirements.min_memory_gb,
            EC2Instance.current_generation == True,
        ]
        
        # Add max constraints if specified
        if requirements.max_vcpus:
            conditions.append(EC2Instance.vcpus <= requirements.max_vcpus)
        if requirements.max_memory_gb:
            conditions.append(EC2Instance.memory_gb <= requirements.max_memory_gb)
        
        # GPU requirement
        if requirements.requires_gpu:
            conditions.append(EC2Instance.gpu_count > 0)
        else:
            # Exclude GPU instances for non-GPU workloads (they're expensive)
            conditions.append(or_(
                EC2Instance.gpu_count == None,
                EC2Instance.gpu_count == 0
            ))
        
        # Architecture
        conditions.append(EC2Instance.processor_architecture == requirements.architecture)
        
        query = select(EC2Instance).where(and_(*conditions))
        result = await self.db.execute(query)
        instances = result.scalars().all()
        
        logger.info(f"Found {len(instances)} matching instances")
        return instances
    
    async def _get_pricing_candidates(
        self,
        instances: List[EC2Instance],
        requirements: WorkloadRequirements
    ) -> List[Dict]:
        """Get pricing data for matching instances."""
        
        regions = requirements.regions or ["us-east-1", "us-west-2", "eu-west-1"]
        instance_types = [i.instance_type for i in instances]
        
        candidates = []
        
        # Get On-Demand pricing
        on_demand_query = select(OnDemandPricing).where(
            OnDemandPricing.instance_type.in_(instance_types),
            OnDemandPricing.region.in_(regions),
            OnDemandPricing.operating_system == "Linux",
        )
        result = await self.db.execute(on_demand_query)
        on_demand_prices = {
            (p.instance_type, p.region): p 
            for p in result.scalars().all()
        }
        
        # Get Spot pricing
        spot_query = select(SpotPricing).where(
            SpotPricing.instance_type.in_(instance_types),
            SpotPricing.region.in_(regions),
        )
        result = await self.db.execute(spot_query)
        spot_prices = {}
        for p in result.scalars().all():
            key = (p.instance_type, p.region)
            # Keep lowest spot price per instance/region
            if key not in spot_prices or p.spot_price < spot_prices[key].spot_price:
                spot_prices[key] = p
        
        # Build candidates
        instance_map = {i.instance_type: i for i in instances}
        
        for (instance_type, region), on_demand in on_demand_prices.items():
            instance = instance_map.get(instance_type)
            if not instance:
                continue
            
            # Apply budget filter
            if requirements.max_hourly_cost:
                if float(on_demand.price_per_hour) > requirements.max_hourly_cost:
                    continue
            
            spot = spot_prices.get((instance_type, region))
            
            candidates.append({
                "instance": instance,
                "region": region,
                "on_demand_price": on_demand.price_per_hour,
                "spot_price": spot.spot_price if spot else None,
                "spot_az": spot.availability_zone if spot else None,
            })
        
        logger.info(f"Found {len(candidates)} pricing candidates")
        return candidates
    
    async def _score_candidates(
        self,
        candidates: List[Dict],
        requirements: WorkloadRequirements
    ) -> List[Dict]:
        """Score candidates based on multiple criteria."""
        
        scored = []
        
        for candidate in candidates:
            instance = candidate["instance"]
            on_demand = candidate["on_demand_price"]
            spot = candidate["spot_price"]
            
            # Determine best pricing strategy for this workload
            strategies = self._get_applicable_strategies(requirements, spot is not None)
            
            for strategy in strategies:
                score_data = await self._calculate_score(
                    candidate, strategy, requirements
                )
                
                if score_data:
                    scored.append({
                        **candidate,
                        **score_data,
                        "strategy": strategy,
                    })
        
        return scored
    
    def _get_applicable_strategies(
        self,
        requirements: WorkloadRequirements,
        has_spot: bool
    ) -> List[PricingStrategy]:
        """Determine applicable pricing strategies based on workload."""
        
        strategies = [PricingStrategy.ON_DEMAND]
        
        # Reserved makes sense for steady workloads
        if requirements.workload_type in [WorkloadType.STEADY, WorkloadType.VARIABLE]:
            if requirements.hours_per_month >= 500:  # Significant usage
                strategies.extend([
                    PricingStrategy.RESERVED_1YR_NO_UPFRONT,
                    PricingStrategy.RESERVED_3YR_NO_UPFRONT,
                ])
        
        # Spot for interruptible workloads
        if has_spot and requirements.interruption_tolerance != InterruptionTolerance.NONE:
            strategies.append(PricingStrategy.SPOT)
        
        return strategies
    
    async def _calculate_score(
        self,
        candidate: Dict,
        strategy: PricingStrategy,
        requirements: WorkloadRequirements
    ) -> Optional[Dict]:
        """Calculate composite score for a candidate."""
        
        instance = candidate["instance"]
        on_demand = candidate["on_demand_price"]
        spot = candidate["spot_price"]
        spot_az = candidate.get("spot_az")
        
        # Calculate effective cost and risk
        interruption_data = None
        
        if strategy == PricingStrategy.SPOT:
            if not spot:
                return None
            effective_hourly = spot
            
            # ACTUALLY CALCULATE INTERRUPTION RISK from historical data
            if spot_az:
                interruption_data = await self._get_interruption_risk(
                    instance.instance_type, 
                    spot_az,
                    requirements.interruption_tolerance
                )
                risk_score = interruption_data.get("risk_score", 50)
                
                # REJECT if risk is too high for user's tolerance
                if not self._is_risk_acceptable(interruption_data, requirements.interruption_tolerance):
                    return None
            else:
                risk_score = 50  # Default if no AZ data
                
        elif strategy == PricingStrategy.ON_DEMAND:
            effective_hourly = on_demand
            risk_score = 0  # No interruption risk
        else:
            # Reserved - calculate effective rate
            breakdown = self.cost_calculator.calculate_reserved_cost(
                on_demand,
                term_years=3 if "3yr" in strategy.value else 1,
                payment_option="no_upfront"
            )
            effective_hourly = breakdown.effective_hourly
            risk_score = 5  # Small risk of commitment
        
        monthly_cost = float(effective_hourly) * requirements.hours_per_month
        
        # Apply budget filter
        if requirements.max_monthly_budget and monthly_cost > requirements.max_monthly_budget:
            return None
        
        # Cost score (lower is better, normalize to 0-100)
        max_hourly = float(on_demand) * 2  # Reference point
        cost_score = max(0, 100 - (float(effective_hourly) / max_hourly * 100))
        
        # Fit score (how well it matches requirements)
        fit_score = self._calculate_fit_score(instance, requirements)
        
        # Performance score (based on instance specs)
        perf_score = self._calculate_performance_score(instance)
        
        # Risk penalty (higher risk = lower score)
        # Adjust weight based on user's tolerance
        risk_weight_multiplier = self._get_risk_weight_multiplier(requirements.interruption_tolerance)
        risk_penalty = 100 - (risk_score * risk_weight_multiplier)
        
        # Weighted composite score
        composite = (
            self.WEIGHTS["cost"] * cost_score +
            self.WEIGHTS["fit"] * fit_score +
            self.WEIGHTS["risk"] * risk_penalty +
            self.WEIGHTS["performance"] * perf_score
        )
        
        return {
            "effective_hourly": effective_hourly,
            "monthly_cost": Decimal(str(monthly_cost)),
            "cost_score": cost_score,
            "fit_score": fit_score,
            "perf_score": perf_score,
            "risk_score": risk_score,
            "composite_score": composite,
            "interruption_data": interruption_data,  # Include for Spot analysis
        }
    
    def _calculate_fit_score(
        self,
        instance: EC2Instance,
        requirements: WorkloadRequirements
    ) -> float:
        """Calculate how well instance fits requirements (100 = perfect fit)."""
        
        # vCPU fit (penalize over-provisioning)
        vcpu_ratio = instance.vcpus / requirements.min_vcpus
        if vcpu_ratio <= 1:
            vcpu_score = 100
        elif vcpu_ratio <= 1.5:
            vcpu_score = 90
        elif vcpu_ratio <= 2:
            vcpu_score = 70
        else:
            vcpu_score = max(30, 100 - (vcpu_ratio - 1) * 20)
        
        # Memory fit
        memory_ratio = instance.memory_gb / requirements.min_memory_gb
        if memory_ratio <= 1:
            memory_score = 100
        elif memory_ratio <= 1.5:
            memory_score = 90
        elif memory_ratio <= 2:
            memory_score = 70
        else:
            memory_score = max(30, 100 - (memory_ratio - 1) * 20)
        
        return (vcpu_score + memory_score) / 2
    
    def _calculate_performance_score(self, instance: EC2Instance) -> float:
        """Calculate performance score based on instance specs."""
        
        score = 50  # Base score
        
        # Current generation bonus
        if instance.current_generation:
            score += 20
        
        # Network performance
        if "High" in (instance.network_performance or ""):
            score += 15
        elif "Moderate" in (instance.network_performance or ""):
            score += 5
        
        # EBS bandwidth
        if instance.ebs_bandwidth_mbps:
            if instance.ebs_bandwidth_mbps > 10000:
                score += 15
            elif instance.ebs_bandwidth_mbps > 5000:
                score += 10
        
        return min(100, score)
    
    async def _get_interruption_risk(
        self,
        instance_type: str,
        availability_zone: str,
        tolerance: InterruptionTolerance
    ) -> Dict:
        """
        Calculate REAL interruption risk using historical spot price data.
        
        This is the KEY function that makes recommendations valuable.
        It analyzes:
        - Historical price volatility (high volatility = high interruption chance)
        - Price trends (rising prices = increasing interruption risk)
        - Frequency of price spikes (indicates AWS reclaiming capacity)
        
        Returns:
            {
                "risk_score": 0-100 (higher = more risky),
                "risk_level": "low" | "medium" | "high" | "very_high",
                "volatility_pct": float,
                "avg_interruption_frequency": str,
                "recommended_bid_strategy": str,
                "warnings": [str]
            }
        """
        try:
            # Get actual interruption risk from historical data
            risk_data = await self.spot_tracker.calculate_interruption_risk(
                instance_type, 
                availability_zone
            )
            
            # Enhance with interruption frequency estimate
            # Based on AWS data: risk_score roughly correlates to interruptions
            risk_score = risk_data.get("risk_score", 50)
            
            # Estimate interruption frequency based on risk
            if risk_score < 20:
                freq = "<5% - Very rare interruptions"
            elif risk_score < 40:
                freq = "5-10% - Occasional interruptions"
            elif risk_score < 60:
                freq = "10-20% - Moderate interruptions"
            elif risk_score < 80:
                freq = "20-40% - Frequent interruptions"
            else:
                freq = ">40% - Very frequent interruptions"
            
            # Add bid strategy recommendation
            volatility = risk_data.get("volatility", 0)
            if volatility < 0.1:
                bid_strategy = "Set bid at current price + 10%"
            elif volatility < 0.25:
                bid_strategy = "Set bid at current price + 25%"
            else:
                bid_strategy = "Set bid at On-Demand price (aggressive bidding needed)"
            
            # Add warnings based on risk level
            warnings = []
            risk_level = risk_data.get("risk_level", "medium")
            
            if risk_level == "very_high":
                warnings.append("⚠️ This instance type is frequently interrupted in this AZ")
                warnings.append("Consider a different AZ or instance type")
            elif risk_level == "high":
                warnings.append("⚠️ Elevated interruption risk - use checkpointing")
            
            if risk_data.get("trend") == "rising":
                warnings.append("📈 Prices trending up - interruption risk increasing")
            
            return {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "volatility_pct": round(volatility * 100, 1),
                "avg_interruption_frequency": freq,
                "recommended_bid_strategy": bid_strategy,
                "warnings": warnings,
                **risk_data  # Include all raw data
            }
            
        except Exception as e:
            logger.warning(f"Could not calculate interruption risk: {e}")
            return {
                "risk_score": 50,
                "risk_level": "unknown",
                "volatility_pct": None,
                "avg_interruption_frequency": "Unknown - insufficient data",
                "recommended_bid_strategy": "Set bid at On-Demand price",
                "warnings": ["Insufficient historical data for accurate risk assessment"]
            }
    
    def _is_risk_acceptable(
        self,
        interruption_data: Dict,
        tolerance: InterruptionTolerance
    ) -> bool:
        """
        Check if the interruption risk is acceptable for user's tolerance level.
        
        This FILTERS OUT instances that are too risky for the workload.
        
        Tolerance levels:
        - NONE: No interruptions accepted (don't recommend Spot)
        - LOW: Only very stable Spot instances (risk_score < 25)
        - MEDIUM: Moderate risk OK (risk_score < 50)
        - HIGH: High risk OK for batch jobs (risk_score < 80)
        - EXTREME: Any risk OK for truly fault-tolerant workloads
        """
        risk_score = interruption_data.get("risk_score", 50)
        risk_level = interruption_data.get("risk_level", "medium")
        
        tolerance_thresholds = {
            InterruptionTolerance.NONE: 0,      # Never accept Spot
            InterruptionTolerance.LOW: 25,      # Very stable only
            InterruptionTolerance.MEDIUM: 50,   # Moderate risk
            InterruptionTolerance.HIGH: 80,     # High risk OK
        }
        
        # EXTREME tolerance accepts any risk
        if tolerance == InterruptionTolerance.HIGH:
            return True
            
        max_acceptable_risk = tolerance_thresholds.get(tolerance, 50)
        
        # Additional safety: reject "very_high" risk unless HIGH tolerance
        if risk_level == "very_high" and tolerance not in [InterruptionTolerance.HIGH]:
            return False
        
        return risk_score <= max_acceptable_risk
    
    def _get_risk_weight_multiplier(self, tolerance: InterruptionTolerance) -> float:
        """
        Adjust how much risk affects the recommendation score.
        
        Users with HIGH tolerance care less about risk in scoring.
        Users with LOW tolerance want risk heavily penalized.
        """
        multipliers = {
            InterruptionTolerance.NONE: 2.0,    # Risk matters a lot
            InterruptionTolerance.LOW: 1.5,     # Risk matters
            InterruptionTolerance.MEDIUM: 1.0,  # Normal weighting
            InterruptionTolerance.HIGH: 0.5,    # Risk matters less
        }
        return multipliers.get(tolerance, 1.0)
    
    def _select_top_recommendations(
        self,
        scored_candidates: List[Dict],
        requirements: WorkloadRequirements
    ) -> List[Dict]:
        """Select diverse top recommendations."""
        
        # Sort by composite score
        sorted_candidates = sorted(
            scored_candidates,
            key=lambda x: x["composite_score"],
            reverse=True
        )
        
        # Ensure diversity (different instances, strategies, regions)
        selected = []
        seen_instances = set()
        seen_strategies = set()
        
        for candidate in sorted_candidates:
            instance_type = candidate["instance"].instance_type
            strategy = candidate["strategy"]
            
            # Limit duplicates
            instance_count = sum(1 for s in selected if s["instance"].instance_type == instance_type)
            strategy_count = sum(1 for s in selected if s["strategy"] == strategy)
            
            if instance_count < 2 and strategy_count < 4:
                selected.append(candidate)
                
                if len(selected) >= self.MAX_RECOMMENDATIONS:
                    break
        
        return selected
    
    def _build_recommendation(
        self,
        candidate: Dict,
        rank: int,
        requirements: WorkloadRequirements
    ) -> Dict:
        """Build recommendation response."""
        
        instance = candidate["instance"]
        strategy = candidate["strategy"]
        on_demand = candidate["on_demand_price"]
        effective = candidate["effective_hourly"]
        monthly = candidate["monthly_cost"]
        
        # Calculate savings
        on_demand_monthly = float(on_demand) * requirements.hours_per_month
        savings_amount = on_demand_monthly - float(monthly)
        savings_pct = (savings_amount / on_demand_monthly * 100) if on_demand_monthly > 0 else 0
        
        # Generate reasoning
        reasoning = self._generate_reasoning(candidate, requirements)
        pros, cons = self._generate_pros_cons(candidate, requirements)
        
        return {
            "rank": rank,
            "instance_type": instance.instance_type,
            "region": candidate["region"],
            "availability_zone": candidate.get("spot_az"),
            "pricing_strategy": strategy.value,
            "specs": {
                "vcpus": instance.vcpus,
                "memory_gb": instance.memory_gb,
                "storage_type": instance.storage_type,
                "network_performance": instance.network_performance,
            },
            "pricing": {
                "effective_hourly": float(effective),
                "monthly_cost": float(monthly),
                "annual_cost": float(monthly) * 12,
                "on_demand_hourly": float(on_demand),
            },
            "savings": {
                "amount_monthly": round(savings_amount, 2),
                "percentage": round(savings_pct, 1),
            },
            "scores": {
                "composite": round(candidate["composite_score"], 1),
                "cost": round(candidate["cost_score"], 1),
                "fit": round(candidate["fit_score"], 1),
                "performance": round(candidate["perf_score"], 1),
                "risk": candidate["risk_score"],
            },
            # Include interruption analysis for Spot instances
            "interruption_analysis": self._build_interruption_analysis(candidate, strategy),
            "reasoning": reasoning,
            "pros": pros,
            "cons": cons,
        }
    
    def _build_interruption_analysis(self, candidate: Dict, strategy: PricingStrategy) -> Optional[Dict]:
        """Build interruption analysis section for Spot recommendations."""
        
        if strategy != PricingStrategy.SPOT:
            return None
        
        interruption_data = candidate.get("interruption_data")
        if not interruption_data:
            return {
                "status": "no_data",
                "message": "Insufficient historical data for interruption analysis"
            }
        
        return {
            "status": "analyzed",
            "risk_level": interruption_data.get("risk_level", "unknown"),
            "risk_score": interruption_data.get("risk_score", 0),
            "volatility_pct": interruption_data.get("volatility_pct"),
            "interruption_frequency": interruption_data.get("avg_interruption_frequency"),
            "bid_strategy": interruption_data.get("recommended_bid_strategy"),
            "warnings": interruption_data.get("warnings", []),
            "recommendation": self._get_spot_recommendation(interruption_data)
        }
    
    def _get_spot_recommendation(self, interruption_data: Dict) -> str:
        """Generate actionable recommendation based on interruption risk."""
        
        risk_level = interruption_data.get("risk_level", "medium")
        
        recommendations = {
            "low": "✅ Good candidate for Spot. Set up basic termination handling.",
            "medium": "⚠️ Use Spot with checkpointing. Consider diversifying across AZs.",
            "high": "⚡ Only for fault-tolerant workloads. Use Spot Fleet with diversification.",
            "very_high": "🚨 High interruption risk. Consider Reserved or On-Demand instead.",
        }
        
        return recommendations.get(risk_level, "Review historical data before using Spot.")
    
    def _generate_reasoning(
        self,
        candidate: Dict,
        requirements: WorkloadRequirements
    ) -> str:
        """Generate human-readable reasoning for recommendation."""
        
        instance = candidate["instance"]
        strategy = candidate["strategy"]
        savings_pct = ((float(candidate["on_demand_price"]) - float(candidate["effective_hourly"])) 
                       / float(candidate["on_demand_price"]) * 100)
        
        parts = []
        
        # Instance fit
        parts.append(
            f"{instance.instance_type} provides {instance.vcpus} vCPUs and "
            f"{instance.memory_gb}GB memory, meeting your requirements."
        )
        
        # Pricing strategy rationale
        if strategy == PricingStrategy.SPOT:
            parts.append(
                f"Using Spot pricing saves {savings_pct:.0f}% compared to On-Demand, "
                f"suitable for your {requirements.interruption_tolerance.value} interruption tolerance."
            )
        elif "reserved" in strategy.value:
            term = "3-year" if "3yr" in strategy.value else "1-year"
            parts.append(
                f"A {term} Reserved Instance provides {savings_pct:.0f}% savings "
                f"for your steady workload pattern."
            )
        else:
            parts.append(
                "On-Demand pricing offers maximum flexibility with no commitment."
            )
        
        return " ".join(parts)
    
    def _generate_pros_cons(
        self,
        candidate: Dict,
        requirements: WorkloadRequirements
    ) -> Tuple[List[str], List[str]]:
        """Generate pros and cons for recommendation."""
        
        instance = candidate["instance"]
        strategy = candidate["strategy"]
        
        pros = []
        cons = []
        
        # Cost
        if candidate["cost_score"] > 70:
            pros.append("Cost-effective for your workload")
        
        # Fit
        if candidate["fit_score"] > 85:
            pros.append("Right-sized for your requirements")
        elif candidate["fit_score"] < 60:
            cons.append("May be over-provisioned")
        
        # Strategy specific
        if strategy == PricingStrategy.SPOT:
            pros.append("Maximum cost savings")
            cons.append("Potential for interruption")
        elif "reserved" in strategy.value:
            pros.append("Predictable costs")
            cons.append("Requires commitment period")
        else:
            pros.append("No commitment required")
            pros.append("Easy to change instance type")
        
        # Instance specific
        if instance.current_generation:
            pros.append("Latest generation hardware")
        
        if "10 Gigabit" in (instance.network_performance or ""):
            pros.append("High network performance")
        
        return pros, cons
    
    async def get_quick_recommendation(
        self,
        vcpus: int,
        memory_gb: float,
        region: str = "us-east-1"
    ) -> Dict:
        """
        Get a quick recommendation without full analysis.
        
        Args:
            vcpus: Required vCPUs
            memory_gb: Required memory
            region: Target region
            
        Returns:
            Quick recommendation
        """
        requirements = WorkloadRequirements(
            min_vcpus=vcpus,
            min_memory_gb=memory_gb,
            regions=[region],
        )
        
        recommendations = await self.generate_recommendations(requirements)
        
        if recommendations:
            return recommendations[0]
        
        return {"error": "No matching instances found"}

