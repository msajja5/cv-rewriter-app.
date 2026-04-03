kill $(lsof -t -i :3000) 2>/dev/null || true
sleep 1
uvicorn main:app --host 0.0.0.0 --port 3000 > uvicorn.log 2>&1 &
sleep 2
