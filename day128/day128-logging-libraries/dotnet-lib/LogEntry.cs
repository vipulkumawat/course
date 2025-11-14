using System.Text.Json.Serialization;

namespace DistributedLogging
{
    public class LogEntry
    {
        [JsonPropertyName("timestamp")]
        public string Timestamp { get; set; } = DateTime.UtcNow.ToString("O");
        
        [JsonPropertyName("level")]
        public string Level { get; set; } = string.Empty;
        
        [JsonPropertyName("message")]
        public string Message { get; set; } = string.Empty;
        
        [JsonPropertyName("service")]
        public string Service { get; set; } = string.Empty;
        
        [JsonPropertyName("component")]
        public string Component { get; set; } = string.Empty;
        
        [JsonPropertyName("metadata")]
        public Dictionary<string, object> Metadata { get; set; } = new();
        
        [JsonPropertyName("request_id")]
        public string RequestId { get; set; } = Guid.NewGuid().ToString();
        
        [JsonPropertyName("session_id")]
        public string? SessionId { get; set; }
        
        [JsonPropertyName("user_id")]
        public string? UserId { get; set; }
        
        public LogEntry() { }
        
        public LogEntry(LogLevel level, string message, string service, string component, 
                       Dictionary<string, object>? metadata = null)
        {
            Level = level.ToStringValue();
            Message = message;
            Service = service;
            Component = component;
            Metadata = metadata ?? new Dictionary<string, object>();
        }
    }
}
