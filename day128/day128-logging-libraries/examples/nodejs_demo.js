const { DistributedLogger } = require('../nodejs-lib');

async function main() {
    console.log('🟨 Starting Node.js logging demo...');
    
    const logger = new DistributedLogger({
        endpoint: process.env.LOG_ENDPOINT || 'http://localhost:5000/api/logs',
        serviceName: process.env.SERVICE_NAME || 'nodejs-demo-service',
        componentName: 'demo-app',
        batchSize: 10,
        batchTimeoutMs: 3000
    });
    
    logger.start();
    
    // Simulate application activity
    for (let i = 0; i < 100; i++) {
        const rand = Math.random();
        
        if (rand < 0.1) {
            logger.error(`Simulated error in operation ${i+1}`, {
                operation_id: i+1,
                error_type: 'simulation',
                source_language: 'nodejs'
            });
        } else if (rand < 0.2) {
            logger.warning(`Warning: High CPU usage in operation ${i+1}`, {
                operation_id: i+1,
                cpu_usage_percent: Math.floor(Math.random() * 40) + 60,
                source_language: 'nodejs'
            });
        } else {
            logger.info(`Successfully processed request ${i+1}`, {
                operation_id: i+1,
                response_time_ms: Math.floor(Math.random() * 500) + 10,
                source_language: 'nodejs'
            });
        }
        
        // Random custom events
        if (Math.random() < 0.05) {
            logger.custom('api_call', {
                endpoint: '/api/users',
                method: 'GET',
                status_code: 200,
                source_language: 'nodejs'
            });
        }
        
        await new Promise(resolve => setTimeout(resolve, Math.random() * 1500 + 500));
    }
    
    console.log('📊 Final stats:', logger.getStats());
    logger.stop();
}

main().catch(console.error);
