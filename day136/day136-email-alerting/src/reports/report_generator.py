import asyncio
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Dict, Any, List
import io
import base64
from dataclasses import dataclass
import redis
import logging

@dataclass
class ReportConfig:
    title: str
    description: str
    metrics: List[str]
    time_range_hours: int = 24
    chart_types: List[str] = None  # line, bar, pie
    recipients: List[str] = None

class ReportGenerator:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        try:
            plt.style.use('seaborn-v0_8')
        except OSError:
            # Fallback to default style if seaborn-v0_8 is not available
            plt.style.use('default')
        
    async def generate_daily_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate daily metrics report"""
        try:
            # Fetch metrics data
            metrics_data = await self._fetch_metrics_data(config.metrics, config.time_range_hours)
            
            # Generate charts
            charts = await self._generate_charts(metrics_data, config.chart_types or ['line'])
            
            # Calculate statistics
            stats = self._calculate_statistics(metrics_data)
            
            # Create report data
            report_data = {
                'title': config.title,
                'description': config.description,
                'generation_time': datetime.now().isoformat(),
                'time_range': f"Last {config.time_range_hours} hours",
                'metrics': stats,
                'charts': charts,
                'summary': self._generate_summary(stats),
                'recommendations': self._generate_recommendations(stats)
            }
            
            logging.info(f"📊 Generated report: {config.title}")
            return report_data
            
        except Exception as e:
            logging.error(f"❌ Report generation failed: {str(e)}")
            return {"error": str(e)}
    
    async def _fetch_metrics_data(self, metrics: List[str], hours: int) -> Dict[str, List[Dict]]:
        """Fetch time-series metrics data from Redis"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        metrics_data = {}
        
        # Simulate metrics data (in production, fetch from your metrics store)
        for metric in metrics:
            data_points = []
            current_time = start_time
            
            while current_time <= end_time:
                # Generate realistic sample data
                value = self._generate_sample_metric_value(metric, current_time)
                data_points.append({
                    'timestamp': current_time.isoformat(),
                    'value': value
                })
                current_time += timedelta(minutes=15)  # 15-minute intervals
            
            metrics_data[metric] = data_points
        
        return metrics_data
    
    def _generate_sample_metric_value(self, metric: str, timestamp: datetime) -> float:
        """Generate realistic sample metric values"""
        import random
        import math
        
        hour = timestamp.hour
        
        if metric == "requests_per_second":
            # Higher during business hours
            base = 100 + 50 * math.sin((hour - 9) * math.pi / 12)
            return max(10, base + random.uniform(-20, 20))
        elif metric == "error_rate":
            # Lower error rates generally
            base = 2.0 + math.sin(hour * math.pi / 12)
            return max(0.1, base + random.uniform(-1, 1))
        elif metric == "response_time_ms":
            # Higher response times during peak hours
            base = 150 + 50 * math.sin((hour - 12) * math.pi / 8)
            return max(50, base + random.uniform(-30, 30))
        else:
            return random.uniform(0, 100)
    
    async def _generate_charts(self, metrics_data: Dict[str, List[Dict]], chart_types: List[str]) -> Dict[str, str]:
        """Generate charts and return as base64 encoded images"""
        charts = {}
        
        for chart_type in chart_types:
            if chart_type == "line":
                chart_data = await self._create_line_chart(metrics_data)
                charts["line_chart"] = chart_data
            elif chart_type == "bar":
                chart_data = await self._create_bar_chart(metrics_data)
                charts["bar_chart"] = chart_data
            elif chart_type == "pie":
                chart_data = await self._create_pie_chart(metrics_data)
                charts["pie_chart"] = chart_data
        
        return charts
    
    async def _create_line_chart(self, metrics_data: Dict[str, List[Dict]]) -> str:
        """Create line chart showing metrics over time"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for metric, data_points in metrics_data.items():
            timestamps = [datetime.fromisoformat(dp['timestamp']) for dp in data_points]
            values = [dp['value'] for dp in data_points]
            
            ax.plot(timestamps, values, label=metric.replace('_', ' ').title(), linewidth=2)
        
        ax.set_xlabel('Time')
        ax.set_ylabel('Value')
        ax.set_title('Metrics Over Time')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Convert to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        chart_data = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close(fig)
        
        return chart_data
    
    async def _create_bar_chart(self, metrics_data: Dict[str, List[Dict]]) -> str:
        """Create bar chart showing average values"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        metrics_averages = {}
        for metric, data_points in metrics_data.items():
            avg_value = sum(dp['value'] for dp in data_points) / len(data_points)
            metrics_averages[metric.replace('_', ' ').title()] = avg_value
        
        metrics_names = list(metrics_averages.keys())
        values = list(metrics_averages.values())
        
        bars = ax.bar(metrics_names, values, color=['#3498db', '#e74c3c', '#f39c12'])
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(values) * 0.01,
                   f'{value:.1f}', ha='center', va='bottom')
        
        ax.set_title('Average Metric Values')
        ax.set_ylabel('Value')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Convert to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        chart_data = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close(fig)
        
        return chart_data
    
    async def _create_pie_chart(self, metrics_data: Dict[str, List[Dict]]) -> str:
        """Create pie chart showing metric distribution"""
        if len(metrics_data) < 2:
            return ""
            
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Calculate totals for each metric
        metric_totals = {}
        for metric, data_points in metrics_data.items():
            total = sum(dp['value'] for dp in data_points)
            metric_totals[metric.replace('_', ' ').title()] = total
        
        labels = list(metric_totals.keys())
        sizes = list(metric_totals.values())
        colors = ['#3498db', '#e74c3c', '#f39c12', '#2ecc71']
        
        ax.pie(sizes, labels=labels, colors=colors[:len(labels)], autopct='%1.1f%%', startangle=90)
        ax.set_title('Metric Distribution')
        
        plt.tight_layout()
        
        # Convert to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        chart_data = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close(fig)
        
        return chart_data
    
    def _calculate_statistics(self, metrics_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Calculate statistical summaries for metrics"""
        stats = {}
        
        for metric, data_points in metrics_data.items():
            values = [dp['value'] for dp in data_points]
            
            stats[metric] = {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'average': sum(values) / len(values),
                'median': sorted(values)[len(values) // 2],
                'std_dev': pd.Series(values).std()
            }
        
        return stats
    
    def _generate_summary(self, stats: Dict[str, Any]) -> str:
        """Generate natural language summary of the report"""
        summaries = []
        
        for metric, metric_stats in stats.items():
            avg = metric_stats['average']
            metric_name = metric.replace('_', ' ').title()
            
            if metric == "error_rate":
                if avg < 1.0:
                    summaries.append(f"✅ {metric_name} is excellent at {avg:.2f}%")
                elif avg < 5.0:
                    summaries.append(f"⚠️ {metric_name} is acceptable at {avg:.2f}%")
                else:
                    summaries.append(f"🚨 {metric_name} is concerning at {avg:.2f}%")
            elif metric == "response_time_ms":
                if avg < 100:
                    summaries.append(f"✅ {metric_name} is fast at {avg:.0f}ms")
                elif avg < 500:
                    summaries.append(f"⚠️ {metric_name} is moderate at {avg:.0f}ms")
                else:
                    summaries.append(f"🚨 {metric_name} is slow at {avg:.0f}ms")
            else:
                summaries.append(f"📊 {metric_name} averaged {avg:.2f}")
        
        return ". ".join(summaries)
    
    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on metrics"""
        recommendations = []
        
        for metric, metric_stats in stats.items():
            avg = metric_stats['average']
            
            if metric == "error_rate" and avg > 5.0:
                recommendations.append("Consider investigating error patterns and implementing additional monitoring")
            elif metric == "response_time_ms" and avg > 500:
                recommendations.append("Review application performance and consider scaling or optimization")
            elif metric == "requests_per_second" and avg > 1000:
                recommendations.append("Monitor capacity and consider auto-scaling policies")
        
        if not recommendations:
            recommendations.append("System performance is within normal parameters")
        
        return recommendations
