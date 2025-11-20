FROM docker.elastic.co/elasticsearch/elasticsearch:7.17.10

# 플러그인 설치
RUN /usr/share/elasticsearch/bin/elasticsearch-plugin install --batch analysis-nori

# Config 파일 복사
ADD ./config/userdict_ko.txt /usr/share/elasticsearch/config/
ADD ./config/synonym-set.txt /usr/share/elasticsearch/config/
ADD ./config/stopwords.txt /usr/share/elasticsearch/config/

# Entrypoint 및 init 스크립트 복사
COPY ./init-es.sh /usr/local/bin/init-es.sh
COPY ./docker-entrypoint-es.sh /usr/local/bin/docker-entrypoint-es.sh
RUN chmod +x /usr/local/bin/init-es.sh /usr/local/bin/docker-entrypoint-es.sh

# 권한 설정
RUN chown -R elasticsearch:elasticsearch /usr/share/elasticsearch/config \
    && chown -R elasticsearch:elasticsearch /usr/local/bin/init-es.sh \
    && chown -R elasticsearch:elasticsearch /usr/local/bin/docker-entrypoint-es.sh

# 컨테이너 실행 사용자 변경
USER elasticsearch

# Entry point
ENTRYPOINT ["/usr/local/bin/docker-entrypoint-es.sh"]
