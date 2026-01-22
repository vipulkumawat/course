#!/usr/bin/env python3
"""
Comprehensive demonstration of capacity planning system
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from collectors.metrics_collector import MetricsCollector
from analyzers.time_series_analyzer import TimeSeriesAnalyzer
from analyzers.forecasting_engine import ForecastingEngine
from calculators.resource_calculator import ResourceCalculator
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def demo_data_collection():
    print_section("1. Historical Data Collection")
    
    collector = MetricsCollector()
    df = collector.collect_historical_data(days=90)
    collector.save_historical_data(df)
    
    summary = collector.get_data_summary(df)
    print(f"\n📊 Collected Data Summary:")
    print(f"   Total data points: {summary['total_points']}")
    print(f"   Date range: {summary['date_range']['days']} days")
    print(f"   Log volume range: {summary['log_volume']['min']:.0f} - {summary['log_volume']['max']:.0f} logs/sec")
    print(f"   Current load: {summary['log_volume']['current']:.0f} logs/sec")
    
    return df


def demo_pattern_analysis(df):
    print_section("2. Time-Series Pattern Analysis")
    
    analyzer = TimeSeriesAnalyzer()
    patterns = analyzer.get_pattern_summary(df)
    
    print(f"\n📈 Detected Patterns:")
    print(f"   Trend Strength: {patterns['trend_strength']:.1%} ({'Strong' if patterns['has_strong_trend'] else 'Weak'})")
    print(f"   Seasonal Strength: {patterns['seasonal_strength']:.1%} ({'Strong' if patterns['has_strong_seasonality'] else 'Weak'})")
    print(f"   Growth Rate: {patterns['growth_rate_monthly']:.1%} per month")
    
    if patterns['has_strong_trend']:
        print(f"   → System shows consistent growth trend")
    if patterns['has_strong_seasonality']:
        print(f"   → Clear daily/weekly usage patterns detected")


def demo_forecasting():
    print_section("3. Multi-Algorithm Forecasting")
    
    engine = ForecastingEngine()
    engine.load_historical_data('data/historical.csv')
    
    # Generate forecasts
    forecast_7d = engine.predict(days=7, confidence=0.90)
    forecast_30d = engine.predict(days=30, confidence=0.90)
    
    current_load = engine.historical_data['logs_per_second'].iloc[-1]
    predicted_7d = forecast_7d['predictions'][-24]  # Last day
    predicted_30d = forecast_30d['predictions'][-24]
    
    print(f"\n🔮 Forecast Results:")
    print(f"   Current Load: {current_load:.0f} logs/sec")
    print(f"   7-day Prediction: {predicted_7d:.0f} logs/sec ({(predicted_7d/current_load-1)*100:+.1f}%)")
    print(f"   30-day Prediction: {predicted_30d:.0f} logs/sec ({(predicted_30d/current_load-1)*100:+.1f}%)")
    
    # Evaluate models
    print(f"\n📊 Model Performance:")
    evaluation = engine.evaluate_models()
    for model, metrics in evaluation.items():
        print(f"   {model.title()}: RMSE {metrics['rmse_percent']:.1f}%, MAPE {metrics['mape']:.1%}")
    
    return forecast_30d


def demo_capacity_planning(forecast):
    print_section("4. Infrastructure Capacity Planning")
    
    calculator = ResourceCalculator()
    plan = calculator.generate_capacity_plan(forecast)
    
    print(f"\n💻 Current Infrastructure:")
    print(f"   Nodes: {plan['current_capacity']['nodes']}")
    print(f"   Capacity: {plan['current_capacity']['logs_per_second']:.0f} logs/sec")
    print(f"   Monthly Cost: ${plan['cost_projection']['current_monthly_usd']:.2f}")
    
    print(f"\n📈 Peak Requirements (30-day forecast):")
    print(f"   Day: {plan['peak_requirement']['day']}")
    print(f"   Required Nodes: {plan['peak_requirement']['nodes']}")
    print(f"   Peak Load: {plan['peak_requirement']['logs_per_second']:.0f} logs/sec")
    print(f"   Projected Monthly Cost: ${plan['cost_projection']['projected_monthly_usd']:.2f}")
    
    if plan['scale_events']:
        print(f"\n🚨 Scaling Events Detected: {len(plan['scale_events'])}")
        for event in plan['scale_events'][:3]:  # Show first 3
            print(f"   Day {event['day']}: {event['action']} (Load: {event['predicted_load']:.0f} logs/sec)")
    
    print(f"\n💰 Cost Analysis:")
    print(f"   Additional Monthly: ${plan['cost_projection']['additional_monthly_usd']:.2f}")
    print(f"   Additional Annual: ${plan['cost_projection']['annual_additional_usd']:.2f}")
    
    return plan


def demo_recommendations(plan):
    print_section("5. Actionable Recommendations")
    
    nodes_to_add = plan['peak_requirement']['nodes'] - plan['current_capacity']['nodes']
    
    print(f"\n✅ Capacity Planning Recommendations:")
    
    if nodes_to_add > 0:
        print(f"   1. Add {nodes_to_add} nodes by day {plan['peak_requirement']['day']}")
        print(f"      → Maintains headroom for predicted load spikes")
        print(f"      → Estimated cost: ${nodes_to_add * 150:.2f}/month")
        
        print(f"\n   2. Scale gradually to optimize costs:")
        if len(plan['scale_events']) > 0:
            for i, event in enumerate(plan['scale_events'][:2], 1):
                print(f"      Step {i}: Day {event['day']} - {event['action']}")
        
        print(f"\n   3. Monitor utilization approaching 80% threshold")
        print(f"      → Set up automated alerts")
        print(f"      → Review forecasts weekly")
    else:
        print(f"   ✅ Current capacity sufficient for 30-day forecast")
        print(f"   → Monitor for unexpected growth patterns")
        print(f"   → Review forecast next week")


def main():
    print("\n🚀 Capacity Planning System - Complete Demonstration")
    print("="*60)
    
    try:
        # Run demonstration
        df = demo_data_collection()
        demo_pattern_analysis(df)
        forecast = demo_forecasting()
        plan = demo_capacity_planning(forecast)
        demo_recommendations(plan)
        
        print_section("Demonstration Complete")
        print("\n✅ All capacity planning components working correctly!")
        print("\n📊 Next Steps:")
        print("   1. Start API server: python -m src.api.forecast_api")
        print("   2. Access API docs: http://localhost:8000/docs")
        print("   3. Get recommendations: curl http://localhost:8000/api/capacity/recommendations")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
