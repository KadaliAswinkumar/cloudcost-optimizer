"""
Cost Calculator Service
Calculates and compares costs across different pricing models.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PricingStrategy(str, Enum):
    """Available pricing strategies."""
    ON_DEMAND = "on_demand"
    RESERVED_1YR_NO_UPFRONT = "reserved_1yr_no_upfront"
    RESERVED_1YR_PARTIAL = "reserved_1yr_partial"
    RESERVED_1YR_ALL_UPFRONT = "reserved_1yr_all_upfront"
    RESERVED_3YR_NO_UPFRONT = "reserved_3yr_no_upfront"
    RESERVED_3YR_PARTIAL = "reserved_3yr_partial"
    RESERVED_3YR_ALL_UPFRONT = "reserved_3yr_all_upfront"
    SPOT = "spot"
    SAVINGS_PLAN = "savings_plan"


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for a pricing strategy."""
    strategy: PricingStrategy
    hourly_cost: Decimal
    daily_cost: Decimal
    monthly_cost: Decimal
    annual_cost: Decimal
    upfront_cost: Decimal
    effective_hourly: Decimal  # Including upfront amortized
    total_commitment: Decimal  # Total cost over commitment period
    
    def to_dict(self) -> Dict:
        return {
            "strategy": self.strategy.value,
            "hourly_cost": float(self.hourly_cost),
            "daily_cost": float(self.daily_cost),
            "monthly_cost": float(self.monthly_cost),
            "annual_cost": float(self.annual_cost),
            "upfront_cost": float(self.upfront_cost),
            "effective_hourly": float(self.effective_hourly),
            "total_commitment": float(self.total_commitment),
        }


class CostCalculator:
    """
    Calculates costs and savings across pricing models.
    
    Supports:
    - On-Demand pricing
    - Reserved Instances (1yr/3yr, various payment options)
    - Spot pricing
    - Break-even analysis
    """
    
    # Hours in different periods
    HOURS_PER_DAY = 24
    HOURS_PER_MONTH = 730  # Average
    HOURS_PER_YEAR = 8760
    
    # Reserved instance discount estimates (when actual pricing unavailable)
    RESERVED_DISCOUNTS = {
        "1yr_no_upfront": 0.31,
        "1yr_partial": 0.38,
        "1yr_all_upfront": 0.40,
        "3yr_no_upfront": 0.45,
        "3yr_partial": 0.55,
        "3yr_all_upfront": 0.60,
    }
    
    def __init__(self):
        """Initialize calculator."""
        pass
    
    def calculate_on_demand_cost(
        self,
        hourly_rate: Decimal,
        hours: int = None
    ) -> CostBreakdown:
        """
        Calculate On-Demand costs.
        
        Args:
            hourly_rate: On-Demand hourly rate
            hours: Custom hours (defaults to 730/month)
            
        Returns:
            Cost breakdown
        """
        hours = hours or self.HOURS_PER_MONTH
        
        hourly = hourly_rate
        daily = hourly * self.HOURS_PER_DAY
        monthly = hourly * self.HOURS_PER_MONTH
        annual = hourly * self.HOURS_PER_YEAR
        
        return CostBreakdown(
            strategy=PricingStrategy.ON_DEMAND,
            hourly_cost=hourly.quantize(Decimal("0.000001")),
            daily_cost=daily.quantize(Decimal("0.01")),
            monthly_cost=monthly.quantize(Decimal("0.01")),
            annual_cost=annual.quantize(Decimal("0.01")),
            upfront_cost=Decimal("0"),
            effective_hourly=hourly.quantize(Decimal("0.000001")),
            total_commitment=monthly.quantize(Decimal("0.01")),  # No commitment
        )
    
    def calculate_reserved_cost(
        self,
        on_demand_hourly: Decimal,
        term_years: int = 1,
        payment_option: str = "no_upfront",
        reserved_hourly: Optional[Decimal] = None,
        upfront_cost: Optional[Decimal] = None,
    ) -> CostBreakdown:
        """
        Calculate Reserved Instance costs.
        
        Args:
            on_demand_hourly: On-Demand hourly rate for comparison
            term_years: 1 or 3 years
            payment_option: no_upfront, partial, or all_upfront
            reserved_hourly: Actual reserved hourly rate (if known)
            upfront_cost: Actual upfront cost (if known)
            
        Returns:
            Cost breakdown
        """
        # Determine discount
        discount_key = f"{term_years}yr_{payment_option}"
        discount = self.RESERVED_DISCOUNTS.get(discount_key, 0.30)
        
        # Calculate effective rate
        if reserved_hourly is not None and upfront_cost is not None:
            # Use actual pricing
            hourly = reserved_hourly
            upfront = upfront_cost
        else:
            # Estimate based on discount
            if payment_option == "all_upfront":
                hourly = Decimal("0")
                upfront = on_demand_hourly * self.HOURS_PER_YEAR * term_years * (1 - Decimal(str(discount)))
            elif payment_option == "partial":
                hourly = on_demand_hourly * (1 - Decimal(str(discount))) * Decimal("0.5")
                upfront = on_demand_hourly * self.HOURS_PER_YEAR * term_years * (1 - Decimal(str(discount))) * Decimal("0.5")
            else:  # no_upfront
                hourly = on_demand_hourly * (1 - Decimal(str(discount)))
                upfront = Decimal("0")
        
        # Calculate totals
        total_hours = self.HOURS_PER_YEAR * term_years
        total_cost = (hourly * total_hours) + upfront
        effective_hourly = total_cost / total_hours
        
        # Map to strategy enum
        strategy_map = {
            (1, "no_upfront"): PricingStrategy.RESERVED_1YR_NO_UPFRONT,
            (1, "partial"): PricingStrategy.RESERVED_1YR_PARTIAL,
            (1, "all_upfront"): PricingStrategy.RESERVED_1YR_ALL_UPFRONT,
            (3, "no_upfront"): PricingStrategy.RESERVED_3YR_NO_UPFRONT,
            (3, "partial"): PricingStrategy.RESERVED_3YR_PARTIAL,
            (3, "all_upfront"): PricingStrategy.RESERVED_3YR_ALL_UPFRONT,
        }
        strategy = strategy_map.get((term_years, payment_option), PricingStrategy.RESERVED_1YR_NO_UPFRONT)
        
        return CostBreakdown(
            strategy=strategy,
            hourly_cost=hourly.quantize(Decimal("0.000001")),
            daily_cost=(hourly * self.HOURS_PER_DAY).quantize(Decimal("0.01")),
            monthly_cost=(hourly * self.HOURS_PER_MONTH).quantize(Decimal("0.01")),
            annual_cost=(hourly * self.HOURS_PER_YEAR).quantize(Decimal("0.01")),
            upfront_cost=upfront.quantize(Decimal("0.01")),
            effective_hourly=effective_hourly.quantize(Decimal("0.000001")),
            total_commitment=total_cost.quantize(Decimal("0.01")),
        )
    
    def calculate_spot_cost(
        self,
        spot_price: Decimal,
        on_demand_hourly: Optional[Decimal] = None,
    ) -> CostBreakdown:
        """
        Calculate Spot Instance costs.
        
        Args:
            spot_price: Current spot price
            on_demand_hourly: On-Demand rate for comparison
            
        Returns:
            Cost breakdown
        """
        hourly = spot_price
        daily = hourly * self.HOURS_PER_DAY
        monthly = hourly * self.HOURS_PER_MONTH
        annual = hourly * self.HOURS_PER_YEAR
        
        return CostBreakdown(
            strategy=PricingStrategy.SPOT,
            hourly_cost=hourly.quantize(Decimal("0.000001")),
            daily_cost=daily.quantize(Decimal("0.01")),
            monthly_cost=monthly.quantize(Decimal("0.01")),
            annual_cost=annual.quantize(Decimal("0.01")),
            upfront_cost=Decimal("0"),
            effective_hourly=hourly.quantize(Decimal("0.000001")),
            total_commitment=Decimal("0"),  # No commitment
        )
    
    def compare_all_strategies(
        self,
        on_demand_hourly: Decimal,
        spot_price: Optional[Decimal] = None,
    ) -> List[Dict]:
        """
        Compare costs across all pricing strategies.
        
        Args:
            on_demand_hourly: On-Demand hourly rate
            spot_price: Current spot price (optional)
            
        Returns:
            List of cost comparisons sorted by effective hourly rate
        """
        comparisons = []
        
        # On-Demand
        on_demand = self.calculate_on_demand_cost(on_demand_hourly)
        comparisons.append(self._add_savings_info(on_demand, on_demand_hourly))
        
        # Reserved options
        for term in [1, 3]:
            for payment in ["no_upfront", "partial", "all_upfront"]:
                reserved = self.calculate_reserved_cost(
                    on_demand_hourly, term, payment
                )
                comparisons.append(self._add_savings_info(reserved, on_demand_hourly))
        
        # Spot (if available)
        if spot_price:
            spot = self.calculate_spot_cost(spot_price, on_demand_hourly)
            comparisons.append(self._add_savings_info(spot, on_demand_hourly))
        
        # Sort by effective hourly rate
        comparisons.sort(key=lambda x: x["effective_hourly"])
        
        return comparisons
    
    def _add_savings_info(
        self,
        breakdown: CostBreakdown,
        on_demand_hourly: Decimal
    ) -> Dict:
        """Add savings information to cost breakdown."""
        result = breakdown.to_dict()
        
        savings_amount = on_demand_hourly - breakdown.effective_hourly
        savings_pct = (savings_amount / on_demand_hourly * 100) if on_demand_hourly > 0 else 0
        
        result["savings_vs_ondemand"] = float(savings_amount.quantize(Decimal("0.000001")))
        result["savings_percentage"] = float(savings_pct.quantize(Decimal("0.01")))
        result["on_demand_hourly"] = float(on_demand_hourly)
        
        return result
    
    def calculate_break_even(
        self,
        on_demand_hourly: Decimal,
        reserved_effective_hourly: Decimal,
        upfront_cost: Decimal,
    ) -> Dict:
        """
        Calculate break-even point for Reserved vs On-Demand.
        
        Args:
            on_demand_hourly: On-Demand hourly rate
            reserved_effective_hourly: Reserved effective hourly rate
            upfront_cost: Reserved upfront cost
            
        Returns:
            Break-even analysis
        """
        if on_demand_hourly <= reserved_effective_hourly:
            return {
                "break_even_possible": False,
                "reason": "Reserved pricing is not cheaper than On-Demand",
            }
        
        hourly_savings = on_demand_hourly - reserved_effective_hourly
        
        if upfront_cost > 0:
            break_even_hours = upfront_cost / hourly_savings
            break_even_days = break_even_hours / self.HOURS_PER_DAY
            break_even_months = break_even_hours / self.HOURS_PER_MONTH
        else:
            break_even_hours = Decimal("0")
            break_even_days = Decimal("0")
            break_even_months = Decimal("0")
        
        return {
            "break_even_possible": True,
            "break_even_hours": float(break_even_hours.quantize(Decimal("0.1"))),
            "break_even_days": float(break_even_days.quantize(Decimal("0.1"))),
            "break_even_months": float(break_even_months.quantize(Decimal("0.1"))),
            "hourly_savings": float(hourly_savings),
            "monthly_savings": float(hourly_savings * self.HOURS_PER_MONTH),
            "recommendation": self._get_break_even_recommendation(break_even_months),
        }
    
    def _get_break_even_recommendation(self, break_even_months: Decimal) -> str:
        """Get recommendation based on break-even point."""
        months = float(break_even_months)
        
        if months <= 3:
            return "Excellent choice - breaks even quickly"
        elif months <= 6:
            return "Good choice - reasonable break-even period"
        elif months <= 9:
            return "Consider if your usage will be consistent"
        else:
            return "Long break-even period - ensure usage commitment"
    
    def project_costs(
        self,
        hourly_rate: Decimal,
        hours_per_month: int,
        months: int = 12,
    ) -> Dict:
        """
        Project costs over time.
        
        Args:
            hourly_rate: Hourly rate
            hours_per_month: Expected hours of usage per month
            months: Number of months to project
            
        Returns:
            Cost projection
        """
        monthly_cost = hourly_rate * hours_per_month
        projections = []
        
        cumulative = Decimal("0")
        for month in range(1, months + 1):
            cumulative += monthly_cost
            projections.append({
                "month": month,
                "monthly_cost": float(monthly_cost.quantize(Decimal("0.01"))),
                "cumulative_cost": float(cumulative.quantize(Decimal("0.01"))),
            })
        
        return {
            "hourly_rate": float(hourly_rate),
            "hours_per_month": hours_per_month,
            "monthly_cost": float(monthly_cost.quantize(Decimal("0.01"))),
            "total_months": months,
            "total_cost": float(cumulative.quantize(Decimal("0.01"))),
            "projections": projections,
        }

