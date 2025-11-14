package com.distributedlogs;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;

public class LogEntry {
    @JsonProperty("timestamp")
    @JsonFormat(shape = JsonFormat.Shape.STRING)
    private String timestamp;
    
    @JsonProperty("level")
    private String level;
    
    @JsonProperty("message")
    private String message;
    
    @JsonProperty("service")
    private String service;
    
    @JsonProperty("component")
    private String component;
    
    @JsonProperty("metadata")
    private Map<String, Object> metadata;
    
    @JsonProperty("request_id")
    private String requestId;
    
    @JsonProperty("session_id")
    private String sessionId;
    
    @JsonProperty("user_id")
    private String userId;
    
    public LogEntry() {}
    
    public LogEntry(LogLevel level, String message, String service, String component, 
                   Map<String, Object> metadata) {
        this.timestamp = Instant.now().toString();
        this.level = level.getValue();
        this.message = message;
        this.service = service;
        this.component = component;
        this.metadata = metadata;
        this.requestId = UUID.randomUUID().toString();
    }
    
    // Getters and setters
    public String getTimestamp() { return timestamp; }
    public void setTimestamp(String timestamp) { this.timestamp = timestamp; }
    
    public String getLevel() { return level; }
    public void setLevel(String level) { this.level = level; }
    
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
    
    public String getService() { return service; }
    public void setService(String service) { this.service = service; }
    
    public String getComponent() { return component; }
    public void setComponent(String component) { this.component = component; }
    
    public Map<String, Object> getMetadata() { return metadata; }
    public void setMetadata(Map<String, Object> metadata) { this.metadata = metadata; }
    
    public String getRequestId() { return requestId; }
    public void setRequestId(String requestId) { this.requestId = requestId; }
    
    public String getSessionId() { return sessionId; }
    public void setSessionId(String sessionId) { this.sessionId = sessionId; }
    
    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }
}
