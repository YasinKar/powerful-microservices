FROM fluent/fluentd:latest

USER root
RUN apt-get update && apt-get install -y netcat-openbsd

RUN gem install fluent-plugin-elasticsearch

USER fluent