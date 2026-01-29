#!/bin/bash
echo 'WSL IP Address:'
wsl hostname -I | awk '{print }'
echo ''
echo 'Use this IP to access from Windows:'
echo 'Dashboard: http://:3000'
echo 'API: http://:8000'
