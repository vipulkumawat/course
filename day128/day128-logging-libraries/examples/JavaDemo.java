import com.distributedlogs.DistributedLogger;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;

public class JavaDemo {
    public static void main(String[] args) throws InterruptedException {
        System.out.println("☕ Starting Java logging demo...");
        
        String endpoint = System.getenv().getOrDefault("LOG_ENDPOINT", "http://localhost:5000/api/logs");
        String serviceName = System.getenv().getOrDefault("SERVICE_NAME", "java-demo-service");
        
        DistributedLogger logger = new DistributedLogger(endpoint, serviceName, "demo-app");
        Random random = new Random();
        
        // Simulate application activity
        for (int i = 0; i < 100; i++) {
            Map<String, Object> metadata = new HashMap<>();
            metadata.put("operation_id", i + 1);
            metadata.put("source_language", "java");
            
            double rand = random.nextDouble();
            
            if (rand < 0.1) {
                metadata.put("error_type", "simulation");
                logger.error("Simulated database connection error in operation " + (i + 1), metadata);
            } else if (rand < 0.2) {
                metadata.put("disk_usage_percent", random.nextInt(30) + 70);
                logger.warning("Warning: High disk usage in operation " + (i + 1), metadata);
            } else {
                metadata.put("processing_time_ms", random.nextInt(400) + 50);
                logger.info("Successfully executed business logic " + (i + 1), metadata);
            }
            
            // Random custom events
            if (random.nextDouble() < 0.05) {
                Map<String, Object> customData = new HashMap<>();
                customData.put("transaction_id", "txn_" + (random.nextInt(1000) + 1));
                customData.put("amount", random.nextDouble() * 1000);
                customData.put("source_language", "java");
                logger.custom("payment_processed", customData);
            }
            
            Thread.sleep(random.nextInt(1500) + 500);
        }
        
        System.out.println("📊 Final stats: " + logger.getStats());
        logger.stop();
    }
}
