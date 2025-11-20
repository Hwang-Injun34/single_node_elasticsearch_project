#!/bin/bash
set -e

# ===============================
# 1. 환경 변수 파일 로드 부분 삭제 (수정됨)
# ===============================
# Docker Compose의 'env_file' 설정을 통해 이미 환경 변수가 주입되었습니다.
# source /path/to/secrets.env  <-- 이 줄을 주석 처리하거나 삭제했습니다.

# 기본값 설정 (만약 변수가 비어있을 경우를 대비)
ELASTIC_URL="http://localhost:9200"
ELASTIC_USERNAME=${ELASTIC_USERNAME:-elastic}

# ===============================
# Elasticsearch 준비 대기
# ===============================
echo "Waiting for Elasticsearch to be ready..."
until curl -s -u "$ELASTIC_USERNAME:$ELASTIC_PASSWORD" "$ELASTIC_URL/_cluster/health?wait_for_status=yellow" > /dev/null; do
  echo "Elasticsearch is unavailable - sleeping"
  sleep 5
done
echo "Elasticsearch is up and running!"

# ===============================
# kibana_system 사용자 비밀번호 설정
# ===============================
echo "Setting password for kibana_system user..."
curl -s -X PUT -u "$ELASTIC_USERNAME:$ELASTIC_PASSWORD" "$ELASTIC_URL/_security/user/kibana_system/_password" \
  -H "Content-Type: application/json" -d "
{
  \"password\": \"$KIBANA_PASSWORD\"
}
"
echo ""

# ===============================
# backend_user 존재 여부 확인 후 생성
# ===============================
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -u "$ELASTIC_USERNAME:$ELASTIC_PASSWORD" "$ELASTIC_URL/_security/user/backend_user")

if [ $STATUS_CODE -eq 404 ]; then
  echo "User backend_user does not exist. Creating..."
  curl -s -X PUT -u "$ELASTIC_USERNAME:$ELASTIC_PASSWORD" "$ELASTIC_URL/_security/user/backend_user" \
    -H "Content-Type: application/json" -d "
  {
    \"password\" : \"$BACKEND_USER_PASSWORD\",
    \"roles\" : [ \"superuser\" ],
    \"full_name\" : \"Backend Application User\"
  }
  "
  echo ""
  echo "User backend_user created."
else
  echo "User backend_user already exists. Skipping creation."
fi

echo "Elasticsearch user setup complete."