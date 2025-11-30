FROM docker.elastic.co/elasticsearch/elasticsearch:8.11.0

# root 권한으로 플러그인 설치
USER root

RUN /usr/share/elasticsearch/bin/elasticsearch-plugin install --batch analysis-nori

# 설정 파일 복사
COPY --chown=elasticsearch:elasticsearch ./config/userdict_ko.txt /usr/share/elasticsearch/config/userdict_ko.txt
COPY --chown=elasticsearch:elasticsearch ./config/synonym-set.txt /usr/share/elasticsearch/config/synonym-set.txt
COPY --chown=elasticsearch:elasticsearch ./config/stopwords.txt /usr/share/elasticsearch/config/stopwords.txt

# init 및 entrypoint 스크립트 복사
COPY --chown=elasticsearch:elasticsearch --chmod=755 ./init-es.sh /usr/local/bin/init-es.sh
COPY --chown=elasticsearch:elasticsearch --chmod=755 ./docker-entrypoint-es.sh /usr/local/bin/docker-entrypoint-es.sh

# 실행 사용자 변경
USER elasticsearch

# Entry point
ENTRYPOINT ["/usr/local/bin/docker-entrypoint-es.sh"]
