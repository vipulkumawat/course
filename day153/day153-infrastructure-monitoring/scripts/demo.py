"""Demo script to showcase monitoring integration"""
import time
import random
import multiprocessing
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_cpu_load(duration=30):
    """Generate CPU load"""
    logger.info("Generating CPU load...")
    end_time = time.time() + duration
    while time.time() < end_time:
        _ = sum(i*i for i in range(10000))

def check_metrics():
    """Check if metrics are being collected"""
    try:
        response = requests.get('http://localhost:9090/api/v1/query?query=log_ingestion_rate', timeout=5)
        if response.status_code == 200:
            logger.info("✅ Prometheus is collecting metrics")
            return True
    except:
        pass
    return False

def check_dashboard():
    """Check if dashboard is accessible"""
    try:
        response = requests.get('http://localhost:5000/', timeout=5)
        if response.status_code == 200:
            logger.info("✅ Dashboard is accessible at http://localhost:5000")
            return True
    except:
        pass
    return False

def run_demo():
    """Run complete demo"""
    logger.info("🚀 Starting Day 153 Monitoring Integration Demo")
    logger.info("=" * 60)
    
    # Check services
    logger.info("\n1️⃣ Checking services...")
    time.sleep(2)
    
    if check_metrics():
        logger.info("   Prometheus: ✅ Running")
    else:
        logger.warning("   Prometheus: ⚠️  Not accessible")
    
    if check_dashboard():
        logger.info("   Dashboard: ✅ Running")
    else:
        logger.warning("   Dashboard: ⚠️  Not accessible")
    
    # Demonstrate correlation
    logger.info("\n2️⃣ Demonstrating CPU-Latency Correlation...")
    logger.info("   Generating high CPU load for 30 seconds...")
    
    processes = []
    for _ in range(4):
        p = multiprocessing.Process(target=generate_cpu_load, args=(30,))
        p.start()
        processes.append(p)
    
    logger.info("   Monitor dashboard at http://localhost:5000")
    logger.info("   You should see:")
    logger.info("   - CPU usage increase")
    logger.info("   - Processing latency increase")
    logger.info("   - Queue depth grow")
    logger.info("   - High correlation between CPU and latency")
    
    for p in processes:
        p.join()
    
    logger.info("\n3️⃣ Waiting for metrics to normalize...")
    time.sleep(15)
    
    logger.info("\n✅ Demo completed!")
    logger.info("\nAccess points:")
    logger.info("  - Dashboard: http://localhost:5000")
    logger.info("  - Prometheus: http://localhost:9090")
    logger.info("  - Grafana: http://localhost:3000 (admin/admin)")
    logger.info("\nTry:")
    logger.info("  - Run scripts/load_generator.py for sustained load")
    logger.info("  - Watch operator auto-scaling in K8s")
    logger.info("  - Explore correlations in Grafana")

if __name__ == '__main__':
    run_demo()
