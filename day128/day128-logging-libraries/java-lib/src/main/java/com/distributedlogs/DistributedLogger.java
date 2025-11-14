package com.distributedlogs;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.hc.client5.http.async.methods.SimpleHttpRequest;
import org.apache.hc.client5.http.async.methods.SimpleHttpResponse;
import org.apache.hc.client5.http.classic.methods.HttpPost;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.http.ContentType;
import org.apache.hc.core5.http.io.entity.StringEntity;

import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;

public class DistributedLogger {
    private final String endpoint;
    private final String serviceName;
    private final String componentName;
    private final int batchSize;
    private final long batchTimeoutMs;
    private final CloseableHttpClient httpClient;
    private final ObjectMapper objectMapper;
    private final ScheduledExecutorService scheduler;
    private final ExecutorService workerPool;
    
    private final List<LogEntry> currentBatch;
    private final AtomicLong lastBatchTime;
    private final AtomicBoolean running;
    private final BlockingQueue<List<LogEntry>> batchQueue;
    
    // Statistics
    private final AtomicLong logsSent = new AtomicLong(0);
    private final AtomicLong logsFailed = new AtomicLong(0);
    private final AtomicLong batchesSent = new AtomicLong(0);
    
    public DistributedLogger(String endpoint, String serviceName, String componentName) {
        this(endpoint, serviceName, componentName, 100, 5000L);
    }
    
    public DistributedLogger(String endpoint, String serviceName, String componentName,
                           int batchSize, long batchTimeoutMs) {
        this.endpoint = endpoint;
        this.serviceName = serviceName;
        this.componentName = componentName;
        this.batchSize = batchSize;
        this.batchTimeoutMs = batchTimeoutMs;
        
        this.httpClient = HttpClients.createDefault();
        this.objectMapper = new ObjectMapper();
        this.scheduler = Executors.newScheduledThreadPool(2);
        this.workerPool = Executors.newFixedThreadPool(4);
        
        this.currentBatch = Collections.synchronizedList(new ArrayList<>());
        this.lastBatchTime = new AtomicLong(System.currentTimeMillis());
        this.running = new AtomicBoolean(false);
        this.batchQueue = new LinkedBlockingQueue<>();
        
        start();
    }
    
    public void start() {
        if (running.compareAndSet(false, true)) {
            // Start batch timeout checker
            scheduler.scheduleAtFixedRate(this::checkBatchTimeout, 
                                        batchTimeoutMs, batchTimeoutMs, TimeUnit.MILLISECONDS);
            
            // Start batch processor
            scheduler.execute(this::processBatches);
        }
    }
    
    public void stop() {
        running.set(false);
        
        // Send remaining logs
        if (!currentBatch.isEmpty()) {
            synchronized (currentBatch) {
                if (!currentBatch.isEmpty()) {
                    batchQueue.offer(new ArrayList<>(currentBatch));
                    currentBatch.clear();
                }
            }
        }
        
        scheduler.shutdown();
        workerPool.shutdown();
    }
    
    private void checkBatchTimeout() {
        long currentTime = System.currentTimeMillis();
        if (!currentBatch.isEmpty() && 
            (currentTime - lastBatchTime.get()) >= batchTimeoutMs) {
            
            synchronized (currentBatch) {
                if (!currentBatch.isEmpty()) {
                    batchQueue.offer(new ArrayList<>(currentBatch));
                    currentBatch.clear();
                    lastBatchTime.set(currentTime);
                }
            }
        }
    }
    
    private void processBatches() {
        while (running.get()) {
            try {
                List<LogEntry> batch = batchQueue.poll(100, TimeUnit.MILLISECONDS);
                if (batch != null) {
                    sendBatch(batch);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            } catch (Exception e) {
                System.err.println("Error processing batch: " + e.getMessage());
            }
        }
    }
    
    private void sendBatch(List<LogEntry> batch) {
        try {
            String json = objectMapper.writeValueAsString(batch);
            
            HttpPost request = new HttpPost(endpoint);
            request.setEntity(new StringEntity(json, ContentType.APPLICATION_JSON));
            
            httpClient.execute(request, response -> {
                if (response.getCode() == 200) {
                    logsSent.addAndGet(batch.size());
                    batchesSent.incrementAndGet();
                } else {
                    logsFailed.addAndGet(batch.size());
                    System.err.println("Failed to send batch, status: " + response.getCode());
                }
                return null;
            });
            
        } catch (Exception e) {
            logsFailed.addAndGet(batch.size());
            System.err.println("Error sending batch: " + e.getMessage());
        }
    }
    
    private void addLogEntry(LogEntry entry) {
        synchronized (currentBatch) {
            currentBatch.add(entry);
            
            if (currentBatch.size() >= batchSize) {
                batchQueue.offer(new ArrayList<>(currentBatch));
                currentBatch.clear();
                lastBatchTime.set(System.currentTimeMillis());
            }
        }
    }
    
    public void debug(String message, Map<String, Object> metadata) {
        LogEntry entry = new LogEntry(LogLevel.DEBUG, message, serviceName, componentName, metadata);
        addLogEntry(entry);
    }
    
    public void info(String message, Map<String, Object> metadata) {
        LogEntry entry = new LogEntry(LogLevel.INFO, message, serviceName, componentName, metadata);
        addLogEntry(entry);
    }
    
    public void warning(String message, Map<String, Object> metadata) {
        LogEntry entry = new LogEntry(LogLevel.WARNING, message, serviceName, componentName, metadata);
        addLogEntry(entry);
    }
    
    public void error(String message, Map<String, Object> metadata) {
        LogEntry entry = new LogEntry(LogLevel.ERROR, message, serviceName, componentName, metadata);
        addLogEntry(entry);
    }
    
    public void critical(String message, Map<String, Object> metadata) {
        LogEntry entry = new LogEntry(LogLevel.CRITICAL, message, serviceName, componentName, metadata);
        addLogEntry(entry);
    }
    
    public void custom(String eventType, Map<String, Object> data) {
        Map<String, Object> metadata = new HashMap<>(data);
        metadata.put("event_type", eventType);
        LogEntry entry = new LogEntry(LogLevel.INFO, "Custom event: " + eventType, 
                                    serviceName, componentName, metadata);
        addLogEntry(entry);
    }
    
    public Map<String, Object> getStats() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("logs_sent", logsSent.get());
        stats.put("logs_failed", logsFailed.get());
        stats.put("batches_sent", batchesSent.get());
        stats.put("current_batch_size", currentBatch.size());
        stats.put("queue_size", batchQueue.size());
        stats.put("running", running.get());
        return stats;
    }
}
