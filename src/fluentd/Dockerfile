FROM fluent/fluentd:v1.19.1-2.1

USER root

RUN apt-get update && apt-get install -y netcat-openbsd

# Force a specific version of the client gem
RUN gem install elasticsearch -v 8.15.0 --no-document
RUN gem install fluent-plugin-elasticsearch --no-document

USER fluent