#!/bin/bash
set -e

# init-es.sh를 백그라운드로 실행
/usr/local/bin/init-es.sh &

# 원래 Elasticsearch entrypoint 실행
exec /usr/local/bin/docker-entrypoint.sh "$@"
