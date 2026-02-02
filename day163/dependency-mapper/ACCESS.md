# Accessing the Dashboard

## Services are running and listening on all interfaces (0.0.0.0)

### From Windows Browser:

**Option 1: Use localhost (WSL2 port forwarding)**
```
http://localhost:8000
```

**Option 2: Use WSL IP address**
```
http://172.17.32.19:8000
```

### From WSL/Linux:
```
http://localhost:8000
```

### WebSocket Connection:
- From Windows: `ws://localhost:8765` or `ws://172.17.32.19:8765`
- From WSL: `ws://localhost:8765`

## Troubleshooting ERR_CONNECTION_RESET:

1. **Check if services are running:**
   ```bash
   cd dependency-mapper
   bash run_services.sh
   ```

2. **Verify ports are listening:**
   ```bash
   netstat -tuln | grep -E ':(8000|8765)'
   ```
   Should show `0.0.0.0:8000` and `0.0.0.0:8765`

3. **Check Windows Firewall:**
   - Windows Firewall might be blocking the connection
   - Try temporarily disabling firewall to test

4. **WSL2 Port Forwarding:**
   - WSL2 should automatically forward localhost ports
   - If not working, try the direct IP address

5. **Restart services:**
   ```bash
   cd dependency-mapper
   ./stop.sh
   bash run_services.sh
   ```

## Current Status:
- ✅ HTTP Server: Running on 0.0.0.0:8000
- ✅ WebSocket Server: Running on 0.0.0.0:8765
- ✅ Both services accessible from Windows
