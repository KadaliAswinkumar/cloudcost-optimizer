"""
Historical Spot Price Generator
Generates realistic 30-day price history for charts
"""

from datetime import datetime, timedelta
import random
from typing import List, Dict


class HistoricalPriceGenerator:
    """Generate realistic historical spot price patterns"""
    
    @staticmethod
    def generate_30day_history(
        current_price: float,
        volatility: float,
        provider: str = "aws"
    ) -> List[Dict]:
        """
        Generate 30 days of hourly spot prices with realistic patterns
        
        Args:
            current_price: Current spot price (hourly)
            volatility: Price volatility (0.0 to 1.0)
            provider: Cloud provider for pattern adjustments
        
        Returns:
            List of price points with timestamps
        """
        history = []
        now = datetime.utcnow()
        
        # Base patterns
        # Weekdays (Mon-Fri) have higher prices during business hours (9am-5pm)
        # Weekends (Sat-Sun) have lower prices
        # Night hours (12am-6am) have lowest prices
        
        for days_ago in range(30, -1, -1):  # 30 days to now
            timestamp = now - timedelta(days=days_ago)
            
            # Daily pattern (0-24 hours)
            for hour in range(24):
                point_time = timestamp.replace(hour=hour, minute=0, second=0)
                
                # Base price with some randomness
                base = current_price
                
                # Day of week pattern (0=Monday, 6=Sunday)
                day_of_week = point_time.weekday()
                
                # Weekend discount (10-20% cheaper)
                if day_of_week >= 5:  # Saturday or Sunday
                    base *= random.uniform(0.80, 0.90)
                
                # Business hours premium (9am-5pm on weekdays)
                if day_of_week < 5 and 9 <= hour <= 17:
                    base *= random.uniform(1.10, 1.25)
                
                # Night discount (12am-6am)
                elif hour < 6:
                    base *= random.uniform(0.85, 0.95)
                
                # Apply volatility (random fluctuations)
                fluctuation = random.uniform(-volatility, volatility)
                price = base * (1 + fluctuation)
                
                # Ensure price doesn't go negative or too low
                price = max(price, current_price * 0.3)
                
                # Occasional spikes (demand surge) - 5% chance
                if random.random() < 0.05:
                    price *= random.uniform(1.3, 1.8)
                
                # Occasional drops (low demand) - 3% chance
                if random.random() < 0.03:
                    price *= random.uniform(0.5, 0.7)
                
                history.append({
                    "timestamp": point_time.isoformat(),
                    "price": round(price, 4),
                    "day_of_week": day_of_week,
                    "hour": hour
                })
        
        return history
    
    @staticmethod
    def calculate_insights(history: List[Dict]) -> Dict:
        """Calculate insights from historical data"""
        if not history:
            return {}
        
        prices = [h["price"] for h in history]
        
        # Group by day of week
        by_day = {}
        for h in history:
            day = h["day_of_week"]
            if day not in by_day:
                by_day[day] = []
            by_day[day].append(h["price"])
        
        # Group by hour
        by_hour = {}
        for h in history:
            hour = h["hour"]
            if hour not in by_hour:
                by_hour[hour] = []
            by_hour[hour].append(h["price"])
        
        # Calculate averages
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        avg_by_day = {
            day_names[day]: round(sum(prices) / len(prices), 4)
            for day, prices in by_day.items()
        }
        
        avg_by_hour = {
            hour: round(sum(prices) / len(prices), 4)
            for hour, prices in by_hour.items()
        }
        
        # Find best and worst times
        sorted_hours = sorted(avg_by_hour.items(), key=lambda x: x[1])
        sorted_days = sorted(avg_by_day.items(), key=lambda x: x[1])
        
        return {
            "overall": {
                "min": round(min(prices), 4),
                "max": round(max(prices), 4),
                "avg": round(sum(prices) / len(prices), 4),
                "median": round(sorted(prices)[len(prices) // 2], 4)
            },
            "by_day_of_week": avg_by_day,
            "by_hour": avg_by_hour,
            "best_times": {
                "cheapest_hours": [
                    {"hour": h, "avg_price": p}
                    for h, p in sorted_hours[:5]
                ],
                "cheapest_days": [
                    {"day": d, "avg_price": p}
                    for d, p in sorted_days[:3]
                ]
            },
            "worst_times": {
                "most_expensive_hours": [
                    {"hour": h, "avg_price": p}
                    for h, p in sorted_hours[-5:]
                ],
                "most_expensive_days": [
                    {"day": d, "avg_price": p}
                    for d, p in sorted_days[-3:]
                ]
            }
        }
    
    @staticmethod
    def get_launch_recommendations(insights: Dict, on_demand_price: float) -> List[Dict]:
        """Generate actionable launch recommendations"""
        if not insights or "best_times" not in insights:
            return []
        
        recommendations = []
        
        # Best time recommendations
        cheapest_hours = insights["best_times"]["cheapest_hours"]
        if cheapest_hours:
            best_hour = cheapest_hours[0]
            savings_pct = ((on_demand_price - best_hour["avg_price"]) / on_demand_price) * 100
            
            # Convert 24h to 12h format
            hour_12h = best_hour["hour"] % 12 or 12
            am_pm = "AM" if best_hour["hour"] < 12 else "PM"
            
            recommendations.append({
                "type": "best_hour",
                "title": f"🟢 Best Time to Launch",
                "description": f"Launch instances around {hour_12h}:00 {am_pm} for lowest prices",
                "savings": f"{savings_pct:.0f}% cheaper than on-demand",
                "price": f"${best_hour['avg_price']}/hr",
                "confidence": "high"
            })
        
        # Weekend recommendation
        cheapest_days = insights["best_times"]["cheapest_days"]
        if cheapest_days and any(d["day"] in ["Sat", "Sun"] for d in cheapest_days[:2]):
            recommendations.append({
                "type": "weekend",
                "title": "🟢 Weekend Advantage",
                "description": "Spot prices are typically 10-20% lower on weekends",
                "tip": "Schedule non-urgent batch jobs for Saturday/Sunday",
                "confidence": "high"
            })
        
        # Avoid peak hours
        worst_hours = insights["worst_times"]["most_expensive_hours"]
        if worst_hours:
            worst_hour = worst_hours[-1]
            hour_12h = worst_hour["hour"] % 12 or 12
            am_pm = "AM" if worst_hour["hour"] < 12 else "PM"
            
            recommendations.append({
                "type": "avoid_peak",
                "title": "🔴 Avoid Peak Hours",
                "description": f"Prices spike around {hour_12h}:00 {am_pm} (business hours)",
                "tip": "Delay non-critical launches until off-peak hours",
                "price": f"${worst_hour['avg_price']}/hr",
                "confidence": "medium"
            })
        
        return recommendations
