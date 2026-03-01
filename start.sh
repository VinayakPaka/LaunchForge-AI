#!/bin/bash
# LaunchForge AI — Start script
set -e

BASE_DIR="/mnt/efs/spaces/816c522e-4986-4150-9046-877cd4d0d500/09030478-659e-4f34-8572-199ae830e8c3/launchforge-ai"
LOG_DIR="/mnt/efs/spaces/816c522e-4986-4150-9046-877cd4d0d500/09030478-659e-4f34-8572-199ae830e8c3/logs"
mkdir -p "$LOG_DIR"

echo "=== Starting LaunchForge AI ==="

# 1. Start FastAPI backend on port 8001
echo "Starting FastAPI backend..."
cd "$BASE_DIR/apps/api"
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload > "$LOG_DIR/api.log" 2>&1 &
API_PID=$!
echo "FastAPI PID: $API_PID"
sleep 3

# 2. Start Next.js frontend on port 3000
echo "Starting Next.js frontend..."
cd "$BASE_DIR/apps/web"
nohup npm start > "$LOG_DIR/web.log" 2>&1 &
WEB_PID=$!
echo "Next.js PID: $WEB_PID"

echo ""
echo "=== LaunchForge AI started ==="
echo "  API  → http://localhost:8001"
echo "  Web  → https://tb314nms.run.complete.dev"
echo ""
echo "PIDs written to $LOG_DIR/pids.txt"
echo "$API_PID $WEB_PID" > "$LOG_DIR/pids.txt"
