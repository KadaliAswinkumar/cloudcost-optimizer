"""
Spot Intelligence™ - Interruption Prediction & Savings Calculator
Analyzes spot pricing volatility and predicts interruption risk
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import statistics

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.cloud_provider import CloudInstance, CloudPricing
from src.services.historical_price_generator import HistoricalPriceGenerator

logger = logging.getLogger(__name__)


class SpotIntelligence:
    """
    Analyze spot instance pricing and predict interruption risk
    Calculate potential savings and recommend best regions
    """
    
    # Interruption risk thresholds based on price volatility
    VOLATILITY_THRESHOLDS = {
        "low": 0.15,      # <15% std deviation = low risk
        "medium": 0.30,   # 15-30% = medium risk
        "high": 1.0       # >30% = high risk
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def analyze_instance(
        self,
        provider: str,
        instance_type: str,
        region: Optional[str] = None,
        hours_per_month: int = 730
    ) -> Dict:
        """
        Comprehensive spot intelligence analysis for an instance
        
        Args:
            provider: Cloud provider (aws, gcp, azure)
            instance_type: Instance type (e.g., m5.xlarge)
            region: Specific region (optional, analyzes all if not provided)
            hours_per_month: Usage hours per month (default 730 = 24/7)
        
        Returns:
            Complete analysis with pricing, risk, and savings data
        """
        try:
            # Get on-demand pricing
            on_demand_price = await self._get_on_demand_price(provider, instance_type, region)
            
            if not on_demand_price:
                return {
                    "success": False,
                    "error": f"No on-demand pricing found for {provider} {instance_type}"
                }
            
            # Get spot pricing across regions
            spot_prices = await self._get_spot_prices(provider, instance_type, region)
            
            if not spot_prices:
                return {
                    "success": False,
                    "error": f"No spot pricing available for {provider} {instance_type}"
                }
            
            # Calculate statistics
            analysis = await self._calculate_analysis(
                on_demand_price,
                spot_prices,
                hours_per_month
            )
            
            # Get instance details
            instance_details = await self._get_instance_details(provider, instance_type)
            
            # Get reserved pricing for comparison
            reserved_prices = await self._get_reserved_prices(provider, instance_type, region)
            
            # Generate recommendation (spot vs reserved)
            recommendation = self._generate_recommendation(
                on_demand_price,
                spot_prices,
                reserved_prices,
                analysis
            )
            
            # Generate historical price data (30 days)
            avg_spot_hourly = analysis.get("average", {}).get("hourly", 0)
            volatility_decimal = analysis.get("volatility", {}).get("percent", 10) / 100
            
            historical_data = HistoricalPriceGenerator.generate_30day_history(
                current_price=avg_spot_hourly,
                volatility=volatility_decimal,
                provider=provider
            )
            
            # Calculate insights from historical data
            historical_insights = HistoricalPriceGenerator.calculate_insights(historical_data)
            
            # Get launch recommendations
            launch_recommendations = HistoricalPriceGenerator.get_launch_recommendations(
                historical_insights,
                on_demand_price["hourly"]
            )
            
            # Calculate interruption frequency
            interruption_analysis = self._calculate_interruption_frequency(
                analysis.get("volatility", {}).get("percent", 0),
                analysis.get("risk", {}).get("level", "unknown")
            )
            
            return {
                "success": True,
                "provider": provider,
                "instance_type": instance_type,
                "instance_details": instance_details,
                "on_demand": on_demand_price,
                "spot_analysis": analysis,
                "reserved_pricing": reserved_prices,
                "recommendation": recommendation,
                "historical_data": {
                    "prices": historical_data[-168:],  # Last 7 days (168 hours)
                    "insights": historical_insights
                },
                "launch_recommendations": launch_recommendations,
                "interruption_analysis": interruption_analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing spot instance: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_on_demand_price(
        self,
        provider: str,
        instance_type: str,
        region: Optional[str]
    ) -> Optional[Dict]:
        """Get on-demand pricing for comparison"""
        try:
            query = select(CloudPricing).where(
                and_(
                    CloudPricing.provider == provider,
                    CloudPricing.instance_type == instance_type,
                    CloudPricing.pricing_type == "on_demand"
                )
            )
            
            if region:
                query = query.where(CloudPricing.region == region)
            
            query = query.order_by(CloudPricing.hourly_price).limit(1)
            
            result = await self.db.execute(query)
            pricing = result.scalar_one_or_none()
            
            if pricing:
                return {
                    "hourly": float(pricing.hourly_price),
                    "monthly": float(pricing.hourly_price) * 730,
                    "region": pricing.region
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting on-demand price: {e}")
            return None
    
    async def _get_spot_prices(
        self,
        provider: str,
        instance_type: str,
        region: Optional[str]
    ) -> List[Dict]:
        """Get spot/preemptible pricing across regions"""
        try:
            spot_types = ["spot", "preemptible"]  # AWS/Azure and GCP
            
            query = select(CloudPricing).where(
                and_(
                    CloudPricing.provider == provider,
                    CloudPricing.instance_type == instance_type,
                    CloudPricing.pricing_type.in_(spot_types)
                )
            )
            
            if region:
                query = query.where(CloudPricing.region == region)
            
            result = await self.db.execute(query)
            spot_pricings = result.scalars().all()
            
            spot_prices = []
            for pricing in spot_pricings:
                spot_prices.append({
                    "region": pricing.region,
                    "hourly": float(pricing.hourly_price),
                    "monthly": float(pricing.hourly_price) * 730,
                    "pricing_type": pricing.pricing_type
                })
            
            return spot_prices
            
        except Exception as e:
            logger.error(f"Error getting spot prices: {e}")
            return []
    
    async def _get_instance_details(self, provider: str, instance_type: str) -> Optional[Dict]:
        """Get instance specifications"""
        try:
            query = select(CloudInstance).where(
                and_(
                    CloudInstance.provider == provider,
                    CloudInstance.instance_type == instance_type
                )
            )
            
            result = await self.db.execute(query)
            instance = result.scalar_one_or_none()
            
            if instance:
                return {
                    "vcpus": instance.vcpus,
                    "memory_gb": instance.memory_gb,
                    "processor_architecture": instance.processor_architecture,
                    "category": instance.category,
                    "supports_spot": instance.supports_spot
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting instance details: {e}")
            return None
    
    async def _calculate_analysis(
        self,
        on_demand: Dict,
        spot_prices: List[Dict],
        hours_per_month: int
    ) -> Dict:
        """Calculate comprehensive spot analysis"""
        
        if not spot_prices:
            return {}
        
        # Extract hourly prices
        hourly_prices = [sp["hourly"] for sp in spot_prices]
        
        # Calculate statistics
        avg_spot_hourly = statistics.mean(hourly_prices)
        min_spot_hourly = min(hourly_prices)
        max_spot_hourly = max(hourly_prices)
        
        # Calculate volatility (standard deviation)
        if len(hourly_prices) > 1:
            volatility = statistics.stdev(hourly_prices)
            volatility_percent = (volatility / avg_spot_hourly) * 100
        else:
            volatility = 0
            volatility_percent = 0
        
        # Determine risk level
        risk_level = self._calculate_risk_level(volatility_percent / 100)
        
        # Calculate savings
        on_demand_hourly = on_demand["hourly"]
        on_demand_monthly = on_demand_hourly * hours_per_month
        avg_spot_monthly = avg_spot_hourly * hours_per_month
        min_spot_monthly = min_spot_hourly * hours_per_month
        max_spot_monthly = max_spot_hourly * hours_per_month
        
        savings_monthly = on_demand_monthly - avg_spot_monthly
        savings_percent = ((on_demand_monthly - avg_spot_monthly) / on_demand_monthly) * 100
        savings_annual = savings_monthly * 12
        
        # Find best regions (lowest spot price)
        best_regions = sorted(spot_prices, key=lambda x: x["hourly"])[:3]
        
        return {
            "average": {
                "hourly": round(avg_spot_hourly, 4),
                "monthly": round(avg_spot_monthly, 2),
                "annual": round(avg_spot_monthly * 12, 2)
            },
            "range": {
                "min_hourly": round(min_spot_hourly, 4),
                "max_hourly": round(max_spot_hourly, 4),
                "min_monthly": round(min_spot_monthly, 2),
                "max_monthly": round(max_spot_monthly, 2)
            },
            "volatility": {
                "value": round(volatility, 4),
                "percent": round(volatility_percent, 2),
                "level": "low" if volatility_percent < 15 else "medium" if volatility_percent < 30 else "high"
            },
            "risk": {
                "level": risk_level,
                "score": round(volatility_percent, 1),
                "description": self._get_risk_description(risk_level),
                "recommendation": self._get_risk_recommendation(risk_level)
            },
            "savings": {
                "monthly_amount": round(savings_monthly, 2),
                "annual_amount": round(savings_annual, 2),
                "percent": round(savings_percent, 1),
                "break_even_hours": round(on_demand_monthly / avg_spot_hourly, 0) if avg_spot_hourly > 0 else 0
            },
            "best_regions": [
                {
                    "region": r["region"],
                    "hourly": round(r["hourly"], 4),
                    "monthly": round(r["monthly"], 2),
                    "savings_vs_ondemand": round(((on_demand_hourly - r["hourly"]) / on_demand_hourly) * 100, 1)
                }
                for r in best_regions
            ],
            "regional_prices": [
                {
                    "region": sp["region"],
                    "hourly": round(sp["hourly"], 4),
                    "monthly": round(sp["monthly"], 2)
                }
                for sp in sorted(spot_prices, key=lambda x: x["hourly"])
            ]
        }
    
    def _calculate_risk_level(self, volatility: float) -> str:
        """Determine interruption risk level based on volatility"""
        if volatility < self.VOLATILITY_THRESHOLDS["low"]:
            return "low"
        elif volatility < self.VOLATILITY_THRESHOLDS["medium"]:
            return "medium"
        else:
            return "high"
    
    def _get_risk_description(self, risk_level: str) -> str:
        """Get human-readable risk description"""
        descriptions = {
            "low": "Stable pricing, low interruption risk (5-10%)",
            "medium": "Moderate volatility, medium interruption risk (15-25%)",
            "high": "High volatility, frequent interruptions possible (30-50%)"
        }
        return descriptions.get(risk_level, "Unknown")
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level"""
        recommendations = {
            "low": "✅ Excellent for production workloads with fault tolerance",
            "medium": "⚠️ Good for batch jobs and dev/test environments",
            "high": "🚫 Only for highly fault-tolerant workloads"
        }
        return recommendations.get(risk_level, "")
    
    async def compare_providers(
        self,
        instance_specs: Dict,
        hours_per_month: int = 730
    ) -> Dict:
        """
        Compare spot pricing across all providers for similar specs
        
        Args:
            instance_specs: {"vcpus": 4, "memory_gb": 16}
            hours_per_month: Usage hours
        
        Returns:
            Comparison across AWS, GCP, Azure
        """
        try:
            providers = ["aws", "gcp", "azure"]
            comparisons = []
            
            for provider in providers:
                # Find instances matching specs
                query = select(CloudInstance).where(
                    and_(
                        CloudInstance.provider == provider,
                        CloudInstance.vcpus >= instance_specs.get("vcpus", 2) * 0.9,
                        CloudInstance.vcpus <= instance_specs.get("vcpus", 2) * 1.1,
                        CloudInstance.memory_gb >= instance_specs.get("memory_gb", 8) * 0.9,
                        CloudInstance.memory_gb <= instance_specs.get("memory_gb", 8) * 1.1,
                    )
                ).limit(5)
                
                result = await self.db.execute(query)
                instances = result.scalars().all()
                
                for instance in instances:
                    analysis = await self.analyze_instance(
                        provider=provider,
                        instance_type=instance.instance_type,
                        hours_per_month=hours_per_month
                    )
                    
                    if analysis.get("success"):
                        comparisons.append(analysis)
            
            # Sort by savings
            comparisons.sort(
                key=lambda x: x.get("spot_analysis", {}).get("savings", {}).get("monthly_amount", 0),
                reverse=True
            )
            
            return {
                "success": True,
                "specs": instance_specs,
                "comparisons": comparisons[:10]  # Top 10
            }
            
        except Exception as e:
            logger.error(f"Error comparing providers: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_reserved_prices(
        self,
        provider: str,
        instance_type: str,
        region: Optional[str]
    ) -> Dict:
        """Get reserved instance pricing for comparison"""
        try:
            # Determine pricing types based on provider
            if provider == "aws":
                pricing_types = ["reserved_1yr", "reserved_3yr"]
            elif provider == "gcp":
                pricing_types = ["committed_1yr", "committed_3yr"]
            elif provider == "azure":
                pricing_types = ["reserved_1yr", "reserved_3yr"]
            else:
                return {}
            
            reserved_pricing = {}
            
            for pricing_type in pricing_types:
                query = select(CloudPricing).where(
                    and_(
                        CloudPricing.provider == provider,
                        CloudPricing.instance_type == instance_type,
                        CloudPricing.pricing_type == pricing_type
                    )
                )
                
                if region:
                    query = query.where(CloudPricing.region == region)
                
                query = query.order_by(CloudPricing.hourly_price).limit(1)
                
                result = await self.db.execute(query)
                pricing = result.scalar_one_or_none()
                
                if pricing:
                    reserved_pricing[pricing_type] = {
                        "hourly": float(pricing.hourly_price),
                        "monthly": float(pricing.hourly_price) * 730,
                        "annual": float(pricing.hourly_price) * 730 * 12,
                        "region": pricing.region,
                        "commitment_term": pricing.commitment_term
                    }
            
            return reserved_pricing
            
        except Exception as e:
            logger.error(f"Error getting reserved prices: {e}")
            return {}
    
    def _generate_recommendation(
        self,
        on_demand: Dict,
        spot_prices: List[Dict],
        reserved_prices: Dict,
        spot_analysis: Dict
    ) -> Dict:
        """Generate smart recommendation: spot vs reserved vs on-demand"""
        try:
            on_demand_monthly = on_demand["monthly"]
            avg_spot_monthly = spot_analysis.get("average", {}).get("monthly", 0)
            risk_level = spot_analysis.get("risk", {}).get("level", "unknown")
            
            # Calculate savings for each option
            options = {
                "on_demand": {
                    "monthly_cost": on_demand_monthly,
                    "savings_amount": 0,
                    "savings_percent": 0,
                    "commitment": "None",
                    "pros": ["No commitment", "Guaranteed availability", "Flexible"],
                    "cons": ["Most expensive", "No discounts"],
                    "best_for": "Short-term testing, unpredictable workloads"
                },
                "spot": {
                    "monthly_cost": avg_spot_monthly,
                    "savings_amount": on_demand_monthly - avg_spot_monthly,
                    "savings_percent": ((on_demand_monthly - avg_spot_monthly) / on_demand_monthly) * 100 if on_demand_monthly > 0 else 0,
                    "commitment": "None",
                    "risk": risk_level,
                    "pros": ["Massive savings (60-90%)", "No commitment", "Flexible"],
                    "cons": ["Can be interrupted", "Requires fault tolerance"],
                    "best_for": "Batch jobs, dev/test, fault-tolerant workloads"
                }
            }
            
            # Add reserved options if available
            for res_type, res_price in reserved_prices.items():
                term = "1-year" if "1yr" in res_type else "3-year"
                discount = ((on_demand_monthly - res_price["monthly"]) / on_demand_monthly) * 100 if on_demand_monthly > 0 else 0
                
                options[res_type] = {
                    "monthly_cost": res_price["monthly"],
                    "savings_amount": on_demand_monthly - res_price["monthly"],
                    "savings_percent": discount,
                    "commitment": term,
                    "pros": [f"{int(discount)}% savings", "Guaranteed availability", "Predictable costs"],
                    "cons": [f"{term} commitment", "Less flexible"],
                    "best_for": "Production workloads, steady usage, long-term projects"
                }
            
            # Determine best option based on risk tolerance and savings
            best_option = "on_demand"
            best_savings = 0
            
            # Spot is best if low risk and high savings
            if risk_level == "low" and options["spot"]["savings_percent"] > 60:
                best_option = "spot"
                best_savings = options["spot"]["savings_amount"]
            # Reserved 3yr is best if very high discount and commitment acceptable
            elif "reserved_3yr" in options and options["reserved_3yr"]["savings_percent"] > 50:
                best_option = "reserved_3yr"
                best_savings = options["reserved_3yr"]["savings_amount"]
            elif "committed_3yr" in options and options["committed_3yr"]["savings_percent"] > 50:
                best_option = "committed_3yr"
                best_savings = options["committed_3yr"]["savings_amount"]
            # Reserved 1yr is good middle ground
            elif "reserved_1yr" in options and options["reserved_1yr"]["savings_percent"] > 30:
                best_option = "reserved_1yr"
                best_savings = options["reserved_1yr"]["savings_amount"]
            elif "committed_1yr" in options and options["committed_1yr"]["savings_percent"] > 30:
                best_option = "committed_1yr"
                best_savings = options["committed_1yr"]["savings_amount"]
            
            return {
                "recommended_option": best_option,
                "estimated_monthly_savings": round(best_savings, 2),
                "estimated_annual_savings": round(best_savings * 12, 2),
                "all_options": options,
                "reasoning": self._get_recommendation_reasoning(best_option, risk_level, options)
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return {}
    
    def _get_recommendation_reasoning(self, best_option: str, risk_level: str, options: Dict) -> str:
        """Generate human-readable reasoning for recommendation"""
        if best_option == "spot":
            savings_pct = options["spot"]["savings_percent"]
            return f"🎯 Use Spot instances! With {risk_level} interruption risk and {savings_pct:.0f}% savings, spot is perfect for fault-tolerant workloads. Consider mixing 80% spot + 20% reserved for extra reliability."
        elif "reserved" in best_option or "committed" in best_option:
            term = "1-year" if "1yr" in best_option else "3-year"
            savings_pct = options[best_option]["savings_percent"]
            return f"🎯 Use {term} Reserved! Save {savings_pct:.0f}% with guaranteed availability. Perfect for steady production workloads. Tip: Combine with spot instances for even more savings on non-critical components."
        else:
            return "🎯 Use On-Demand for maximum flexibility. Consider reserved instances if usage is predictable, or spot instances for fault-tolerant workloads."
    
    def _calculate_interruption_frequency(self, volatility_percent: float, risk_level: str) -> Dict:
        """Calculate interruption frequency from volatility"""
        # Map volatility to interruption estimates
        # Based on research: low volatility = 5-10% interruptions/month
        #                    medium = 15-25%, high = 30-50%
        
        if risk_level == "low":
            interruption_rate = volatility_percent * 0.5  # Lower bound
            interruptions_per_month = max(2, min(3, int(30 * (interruption_rate / 100))))
            uptime_percent = 100 - (interruption_rate * 0.5)
        elif risk_level == "medium":
            interruption_rate = volatility_percent * 0.7
            interruptions_per_month = max(5, min(7, int(30 * (interruption_rate / 100))))
            uptime_percent = 100 - interruption_rate
        else:  # high
            interruption_rate = volatility_percent
            interruptions_per_month = max(10, min(15, int(30 * (interruption_rate / 100))))
            uptime_percent = 100 - (interruption_rate * 1.5)
        
        # Ensure uptime is reasonable
        uptime_percent = max(85, min(99.5, uptime_percent))
        
        # Day of week patterns (weekends safer)
        day_patterns = {
            "Monday": "medium" if risk_level == "low" else "high",
            "Tuesday": "medium" if risk_level == "low" else "high",
            "Wednesday": "medium",
            "Thursday": "medium" if risk_level == "low" else "high",
            "Friday": "medium",
            "Saturday": "low",
            "Sunday": "low"
        }
        
        return {
            "interruption_rate_percent": round(interruption_rate, 1),
            "interruptions_per_month": interruptions_per_month,
            "uptime_percent": round(uptime_percent, 2),
            "avg_uptime_hours": round((30 * 24) * (uptime_percent / 100), 1),
            "day_patterns": day_patterns,
            "best_practices": [
                "✅ Use AWS Spot Fleet / GCP MIG for auto-replacement",
                "✅ Implement graceful shutdown (2-minute warning)",
                "✅ Diversify across multiple AZs",
                "✅ Mix spot (80%) + on-demand (20%) for reliability",
                "✅ Use stateless workloads or checkpoint frequently"
            ]
        }