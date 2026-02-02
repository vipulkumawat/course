"""
WebSocket server for real-time dependency updates
Watches log files and pushes updates to frontend
"""
import asyncio
import json
from datetime import datetime
import websockets
from parser import DependencyParser
from graph import DependencyGraph
from analyzer import ImpactAnalyzer

class DependencyServer:
    def __init__(self, log_file: str, port: int = 8765):
        self.log_file = log_file
        self.port = port
        self.parser = DependencyParser()
        self.graph = DependencyGraph()
        self.analyzer = ImpactAnalyzer(self.graph)
        self.clients = set()
        self.last_position = 0
    
    async def register(self, websocket):
        self.clients.add(websocket)
        # Send current graph state
        await websocket.send(json.dumps({
            'type': 'init',
            'data': json.loads(self.graph.to_json())
        }))
    
    async def unregister(self, websocket):
        self.clients.discard(websocket)
    
    async def broadcast(self, message):
        if self.clients:
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )
    
    async def watch_logs(self):
        """Watch log file for new entries"""
        while True:
            try:
                with open(self.log_file, 'r') as f:
                    f.seek(self.last_position)
                    for line in f:
                        dep = self.parser.parse_log_line(line.strip())
                        if dep:
                            self.graph.add_dependency(
                                dep['caller'],
                                dep['callee'],
                                dep['latency'],
                                dep['type'],
                                dep['timestamp']
                            )
                            
                            # Broadcast update
                            await self.broadcast(json.dumps({
                                'type': 'update',
                                'dependency': {
                                    'caller': dep['caller'],
                                    'callee': dep['callee'],
                                    'latency': dep['latency'],
                                    'type': dep['type']
                                }
                            }))
                            
                            # Check for patterns
                            cycles = self.graph.find_cycles()
                            if cycles:
                                await self.broadcast(json.dumps({
                                    'type': 'alert',
                                    'alert_type': 'cycle',
                                    'cycles': cycles
                                }))
                            
                            spofs = self.graph.find_single_points_of_failure()
                            if spofs:
                                await self.broadcast(json.dumps({
                                    'type': 'alert',
                                    'alert_type': 'spof',
                                    'spofs': [{'service': s, 'count': c} for s, c in spofs[:3]]
                                }))
                    
                    self.last_position = f.tell()
            
            except FileNotFoundError:
                pass
            
            await asyncio.sleep(0.5)
    
    async def handler(self, websocket, path):
        await self.register(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if data['type'] == 'get_impact':
                    service = data['service']
                    impact = self.analyzer.simulate_failure(service)
                    await websocket.send(json.dumps({
                        'type': 'impact_result',
                        'impact': impact
                    }))
                
                elif data['type'] == 'get_critical_paths':
                    paths = self.graph.get_critical_paths()
                    await websocket.send(json.dumps({
                        'type': 'critical_paths',
                        'paths': [{'path': p, 'latency': l} for p, l in paths]
                    }))
        
        finally:
            await self.unregister(websocket)
    
    async def start(self):
        """Start the WebSocket server"""
        async with websockets.serve(self.handler, "0.0.0.0", self.port):
            print(f"WebSocket server started on ws://0.0.0.0:{self.port}")
            await self.watch_logs()

def main():
    import sys
    log_file = sys.argv[1] if len(sys.argv) > 1 else '../logs/sample.log'
    server = DependencyServer(log_file)
    asyncio.run(server.start())

if __name__ == '__main__':
    main()
