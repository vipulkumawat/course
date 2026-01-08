"""
Infrastructure Deployment Dashboard
Real-time monitoring of multi-cloud deployments
"""

from flask import Flask, render_template, jsonify, request
import subprocess
import json
from pathlib import Path
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

PROJECT_ROOT = Path(__file__).parent.parent

class DeploymentMonitor:
    """Monitor and display deployment status"""
    
    # Demo mode - show mock data for demonstration
    DEMO_MODE = True
    
    @staticmethod
    def get_terraform_state(environment: str) -> dict:
        """Retrieve current Terraform state"""
        terraform_dir = PROJECT_ROOT / "terraform" / "environments" / environment
        
        try:
            result = subprocess.run(
                ["terraform", "show", "-json"],
                cwd=terraform_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            return {}
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def get_resource_count(environment: str) -> dict:
        """Count deployed resources by type"""
        # Demo mode: return mock resource counts
        if DeploymentMonitor.DEMO_MODE:
            demo_counts = {
                "dev": {
                    "aws_vpc": 1,
                    "aws_subnet": 6,
                    "aws_security_group": 3,
                    "aws_eks_cluster": 1,
                    "aws_eks_node_group": 2,
                    "aws_db_instance": 1,
                    "aws_elasticache_cluster": 1,
                    "aws_iam_role": 2,
                    "aws_cloudwatch_log_group": 1
                },
                "staging": {
                    "aws_vpc": 1,
                    "aws_subnet": 6,
                    "aws_security_group": 4,
                    "aws_eks_cluster": 1,
                    "aws_eks_node_group": 3,
                    "aws_db_instance": 1,
                    "aws_elasticache_cluster": 1,
                    "aws_iam_role": 3,
                    "aws_cloudwatch_log_group": 1,
                    "aws_nat_gateway": 2
                },
                "prod": {
                    "aws_vpc": 2,
                    "aws_subnet": 12,
                    "aws_security_group": 6,
                    "aws_eks_cluster": 2,
                    "aws_eks_node_group": 5,
                    "aws_db_instance": 2,
                    "aws_elasticache_cluster": 2,
                    "aws_iam_role": 5,
                    "aws_cloudwatch_log_group": 2,
                    "aws_nat_gateway": 4,
                    "aws_route_table": 6
                }
            }
            return demo_counts.get(environment, {})
        
        # Real mode: get from Terraform state
        state = DeploymentMonitor.get_terraform_state(environment)
        
        if "error" in state or not state:
            return {}
        
        resources = state.get("values", {}).get("root_module", {}).get("resources", [])
        
        counts = {}
        for resource in resources:
            resource_type = resource.get("type", "unknown")
            counts[resource_type] = counts.get(resource_type, 0) + 1
        
        return counts
    
    @staticmethod
    def estimate_costs(environment: str, cloud: str = 'aws') -> dict:
        """Estimate infrastructure costs"""
        # Cloud-specific cost estimation (demo data)
        cost_map = {
            "aws": {
                "dev": 150,
                "staging": 500,
                "prod": 2500
            },
            "azure": {
                "dev": 140,
                "staging": 480,
                "prod": 2400
            },
            "gcp": {
                "dev": 130,
                "staging": 450,
                "prod": 2300
            }
        }
        
        cloud_costs = cost_map.get(cloud, cost_map["aws"])
        return {
            "monthly": cloud_costs.get(environment, 0),
            "currency": "USD"
        }
    
    @staticmethod
    def get_demo_metrics(cloud: str) -> dict:
        """Get demo metrics for a specific cloud provider"""
        # Demo resource counts per cloud provider
        demo_data = {
            "aws": {
                "dev": {
                    "vpc": 1,
                    "subnet": 6,
                    "security_group": 3,
                    "eks_cluster": 1,
                    "eks_node_group": 2,
                    "rds_instance": 1,
                    "elasticache": 1,
                    "iam_role": 2,
                    "cloudwatch_log": 1
                },
                "staging": {
                    "vpc": 1,
                    "subnet": 6,
                    "security_group": 4,
                    "eks_cluster": 1,
                    "eks_node_group": 3,
                    "rds_instance": 1,
                    "elasticache": 1,
                    "iam_role": 3,
                    "cloudwatch_log": 1,
                    "nat_gateway": 2
                },
                "prod": {
                    "vpc": 2,
                    "subnet": 12,
                    "security_group": 6,
                    "eks_cluster": 2,
                    "eks_node_group": 5,
                    "rds_instance": 2,
                    "elasticache": 2,
                    "iam_role": 5,
                    "cloudwatch_log": 2,
                    "nat_gateway": 4,
                    "route_table": 6
                }
            },
            "azure": {
                "dev": {
                    "virtual_network": 1,
                    "subnet": 6,
                    "network_security_group": 3,
                    "aks_cluster": 1,
                    "vm_scale_set": 2,
                    "sql_database": 1,
                    "redis_cache": 1,
                    "managed_identity": 2,
                    "log_analytics": 1
                },
                "staging": {
                    "virtual_network": 1,
                    "subnet": 6,
                    "network_security_group": 4,
                    "aks_cluster": 1,
                    "vm_scale_set": 3,
                    "sql_database": 1,
                    "redis_cache": 1,
                    "managed_identity": 3,
                    "log_analytics": 1,
                    "load_balancer": 2
                },
                "prod": {
                    "virtual_network": 2,
                    "subnet": 12,
                    "network_security_group": 6,
                    "aks_cluster": 2,
                    "vm_scale_set": 5,
                    "sql_database": 2,
                    "redis_cache": 2,
                    "managed_identity": 5,
                    "log_analytics": 2,
                    "load_balancer": 4,
                    "route_table": 6
                }
            },
            "gcp": {
                "dev": {
                    "vpc_network": 1,
                    "subnet": 6,
                    "firewall_rule": 3,
                    "gke_cluster": 1,
                    "node_pool": 2,
                    "cloud_sql": 1,
                    "memorystore": 1,
                    "service_account": 2,
                    "logging": 1
                },
                "staging": {
                    "vpc_network": 1,
                    "subnet": 6,
                    "firewall_rule": 4,
                    "gke_cluster": 1,
                    "node_pool": 3,
                    "cloud_sql": 1,
                    "memorystore": 1,
                    "service_account": 3,
                    "logging": 1,
                    "cloud_nat": 2
                },
                "prod": {
                    "vpc_network": 2,
                    "subnet": 12,
                    "firewall_rule": 6,
                    "gke_cluster": 2,
                    "node_pool": 5,
                    "cloud_sql": 2,
                    "memorystore": 2,
                    "service_account": 5,
                    "logging": 2,
                    "cloud_nat": 4,
                    "route": 6
                }
            }
        }
        
        return demo_data.get(cloud, demo_data["aws"])

monitor = DeploymentMonitor()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/status/<environment>')
def get_status(environment):
    """Get deployment status for environment (always returns demo data)"""
    # Always return demo data, never check actual deployments
    resource_counts = monitor.get_resource_count(environment)
    costs = monitor.estimate_costs(environment)
    total_resources = sum(resource_counts.values()) if resource_counts else 0
    
    return jsonify({
        "environment": environment,
        "timestamp": datetime.now().isoformat(),
        "resource_counts": resource_counts,
        "total_resources": total_resources,
        "estimated_costs": costs,
        "status": "not_deployed",  # Always show as not deployed (demo mode)
        "demo_mode": True
    })

@app.route('/api/demo/<cloud>')
def get_demo_metrics_endpoint(cloud):
    """Get demo metrics for a specific cloud provider"""
    demo_metrics = monitor.get_demo_metrics(cloud)
    
    result = {
        "cloud": cloud,
        "timestamp": datetime.now().isoformat(),
        "environments": {}
    }
    
    for env in ["dev", "staging", "prod"]:
        env_resources = demo_metrics.get(env, {})
        total_resources = sum(env_resources.values())
        costs = monitor.estimate_costs(env, cloud)
        
        result["environments"][env] = {
            "environment": env,
            "resource_counts": env_resources,
            "total_resources": total_resources,
            "estimated_costs": costs,
            "status": "deployed"  # Show as deployed in demo
        }
    
    return jsonify(result)

@app.route('/api/deploy', methods=['POST'])
def trigger_deployment():
    """Trigger a new deployment"""
    data = request.json
    environment = data.get('environment')
    cloud = data.get('cloud', 'aws')
    
    # In production, this would queue a deployment job
    return jsonify({
        "message": f"Deployment to {cloud}/{environment} queued",
        "status": "queued"
    })

if __name__ == '__main__':
    import sys
    print("=" * 60)
    print("🚀 Starting Multi-Cloud Deployment Dashboard")
    print("=" * 60)
    print(f"📁 Project root: {PROJECT_ROOT}")
    print(f"🌐 Server will be available at:")
    print(f"   - http://localhost:5000")
    print(f"   - http://127.0.0.1:5000")
    print(f"   - http://0.0.0.0:5000")
    print("=" * 60)
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except OSError as e:
        if "Address already in use" in str(e) or "address is already in use" in str(e):
            print(f"❌ Error: Port 5000 is already in use.")
            print(f"   Try: ./stop.sh or kill the process using port 5000")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
