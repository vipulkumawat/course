using DistributedLogging;

class Program
{
    static async Task Main(string[] args)
    {
        Console.WriteLine("🔷 Starting .NET logging demo...");
        
        var config = new DistributedLoggerConfig
        {
            Endpoint = Environment.GetEnvironmentVariable("LOG_ENDPOINT") ?? "http://localhost:5000/api/logs",
            ServiceName = Environment.GetEnvironmentVariable("SERVICE_NAME") ?? "dotnet-demo-service",
            ComponentName = "demo-app",
            BatchSize = 10,
            BatchTimeoutMs = 3000
        };
        
        using var logger = new DistributedLogger(config);
        var random = new Random();
        
        // Simulate application activity
        for (int i = 0; i < 100; i++)
        {
            var metadata = new Dictionary<string, object>
            {
                ["operation_id"] = i + 1,
                ["source_language"] = "dotnet"
            };
            
            var rand = random.NextDouble();
            
            if (rand < 0.1)
            {
                metadata["error_type"] = "simulation";
                logger.Error($"Simulated authentication error in operation {i + 1}", metadata);
            }
            else if (rand < 0.2)
            {
                metadata["memory_usage_mb"] = random.Next(200, 800);
                logger.Warning($"Warning: High memory allocation in operation {i + 1}", metadata);
            }
            else
            {
                metadata["cache_hit"] = random.NextDouble() > 0.3;
                logger.Info($"Successfully served request {i + 1}", metadata);
            }
            
            // Random custom events
            if (random.NextDouble() < 0.05)
            {
                var customData = new Dictionary<string, object>
                {
                    ["file_size_bytes"] = random.Next(1024, 1024000),
                    ["file_type"] = "pdf",
                    ["source_language"] = "dotnet"
                };
                logger.Custom("file_uploaded", customData);
            }
            
            await Task.Delay(random.Next(500, 2000));
        }
        
        Console.WriteLine($"📊 Final stats: {string.Join(", ", logger.GetStats().Select(kv => $"{kv.Key}: {kv.Value}"))}");
    }
}
