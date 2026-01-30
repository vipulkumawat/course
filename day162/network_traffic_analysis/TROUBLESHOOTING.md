# Troubleshooting Connection Issues

## ERR_CONNECTION_RESET Fix

If you're getting `ERR_CONNECTION_RESET` when accessing from Windows:

### 1. Verify Services Are Running

From WSL, run:
```bash
cd /home/systemdr03/git/course/day162/network_traffic_analysis
ps aux | grep -E 'uvicorn|vite' | grep -v grep
```

Both `uvicorn` and `vite` processes should be running.

### 2. Check Ports Are Listening

```bash
ss -tuln | grep -E ':(8000|3000)'
```

You should see:
- `0.0.0.0:8000` for backend
- `0.0.0.0:3000` for frontend

### 3. Access URLs

**From Windows Browser:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

**From WSL:**
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

### 4. Restart Services

If services aren't running, use the startup script:

```bash
cd /home/systemdr03/git/course/day162/network_traffic_analysis
bash start_services.sh
```

### 5. Check Logs

```bash
# Backend logs
tail -f backend.log

# Frontend logs  
tail -f frontend.log
```

### 6. WSL2 Port Forwarding

WSL2 should automatically forward ports. If not working:

1. Check Windows Firewall isn't blocking ports 3000 and 8000
2. Try accessing via WSL IP address (shown in vite output)
3. Restart WSL: `wsl --shutdown` then restart

### 7. Common Issues

**Issue: Port already in use**
```bash
# Kill existing processes
pkill -f "uvicorn main:app"
pkill -f "vite"
```

**Issue: Services start but immediately stop**
- Check logs for errors
- Ensure virtual environment is activated
- Verify all dependencies are installed

**Issue: Connection reset from Windows**
- Ensure services are binding to `0.0.0.0` (not just `127.0.0.1`)
- Check Windows Firewall settings
- Try accessing from WSL first to verify services work

### 8. Manual Service Start

If the startup script doesn't work:

```bash
# Activate venv
source venv/bin/activate

# Start backend (in one terminal)
cd /home/systemdr03/git/course/day162/network_traffic_analysis
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend

# Start frontend (in another terminal)
cd /home/systemdr03/git/course/day162/network_traffic_analysis/frontend
npm run dev -- --host 0.0.0.0
```

### 9. Verify Backend Health

```bash
curl http://localhost:8000/api/health
```

Should return: `{"status":"healthy","timestamp":"..."}`

### 10. Verify Frontend

```bash
curl http://localhost:3000
```

Should return HTML content.
