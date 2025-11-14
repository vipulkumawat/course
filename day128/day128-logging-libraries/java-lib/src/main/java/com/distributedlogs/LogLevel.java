package com.distributedlogs;

public enum LogLevel {
    DEBUG("DEBUG"),
    INFO("INFO"),
    WARNING("WARNING"),
    ERROR("ERROR"),
    CRITICAL("CRITICAL");
    
    private final String value;
    
    LogLevel(String value) {
        this.value = value;
    }
    
    public String getValue() {
        return value;
    }
}
