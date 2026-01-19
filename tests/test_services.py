"""
Service Layer Tests
"""

import pytest
from decimal import Decimal

from src.services.cost_calculator import CostCalculator, PricingStrategy


class TestCostCalculator:
    """Tests for CostCalculator service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = CostCalculator()
        self.sample_hourly_rate = Decimal("0.10")  # $0.10/hour
    
    def test_on_demand_calculation(self):
        """Test on-demand cost calculation."""
        result = self.calculator.calculate_on_demand_cost(self.sample_hourly_rate)
        
        assert result.strategy == PricingStrategy.ON_DEMAND
        assert result.hourly_cost == Decimal("0.100000")
        assert result.daily_cost == Decimal("2.40")
        assert result.monthly_cost == Decimal("73.00")
        assert result.upfront_cost == Decimal("0")
    
    def test_reserved_1yr_calculation(self):
        """Test 1-year reserved calculation."""
        result = self.calculator.calculate_reserved_cost(
            self.sample_hourly_rate,
            term_years=1,
            payment_option="no_upfront"
        )
        
        assert result.strategy == PricingStrategy.RESERVED_1YR_NO_UPFRONT
        assert result.effective_hourly < self.sample_hourly_rate
        assert result.upfront_cost == Decimal("0")
    
    def test_reserved_3yr_calculation(self):
        """Test 3-year reserved calculation."""
        result = self.calculator.calculate_reserved_cost(
            self.sample_hourly_rate,
            term_years=3,
            payment_option="all_upfront"
        )
        
        assert result.strategy == PricingStrategy.RESERVED_3YR_ALL_UPFRONT
        assert result.effective_hourly < self.sample_hourly_rate
        assert result.hourly_cost == Decimal("0")  # All upfront means no hourly
        assert result.upfront_cost > Decimal("0")
    
    def test_spot_calculation(self):
        """Test spot cost calculation."""
        spot_price = Decimal("0.03")  # 70% discount
        result = self.calculator.calculate_spot_cost(spot_price, self.sample_hourly_rate)
        
        assert result.strategy == PricingStrategy.SPOT
        assert result.hourly_cost == Decimal("0.030000")
        assert result.upfront_cost == Decimal("0")
        assert result.total_commitment == Decimal("0")
    
    def test_compare_all_strategies(self):
        """Test comparing all pricing strategies."""
        comparisons = self.calculator.compare_all_strategies(
            self.sample_hourly_rate,
            spot_price=Decimal("0.03")
        )
        
        assert len(comparisons) > 0
        
        # Should be sorted by effective hourly rate
        for i in range(len(comparisons) - 1):
            assert comparisons[i]["effective_hourly"] <= comparisons[i+1]["effective_hourly"]
        
        # Each comparison should have savings info
        for comp in comparisons:
            assert "savings_percentage" in comp
            assert "savings_vs_ondemand" in comp
    
    def test_break_even_analysis(self):
        """Test break-even calculation."""
        reserved_hourly = Decimal("0.07")
        upfront = Decimal("100")
        
        result = self.calculator.calculate_break_even(
            self.sample_hourly_rate,
            reserved_hourly,
            upfront
        )
        
        assert result["break_even_possible"] == True
        assert result["break_even_hours"] > 0
        assert "recommendation" in result
    
    def test_break_even_not_possible(self):
        """Test break-even when reserved is more expensive."""
        result = self.calculator.calculate_break_even(
            self.sample_hourly_rate,
            Decimal("0.15"),  # More expensive than on-demand
            Decimal("0")
        )
        
        assert result["break_even_possible"] == False
    
    def test_cost_projection(self):
        """Test cost projection over time."""
        result = self.calculator.project_costs(
            self.sample_hourly_rate,
            hours_per_month=500,
            months=12
        )
        
        assert result["total_months"] == 12
        assert len(result["projections"]) == 12
        assert result["projections"][-1]["cumulative_cost"] == result["total_cost"]
        
        # Verify cumulative is increasing
        prev_cumulative = 0
        for proj in result["projections"]:
            assert proj["cumulative_cost"] > prev_cumulative
            prev_cumulative = proj["cumulative_cost"]


class TestCostBreakdown:
    """Tests for CostBreakdown dataclass."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        calc = CostCalculator()
        breakdown = calc.calculate_on_demand_cost(Decimal("0.10"))
        
        result = breakdown.to_dict()
        
        assert isinstance(result, dict)
        assert "strategy" in result
        assert "hourly_cost" in result
        assert isinstance(result["hourly_cost"], float)

