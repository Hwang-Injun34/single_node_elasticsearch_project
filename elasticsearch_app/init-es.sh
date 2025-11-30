#!/bin/bash
set -e

ELASTIC_URL="http://localhost:9200"

# ===============================
# Elasticsearch 준비 대기
# ===============================
echo "Waiting for Elasticsearch to be ready..."
until curl -s -u "$ELASTIC_USERNAME:$ELASTIC_PASSWORD" \
    "$ELASTIC_URL/_cluster/health?wait_for_status=yellow" > /dev/null; do
  echo "Elasticsearch is unavailable - sleeping"
  sleep 5
done
echo "Elasticsearch is up and running!"

# ===============================
# Kibana 사용자 존재 여부 확인 후 생성/비밀번호 설정
# ===============================
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -u "$ELASTIC_USERNAME:$ELASTIC_PASSWORD" \
  "$ELASTIC_URL/_security/user/$KIBANA_USERNAME")

if [ $STATUS_CODE -eq 404 ]; then
  echo "User $KIBANA_USERNAME does not exist. Creating..."
  curl -s -X POST -u "$ELASTIC_USERNAME:$ELASTIC_PASSWORD" \
    "$ELASTIC_URL/_security/user/$KIBANA_USERNAME" \
    -H "Content-Type: application/json" -d "
{
  \"password\" : \"$KIBANA_PASSWORD\",
  \"roles\" : [\"kibana_system\"],
  \"full_name\" : \"Kibana System User\"
}
"
  echo "User $KIBANA_USERNAME created."
else
  echo "User $KIBANA_USERNAME exists. Updating password..."
  curl -s -X PUT -u "$ELASTIC_USERNAME:$ELASTIC_PASSWORD" \
    "$ELASTIC_URL/_security/user/$KIBANA_USERNAME/_password" \
    -H "Content-Type: application/json" -d "
{
  \"password\" : \"$KIBANA_PASSWORD\"
}
"
fi

# ===============================
# Backend 사용자 존재 여부 확인 후 생성
# ===============================
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -u "$ELASTIC_USERNAME:$ELASTIC_PASSWORD" \
  "$ELASTIC_URL/_security/user/$BACKEND_USERNAME")

if [ $STATUS_CODE -eq 404 ]; then
  echo "User $BACKEND_USERNAME does not exist. Creating..."
  curl -s -X PUT -u "$ELASTIC_USERNAME:$ELASTIC_PASSWORD" \
    "$ELASTIC_URL/_security/user/$BACKEND_USERNAME" \
    -H "Content-Type: application/json" -d "
{
  \"password\" : \"$BACKEND_USER_PASSWORD\",
  \"roles\" : [ \"superuser\" ],
  \"full_name\" : \"Backend Application User\"
}
"
  echo "User $BACKEND_USERNAME created."
else
  echo "User $BACKEND_USERNAME already exists. Skipping creation."
fi

echo "Elasticsearch user setup complete."
