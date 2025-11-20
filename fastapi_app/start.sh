#!/bin/sh

echo "===== [Backend] FastAPI 서버 시작 ====="

# 메인 애플리케이션 실행
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload