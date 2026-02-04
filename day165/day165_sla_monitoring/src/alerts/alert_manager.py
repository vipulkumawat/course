import asyncio
from datetime import datetime
from typing import List
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class AlertManager:
    def __init__(self, config):
        self.config = config
        self.alerts_sent = {}
        self.running = False
    
    async def start_monitoring(self, evaluator):
        self.running = True
        self.evaluator = evaluator
        print("📢 Alert monitoring started")
        while self.running:
            try:
                violations = await self.evaluator.get_violations()
                for v in violations:
                    if self._should_alert(v):
                        await self._send_alert(v)
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Alert error: {e}")
                await asyncio.sleep(10)
    
    def _should_alert(self, v) -> bool:
        severity_cfg = self.config['alerting']['severity_levels'][v.severity]
        return v.breach_duration_seconds >= severity_cfg['breach_duration_seconds']
    
    async def _send_alert(self, v):
        key = f"{v.slo_name}_{v.timestamp.date()}"
        if key not in self.alerts_sent:
            print(f"📧 ALERT: {v.slo_name} - {v.severity.upper()} (actual={v.actual_value:.2f}, target={v.target_value})")
            self.alerts_sent[key] = datetime.now()
    
    async def stop(self):
        self.running = False
