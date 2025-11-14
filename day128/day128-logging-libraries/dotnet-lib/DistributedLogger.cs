using System.Collections.Concurrent;
using System.Text;
using System.Text.Json;

namespace DistributedLogging
{
    public class DistributedLoggerConfig
    {
        public string Endpoint { get; set; } = "http://localhost:8080/api/logs";
        public string? ApiKey { get; set; }
        public string ServiceName { get; set; } = "unknown-service";
        public string ComponentName { get; set; } = "main";
        public int BatchSize { get; set; } = 100;
        public int BatchTimeoutMs { get; set; } = 5000;
        public int RetryAttempts { get; set; } = 3;
        public int RetryBackoffBaseMs { get; set; } = 1000;
    }
    
    public class LogBatch
    {
        public List<LogEntry> Entries { get; } = new();
        public DateTime CreatedAt { get; } = DateTime.UtcNow;
        public int MaxSize { get; }
        
        public LogBatch(int maxSize = 100)
        {
            MaxSize = maxSize;
        }
        
        public bool AddEntry(LogEntry entry)
        {
            Entries.Add(entry);
            return Entries.Count >= MaxSize;
        }
        
        public bool IsEmpty => Entries.Count == 0;
        public int Size => Entries.Count;
        
        public string ToJson()
        {
            return JsonSerializer.Serialize(Entries);
        }
    }
    
    public class DistributedLogger : IDisposable
    {
        private readonly DistributedLoggerConfig _config;
        private readonly HttpClient _httpClient;
        private readonly ConcurrentQueue<LogBatch> _batchQueue;
        private readonly Timer _batchTimer;
        private readonly CancellationTokenSource _cancellationTokenSource;
        private readonly Task _processingTask;
        
        private LogBatch _currentBatch;
        private DateTime _lastBatchTime;
        private readonly object _batchLock = new();
        
        // Statistics
        private long _logsSent = 0;
        private long _logsFailed = 0;
        private long _batchesSent = 0;
        private readonly List<string> _errors = new();
        
        public DistributedLogger(DistributedLoggerConfig config)
        {
            _config = config;
            _currentBatch = new LogBatch(config.BatchSize);
            _lastBatchTime = DateTime.UtcNow;
            _batchQueue = new ConcurrentQueue<LogBatch>();
            _cancellationTokenSource = new CancellationTokenSource();
            
            // Setup HTTP client
            _httpClient = new HttpClient();
            _httpClient.DefaultRequestHeaders.Add("Content-Type", "application/json");
            if (!string.IsNullOrEmpty(config.ApiKey))
            {
                _httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {config.ApiKey}");
            }
            
            // Start batch timeout timer
            _batchTimer = new Timer(CheckBatchTimeout, null, 
                                  TimeSpan.FromMilliseconds(config.BatchTimeoutMs),
                                  TimeSpan.FromMilliseconds(config.BatchTimeoutMs));
            
            // Start processing task
            _processingTask = Task.Run(ProcessBatches, _cancellationTokenSource.Token);
        }
        
        private void CheckBatchTimeout(object? state)
        {
            var currentTime = DateTime.UtcNow;
            
            lock (_batchLock)
            {
                if (!_currentBatch.IsEmpty && 
                    (currentTime - _lastBatchTime).TotalMilliseconds >= _config.BatchTimeoutMs)
                {
                    _batchQueue.Enqueue(_currentBatch);
                    _currentBatch = new LogBatch(_config.BatchSize);
                    _lastBatchTime = currentTime;
                }
            }
        }
        
        private async Task ProcessBatches()
        {
            while (!_cancellationTokenSource.Token.IsCancellationRequested)
            {
                try
                {
                    if (_batchQueue.TryDequeue(out var batch))
                    {
                        await SendBatch(batch);
                    }
                    else
                    {
                        await Task.Delay(100, _cancellationTokenSource.Token);
                    }
                }
                catch (OperationCanceledException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    _errors.Add($"Batch processing error: {ex.Message}");
                }
            }
        }
        
        private async Task SendBatch(LogBatch batch)
        {
            if (batch.IsEmpty) return;
            
            int retryCount = 0;
            
            while (retryCount < _config.RetryAttempts)
            {
                try
                {
                    var json = batch.ToJson();
                    var content = new StringContent(json, Encoding.UTF8, "application/json");
                    
                    var response = await _httpClient.PostAsync(_config.Endpoint, content);
                    
                    if (response.IsSuccessStatusCode)
                    {
                        Interlocked.Add(ref _logsSent, batch.Size);
                        Interlocked.Increment(ref _batchesSent);
                        return;
                    }
                }
                catch (Exception ex)
                {
                    if (retryCount >= _config.RetryAttempts - 1)
                    {
                        Interlocked.Add(ref _logsFailed, batch.Size);
                        _errors.Add($"Failed to send batch: {ex.Message}");
                        return;
                    }
                }
                
                retryCount++;
                var delay = _config.RetryBackoffBaseMs * Math.Pow(2, retryCount);
                await Task.Delay(TimeSpan.FromMilliseconds(delay), _cancellationTokenSource.Token);
            }
        }
        
        private LogEntry CreateLogEntry(LogLevel level, string message, 
                                      Dictionary<string, object>? metadata = null)
        {
            return new LogEntry(level, message, _config.ServiceName, _config.ComponentName, metadata);
        }
        
        private void AddLogEntry(LogEntry entry)
        {
            lock (_batchLock)
            {
                var batchFull = _currentBatch.AddEntry(entry);
                
                if (batchFull)
                {
                    _batchQueue.Enqueue(_currentBatch);
                    _currentBatch = new LogBatch(_config.BatchSize);
                    _lastBatchTime = DateTime.UtcNow;
                }
            }
        }
        
        public void Debug(string message, Dictionary<string, object>? metadata = null)
        {
            var entry = CreateLogEntry(LogLevel.Debug, message, metadata);
            AddLogEntry(entry);
        }
        
        public void Info(string message, Dictionary<string, object>? metadata = null)
        {
            var entry = CreateLogEntry(LogLevel.Info, message, metadata);
            AddLogEntry(entry);
        }
        
        public void Warning(string message, Dictionary<string, object>? metadata = null)
        {
            var entry = CreateLogEntry(LogLevel.Warning, message, metadata);
            AddLogEntry(entry);
        }
        
        public void Error(string message, Dictionary<string, object>? metadata = null)
        {
            var entry = CreateLogEntry(LogLevel.Error, message, metadata);
            AddLogEntry(entry);
        }
        
        public void Critical(string message, Dictionary<string, object>? metadata = null)
        {
            var entry = CreateLogEntry(LogLevel.Critical, message, metadata);
            AddLogEntry(entry);
        }
        
        public void Custom(string eventType, Dictionary<string, object> data)
        {
            var metadata = new Dictionary<string, object>(data) { ["event_type"] = eventType };
            var entry = CreateLogEntry(LogLevel.Info, $"Custom event: {eventType}", metadata);
            AddLogEntry(entry);
        }
        
        public Dictionary<string, object> GetStats()
        {
            return new Dictionary<string, object>
            {
                ["logs_sent"] = _logsSent,
                ["logs_failed"] = _logsFailed,
                ["batches_sent"] = _batchesSent,
                ["current_batch_size"] = _currentBatch.Size,
                ["queue_size"] = _batchQueue.Count,
                ["errors"] = _errors.ToArray()
            };
        }
        
        public void Dispose()
        {
            // Send remaining logs
            lock (_batchLock)
            {
                if (!_currentBatch.IsEmpty)
                {
                    _batchQueue.Enqueue(_currentBatch);
                }
            }
            
            _cancellationTokenSource.Cancel();
            _batchTimer?.Dispose();
            
            try
            {
                _processingTask.Wait(TimeSpan.FromSeconds(5));
            }
            catch (AggregateException) { }
            
            _httpClient?.Dispose();
            _cancellationTokenSource?.Dispose();
        }
    }
}
