#!/bin/bash
set -e

# 1. 우리의 사용자 생성 스크립트를 백그라운드에서 실행합니다.
#    '&'는 스크립트를 백그라운드로 보내고, 즉시 다음 줄로 넘어가게 합니다.
#    스크립트 내부의 'until' 루프가 ES가 준비될 때까지 기다려 줄 것입니다.
/usr/local/bin/init-es.sh &

# 2. Elasticsearch의 원래 시작 스크립트를 실행합니다.
#    "$@"는 이 스크립트로 전달된 모든 인자(docker-compose가 전달하는 'es-docker' 등)를
#    그대로 원래 스크립트로 넘겨주는 역할을 합니다.
exec /usr/local/bin/docker-entrypoint.sh "$@"