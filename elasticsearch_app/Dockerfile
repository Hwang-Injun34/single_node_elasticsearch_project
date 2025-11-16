FROM docker.elastic.co/elasticsearch/elasticsearch:7.17.10

RUN /usr/share/elasticsearch/bin/elasticsearch-plugin install --batch analysis-nori

ADD ./config/userdict_ko.txt /usr/share/elasticsearch/config/
ADD ./config/synonym-set.txt /usr/share/elasticsearch/config/
ADD ./config/stopwords.txt /usr/share/elasticsearch/config/

COPY ./init-es.sh /usr/local/bin/init-es.sh
COPY ./docker-entrypoint-es.sh /usr/local/bin/docker-entrypoint-es.sh
RUN chmod +x /usr/local/bin/init-es.sh /usr/local/bin/docker-entrypoint-es.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint-es.sh"]