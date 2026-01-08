# Quick Start Guide - Fixing Connection Refused

If you're getting "ERR_CONNECTION_REFUSED" when accessing http://localhost:5000, follow these steps:

## Step 1: Stop any existing processes
```bash
./stop.sh
```

## Step 2: Diagnose the issue
```bash
./diagnose.sh
```

This will check:
- Python installation
- Virtual environment
- Flask installation
- App files
- Port availability

## Step 3: Start the server

### Option A: Foreground (see errors immediately)
```bash
./start_server.sh
```
This runs Flask in the foreground so you can see any errors. Press Ctrl+C to stop.

### Option B: Background (recommended)
```bash
./start_background.sh
```
This runs Flask in the background. Check logs with: `tail -f flask.log`

### Option C: Use the main start script
```bash
./start.sh
```

## Step 4: Verify it's running

1. Check if the process is running:
   ```bash
   ps aux | grep "python.*app.py" | grep -v grep
   ```

2. Check if port 5000 is listening:
   ```bash
   lsof -i :5000
   # or
   netstat -tuln | grep 5000
   ```

3. Check the logs:
   ```bash
   tail -f flask.log
   ```

## Troubleshooting

### Flask not installed
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Port 5000 already in use
```bash
./stop.sh
# Wait a moment, then try again
```

### Still not working?
1. Run `./diagnose.sh` to see what's wrong
2. Check `flask.log` for error messages
3. Try running in foreground: `./start_server.sh` to see errors

## Access the Dashboard

Once running, access at:
- http://localhost:5000
- http://127.0.0.1:5000

If using WSL2, make sure Windows Firewall isn't blocking the connection.
