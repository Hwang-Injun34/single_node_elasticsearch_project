#!/bin/sh

# 스크립트 실행 중 오류 발생 시 즉시 중단
set -e

echo "===== [Backend] 컨테이너 시작 스크립트 실행 ====="

# 1. Cron 작업 등록 및 Cron 데몬 백그라운드 실행
echo "=> Cron 작업을 등록하고, 데몬을 시작합니다."
crontab /app/crontab.txt
cron -f &

# 2. 애플리케이션 시작 전 필수 작업 실행
echo "=> Elasticsearch 인덱스 및 매핑을 확인/생성합니다."
PYTHONPATH=. python app/F11_search/ES5_index_manager.py

# 3. 로그 디렉토리 및 파일 준비
echo "=> 로그 디렉토리를 생성합니다."
mkdir -p /app/logs
touch /app/logs/reindexing.log

# 4. FastAPI 애플리케이션 실행 (컨테이너의 메인 프로세스)
echo "=> FastAPI 애플리케이션(uvicorn)을 시작합니다."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload